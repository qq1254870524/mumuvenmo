# -*- coding: utf-8 -*-
"""SOCKS5 代理池与 Profile 标识分配（qiang15/chong15/...）。

- 从 proxies/cocks5.txt 同时解析 SOCKS5 行与 change-ip 刷新链接
- 线程数 > 代理数时允许复用同一代理（round-robin）
- 同一 change-ip 链接默认 3 分钟只能刷新一次
- 刷新后等待 N 秒再测网络连通性，通了才继续登录

更新记录 2026-07-24:
- 增加 last_refresh_ts / 3 分钟限流
- 增加 refresh_and_wait_network（刷新→等待→连通性）
- 主机侧与设备侧网络探测
- 导入 NekoBox 前：主机经 SOCKS5 测连通；不通则刷 IP、等 10 秒后多次复测，通了才导入
- 2026-07-24 recycle: rebind(old_key,new_key) 删建模拟器后迁移 sticky SOCKS5 绑定
- 2026-07-25 reassign-atomic-v1:
  * reassign 换绑时整包切换 ProxyProfile（SOCKS5 + change-ip 刷新链接一体）
  * 有空闲代理时绝不抢占用中的 profile；仅线程数>代理数才允许 min(ref_count) 复用
  * change-ip HTTP 400 短退避重试；失败写短暂 cooldown，避免同 profile 并发打爆
- 2026-07-25 refresh-error-netcheck-v1: change_ip_error 后仍主机测 SOCKS5，通则可继续
- 2026-07-25 reassign-atomic-v2: reassign 返回前断言 change_ip_url 与 profile_name 成套
"""
from __future__ import annotations

import hashlib
import json
import re
import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.request import Request, urlopen

from paths import DATA_STATE_DIR, PROXY_FILE, ensure_under_root

PROFILE_RE = re.compile(r"\.([a-zA-Z]+\d+)_pp\b")
PROFILE_PATH_RE = re.compile(r"/([a-zA-Z]+\d+)_pp/")
CHANGE_IP_RE = re.compile(r"https?://\S*change-ip\S+", re.I)

# 默认：3 分钟限流、刷新后等 10 秒
DEFAULT_MIN_REFRESH_INTERVAL = 180.0
DEFAULT_REFRESH_WAIT_SECONDS = 10.0
DEFAULT_REFRESH_STATE_FILE = DATA_STATE_DIR / "proxy_refresh_state.json"
DEFAULT_NETWORK_CHECK_URLS = (
    "http://connectivitycheck.gstatic.com/generate_204",
    "http://www.gstatic.com/generate_204",
    "http://clients3.google.com/generate_204",
)

OptionalCheckFn = Optional[Callable[[], bool]]
OptionalStop = Optional[threading.Event]


@dataclass
class ProxyProfile:
    host: str
    port: int
    username: str
    password: str
    profile_name: str  # qiang15 / chong15 ...
    raw: str = ""
    change_ip_url: str = ""
    ref_count: int = 0  # 当前被多少 worker 引用（复用计数）
    last_refresh_ts: float = 0.0  # 上次成功触发 change-ip 的时间戳
    last_refresh_body: str = ""

    @property
    def endpoint(self) -> str:
        return f"{self.host}:{self.port}"

    def masked(self) -> str:
        return (
            f"{self.profile_name}@{self.host}:{self.port} "
            f"user={self.username[:8]}*** refs={self.ref_count}"
        )


def parse_proxy_line(line: str) -> Optional[ProxyProfile]:
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    # GUI 持久化格式为 proxy|change-ip-url；这里只解析左侧 SOCKS5。
    if "|" in raw:
        raw = raw.split("|", 1)[0].strip()
    # 跳过刷新链接行
    if raw.lower().startswith("http://") or raw.lower().startswith("https://"):
        return None
    if "change-ip" in raw.lower():
        return None
    parts = raw.split(":")
    if len(parts) < 4:
        return None
    host = parts[0]
    # host 不应是 http
    if "/" in host or not host[0].isdigit() and "." not in host:
        # 允许域名
        if not re.match(r"^[A-Za-z0-9._-]+$", host):
            return None
    try:
        port = int(parts[1])
    except ValueError:
        return None
    username = parts[2]
    password = ":".join(parts[3:])
    m = PROFILE_RE.search(username)
    if m:
        profile = m.group(1)
    else:
        # 普通用户名不含 xxx_pp 时生成稳定短名，避免不同 endpoint 同名互相去重。
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10]
        profile = f"proxy_{digest}"
    return ProxyProfile(
        host=host,
        port=port,
        username=username,
        password=password,
        profile_name=profile,
        raw=raw,
    )


def parse_proxy_pair_line(line: str) -> tuple[str, str] | None:
    """解析 GUI 的 ``host:port:user:password|change-url`` 单行格式。"""
    raw = str(line or "").strip()
    if not raw or raw.startswith("#") or "|" not in raw:
        return None
    proxy_text, change_url = raw.split("|", 1)
    proxy_text = proxy_text.strip()
    change_url = change_url.strip()
    if not parse_proxy_line(proxy_text):
        return None
    if not re.match(r"^https?://\S+$", change_url, re.I):
        return None
    return proxy_text, change_url


def parse_change_ip_line(line: str) -> tuple[str, str] | None:
    """返回 (profile_name, url) 或 None。"""
    raw = line.strip()
    if not raw or raw.startswith("#"):
        return None
    m = CHANGE_IP_RE.search(raw)
    if not m:
        return None
    url = m.group(0).rstrip("),];'\"")
    pm = PROFILE_PATH_RE.search(url)
    if not pm:
        # 也兼容 username 形式
        pm = re.search(r"([a-zA-Z]+\d+)_pp", url)
    if not pm:
        return None
    return pm.group(1), url


def load_change_ip_map(text_or_path: str | Path) -> dict[str, str]:
    """从文件或文本解析 change-ip 链接，按 profile 名映射。"""
    path = Path(str(text_or_path))
    if path.exists() and path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        text = str(text_or_path)
    mapping: dict[str, str] = {}
    for line in text.splitlines():
        item = parse_change_ip_line(line)
        if item:
            mapping[item[0]] = item[1]
    return mapping


def load_proxy_entries(path: str | Path | None = None) -> list[tuple[str, str]]:
    """按 GUI 行加载 ``(SOCKS5, 刷新链接)``，兼容旧版分段文件。"""
    p = ensure_under_root(path or PROXY_FILE)
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8", errors="replace")
    legacy_change_map = load_change_ip_map(text)
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in text.splitlines():
        pair = parse_proxy_pair_line(line)
        if pair:
            proxy_text, change_url = pair
            item = parse_proxy_line(proxy_text)
        else:
            item = parse_proxy_line(line)
            if not item:
                continue
            proxy_text = item.raw
            change_url = legacy_change_map.get(item.profile_name, "")
        if not item or item.profile_name in seen:
            continue
        seen.add(item.profile_name)
        out.append((proxy_text, change_url))
    return out


def save_proxy_entries(
    entries: list[tuple[str, str]],
    path: str | Path | None = None,
) -> int:
    """校验并原子保存 GUI 代理池；每个 SOCKS5 与自己的刷新链接同一行。"""
    p = ensure_under_root(path or PROXY_FILE)
    clean: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row_no, (proxy_text, change_url) in enumerate(entries, 1):
        proxy_text = str(proxy_text or "").strip()
        change_url = str(change_url or "").strip()
        if not proxy_text and not change_url:
            continue
        item = parse_proxy_line(proxy_text)
        if item is None:
            raise ValueError(
                f"第 {row_no} 行 SOCKS5 格式错误，应为 host:port:username:password"
            )
        if not re.match(r"^https?://\S+$", change_url, re.I):
            raise ValueError(f"第 {row_no} 行刷新链接必须是完整 http/https URL")
        if item.profile_name in seen:
            raise ValueError(f"第 {row_no} 行与前面的 SOCKS5 重复")
        seen.add(item.profile_name)
        clean.append((item.raw, change_url))
    if not clean:
        raise ValueError("代理池至少需要一套 SOCKS5 和刷新链接")
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    body = "# GUI SOCKS5代理池：每行 SOCKS5|刷新链接\n"
    body += "\n".join(f"{proxy}|{url}" for proxy, url in clean) + "\n"
    tmp.write_text(body, encoding="utf-8")
    tmp.replace(p)
    return len(clean)


def load_proxies(path: str | Path | None = None) -> list[ProxyProfile]:
    """加载 SOCKS5，并自动挂上同文件中的 change-ip。"""
    out: list[ProxyProfile] = []
    seen: set[str] = set()
    for proxy_text, change_url in load_proxy_entries(path):
        item = parse_proxy_line(proxy_text)
        if not item:
            continue
        # 去重：同 profile 只保留第一条
        if item.profile_name in seen:
            continue
        seen.add(item.profile_name)
        item.change_ip_url = change_url
        out.append(item)
    return out


def check_host_network(
    urls: tuple[str, ...] | list[str] | None = None,
    timeout: float = 8.0,
) -> bool:
    """主机侧连通性探测（不经 SOCKS）。用于刷新后粗检。"""
    targets = list(urls or DEFAULT_NETWORK_CHECK_URLS)
    for url in targets:
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "*/*",
                },
            )
            with urlopen(req, timeout=timeout) as resp:
                code = getattr(resp, "status", None) or resp.getcode()
                # 204 / 200 都算通
                if int(code) in (200, 204):
                    return True
        except Exception:
            continue
    return False


def check_socks5_proxy_host(
    host: str,
    port: int,
    username: str = "",
    password: str = "",
    *,
    timeout: float = 10.0,
    dest_host: str = "connectivitycheck.gstatic.com",
    dest_port: int = 80,
) -> bool:
    """主机侧经 SOCKS5 代理探测连通性（TCP CONNECT + 可选 HTTP 204）。

    用于导入 NekoBox 配置前确认代理可用；不依赖第三方库。
    """
    if not host or not port:
        return False
    sock = None
    try:
        sock = socket.create_connection((str(host), int(port)), timeout=float(timeout))
        sock.settimeout(float(timeout))
        user = (username or "").encode("utf-8")
        pwd = (password or "").encode("utf-8")
        if user:
            sock.sendall(b"\x05\x01\x02")
        else:
            sock.sendall(b"\x05\x01\x00")
        resp = sock.recv(2)
        if len(resp) < 2 or resp[0] != 5:
            return False
        method = resp[1]
        if method == 0xFF:
            return False
        if method == 2:
            if len(user) > 255 or len(pwd) > 255:
                return False
            sock.sendall(bytes([1, len(user)]) + user + bytes([len(pwd)]) + pwd)
            auth = sock.recv(2)
            if len(auth) < 2 or auth[1] != 0:
                return False
        elif method != 0:
            return False
        try:
            dest = dest_host.encode("idna")
        except Exception:
            dest = dest_host.encode("ascii", errors="ignore")
        if not dest or len(dest) > 255:
            return False
        req = (
            b"\x05\x01\x00\x03"
            + bytes([len(dest)])
            + dest
            + struct.pack("!H", int(dest_port))
        )
        sock.sendall(req)
        hdr = sock.recv(4)
        if len(hdr) < 4 or hdr[0] != 5 or hdr[1] != 0:
            return False
        atyp = hdr[3]
        if atyp == 1:
            rest = sock.recv(4 + 2)
            if len(rest) < 6:
                return False
        elif atyp == 3:
            ln = sock.recv(1)
            if not ln:
                return False
            rest = sock.recv(ln[0] + 2)
            if len(rest) < ln[0] + 2:
                return False
        elif atyp == 4:
            rest = sock.recv(16 + 2)
            if len(rest) < 18:
                return False
        else:
            return False
        try:
            http = (
                "GET /generate_204 HTTP/1.1\r\n"
                f"Host: {dest_host}\r\n"
                "User-Agent: Mozilla/5.0\r\n"
                "Connection: close\r\n\r\n"
            ).encode("ascii")
            sock.sendall(http)
            data = sock.recv(256) or b""
            if data:
                head = data.split(b"\r\n", 1)[0].decode("latin-1", errors="replace")
                if " 204" in head or " 200" in head or head.startswith("HTTP/"):
                    return True
        except Exception:
            pass
        return True
    except Exception:
        return False
    finally:
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass


def check_proxy_profile_host(
    profile: "ProxyProfile",
    *,
    timeout: float = 10.0,
) -> bool:
    """对 ProxyProfile 做主机侧 SOCKS5 连通检测。"""
    if profile is None:
        return False
    return check_socks5_proxy_host(
        profile.host,
        int(profile.port),
        profile.username or "",
        profile.password or "",
        timeout=timeout,
    )


def check_device_network(adb, timeout: int = 12) -> bool:
    """模拟器内网络探测（经 NekoBox 时更能反映登录路径）。

    adb 需提供 shell(*args, timeout=...) -> str。
    """
    if adb is None:
        return False
    probes = [
        ("ping -c 1 -W 3 8.8.8.8", ("bytes from", "1 received", "1 packets received")),
        (
            "curl -s -o /dev/null -w %{http_code} --connect-timeout 5 "
            "http://connectivitycheck.gstatic.com/generate_204",
            ("204", "200"),
        ),
        (
            "wget -q -O - --timeout=5 http://connectivitycheck.gstatic.com/generate_204; echo OK",
            ("OK",),
        ),
    ]
    for cmd, needles in probes:
        try:
            out = (adb.shell(cmd, timeout=timeout) or "").strip()
        except Exception:
            continue
        low = out.lower()
        for n in needles:
            if n.lower() in low:
                return True
        # ping 有时只有 "1 packets transmitted" 无 received
        if "ttl=" in low and "from" in low:
            return True
    return False


class ProxyPool:
    def __init__(
        self,
        proxies: list[ProxyProfile] | None = None,
        min_refresh_interval_seconds: float = DEFAULT_MIN_REFRESH_INTERVAL,
        refresh_wait_seconds: float = DEFAULT_REFRESH_WAIT_SECONDS,
        persist_refresh_state: bool = True,
    ):
        self._lock = threading.RLock()
        self.proxies = list(proxies or [])
        self._rr = 0
        self._assigned: dict[str, ProxyProfile] = {}  # worker_key -> proxy
        self.allow_reuse = True  # 线程超过代理数时允许复用
        self.min_refresh_interval_seconds = float(min_refresh_interval_seconds)
        self.refresh_wait_seconds = float(refresh_wait_seconds)
        self.persist_refresh_state = bool(persist_refresh_state)
        self.refresh_state_path = ensure_under_root(DEFAULT_REFRESH_STATE_FILE)
        self._refresh_state: dict[str, dict] = self._load_refresh_state()
        self._apply_refresh_state(self.proxies)
        # change-ip URL 指纹 -> 刷新互斥，避免同链接并发刷
        self._refresh_locks: dict[str, threading.Lock] = {}

    @staticmethod
    def _refresh_state_key(profile: ProxyProfile) -> str:
        url = str(getattr(profile, "change_ip_url", "") or "").strip()
        if not url:
            return ""
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _load_refresh_state(self) -> dict[str, dict]:
        if not self.persist_refresh_state or not self.refresh_state_path.exists():
            return {}
        try:
            raw = json.loads(self.refresh_state_path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except Exception:
            return {}

    def _apply_refresh_state(self, profiles: list[ProxyProfile]) -> None:
        now = time.time()
        for profile in profiles:
            key = self._refresh_state_key(profile)
            state = self._refresh_state.get(key) if key else None
            if not isinstance(state, dict):
                continue
            try:
                ts = float(state.get("last_refresh_ts") or 0.0)
            except Exception:
                ts = 0.0
            # 只需跨重载/重启保留 3 分钟窗口；丢弃未来时间或一天前的陈旧数据。
            if 0.0 < ts <= now + 60.0 and now - ts < 86400.0:
                profile.last_refresh_ts = max(profile.last_refresh_ts, ts)
                profile.last_refresh_body = str(state.get("last_refresh_body") or "")[:200]

    def _persist_refresh_state(self, profile: ProxyProfile) -> None:
        if not self.persist_refresh_state:
            return
        key = self._refresh_state_key(profile)
        if not key:
            return
        now = time.time()
        with self._lock:
            self._refresh_state[key] = {
                "last_refresh_ts": float(profile.last_refresh_ts or 0.0),
                "last_refresh_body": str(profile.last_refresh_body or "")[:200],
            }
            kept: dict[str, dict] = {}
            for state_key, state_value in self._refresh_state.items():
                if not isinstance(state_value, dict):
                    continue
                try:
                    state_ts = float(state_value.get("last_refresh_ts") or 0.0)
                except Exception:
                    continue
                if 0.0 <= now - state_ts < 86400.0:
                    kept[state_key] = state_value
            self._refresh_state = kept
            self.refresh_state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.refresh_state_path.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(self._refresh_state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            tmp.replace(self.refresh_state_path)

    def _profile_lock(self, profile_name: str) -> threading.Lock:
        with self._lock:
            lk = self._refresh_locks.get(profile_name)
            if lk is None:
                lk = threading.Lock()
                self._refresh_locks[profile_name] = lk
            return lk

    def configure(
        self,
        min_refresh_interval_seconds: float | None = None,
        refresh_wait_seconds: float | None = None,
    ) -> None:
        with self._lock:
            if min_refresh_interval_seconds is not None:
                self.min_refresh_interval_seconds = float(min_refresh_interval_seconds)
            if refresh_wait_seconds is not None:
                self.refresh_wait_seconds = float(refresh_wait_seconds)

    def load_file(self, path: str | Path | None = None) -> int:
        with self._lock:
            old_state = {
                self._refresh_state_key(p): (p.last_refresh_ts, p.last_refresh_body)
                for p in self.proxies
                if self._refresh_state_key(p)
            }
            self.proxies = load_proxies(path)
            self._refresh_state = self._load_refresh_state()
            self._apply_refresh_state(self.proxies)
            for p in self.proxies:
                old = old_state.get(self._refresh_state_key(p))
                if old and old[0] > p.last_refresh_ts:
                    p.last_refresh_ts, p.last_refresh_body = old
            self._rr = 0
            # 不强制清 assignment，避免运行中丢 profile；调用方可 release
            return len(self.proxies)

    def attach_change_ip(self, mapping: dict[str, str]) -> None:
        with self._lock:
            for p in self.proxies:
                if p.profile_name in mapping and mapping[p.profile_name]:
                    p.change_ip_url = mapping[p.profile_name]
            self._apply_refresh_state(self.proxies)

    def names(self) -> list[str]:
        with self._lock:
            return [p.profile_name for p in self.proxies]

    def stats(self) -> dict:
        with self._lock:
            now = time.time()
            return {
                "total": len(self.proxies),
                "assigned_workers": len(self._assigned),
                "names": [p.profile_name for p in self.proxies],
                "refs": {p.profile_name: p.ref_count for p in self.proxies},
                "with_change_ip": sum(1 for p in self.proxies if p.change_ip_url),
                "min_refresh_interval_seconds": self.min_refresh_interval_seconds,
                "refresh_wait_seconds": self.refresh_wait_seconds,
                "last_refresh_age": {
                    p.profile_name: (
                        None if p.last_refresh_ts <= 0 else round(now - p.last_refresh_ts, 1)
                    )
                    for p in self.proxies
                },
            }

    def assign(self, worker_key: str) -> Optional[ProxyProfile]:
        """为 worker/模拟器分配 profile。

        策略：
        1. 已分配则复用同一绑定
        2. 优先 ref_count==0 的空闲代理
        3. 无空闲且 allow_reuse=True 时，按 round-robin 复用（线程>代理数）
        """
        with self._lock:
            if worker_key in self._assigned:
                return self._assigned[worker_key]
            if not self.proxies:
                return None

            free = [p for p in self.proxies if p.ref_count <= 0]
            if free:
                # 稳定顺序取第一个空闲
                p = free[0]
            elif self.allow_reuse:
                p = self.proxies[self._rr % len(self.proxies)]
                self._rr += 1
            else:
                return None

            p.ref_count += 1
            self._assigned[worker_key] = p
            return p

    def rebind(self, old_key: str, new_key: str) -> Optional[ProxyProfile]:
        """将 sticky 绑定从 old_key 迁移到 new_key，保持同一 SOCKS5/刷新链接。

        模拟器删建后 worker_key 从 vm-{old} 变为 vm-{new}，但代理会话不变。
        ref_count 只迁移不增减。
        """
        with self._lock:
            if not old_key and not new_key:
                return None
            if old_key == new_key:
                return self._assigned.get(old_key)
            p = self._assigned.pop(old_key, None) if old_key else None
            if p is None:
                # 旧 key 无绑定：直接给新 key 分配
                if new_key:
                    # 临时释放锁外再 assign 会重入 RLock，这里内联
                    if new_key in self._assigned:
                        return self._assigned[new_key]
                    if not self.proxies:
                        return None
                    free = [x for x in self.proxies if x.ref_count <= 0]
                    if free:
                        p2 = free[0]
                    elif self.allow_reuse:
                        p2 = self.proxies[self._rr % len(self.proxies)]
                        self._rr += 1
                    else:
                        return None
                    p2.ref_count += 1
                    self._assigned[new_key] = p2
                    return p2
                return None
            # 若 new_key 已有其它绑定，先释放其引用
            if new_key:
                prev = self._assigned.pop(new_key, None)
                if prev is not None and prev is not p:
                    prev.ref_count = max(0, prev.ref_count - 1)
                self._assigned[new_key] = p
            else:
                # 无新 key：等同 release
                p.ref_count = max(0, p.ref_count - 1)
            return p

    def release(self, worker_key: str) -> None:
        with self._lock:
            p = self._assigned.pop(worker_key, None)
            if p is not None:
                p.ref_count = max(0, p.ref_count - 1)

    def reassign(
        self,
        worker_key: str,
        exclude_names: set[str] | list[str] | None = None,
    ) -> Optional[ProxyProfile]:
        """换绑到另一个 ProxyProfile 整包（SOCKS5 + change-ip 刷新链接一体切换）。

        用户规则：qiang15 不通并刷 IP 仍失败时，可轮到 chong15；
        轮换时刷新链接必须跟着 profile 一起更换，禁止旧 SOCKS5 + 新 change-ip 错配。

        选择策略：
        1. 优先 ref_count==0 且不在 exclude 的空闲代理
        2. 无空闲：allow_reuse 时选 ref_count 最小且不在 exclude（可临时复用）
        3. 找到目标后才释放旧绑定；返回对象自带对应 change_ip_url
        """
        exclude = {str(x) for x in (exclude_names or []) if str(x)}
        with self._lock:
            if not self.proxies:
                return None
            ordered = list(self.proxies)
            old = self._assigned.get(worker_key)

            free = [
                p
                for p in ordered
                if p.ref_count <= 0 and p.profile_name not in exclude
            ]
            if free:
                p = free[0]
            elif self.allow_reuse:
                candidates = [x for x in ordered if x.profile_name not in exclude]
                if not candidates:
                    # 全被 exclude：从非 old 里兜底，避免彻底卡死
                    candidates = [x for x in ordered if x is not old]
                if not candidates:
                    return None
                min_ref = min(x.ref_count for x in candidates)
                lowest = [x for x in candidates if x.ref_count == min_ref]
                p = lowest[self._rr % len(lowest)]
                self._rr += 1
            else:
                return None

            if old is p:
                return old

            # 确认新目标后再释放旧绑定（整包切换 SOCKS5+change-ip）
            if old is not None:
                old.ref_count = max(0, old.ref_count - 1)
            p.ref_count += 1
            self._assigned[worker_key] = p
            # 成套校验：轮到 chong15 时刷新链接必须是 chong15 的，禁止残留 qiang15 链接
            if p.change_ip_url and p.profile_name and p.profile_name not in p.change_ip_url:
                # 尝试从池内同名映射修复（不应发生；防御）
                for other in self.proxies:
                    if other.profile_name == p.profile_name and other.change_ip_url and p.profile_name in other.change_ip_url:
                        p.change_ip_url = other.change_ip_url
                        break
            return p

    def remaining_refresh_seconds(
        self,
        profile: ProxyProfile,
        min_interval_seconds: float | None = None,
    ) -> float:
        """距下次允许刷新还剩多少秒；0 表示可刷新。"""
        interval = float(
            self.min_refresh_interval_seconds
            if min_interval_seconds is None
            else min_interval_seconds
        )
        if interval <= 0 or profile.last_refresh_ts <= 0:
            return 0.0
        elapsed = time.time() - profile.last_refresh_ts
        left = interval - elapsed
        return max(0.0, left)

    def can_refresh(
        self,
        profile: ProxyProfile,
        min_interval_seconds: float | None = None,
    ) -> tuple[bool, float]:
        """返回 (是否可刷新, 剩余秒数)。无 change-ip 视为不可刷新。"""
        if not profile.change_ip_url:
            return False, 0.0
        left = self.remaining_refresh_seconds(profile, min_interval_seconds)
        return left <= 0.0, left


    # 2026-07-24 reassign-v1: 失败代理可换绑其他 profile
# 2026-07-24 post-refresh-multi-check-v1: 刷IP后多轮主机SOCKS5检测
    def ensure_ready_before_import(
        self,
        profile: ProxyProfile,
        *,
        wait_seconds: float | None = None,
        min_interval_seconds: float | None = None,
        check_timeout: float = 10.0,
        max_refresh_rounds: int = 1,
        post_check_rounds: int | None = None,
        post_check_gap_seconds: float | None = None,
        stop_event: OptionalStop = None,
        force_refresh: bool = False,
    ) -> dict:
        """导入代理配置前：主机经 SOCKS5 测连通。

        流程:
        - 主机经 SOCKS5 检测
        - 不通且有 change-ip: 刷新 -> 等 wait_seconds(默认10s) -> 多次检测
        - 通了才 ok=True，调用方才应导入 NekoBox 配置
        """
        wait_sec = float(
            self.refresh_wait_seconds if wait_seconds is None else wait_seconds
        )
        interval = float(
            self.min_refresh_interval_seconds
            if min_interval_seconds is None
            else min_interval_seconds
        )
        post_checks = max(
            1,
            int(
                getattr(self, "post_refresh_check_rounds", 3)
                if post_check_rounds is None
                else post_check_rounds
            ),
        )
        post_gap = max(
            0.0,
            float(
                getattr(self, "post_refresh_check_gap", 5.0)
                if post_check_gap_seconds is None
                else post_check_gap_seconds
            ),
        )
        result: dict = {
            "ok": False,
            "status": "unknown",
            "proxy_ok": False,
            "proxy_ok_before": False,
            "refreshed": False,
            "refresh_body": "",
            "waited": 0.0,
            "remaining_seconds": 0.0,
            "checks": 0,
            "profile": profile.profile_name if profile else "",
            "endpoint": profile.endpoint if profile else "",
        }
        if profile is None:
            result["status"] = "no_proxy"
            return result

        def _stopped() -> bool:
            return stop_event is not None and stop_event.is_set()

        def _check() -> bool:
            result["checks"] = int(result["checks"]) + 1
            return check_proxy_profile_host(profile, timeout=check_timeout)

        def _post_refresh_checks(
            success_status: str,
            failure_status: str,
        ) -> bool:
            """刷新请求后先等 wait_sec，再按 post_gap 做多次 SOCKS5 检查。"""
            waited = self._interruptible_sleep(wait_sec, stop_event=stop_event)
            result["waited"] = float(result.get("waited") or 0.0) + waited
            if _stopped():
                result["status"] = "stopped"
                return False
            for ci in range(post_checks):
                if _stopped():
                    result["status"] = "stopped"
                    return False
                ok_after = _check()
                result["proxy_ok"] = ok_after
                result["post_check_index"] = ci
                if ok_after:
                    result["ok"] = True
                    result["status"] = success_status
                    return True
                if ci + 1 < post_checks:
                    waited_more = self._interruptible_sleep(
                        post_gap,
                        stop_event=stop_event,
                    )
                    result["waited"] = (
                        float(result.get("waited") or 0.0) + waited_more
                    )
            result["ok"] = False
            result["status"] = failure_status
            return False

        if _stopped():
            result["status"] = "stopped"
            return result

        ok = _check()
        result["proxy_ok_before"] = ok
        result["proxy_ok"] = ok
        if ok:
            result["ok"] = True
            result["status"] = "already_ok"
            return result

        rounds = max(0, int(max_refresh_rounds))
        if rounds <= 0 or not profile.change_ip_url:
            result["status"] = (
                "proxy_down_no_refresh"
                if not profile.change_ip_url
                else "proxy_down"
            )
            result["ok"] = False
            return result

        for i in range(rounds):
            if _stopped():
                result["status"] = "stopped"
                return result
            body = self.refresh_ip(
                profile,
                min_interval_seconds=interval,
                force=force_refresh and i == 0,
                mark_timestamp=True,
            )
            result["refresh_body"] = body
            if body.startswith("rate_limited:"):
                result["status"] = "rate_limited"
                try:
                    result["remaining_seconds"] = float(
                        body.split(":", 1)[1].rstrip("s")
                    )
                except Exception:
                    result["remaining_seconds"] = self.remaining_refresh_seconds(
                        profile, interval
                    )
                _post_refresh_checks("ok_while_rate_limited", "rate_limited")
                return result
            if body.startswith("change_ip_error:"):
                result["status"] = "refresh_error"
                _post_refresh_checks("ok_after_refresh_error", "refresh_error")
                return result

            result["refreshed"] = True
            if _post_refresh_checks("refreshed_ok", "proxy_down_after_refresh"):
                return result
            if _stopped():
                return result

        result["ok"] = False
        result["status"] = "proxy_down_after_refresh"
        return result

    def refresh_ip(
        self,
        profile: ProxyProfile,
        timeout: int = 20,
        *,
        min_interval_seconds: float | None = None,
        force: bool = False,
        mark_timestamp: bool = True,
        max_http_retries: int = 0,
    ) -> str:
        """触发 change-ip。默认 3 分钟限流；force=True 跳过限流。

        必须使用当前绑定的 profile.change_ip_url（与 SOCKS5 同 profile 成套）。
        返回：
        - 服务端 body 摘要
        - rate_limited:Ns  距上次不足间隔
        - no_change_ip_url
        - change_ip_error:...
        """
        if not profile.change_ip_url:
            return "no_change_ip_url"

        interval = float(
            self.min_refresh_interval_seconds
            if min_interval_seconds is None
            else min_interval_seconds
        )
        refresh_key = self._refresh_state_key(profile) or profile.profile_name
        plock = self._profile_lock(refresh_key)
        with plock:
            if not force:
                left = self.remaining_refresh_seconds(profile, interval)
                if left > 0:
                    return f"rate_limited:{int(left) + 1}s"

            last_err = ""
            # 参数仅为旧调用兼容；当前规则固定每次只请求刷新链接一次。
            retries = 1
            for attempt in range(retries):
                # 发出刷新请求前即记录本次尝试；成功或失败都遵守同链接 3 分钟一次。
                if mark_timestamp and attempt == 0:
                    profile.last_refresh_ts = time.time()
                    profile.last_refresh_body = "refresh_requested"
                    self._persist_refresh_state(profile)
                try:
                    req = Request(
                        profile.change_ip_url,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "*/*",
                        },
                    )
                    with urlopen(req, timeout=timeout) as resp:
                        body = resp.read(500).decode("utf-8", errors="replace")
                        text = body.strip()[:200]
                    if mark_timestamp:
                        profile.last_refresh_body = text
                        self._persist_refresh_state(profile)
                    return text
                except Exception as exc:
                    last_err = str(exc)
                    low = last_err.lower()
                    # 并发/限流常见 400/429：短退避后同 profile 重试
                    retryable = (
                        "400" in last_err
                        or "429" in last_err
                        or "bad request" in low
                        or "too many" in low
                    )
                    if retryable and attempt + 1 < retries:
                        time.sleep(3.0 + attempt * 2.0)
                        continue
                    # 失败也保留完整 3 分钟冷却，禁止同链接连续请求。
                    if mark_timestamp:
                        profile.last_refresh_body = f"change_ip_error:{last_err}"
                        self._persist_refresh_state(profile)
                    return f"change_ip_error:{last_err}"
            return f"change_ip_error:{last_err or 'unknown'}"

    def refresh_and_wait_network(
        self,
        profile: ProxyProfile,
        *,
        min_interval_seconds: float | None = None,
        wait_seconds: float | None = None,
        check_fn: OptionalCheckFn = None,
        stop_event: OptionalStop = None,
        timeout: int = 20,
        force: bool = False,
        network_retries: int = 2,
        network_retry_gap: float = 2.0,
    ) -> dict:
        """刷新 IP → 等待 wait_seconds → 连通性检测。

        规则：
        - 无 change-ip：status=no_change_ip_url, ok=True（不阻塞登录）
        - 限流：status=rate_limited, 仍用 check_fn 测网；ok=测网结果
        - 刷新成功：等 N 秒后测网，ok=测网结果
        - 刷新失败：status=refresh_error, ok=False

        check_fn 缺省时用主机侧 generate_204。
        """
        wait_sec = float(
            self.refresh_wait_seconds if wait_seconds is None else wait_seconds
        )
        interval = float(
            self.min_refresh_interval_seconds
            if min_interval_seconds is None
            else min_interval_seconds
        )

        result: dict = {
            "ok": False,
            "status": "unknown",
            "body": "",
            "waited": 0.0,
            "remaining_seconds": 0.0,
            "network_ok": False,
            "profile": profile.profile_name,
        }

        if not profile.change_ip_url:
            result["status"] = "no_change_ip_url"
            # 无刷新链接时不挡流程，留给上层决定
            net = self._run_network_check(check_fn)
            result["network_ok"] = net
            result["ok"] = True
            return result

        body = self.refresh_ip(
            profile,
            timeout=timeout,
            min_interval_seconds=interval,
            force=force,
            mark_timestamp=True,
        )
        result["body"] = body

        if body.startswith("rate_limited:"):
            result["status"] = "rate_limited"
            try:
                result["remaining_seconds"] = float(
                    body.split(":", 1)[1].rstrip("s")
                )
            except Exception:
                result["remaining_seconds"] = self.remaining_refresh_seconds(
                    profile, interval
                )
            # 限流时不 sleep 整段 wait，只做连通性；仍可能继续登录
            net = self._run_network_check(
                check_fn,
                retries=max(1, network_retries),
                gap=network_retry_gap,
                stop_event=stop_event,
            )
            result["network_ok"] = net
            result["ok"] = net
            return result

        if body.startswith("change_ip_error:"):
            # 刷 IP 接口 400/失败时，不直接判死：主机侧再测一次 SOCKS5。
            # 代理本身仍通则可继续登录重试；真不通由上层决定换绑/导出 no_network。
            result["status"] = "refresh_error"
            net = self._run_network_check(
                check_fn,
                retries=max(1, network_retries),
                gap=network_retry_gap,
                stop_event=stop_event,
            )
            result["network_ok"] = net
            result["ok"] = net
            if net:
                result["status"] = "refresh_error_but_network_ok"
            return result

        result["status"] = "refreshed"
        # 刷新后固定等待再测网
        waited = self._interruptible_sleep(wait_sec, stop_event)
        result["waited"] = waited
        if stop_event is not None and stop_event.is_set():
            result["status"] = "stopped"
            result["ok"] = False
            return result

        net = self._run_network_check(
            check_fn,
            retries=max(1, network_retries),
            gap=network_retry_gap,
            stop_event=stop_event,
        )
        result["network_ok"] = net
        result["ok"] = net
        if not net:
            result["status"] = "network_fail"
        else:
            result["status"] = "refreshed_ok"
        return result

    @staticmethod
    def _interruptible_sleep(
        seconds: float,
        stop_event: OptionalStop = None,
    ) -> float:
        if seconds <= 0:
            return 0.0
        start = time.time()
        end = start + seconds
        while True:
            if stop_event is not None and stop_event.is_set():
                break
            now = time.time()
            if now >= end:
                break
            time.sleep(min(0.25, end - now))
        return time.time() - start

    @staticmethod
    def _run_network_check(
        check_fn: OptionalCheckFn,
        retries: int = 2,
        gap: float = 2.0,
        stop_event: OptionalStop = None,
    ) -> bool:
        fn = check_fn or (lambda: check_host_network())
        attempts = max(1, int(retries))
        for i in range(attempts):
            if stop_event is not None and stop_event.is_set():
                return False
            try:
                if fn():
                    return True
            except Exception:
                pass
            if i + 1 < attempts:
                if stop_event is not None and stop_event.wait(gap):
                    return False
                elif stop_event is None:
                    time.sleep(gap)
        return False
