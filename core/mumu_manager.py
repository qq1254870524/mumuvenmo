# 2026-08-11 compact-row-v3: 一行排列只在放不下时缩小，禁止自动放大占满屏幕；修正间距方向并恢复最大化窗口
# 2026-07-31 engine-version-v1: create 强制 --version 已装引擎(12)，60014 自动重试 auto/12
# 2026-07-31 instant-stop-v2: launch_and_wait 支持 cancel_check 秒退
# 2026-07-25 kitsune-cache-recreate-v1.1: 修复 DATA_STATE_DIR 局部导入 NameError； create/delete 清理 kitsune_ok_vmN.json，防索引复用误跳过
# 2026-07-25 rename-ui-notify-v1: 改名写磁盘后短超时 rename API，MuMuPlayer 实时刷新；磁盘已正确也通知 UI
# 2026-07-25 layout-boot-win32-v1: 启动后立即一字排列；纯Win32定位(不占MuMuManager锁)；窗口标题强制序号
# 2026-07-25 layout-render-tile-v2: render 实测贴紧+Win32精确定位，消除黑边与缝隙
# 2026-07-25 layout-render-tile-v1: 按 render 区贴紧排列，消除窗口装饰造成的缝隙/黑边
# 2026-07-25 create-name-retry-v2: 新建序号名带重试验证，防 Android Device-N 残留
# create-name-fs-v1: 新建后直接写 extra_config.playerName 为序号，禁用 rename API（防 MuMu 主界面卡死）
# 2026-07-25 create-layout-tight-v1: 一字排列按屏幕分辨率/数量自动算尺寸，margin=0无缝隙，9:16防黑边
# 2026-07-25 create-name-index-v1: 新建后 rename 为序号数字(与vmindex一致)，短超时防卡死
# 2026-07-25 create-no-freeze-v2.1: 成功路径不杀manager；仅批次前后/超时清理
# 2026-07-25 create-no-freeze-v2: create 校验errcode/禁clone兜底/FS索引/清残留manager，防MuMu主界面卡死
# 2026-07-25 create-no-rename-v1: 新建跳过 rename；manager 单线程+超时杀树，防主界面卡死
# 2026-07-25 rename-timeout-v1: rename 20s超时，避免 create_configured 卡死
# 2026-07-25 create-free-index-v1: create 指定空闲 vmindex，避免裸 create 卡住；clone 仅作兜底
# -*- coding: utf-8 -*-
"""MuMuManager.exe 封装：创建/启动/重启/排列/设置/ADB。

关键修复（2026-07-24）：
- 新建后必须关机态用 setting --path 原子写入配置，避免 key-value 逐项丢失
- 对齐可启动模板 VM：phone.0 + custom(2C/2G) + ROOT + 可写系统盘 + mini
- 禁止用默认 performance_mode=low(1C/1G) 起 1440x2560，否则易卡 98%
- launch/restart 短超时 + info 轮询；卡 starting_rom/98% 自动关机重配再启
- 管理员权限下自动降权调用 MuMuManager，避免 VERR_NEED_NO_ADMIN_ERROR
"""
from __future__ import annotations

import json
import threading
import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("mumuvenmo")

LogFn = Optional[Callable[[str], None]]


class MuMuManager:
    _manager_lock = threading.RLock()
    def __init__(
        self,
        manager_path: str | Path,
        adb_path: str | Path | None = None,
        adb_base_port: int = 16384,
        adb_port_step: int = 32,
        settings_dir: str | Path | None = None,
    ):
        self.manager = Path(manager_path)
        self.adb_path = Path(adb_path) if adb_path else self.manager.parent / "adb.exe"
        self.adb_base_port = adb_base_port
        self.adb_port_step = adb_port_step
        # 设置 JSON 落盘目录（必须在项目内）
        if settings_dir is None:
            from paths import DATA_STATE_DIR

            self.settings_dir = DATA_STATE_DIR
        else:
            self.settings_dir = Path(settings_dir)
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        if not self.manager.exists():
            raise FileNotFoundError(f"MuMuManager 不存在: {self.manager}")

    # ------------------------------------------------------------------ helpers
    def _run(self, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
        """执行 MuMuManager。管理员权限下自动降权，避免 VERR_NEED_NO_ADMIN_ERROR。

        同一时刻只允许一个 manager 命令，避免并发把 MuMu 主界面卡未响应。
        """
        cmd = [str(self.manager), *args]
        logger.debug("MuMu cmd: %s", " ".join(cmd))
        with self._manager_lock:
            try:
                from core.win_process import is_elevated, run_process, kill_process_tree

                if is_elevated():
                    logger.debug("current process elevated; MuMuManager will run unelevated")
                cp = run_process(cmd, timeout=timeout, force_unelevated=True)
            except TimeoutError:
                # 残留 manager 可能锁 UI
                try:
                    subprocess.run(
                        ["taskkill", "/IM", "MuMuManager.exe", "/F"],
                        capture_output=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                    )
                except Exception:
                    pass
                raise
            except Exception as exc:
                logger.warning("unelevated MuMu run failed (%s), fallback subprocess", exc)
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True, encoding="utf-8", errors="replace",
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
                    )
                    try:
                        stdout, stderr = proc.communicate(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        try:
                            from core.win_process import kill_process_tree
                            kill_process_tree(proc.pid)
                        except Exception:
                            pass
                        raise TimeoutError(f"MuMuManager 超时: {cmd}")
                    cp = subprocess.CompletedProcess(cmd, int(proc.returncode or 0), stdout, stderr)
                except TimeoutError:
                    raise
            if cp.stdout:
                logger.debug("stdout: %s", cp.stdout[:2000])
            if cp.stderr:
                logger.debug("stderr: %s", cp.stderr[:2000])
            return cp

    def _run_json(self, args: list[str], timeout: int = 120) -> Any:
        cp = self._run(args, timeout=timeout)
        text = (cp.stdout or "").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start : end + 1])
                except json.JSONDecodeError:
                    pass
            logger.warning("MuMu 输出非 JSON: %s", text[:500])
            return {"raw": text, "returncode": cp.returncode}

    def _dummy_ok(self, stdout: str = "ok") -> subprocess.CompletedProcess:
        class _Dummy:
            returncode = 0
            stdout = ""
            stderr = ""

        d = _Dummy()
        d.stdout = stdout
        return d  # type: ignore

    def _node(self, vmindex: int | str) -> dict:
        info = self.info(vmindex)
        if not isinstance(info, dict):
            return {}
        node = info.get(str(vmindex))
        if node is None and "is_android_started" in info:
            node = info
        return node if isinstance(node, dict) else {}

    def _log(self, log: LogFn, msg: str) -> None:
        logger.info(msg)
        if log:
            try:
                log(msg)
            except Exception:
                pass

    # ------------------------------------------------------------------ basic
    def version(self) -> dict:
        return self._run_json(["version"])

    def info(self, vmindex: str | int = "all") -> dict:
        return self._run_json(["info", "--vmindex", str(vmindex)], timeout=20)

    def list_indices(self) -> list[int]:
        """列出模拟器索引。避免 info -v all 挂起：优先 api/ADB，最后才短超时 info。"""
        import re
        out: list[int] = []
        # 1) api get_player_list（快）
        try:
            cp = self._run(["api", "-v", "0", "get_player_list"], timeout=8)
            text_out = (cp.stdout or "") + (cp.stderr or "")
            m = re.search(r"\[([0-9,\s]+)\]", text_out)
            if m:
                for part in m.group(1).split(","):
                    part = part.strip()
                    if part.isdigit():
                        out.append(int(part))
        except Exception:
            pass
        if out:
            return sorted(set(out))
        # 2) ADB 端口探测已启动的
        for i in range(16):
            if self._adb_boot_ready(i, tries=1):
                out.append(i)
        if out:
            return sorted(set(out))
        # 3) 最后 info all 短超时
        try:
            data = self._run_json(["info", "--vmindex", "all"], timeout=6)
            if isinstance(data, dict):
                for k, v in data.items():
                    if str(k).isdigit() and isinstance(v, dict):
                        out.append(int(k))
        except Exception:
            pass
        return sorted(set(out))

    def next_free_indices(self, number: int = 1, start: int = 0, max_scan: int = 64) -> list[int]:
        """返回尚未占用的模拟器索引。"""
        used = set(self.list_indices())
        out: list[int] = []
        i = max(0, int(start))
        while len(out) < max(1, int(number)) and i < max(1, int(max_scan)):
            if i not in used:
                out.append(i)
            i += 1
        return out

    def vms_root(self) -> Path:
        """MuMu 模拟器磁盘目录: <MuMuPlayer>/vms"""
        # manager: .../MuMuPlayer/nx_main/MuMuManager.exe
        return self.manager.parent.parent / "vms"

    def list_indices_fs(self) -> list[int]:
        """从 vms 目录扫描索引，不调用 MuMuManager，避免 create 期间刷命令卡 UI。"""
        root = self.vms_root()
        out: list[int] = []
        if not root.exists():
            return out
        for pth in root.iterdir():
            name = pth.name
            if not pth.is_dir():
                continue
            if "-" not in name:
                continue
            tail = name.rsplit("-", 1)[-1]
            if tail.isdigit():
                out.append(int(tail))
        return sorted(set(out))


    def vm_dir(self, vmindex: int | str) -> Path | None:
        """返回 vms 下指定索引的模拟器目录。"""
        root = self.vms_root()
        if not root.exists():
            return None
        key = str(int(vmindex))
        for pth in root.iterdir():
            if not pth.is_dir() or "-" not in pth.name:
                continue
            tail = pth.name.rsplit("-", 1)[-1]
            if tail == key:
                return pth
        return None

    def _extra_config_path(self, vmindex: int | str) -> Path | None:
        d = self.vm_dir(vmindex)
        if d is None:
            return None
        return d / "configs" / "extra_config.json"

    def read_player_name(self, vmindex: int | str) -> str | None:
        """从 extra_config.json 读取 playerName，不调用 manager。"""
        conf = self._extra_config_path(vmindex)
        if conf is None or not conf.exists():
            return None
        try:
            data = json.loads(conf.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("playerName") is not None:
                return str(data.get("playerName"))
        except Exception:
            return None
        return None

    def rename_player_name(self, vmindex: int | str, name: str, *, notify_ui: bool = True) -> bool:
        """写 extra_config.playerName，并短超时调用 MuMu rename 让 MuMuPlayer 实时刷新。

        仅写磁盘时 MuMuNxMain 列表常仍显示 Android Device-N；必须再走 rename API 通知界面。
        rename 使用已有短超时，失败不影响后续流程。
        """
        conf = self._extra_config_path(vmindex)
        if conf is None:
            return False
        conf.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if conf.exists():
            try:
                raw = json.loads(conf.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    data = raw
            except Exception:
                data = {}
        want = str(name)
        data["playerName"] = want
        data.setdefault("relateId", "")
        data.setdefault("status", 0)
        data.setdefault("errorCode", 0)
        data.setdefault("importFilePath", "")
        tmp = conf.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(conf)
        ok_disk = self.read_player_name(vmindex) == want
        if notify_ui:
            try:
                self.rename(int(vmindex), want)
            except Exception:
                pass
            try:
                self.set_player_window_title(int(vmindex), want)
            except Exception:
                pass
        return ok_disk or (self.read_player_name(vmindex) == want)

    def ensure_index_player_name(
        self,
        vmindex: int | str,
        name: str | None = None,
        *,
        retries: int = 4,
        delay: float = 0.35,
        log: LogFn = None,
    ) -> bool:
        """把 playerName 强制写成序号数字，带重试；并通知 MuMuPlayer 实时改名。"""
        idx = int(vmindex)
        want = str(name if name is not None else idx)
        last = None
        for attempt in range(max(1, int(retries))):
            cur = self.read_player_name(idx)
            last = cur
            # 磁盘已是目标名时，仍通知一次 UI（否则列表可能仍显示 Android Device-N）
            if cur == want:
                try:
                    self.rename(idx, want)
                except Exception:
                    pass
                try:
                    self.set_player_window_title(idx, want)
                except Exception:
                    pass
                if attempt == 0:
                    self._log(log, f"VM={idx} 序号名已是 {want}（已通知 MuMuPlayer 刷新）")
                else:
                    self._log(log, f"VM={idx} 序号名确认 {want} (attempt={attempt+1})")
                return True
            ok = self.rename_player_name(idx, want, notify_ui=True)
            time.sleep(max(0.05, float(delay)))
            got = self.read_player_name(idx)
            info_name = None
            try:
                node = self.info(idx) or {}
                if isinstance(node, dict):
                    info_name = str(node.get("name") or "") or None
            except Exception:
                info_name = None
            last = got or info_name
            self._log(
                log,
                f"VM={idx} 改名序号={want} ok={ok} attempt={attempt+1} "
                f"disk_before={cur!r} disk_after={got!r} info_name={info_name!r}",
            )
            if got == want or info_name == want:
                time.sleep(max(0.05, float(delay)))
                again = self.read_player_name(idx)
                if again == want or info_name == want:
                    try:
                        self.set_player_window_title(idx, want)
                    except Exception:
                        pass
                    return True
                last = again
        self._log(log, f"VM={idx} 序号改名未稳定 want={want} last={last!r}")
        try:
            self.rename(idx, want)
        except Exception:
            pass
        return self.read_player_name(idx) == want


    def _kill_stale_manager(self) -> None:
        """清理残留 MuMuManager，防止把 MuMuNxMain 锁成未响应。"""
        try:
            subprocess.run(
                ["taskkill", "/IM", "MuMuManager.exe", "/F"],
                capture_output=True,
                timeout=8,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
            )
        except Exception:
            pass

    def _parse_create_result(self, text: str) -> dict[int, dict[str, Any]]:
        """解析 create 输出: {"N": {"errcode":0,"errmsg":""}}"""
        result: dict[int, dict[str, Any]] = {}
        raw = (text or "").strip()
        if not raw:
            return result
        data: Any = None
        try:
            data = json.loads(raw)
        except Exception:
            try:
                s = raw.find("{")
                e = raw.rfind("}")
                if s >= 0 and e > s:
                    data = json.loads(raw[s : e + 1])
            except Exception:
                data = None
        if not isinstance(data, dict):
            return result
        for k, v in data.items():
            if not str(k).isdigit():
                continue
            if isinstance(v, dict):
                result[int(k)] = v
            else:
                result[int(k)] = {"errcode": 0 if v else -1, "errmsg": str(v)}
        return result

    def _used_indices_for_create(self) -> set[int]:
        """create 专用：FS + manager 列表并集，避免误复用已存在 index。"""
        used: set[int] = set(self.list_indices_fs())
        try:
            used |= set(self.list_indices())
        except Exception:
            pass
        return used

    def detect_preferred_android_version(self) -> str:
        """检测本机已安装的 Android 引擎版本，供 create --version 使用。

        MuMu 6.3+ create 支持 auto/12/15。升级后若默认走 15 但本机只有 12，
        会返回 errcode=60014 android engine not installed。
        优先读 install_config.engines.*.player.android_version 与 nx_device/*/vms/*base*。
        """
        root = self.manager.parent.parent  # nx_main -> MuMuPlayer
        found: list[str] = []

        # 1) install_config.json engines
        for rel in (
            Path("configs") / "install_config.json",
            Path("configs") / "main" / "install_config.json",
        ):
            fp = root / rel
            if not fp.exists():
                continue
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            engines = data.get("engines") if isinstance(data, dict) else None
            if not isinstance(engines, dict):
                continue
            for _name, eng in engines.items():
                if not isinstance(eng, dict):
                    continue
                player = eng.get("player") if isinstance(eng.get("player"), dict) else {}
                av = str(player.get("android_version") or "").strip()
                if not av:
                    continue
                major = av.split(".")[0].strip()
                if major.isdigit():
                    found.append(major)

        # 2) nx_device/<ver>/vms/*base*
        nx = root / "nx_device"
        if nx.is_dir():
            try:
                for child in sorted(nx.iterdir()):
                    if not child.is_dir():
                        continue
                    name = child.name.strip()
                    major = name.split(".")[0]
                    if not major.isdigit():
                        continue
                    vms = child / "vms"
                    has_base = False
                    if vms.is_dir():
                        try:
                            for f in vms.iterdir():
                                if "base" in f.name.lower():
                                    has_base = True
                                    break
                        except Exception:
                            pass
                    # 只有真正有 base 镜像才算已安装；15.0 空壳不算
                    if has_base:
                        found.append(major)
            except Exception:
                pass

        uniq: list[str] = []
        for v in found:
            if v not in uniq:
                uniq.append(v)
        if "12" in uniq:
            return "12"
        if uniq:
            return uniq[0]
        return "12"

    def create(
        self,
        number: int = 1,
        mini: bool = True,
        vmindex: int | str | None = None,
        timeout: int = 45,
        version: str | int | None = None,
    ) -> subprocess.CompletedProcess:
        """创建模拟器（短超时）。
        必须带 --vmindex 指定空闲索引；裸 create 或超时残留 manager 会卡 MuMu 主界面。
        成功返回后不杀 manager（避免误杀并发命令）；超时由 _run 杀树。
        version: Android 引擎 auto/12/15；None 时自动检测本机已装引擎（避免 60014）。
        """
        args = ["create", "--number", str(max(1, int(number)))]
        if vmindex is not None and str(vmindex) != "":
            args.extend(["--vmindex", str(vmindex)])
        if mini:
            args.append("--mini")
        ver = str(version).strip() if version is not None and str(version).strip() != "" else ""
        if not ver:
            try:
                ver = str(self.detect_preferred_android_version() or "12")
            except Exception:
                ver = "12"
        # MuMu create --version 接受 auto/12/15
        major = ver.split(".")[0]
        if ver.lower() == "auto":
            args.extend(["--version", "auto"])
        elif major.isdigit():
            args.extend(["--version", major])
        else:
            args.extend(["--version", "12"])
        return self._run(args, timeout=timeout)

    def delete(self, vmindex: str | int = "all") -> subprocess.CompletedProcess:
        """删除模拟器。vmindex 支持单索引/逗号列表/all。"""
        return self._run(["delete", "--vmindex", str(vmindex)], timeout=180)

    def delete_vms(
        self,
        indices: list[int],
        *,
        shutdown_first: bool = True,
        wait_after_shutdown: float = 2.0,
        log=None,
    ) -> dict:
        """结束进程(关机)后删除指定模拟器。

        顺序：shutdown → 等待 → MuMu delete --vmindex N
        返回 {"ok":[...], "fail":{idx: err}, "deleted":[...]}
        """
        import time as _time

        result = {"ok": [], "fail": {}, "deleted": [], "shutdown": []}
        ids = []
        for x in indices or []:
            try:
                ids.append(int(x))
            except Exception:
                continue
        ids = sorted(set(ids))
        if not ids:
            result["fail"]["-"] = "empty_selection"
            return result

        def _lg(msg: str) -> None:
            if log:
                try:
                    log(msg)
                except Exception:
                    pass
            logger.info(msg)

        for idx in ids:
            try:
                if shutdown_first:
                    try:
                        self.shutdown(idx)
                        result["shutdown"].append(idx)
                        _lg(f"VM={idx} 删除前已 shutdown/结束进程")
                    except Exception as exc:
                        _lg(f"VM={idx} shutdown 警告(继续删除): {exc}")
                    _time.sleep(max(0.2, float(wait_after_shutdown)))
                cp = self.delete(idx)
                out = ((cp.stdout or "") + (cp.stderr or "")).strip()
                # MuMu 成功时通常无 error
                low = out.lower()
                if "error" in low and "success" not in low and cp.returncode not in (0, None):
                    result["fail"][idx] = out[:200] or f"rc={cp.returncode}"
                    _lg(f"VM={idx} 删除失败: {out[:160]}")
                else:
                    result["ok"].append(idx)
                    result["deleted"].append(idx)
                    _lg(f"VM={idx} 已删除 {out[:80]}")
                    # 删除后清 kitsune 缓存，防止同索引重建误跳过
                    try:
                        from paths import DATA_STATE_DIR
                        kp = Path(getattr(self, "settings_dir", None) or DATA_STATE_DIR) / f"kitsune_ok_vm{int(idx)}.json"
                        if kp.exists():
                            kp.unlink(missing_ok=True)
                            _lg(f"VM={idx} 已清理 kitsune 缓存 {kp.name}")
                    except Exception as exc:
                        _lg(f"VM={idx} 清理 kitsune 缓存警告: {exc}")
            except Exception as exc:
                result["fail"][idx] = str(exc)
                _lg(f"VM={idx} 删除异常: {exc}")
        return result


    def clone(self, vmindex: int, number: int = 1) -> subprocess.CompletedProcess:
        return self._run(["clone", "--vmindex", str(vmindex), "--number", str(number)], timeout=600)

    def rename(self, vmindex: int, name: str) -> subprocess.CompletedProcess:
        # rename 偶发卡死，必须短超时，失败不影响后续 launch/provision
        try:
            return self._run(["rename", "--vmindex", str(vmindex), "--name", name], timeout=12)
        except TimeoutError:
            return self._dummy_ok("rename_timeout")

    def setting(self, vmindex: int | str, key: str, value: str) -> subprocess.CompletedProcess:
        return self._run(
            [
                "setting",
                "--vmindex",
                str(vmindex),
                "--key",
                key,
                "--value",
                str(value),
            ]
        )

    def setting_many(self, vmindex: int | str, pairs: dict[str, Any]) -> None:
        # 多 key 一次写入，减少半写状态
        args: list[str] = ["setting", "--vmindex", str(vmindex)]
        for k, v in pairs.items():
            if isinstance(v, bool):
                val = "true" if v else "false"
            else:
                val = str(v)
            args.extend(["--key", k, "--value", val])
        if len(args) > 3:
            self._run(args, timeout=120)

    def setting_from_path(self, vmindex: int | str, path: Path) -> subprocess.CompletedProcess:
        return self._run(
            ["setting", "--vmindex", str(vmindex), "--path", str(path)],
            timeout=45,
        )

    def read_settings(self, vmindex: int | str, keys: list[str] | None = None) -> dict[str, Any]:
        if keys:
            args = ["setting", "--vmindex", str(vmindex)]
            for k in keys:
                args.extend(["--key", k])
            data = self._run_json(args)
            return data if isinstance(data, dict) else {}
        data = self._run_json(["setting", "--vmindex", str(vmindex), "--all"])
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------------ create settings
    def build_create_settings(self, defaults: dict[str, Any] | None = None) -> dict[str, str]:
        """生成可启动模板设置（对齐已验证可启动 VM1）。

        说明：
        - portrait = resolution_mode phone.0（内置 1440x2560@640）
        - power saving = custom 2C/2G（默认 low=1C/1G 会导致 1440x2560 卡 98%）
        - small disk = mini_disk true
        - ROOT / Writable system disk
        """
        d = defaults or {}
        w = float(int(d.get("resolution_width", 1440)))
        h = float(int(d.get("resolution_height", 2560)))
        dpi = float(int(d.get("resolution_dpi", 640)))
        # 省电但可启动：至少 2C / 2G
        cpu = int(d.get("performance_cpu", d.get("cpu", 2)) or 2)
        mem = float(d.get("performance_mem", d.get("memory_gb", 2.0)) or 2.0)
        if cpu < 2:
            cpu = 2
        if mem < 1.75:
            mem = 2.0
        mode = str(d.get("performance_mode", "custom") or "custom").lower()
        # 强制把 low 的档位也抬高，避免配置里写 low 又卡死
        pairs: dict[str, str] = {
            "root_permission": "true" if d.get("root_permission", True) else "false",
            "system_disk_readonly": "false" if not d.get("system_disk_readonly", False) else "true",
            "mini_disk": "true" if d.get("mini_disk", True) else "false",
            "window_auto_rotate": "false",
            "resolution_mode": "phone.0",
            "resolution_width.phone.0": f"{w:.6f}",
            "resolution_height.phone.0": f"{h:.6f}",
            "resolution_dpi.phone.0": f"{dpi:.6f}",
            "resolution_width.custom": f"{w:.6f}",
            "resolution_height.custom": f"{h:.6f}",
            "resolution_dpi.custom": f"{dpi:.6f}",
            "performance_cpu.low": str(max(2, cpu)),
            "performance_mem.low": f"{max(2.0, mem):.6f}",
            "performance_cpu.custom": str(cpu),
            "performance_mem.custom": f"{mem:.6f}",
        }
        if mode == "low":
            # 用户要求省电：用 low，但已抬高 low 档位
            pairs["performance_mode"] = "low"
        else:
            pairs["performance_mode"] = "custom"
        return pairs

    def write_settings_json(self, vmindex: int, pairs: dict[str, str]) -> Path:
        path = self.settings_dir / f"vm_setting_{vmindex}.json"
        path.write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
        # 同步一份通用模板
        tpl = self.settings_dir / "vm_setting_portrait_root.json"
        tpl.write_text(json.dumps(pairs, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def ensure_offline(self, vmindex: int, timeout: int = 90, log: LogFn = None) -> bool:
        node = self._node(vmindex)
        if not node.get("is_process_started") and not node.get("is_android_started"):
            return True
        self._log(log, f"VM={vmindex} 关机以便写设置...")
        try:
            self.shutdown(vmindex)
        except Exception as exc:
            self._log(log, f"VM={vmindex} shutdown 异常: {exc}")
        deadline = time.time() + timeout
        while time.time() < deadline:
            node = self._node(vmindex)
            if not node.get("is_process_started") and not node.get("is_android_started"):
                time.sleep(1.0)  # 落盘缓冲
                return True
            time.sleep(1.5)
        self._log(log, f"VM={vmindex} 关机超时，仍尝试写设置")
        return False

    def verify_create_settings(self, vmindex: int, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        keys = [
            "root_permission",
            "system_disk_readonly",
            "mini_disk",
            "performance_mode",
            "performance_cpu.custom",
            "performance_mem.custom",
            "performance_cpu.low",
            "performance_mem.low",
            "resolution_mode",
            "resolution_width.phone.0",
            "resolution_height.phone.0",
            "resolution_dpi.phone.0",
            "resolution_width.custom",
            "resolution_height.custom",
            "resolution_dpi.custom",
        ]
        cur = self.read_settings(vmindex, keys)
        d = defaults or {}
        w = float(int(d.get("resolution_width", 1440)))
        h = float(int(d.get("resolution_height", 2560)))
        dpi = float(int(d.get("resolution_dpi", 640)))

        def _bool(v: Any) -> bool:
            return str(v).lower() in ("1", "true", "yes", "on")

        root_ok = _bool(cur.get("root_permission", False))
        writable_ok = not _bool(cur.get("system_disk_readonly", True))
        mini_ok = _bool(cur.get("mini_disk", False))
        mode = str(cur.get("resolution_mode", "")).lower()
        res_ok = mode in ("phone.0", "phone", "custom")
        # 宽高：phone.0 或 custom 任一命中
        try:
            rw = float(cur.get("resolution_width.phone.0") or cur.get("resolution_width.custom") or 0)
            rh = float(cur.get("resolution_height.phone.0") or cur.get("resolution_height.custom") or 0)
            rd = float(cur.get("resolution_dpi.phone.0") or cur.get("resolution_dpi.custom") or 0)
        except Exception:
            rw = rh = rd = 0.0
        size_ok = abs(rw - w) < 1 and abs(rh - h) < 1 and abs(rd - dpi) < 1
        perf = str(cur.get("performance_mode", "")).lower()
        # 禁止 1C/1G
        try:
            cpu_c = int(float(cur.get("performance_cpu.custom") or 0))
            mem_c = float(cur.get("performance_mem.custom") or 0)
            cpu_l = int(float(cur.get("performance_cpu.low") or 0))
            mem_l = float(cur.get("performance_mem.low") or 0)
        except Exception:
            cpu_c = mem_c = cpu_l = mem_l = 0
        if perf == "low":
            perf_ok = cpu_l >= 2 and mem_l >= 1.75
        else:
            perf_ok = cpu_c >= 2 and mem_c >= 1.75
        ok = root_ok and writable_ok and mini_ok and res_ok and size_ok and perf_ok
        return {
            "ok": ok,
            "root": root_ok,
            "writable": writable_ok,
            "mini": mini_ok,
            "resolution_mode": mode,
            "size": f"{rw}x{rh}@{rd}",
            "size_ok": size_ok,
            "performance_mode": perf,
            "perf_ok": perf_ok,
            "cpu_custom": cpu_c,
            "mem_custom": mem_c,
            "raw": cur,
        }

    def apply_create_defaults(
        self,
        vmindex: int,
        defaults: dict[str, Any] | None = None,
        log: LogFn = None,
        force_offline: bool = True,
    ) -> dict[str, Any]:
        """关机态原子写设置并校验。"""
        if force_offline:
            self.ensure_offline(vmindex, log=log)
        pairs = self.build_create_settings(defaults)
        path = self.write_settings_json(vmindex, pairs)
        self._log(log, f"VM={vmindex} 写入设置 {path.name}")
        try:
            self.setting_from_path(vmindex, path)
        except Exception as exc:
            self._log(log, f"VM={vmindex} --path 写设置失败，回退 multi-key: {exc}")
            self.setting_many(vmindex, pairs)
        time.sleep(0.8)
        check = self.verify_create_settings(vmindex, defaults)
        if not check["ok"]:
            self._log(log, f"VM={vmindex} 设置校验失败，重试 multi-key: {check}")
            self.setting_many(vmindex, pairs)
            time.sleep(0.8)
            check = self.verify_create_settings(vmindex, defaults)
        self._log(
            log,
            f"VM={vmindex} 设置校验 ok={check['ok']} root={check['root']} "
            f"writable={check['writable']} mini={check['mini']} "
            f"mode={check['resolution_mode']} size={check['size']} "
            f"perf={check['performance_mode']} cpu={check['cpu_custom']} mem={check['mem_custom']}",
        )
        return check

    def create_configured(
        self,
        number: int,
        defaults: dict[str, Any] | None = None,
        name_prefix: str = "venmo",
        log: LogFn = None,
        cancel_check=None,
    ) -> list[int]:
        """新建并写默认设置。只走 create --vmindex，禁止 clone 兜底（clone 易卡死主界面）。
        cancel_check: 可选 callable()->bool，为 True 时立即停止后续 create。
        """
        defaults = defaults or {}
        need = max(1, int(number))
        mini = bool(defaults.get("mini_disk", True))
        # engine-version-v1: 显式指定已装 Android 引擎，避免升级后默认 15 导致 60014
        raw_ver = (
            defaults.get("android_version")
            or defaults.get("engine_version")
            or defaults.get("create_version")
        )
        if raw_ver is not None and str(raw_ver).strip() != "":
            android_ver = str(raw_ver).strip()
            if android_ver not in ("auto", "12", "15") and android_ver.split(".")[0].isdigit():
                android_ver = android_ver.split(".")[0]
        else:
            try:
                android_ver = self.detect_preferred_android_version()
            except Exception:
                android_ver = "12"
        android_ver_fallbacks: list[str] = []
        for cand in (android_ver, "12", "auto", "15"):
            c = str(cand).strip()
            if c and c not in android_ver_fallbacks:
                android_ver_fallbacks.append(c)

        def _cancelled() -> bool:
            try:
                return bool(cancel_check and cancel_check())
            except Exception:
                return False

        # create 期间尽量少打 manager：先清残留，再 FS+list 并集算空闲位
        self._kill_stale_manager()
        used = self._used_indices_for_create()
        before = set(used)
        targets: list[int] = []
        i = 0
        while len(targets) < need and i < 64:
            if i not in used:
                targets.append(i)
            i += 1
        if not targets:
            start = (max(used) + 1) if used else 0
            targets = list(range(start, start + need))

        self._log(
            log,
            f"创建 {need} 个模拟器 mini={mini} android_version={android_ver} "
            f"fallbacks={android_ver_fallbacks} free_targets={targets} before={sorted(before)} fs={self.list_indices_fs()}",
        )

        new_ids: list[int] = []
        # 预留额外候选：目标被占用/失败时顺延，不走 clone
        scan = list(targets)
        extra_start = (max(scan) + 1) if scan else 0
        for extra in range(extra_start, 64):
            if extra not in used and extra not in scan:
                scan.append(extra)
            if len(scan) >= need + 8:
                break

        for target in scan:
            if _cancelled():
                self._log(log, f"create 已取消，已完成 {len(new_ids)}/{need}")
                break
            if len(new_ids) >= need:
                break
            # 已存在 index 直接跳过，避免 -206 后无意义等待
            if target in before:
                continue
            try:
                self._log(
                    log,
                    f"create --vmindex {target} --number 1 mini={mini} version={android_ver}",
                )
                cp = self.create(
                    number=1, mini=mini, vmindex=target, timeout=45, version=android_ver
                )
                out = ((cp.stdout or "") + (cp.stderr or "")).strip()
                self._log(log, f"create vmindex={target} rc={cp.returncode} out={out[:180]}")
                parsed = self._parse_create_result(out)
                node = parsed.get(int(target))
                if node is None and parsed:
                    node = next(iter(parsed.values()))
                errcode = 0
                errmsg = ""
                if isinstance(node, dict):
                    try:
                        errcode = int(node.get("errcode", 0) or 0)
                    except Exception:
                        errcode = -1
                    errmsg = str(node.get("errmsg") or "")
                # 60014: android engine not installed — 同索引换 version 重试
                if errcode == 60014 or "android engine not installed" in errmsg.lower():
                    for alt in android_ver_fallbacks:
                        if _cancelled():
                            break
                        if alt == android_ver:
                            continue
                        self._log(
                            log,
                            f"create vmindex={target} 60014，改用 --version {alt} 重试",
                        )
                        cp = self.create(
                            number=1, mini=mini, vmindex=target, timeout=45, version=alt
                        )
                        out = ((cp.stdout or "") + (cp.stderr or "")).strip()
                        self._log(
                            log,
                            f"create vmindex={target} retry version={alt} rc={cp.returncode} out={out[:180]}",
                        )
                        parsed = self._parse_create_result(out)
                        node = parsed.get(int(target))
                        if node is None and parsed:
                            node = next(iter(parsed.values()))
                        errcode = 0
                        errmsg = ""
                        if isinstance(node, dict):
                            try:
                                errcode = int(node.get("errcode", 0) or 0)
                            except Exception:
                                errcode = -1
                            errmsg = str(node.get("errmsg") or "")
                        if errcode == 0:
                            android_ver = alt  # 后续 create 沿用成功版本
                            break
                if errcode != 0:
                    self._log(
                        log,
                        f"create vmindex={target} 失败 errcode={errcode} {errmsg[:120]}，换下一个空闲索引",
                    )
                    used.add(target)
                    continue
                # 成功：等 FS 落盘，不再狂刷 list_indices/manager
                ok_fs = False
                for _ in range(25):
                    if _cancelled():
                        break
                    if target in self.list_indices_fs():
                        ok_fs = True
                        break
                    time.sleep(0.2)
                if not ok_fs:
                    self._log(log, f"create vmindex={target} 成功但 FS 暂未见目录，仍采用该索引")
                if target not in new_ids:
                    new_ids.append(target)
                used.add(target)
                # 索引可能复用旧号：新建成功立刻清掉 kitsune_ok 缓存，避免误跳过 Direct Install
                try:
                    from paths import DATA_STATE_DIR
                    kp = Path(self.settings_dir or DATA_STATE_DIR) / f"kitsune_ok_vm{int(target)}.json"
                    if kp.exists():
                        kp.unlink(missing_ok=True)
                        self._log(log, f"VM={target} 新建成功，已清理旧 kitsune 缓存 {kp.name}")
                except Exception as exc:
                    self._log(log, f"VM={target} 清理 kitsune 缓存警告: {exc}")
                # 给 MuMuNxMain 刷新 UI 的时间，避免连续 create 卡未响应
                time.sleep(1.2)
            except TimeoutError as exc:
                self._log(log, f"create vmindex={target} 超时(已杀 MuMuManager): {exc}")
                self._kill_stale_manager()
                used.add(target)
                time.sleep(0.5)
            except Exception as exc:
                self._log(log, f"create vmindex={target} 异常: {exc}")
                self._kill_stale_manager()
                used.add(target)

        if len(new_ids) < need:
            self._log(
                log,
                f"create 仅得到 {len(new_ids)}/{need}，不再 clone 兜底（防主界面卡死） "
                f"android_version={android_ver} before={sorted(before)} fs={self.list_indices_fs()} new={new_ids} "
                f"提示: 若全是 60014，请确认 MuMu 已安装 Android 引擎(本机通常为 12)",
            )

        new_ids = sorted(set(new_ids))[:need]
        self._log(log, f"新模拟器索引: {new_ids}")
        for idx in new_ids:
            if _cancelled():
                self._log(log, "create 配置阶段已取消")
                break
            try:
                self.apply_create_defaults(idx, defaults, log=log, force_offline=True)
            except Exception as exc:
                self._log(log, f"VM={idx} 配置失败: {exc}")
            # 名字用序号数字：直接写 extra_config.playerName，禁止 rename API（防主界面卡死）
            # 带重试：MuMu 创建后可能短暂写回 Android Device-N
            try:
                self.ensure_index_player_name(idx, str(int(idx)), retries=5, delay=0.4, log=log)
            except Exception as exc:
                self._log(log, f"VM={idx} 磁盘改名失败(跳过): {exc}")
        self._kill_stale_manager()
        return new_ids

    # ------------------------------------------------------------------ launch / boot
    def launch(self, vmindex: int, package: str | None = None) -> subprocess.CompletedProcess:
        args = ["control", "--vmindex", str(vmindex), "launch"]
        if package:
            args.extend(["--package", package])
        try:
            cp = self._run(args, timeout=25)
            out = ((cp.stdout or "") + "\n" + (cp.stderr or "")).lower()
            if "administrator" in out or "admin" in out or "verr_need_no_admin" in out or "-30110" in out:
                logger.error(
                    "VM=%s launch 疑似管理员权限冲突，请确认脚本已降权启动 MuMu: %s",
                    vmindex,
                    ((cp.stdout or "") + (cp.stderr or ""))[:500],
                )
            return cp
        except TimeoutError:
            logger.info("launch cmd timeout, continue wait via info vm=%s", vmindex)
            return self._dummy_ok("launch_timeout_continue")

    def shutdown(self, vmindex: int | str) -> subprocess.CompletedProcess:
        return self._run(["control", "--vmindex", str(vmindex), "shutdown"], timeout=120)

    def restart(self, vmindex: int | str) -> subprocess.CompletedProcess:
        """只能用模拟器 restart device。
        2026-07-31: 超时 25->12，避免 10 路并行时 manager 全局锁被单台 restart 占太久。
        """
        try:
            return self._run(["control", "--vmindex", str(vmindex), "restart"], timeout=12)
        except TimeoutError:
            logger.info("restart cmd timeout, continue wait via info vm=%s", vmindex)
            return self._dummy_ok("restart_timeout_continue")

    def sort_windows(self) -> subprocess.CompletedProcess:
        """MuMu 自带 sort（网格），业务一字排列请用 layout_row_from_top_left。"""
        return self._run(["sort"], timeout=60)

    def layout_window(self, vmindex: int, x: int, y: int, w: int, h: int) -> subprocess.CompletedProcess:
        return self._run(
            [
                "control",
                "--vmindex",
                str(vmindex),
                "layout_window",
                "--pos_x",
                str(int(x)),
                "--pos_y",
                str(int(y)),
                "--size_w",
                str(int(w)),
                "--size_h",
                str(int(h)),
            ],
            timeout=20,
        )

    def get_primary_screen_size(self) -> tuple[int, int]:
        """主屏分辨率 (width, height)。优先工作区，失败回退 1920x1080。"""
        # 1) 工作区（去掉任务栏）
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            r = RECT()
            # SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0):
                w = int(r.right - r.left)
                h = int(r.bottom - r.top)
                if w > 0 and h > 0:
                    return w, h
        except Exception:
            pass
        # 2) ctypes GetSystemMetrics
        try:
            import ctypes

            user32 = ctypes.windll.user32
            w = int(user32.GetSystemMetrics(0))
            h = int(user32.GetSystemMetrics(1))
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        # 3) tkinter
        try:
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            w = int(root.winfo_screenwidth())
            h = int(root.winfo_screenheight())
            root.destroy()
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        return 1920, 1080


    def _parse_hwnd_value(self, v) -> int:
        s = str(v or "").strip()
        if not s:
            return 0
        try:
            if s.lower().startswith("0x") or any(c in s.lower() for c in "abcdef"):
                return int(s, 16)
            return int(s, 0)
        except Exception:
            try:
                return int(s, 16)
            except Exception:
                return 0

    def _enum_windows_by_titles(self, titles: set[str]) -> dict[str, int]:
        """返回 title->hwnd（可见大窗口）。不调用 MuMuManager。"""
        out: dict[str, int] = {}
        want = {str(t).strip() for t in titles if str(t).strip()}
        if not want:
            return out
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            EnumWindows = user32.EnumWindows
            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            GetWindowTextW = user32.GetWindowTextW
            GetWindowTextLengthW = user32.GetWindowTextLengthW
            IsWindowVisible = user32.IsWindowVisible
            GetWindowRect = user32.GetWindowRect

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            found: dict[str, int] = {}

            @EnumWindowsProc
            def _cb(hwnd, lParam):
                try:
                    if not IsWindowVisible(hwnd):
                        return True
                    n = GetWindowTextLengthW(hwnd)
                    if n <= 0:
                        return True
                    buf = ctypes.create_unicode_buffer(n + 1)
                    GetWindowTextW(hwnd, buf, n + 1)
                    title = (buf.value or "").strip()
                    if title not in want:
                        return True
                    r = RECT()
                    if not GetWindowRect(hwnd, ctypes.byref(r)):
                        return True
                    w = int(r.right - r.left)
                    h = int(r.bottom - r.top)
                    if w < 80 or h < 80:
                        return True
                    old = found.get(title)
                    if old:
                        r2 = RECT()
                        GetWindowRect(old, ctypes.byref(r2))
                        area_old = max(0, r2.right - r2.left) * max(0, r2.bottom - r2.top)
                        if w * h < area_old:
                            return True
                    found[title] = int(hwnd)
                except Exception:
                    return True
                return True

            EnumWindows(_cb, 0)
            out = found
        except Exception:
            return {}
        return out

    def resolve_main_hwnd(self, vmindex: int | str, *, lock_timeout: float = 0.25) -> int:
        """解析模拟器主窗口 hwnd。优先标题匹配，其次短等 manager info。"""
        idx = int(vmindex)
        titles = {
            str(idx),
            f"Android Device-{idx}",
            f"Android Device - {idx}",
            f"AndroidDevice-{idx}",
        }
        by_title = self._enum_windows_by_titles(titles)
        for t in (str(idx), f"Android Device-{idx}", f"Android Device - {idx}", f"AndroidDevice-{idx}"):
            if t in by_title:
                return int(by_title[t])

        info = None
        got_lock = False
        try:
            got_lock = self._manager_lock.acquire(timeout=max(0.0, float(lock_timeout)))
            if got_lock:
                try:
                    info = self.info(idx) or {}
                except Exception:
                    info = None
        except Exception:
            info = None
        finally:
            if got_lock:
                try:
                    self._manager_lock.release()
                except Exception:
                    pass
        if isinstance(info, dict):
            hwnd = self._parse_hwnd_value(info.get("main_wnd"))
            if hwnd:
                return hwnd
        return 0

    def set_player_window_title(self, vmindex: int | str, title: str | None = None) -> bool:
        """强制主窗口标题为序号数字，避免残留 Android Device-N。"""
        idx = int(vmindex)
        name = str(title if title is not None else idx)
        hwnd = self.resolve_main_hwnd(idx, lock_timeout=0.2)
        if not hwnd:
            return False
        try:
            import ctypes
            return bool(ctypes.windll.user32.SetWindowTextW(hwnd, name))
        except Exception:
            return False

    def measure_player_window_win32(self, vmindex: int, *, hwnd: int | None = None) -> dict[str, int]:
        """纯 Win32 测 main 窗口；不调用 MuMuManager。"""
        out: dict[str, int] = {}
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            user32 = ctypes.windll.user32
            hwin = int(hwnd or 0) or self.resolve_main_hwnd(int(vmindex), lock_timeout=0.05)
            if not hwin:
                return out
            r = RECT()
            if not user32.GetWindowRect(hwin, ctypes.byref(r)):
                return out
            left, top, right, bottom = int(r.left), int(r.top), int(r.right), int(r.bottom)
            out["main_left"], out["main_top"], out["main_right"], out["main_bottom"] = left, top, right, bottom
            out["outer_w"] = max(0, right - left)
            out["outer_h"] = max(0, bottom - top)
            est_il, est_it, est_ir, est_ib = 0, 32, 0, 0
            out["inset_left"] = est_il
            out["inset_top"] = est_it
            out["inset_right"] = est_ir
            out["inset_bottom"] = est_ib
            out["render_left"] = left + est_il
            out["render_top"] = top + est_it
            out["render_right"] = right - est_ir
            out["render_bottom"] = bottom - est_ib
            out["render_w"] = max(0, out["render_right"] - out["render_left"])
            out["render_h"] = max(0, out["render_bottom"] - out["render_top"])
            out["chrome_w"] = max(0, out["outer_w"] - out["render_w"])
            out["chrome_h"] = max(0, out["outer_h"] - out["render_h"])
        except Exception:
            return out
        return out

    def measure_player_window(self, vmindex: int) -> dict[str, int]:
        """读取 MuMu main/render 窗口矩形，用于贴紧排列去缝隙。"""
        out: dict[str, int] = {}
        try:
            info = self.info(int(vmindex)) or {}
        except Exception:
            return out
        if not isinstance(info, dict):
            return out
        try:
            import ctypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long),
                ]

            user32 = ctypes.windll.user32

            def _parse_hwnd(v) -> int:
                s = str(v or "").strip()
                if not s:
                    return 0
                try:
                    return int(s, 16) if s.lower().startswith("0x") or any(c in s.lower() for c in "abcdef") else int(s, 0)
                except Exception:
                    try:
                        return int(s, 16)
                    except Exception:
                        return 0

            def _rect(hwnd: int):
                if not hwnd:
                    return None
                r = RECT()
                if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
                    return None
                return int(r.left), int(r.top), int(r.right), int(r.bottom)

            main_h = _parse_hwnd(info.get("main_wnd"))
            render_h = _parse_hwnd(info.get("render_wnd"))
            mr = _rect(main_h)
            rr = _rect(render_h)
            if mr:
                out["main_left"], out["main_top"], out["main_right"], out["main_bottom"] = mr
                out["outer_w"] = mr[2] - mr[0]
                out["outer_h"] = mr[3] - mr[1]
            if rr:
                out["render_left"], out["render_top"], out["render_right"], out["render_bottom"] = rr
                out["render_w"] = rr[2] - rr[0]
                out["render_h"] = rr[3] - rr[1]
            if mr and rr:
                out["inset_left"] = rr[0] - mr[0]
                out["inset_top"] = rr[1] - mr[1]
                out["inset_right"] = mr[2] - rr[2]
                out["inset_bottom"] = mr[3] - rr[3]
                out["chrome_w"] = max(0, out["outer_w"] - out["render_w"])
                out["chrome_h"] = max(0, out["outer_h"] - out["render_h"])
        except Exception:
            return out
        return out

    def calc_tight_row_cell(
        self,
        count: int,
        *,
        aspect_w: float = 9.0,
        aspect_h: float = 16.0,
        screen_w: int | None = None,
        screen_h: int | None = None,
        start_x: int = 0,
        start_y: int = 0,
        min_width: int = 160,
        min_height: int = 280,
        chrome_w: int = 0,
        chrome_h: int = 0,
    ) -> tuple[int, int]:
        """按数量与屏幕算一字排列单窗尺寸。

        - 目标：render 内容区 9:16 无黑边
        - 相邻窗口 outer 可重叠 chrome，使 render 左右贴紧（无缝隙）
        - chrome_w/h 为窗口装饰估算，首次布局可用 0，二次布局用实测值
        """
        n = max(1, int(count))
        if screen_w is None or screen_h is None:
            sw, sh = self.get_primary_screen_size()
            screen_w = screen_w or sw
            screen_h = screen_h or sh
        usable_w = max(min_width, int(screen_w) - int(start_x))
        usable_h = max(min_height, int(screen_h) - int(start_y))
        cw = max(0, int(chrome_w))
        ch = max(0, int(chrome_h))

        # 总宽 = chrome_w + n * render_w （窗口重叠 chrome）
        # render_w = (usable_w - chrome_w) // n
        render_w = max(min_width - cw, (usable_w - cw) // n)
        render_h = int(round(render_w * float(aspect_h) / float(aspect_w)))
        outer_h = render_h + ch
        if outer_h > usable_h and usable_h > ch + min_height // 2:
            render_h = max(min_height - ch, usable_h - ch)
            render_w = int(round(render_h * float(aspect_w) / float(aspect_h)))
            # 高度受限后仍保证 n 个 render 可贴满可用宽
            max_rw = max(min_width - cw, (usable_w - cw) // n)
            if render_w > max_rw:
                render_w = max_rw
                render_h = int(round(render_w * float(aspect_h) / float(aspect_w)))
        outer_w = max(min_width, render_w + cw)
        outer_h = max(min_height, render_h + ch)
        return int(outer_w), int(outer_h)

    def _set_main_window_rect(
        self,
        vmindex: int,
        x: int,
        y: int,
        w: int,
        h: int,
        *,
        hwnd: int | None = None,
        title: str | None = None,
    ) -> bool:
        """用 Win32 精确定位 main 窗口（不依赖 MuMu layout_window，避免 manager 锁阻塞）。"""
        hwin = int(hwnd or 0)
        if not hwin:
            hwin = self.resolve_main_hwnd(int(vmindex), lock_timeout=0.2)
        if not hwin:
            return False
        try:
            import ctypes

            user32 = ctypes.windll.user32
            # 最大化/最小化状态会让 SetWindowPos 的宽高看似成功但窗口仍占满屏幕。
            # 先恢复为普通窗口，再执行精确的一行定位。
            try:
                if user32.IsIconic(hwin) or user32.IsZoomed(hwin):
                    user32.ShowWindow(hwin, 9)  # SW_RESTORE
            except Exception:
                pass
            flags = 0x0004 | 0x0010  # SWP_NOZORDER | SWP_NOACTIVATE
            ok = user32.SetWindowPos(hwin, 0, int(x), int(y), int(w), int(h), flags)
            t = str(title if title is not None else int(vmindex))
            try:
                user32.SetWindowTextW(hwin, t)
            except Exception:
                pass
            return bool(ok)
        except Exception as exc:
            logger.warning("SetWindowPos VM=%s failed: %s", vmindex, exc)
            return False

    def layout_row_from_top_left(
        self,
        indices: list[int],
        width: int | None = None,
        height: int | None = None,
        margin: int = 0,
        start_x: int = 0,
        start_y: int = 0,
        *,
        auto_fit: bool = True,
        aspect_w: float = 9.0,
        aspect_h: float = 16.0,
        screen_w: int | None = None,
        screen_h: int | None = None,
    ) -> dict[str, Any]:
        """从电脑左上角一字排列：纯 Win32 贴紧，不占用 MuMuManager 锁。

        启动后即可排列（装包期间也能排）。窗口标题同步为序号数字。
        """
        import time

        ids = [int(i) for i in (indices or [])]
        if not ids:
            return {"count": 0, "width": 0, "height": 0, "margin": int(margin)}

        if screen_w is None or screen_h is None:
            sw, sh = self.get_primary_screen_size()
            screen_w = screen_w or sw
            screen_h = screen_h or sh

        # auto_fit 的正确语义是“窗口过多时自动缩小以保持一行”，不是把少量窗口
        # 自动放大铺满整块屏幕。未显式传宽高时以 GUI 默认 360x640 为上限。
        use_auto = bool(auto_fit)
        preferred_width = max(120, int(width or 360))
        preferred_height = max(200, int(height or 640))
        effective_margin = 0 if use_auto else max(0, int(margin))
        if use_auto:
            n = max(1, len(ids))
            usable_w = max(120, int(screen_w) - int(start_x) - effective_margin * (n - 1))
            usable_h = max(200, int(screen_h) - int(start_y))
            max_cell_w = max(120, usable_w // n)
            scale = min(
                1.0,
                float(max_cell_w) / float(preferred_width),
                float(usable_h) / float(preferred_height),
            )
            width = max(120, int(round(preferred_width * scale)))
            height = max(200, int(round(preferred_height * scale)))
        else:
            width = preferred_width
            height = preferred_height

        chrome_w = 0
        chrome_h = 0
        inset_left = 0
        inset_top = 0

        hwnds: dict[int, int] = {}
        for idx in ids:
            h = self.resolve_main_hwnd(idx, lock_timeout=0.15)
            if h:
                hwnds[idx] = h
                try:
                    import ctypes
                    ctypes.windll.user32.SetWindowTextW(h, str(idx))
                except Exception:
                    pass

        # 先按窗口外框宽度严格从左到右排，不再用估算 chrome 预先重叠窗口。
        step_x = int(width) + int(effective_margin)
        placed = 0
        for i, idx in enumerate(ids):
            mx = int(start_x) + i * int(step_x) - int(inset_left)
            my = int(start_y)
            ok = self._set_main_window_rect(
                idx, mx, my, int(width), int(height), hwnd=hwnds.get(idx), title=str(idx)
            )
            if ok:
                placed += 1
        time.sleep(0.12)

        for idx in ids:
            m = self.measure_player_window_win32(idx, hwnd=hwnds.get(idx))
            if m.get("chrome_w") is not None:
                chrome_w = max(int(chrome_w), int(m.get("chrome_w") or 0))
            if m.get("chrome_h") is not None:
                chrome_h = max(int(chrome_h), int(m.get("chrome_h") or 0))
            if m.get("inset_left") is not None:
                inset_left = int(m.get("inset_left") or 0)
            if m.get("inset_top") is not None:
                inset_top = int(m.get("inset_top") or 0)

        # 如 render 实测仍有统一间隙/重叠，只校正一次。旧实现使用 +gap，
        # 遇到负 gap 会进一步加重重叠；这里必须从步长中减去 gap。
        measures2 = [self.measure_player_window_win32(idx, hwnd=hwnds.get(idx)) for idx in ids]
        gaps = []
        for i in range(len(measures2) - 1):
            a = measures2[i]
            b = measures2[i + 1]
            if a.get("render_right") is not None and b.get("render_left") is not None:
                gaps.append(int(b["render_left"]) - int(a["render_right"]))
        if gaps:
            gap = sorted(gaps)[len(gaps) // 2]
            if abs(gap) >= 1:
                step_x = max(100, int(step_x) - int(gap))
                for i, idx in enumerate(ids):
                    target_rl = int(start_x) + i * int(step_x)
                    m = measures2[i] if i < len(measures2) else {}
                    il = int(m.get("inset_left") or inset_left or 0)
                    self._set_main_window_rect(
                        idx,
                        target_rl - il,
                        int(start_y),
                        int(width),
                        int(height),
                        hwnd=hwnds.get(idx),
                        title=str(idx),
                    )

        return {
            "count": len(ids),
            "placed": int(placed),
            "indices": ids,
            "width": int(width),
            "height": int(height),
            "margin": int(effective_margin),
            "step_x": int(step_x),
            "chrome_w": int(chrome_w),
            "chrome_h": int(chrome_h),
            "inset_left": int(inset_left),
            "inset_top": int(inset_top),
            "start_x": int(start_x),
            "start_y": int(start_y),
            "auto_fit": bool(use_auto),
            "compact_cap": True,
            "tile": "win32_no_manager_lock",
        }

    def install_apk(self, vmindex: int, apk: str | Path) -> subprocess.CompletedProcess:
        return self._run(
            [
                "control",
                "--vmindex",
                str(vmindex),
                "app",
                "install",
                "--apk",
                str(apk),
            ],
            timeout=300,
        )

    def launch_app(self, vmindex: int, package: str) -> subprocess.CompletedProcess:
        return self._run(
            [
                "control",
                "--vmindex",
                str(vmindex),
                "app",
                "launch",
                "--package",
                package,
            ],
            timeout=120,
        )

    def close_app(self, vmindex: int, package: str) -> subprocess.CompletedProcess:
        return self._run(
            [
                "control",
                "--vmindex",
                str(vmindex),
                "app",
                "close",
                "--package",
                package,
            ],
            timeout=60,
        )

    def adb_cmd(self, vmindex: int, cmd: str) -> subprocess.CompletedProcess:
        return self._run(["adb", "--vmindex", str(vmindex), "--cmd", cmd], timeout=120)

    def adb_connect(self, vmindex: int) -> subprocess.CompletedProcess:
        return self.adb_cmd(vmindex, "connect")

    def adb_host_port(self, vmindex: int) -> str:
        """优先读取 info.adb_port；失败再回退 base + index * step。"""
        try:
            node = self._node(vmindex)
            if node.get("adb_port"):
                host = node.get("adb_host_ip") or "127.0.0.1"
                return f"{host}:{int(node['adb_port'])}"
        except Exception:
            pass
        port = self.adb_base_port + int(vmindex) * self.adb_port_step
        return f"127.0.0.1:{port}"

    def adb_for(self, vmindex: int):
        """返回绑定到该 VM 的 AdbClient。"""
        from core.adb_client import AdbClient

        serial = self.adb_host_port(vmindex)
        return AdbClient(self.adb_path, serial)

    def recover_stuck_boot(
        self,
        vmindex: int,
        defaults: dict[str, Any] | None = None,
        log: LogFn = None,
    ) -> None:
        """卡 98%/starting_rom：关机 -> 重写可启动设置 -> 再 launch。"""
        self._log(log, f"VM={vmindex} 疑似卡 98%，执行恢复：shutdown + 重写设置 + launch")
        self.ensure_offline(vmindex, timeout=120, log=log)
        self.apply_create_defaults(vmindex, defaults, log=log, force_offline=True)
        try:
            self.launch(vmindex)
        except Exception as exc:
            self._log(log, f"VM={vmindex} 恢复 launch 异常: {exc}")

    def wait_android_started(
        self,
        vmindex: int,
        timeout: int = 240,
        defaults: dict[str, Any] | None = None,
        log: LogFn = None,
        recover: bool = True,
        stuck_seconds: int = 75,
        cancel_check=None,
    ) -> bool:
        """等待 Android 启动；长时间停留 starting_rom 则自动恢复。"""
        def _cancelled() -> bool:
            try:
                return bool(callable(cancel_check) and cancel_check())
            except Exception:
                return False

        deadline = time.time() + timeout
        starting_since: float | None = None
        recovered = False
        last_log = 0.0
        while time.time() < deadline:
            if _cancelled():
                self._log(log, f"VM={vmindex} Android 等待已取消")
                return False
            try:
                node = self._node(vmindex)
                android = bool(node.get("is_android_started"))
                proc = bool(node.get("is_process_started"))
                state = str(node.get("player_state") or "")
                err_msg = str(node.get("launch_err_msg") or node.get("error_msg") or "")
                err_code = node.get("launch_err_code") or node.get("error_code")
                now = time.time()
                if err_msg and ("admin" in err_msg.lower() or "administrator" in err_msg.lower()
                                or "VERR_NEED_NO_ADMIN" in err_msg or str(err_code) in ("-30110", "30110")):
                    self._log(
                        log,
                        f"VM={vmindex} 管理员权限冲突无法启动: code={err_code} msg={err_msg} "
                        f"(脚本应已降权调用 MuMuManager；请关闭所有模拟器后重试，或用非管理员运行)",
                    )
                    # 硬失败：继续轮询也无意义
                    return False
                if android:
                    self._log(log, f"VM={vmindex} Android 已启动 state={state}")
                    return True
                if proc and state in ("starting_rom", "starting", "start_begin", ""):
                    if starting_since is None:
                        starting_since = now
                    stuck_for = now - starting_since
                    if now - last_log >= 10:
                        self._log(
                            log,
                            f"VM={vmindex} 启动中 state={state} stuck={int(stuck_for)}s "
                            f"adb={node.get('adb_port')}",
                        )
                        last_log = now
                    if recover and not recovered and stuck_for >= stuck_seconds:
                        self.recover_stuck_boot(vmindex, defaults=defaults, log=log)
                        recovered = True
                        starting_since = time.time()
                        last_log = 0.0
                else:
                    if proc:
                        starting_since = starting_since or now
                    else:
                        # 进程未起，尝试 launch
                        if now - last_log >= 15:
                            self._log(log, f"VM={vmindex} 进程未启动，重新 launch")
                            last_log = now
                            try:
                                self.launch(vmindex)
                            except Exception:
                                pass
                        starting_since = None
            except Exception as exc:
                logger.debug("wait_android info error: %s", exc)
            # instant-stop-v2: 2.5s 可取消短睡
            end = time.time() + 2.5
            while time.time() < end:
                if _cancelled():
                    self._log(log, f"VM={vmindex} Android 等待已取消")
                    return False
                time.sleep(0.2)
        self._log(log, f"VM={vmindex} Android 启动超时 {timeout}s")
        return False

    def launch_and_wait(
        self,
        vmindex: int,
        timeout: int = 240,
        defaults: dict[str, Any] | None = None,
        log: LogFn = None,
        ensure_settings: bool = True,
        cancel_check=None,
    ) -> bool:
        """确保设置正确后启动并等待 Android。

        更新 2026-07-24:
        - ADB 已 device 时快速返回，避免重复 launch 把正常 VM 打成 starting_rom
        - 仅在未就绪时才 launch + wait/recover
        更新 2026-07-24(adb-false-ready-v2):
        - 快速路径必须同时满足 MuMu is_android_started + 正确 adb_port + boot_completed
        - 禁止仅凭残留 adb devices/假端口误判“已就绪”而跳过 launch（VM5 假阳性根因）
        """
        def _cancelled() -> bool:
            try:
                return bool(callable(cancel_check) and cancel_check())
            except Exception:
                return False

        if _cancelled():
            self._log(log, f"VM={vmindex} launch_and_wait 已取消(开始前)")
            return False

        # 快速路径：MuMu 已 android_started 且端口可连 boot_completed=1，不再二次 launch
        if self._adb_boot_ready(vmindex, tries=2):
            self._log(log, f"VM={vmindex} Android+ADB 已就绪，跳过重复 launch")
            return True

        if ensure_settings:
            # 仅在离线时强校验/重写；运行中只读校验
            node = self._node(vmindex)
            if not node.get("is_process_started"):
                check = self.verify_create_settings(vmindex, defaults)
                if not check["ok"]:
                    self.apply_create_defaults(vmindex, defaults, log=log, force_offline=True)
            else:
                # 已在跑但可能卡死，交给 wait 恢复
                pass
        try:
            self.launch(vmindex)
        except Exception as exc:
            self._log(log, f"VM={vmindex} launch 异常: {exc}")
        ok = self.wait_android_started(
            vmindex,
            timeout=timeout,
            defaults=defaults,
            log=log,
            recover=True,
            cancel_check=cancel_check,
        )
        if not ok:
            return False
        # Android 起来后再确认 ADB 真能 shell（避免 info 已 started 但 adb 未通）
        if self._adb_boot_ready(vmindex, tries=3, require_android_started=True):
            return True
        self._log(log, f"VM={vmindex} Android started 但 ADB 未就绪，继续等 ADB")
        deadline = time.time() + min(60, max(15, int(timeout) // 4))
        while time.time() < deadline:
            if _cancelled():
                self._log(log, f"VM={vmindex} launch_and_wait 已取消(ADB等待)")
                return False
            if self._adb_boot_ready(vmindex, tries=1, require_android_started=True):
                return True
            # instant-stop-v2: 可取消短睡
            end = time.time() + 2.0
            while time.time() < end:
                if _cancelled():
                    self._log(log, f"VM={vmindex} launch_and_wait 已取消(ADB等待)")
                    return False
                time.sleep(0.2)
        self._log(log, f"VM={vmindex} Android started 后 ADB 仍未就绪")
        return False

    def _adb_boot_ready(
        self,
        vmindex: int,
        tries: int = 2,
        require_android_started: bool = True,
    ) -> bool:
        """探测 ADB 是否已 boot；优先 info.adb_port，失败再回退端口公式。

        先看 devices 状态，避免对 offline 端口 shell 挂死。
        更新 2026-07-24: VM0 实际端口可能是 16385 而非 16384。
        更新 2026-07-24(adb-false-ready-v2):
        - 默认 require_android_started=True：MuMu info 必须 is_android_started
        - serial 必须与当前 info.adb_port 一致（若有），避免误连其它 VM/残留端口
        """
        import subprocess

        node: dict[str, Any] = {}
        try:
            node = self._node(vmindex) or {}
        except Exception:
            node = {}
        if require_android_started:
            if not bool(node.get("is_android_started")):
                return False
            if not bool(node.get("is_process_started", True)):
                # process 未起时 android_started 也不应信任
                if not bool(node.get("is_android_started")):
                    return False

        adb = str(self.adb_path)
        cf = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        expected_serial = ""
        try:
            if node.get("adb_port"):
                host = node.get("adb_host_ip") or "127.0.0.1"
                expected_serial = f"{host}:{int(node['adb_port'])}"
        except Exception:
            expected_serial = ""

        candidates: list[str] = []
        if expected_serial:
            candidates.append(expected_serial)
        else:
            try:
                candidates.append(self.adb_host_port(vmindex))
            except Exception:
                pass
            formula = f"127.0.0.1:{self.adb_base_port + int(vmindex) * self.adb_port_step}"
            if formula not in candidates:
                candidates.append(formula)

        for serial in candidates:
            # 若 MuMu 给出了明确 adb_port，只允许该 serial，禁止回落到错误端口的假阳性
            if expected_serial and serial != expected_serial:
                continue
            for _ in range(max(1, tries)):
                try:
                    subprocess.run(
                        [adb, "connect", serial],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=5, creationflags=cf,
                    )
                except Exception:
                    pass
                state = ""
                try:
                    cp = subprocess.run(
                        [adb, "devices"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=6, creationflags=cf,
                    )
                    for line in (cp.stdout or "").splitlines():
                        if line.startswith(serial + "\t") or line.startswith(serial + " "):
                            parts = line.split()
                            if len(parts) >= 2:
                                state = parts[1].strip()
                            break
                except Exception:
                    state = ""
                if state == "offline":
                    try:
                        subprocess.run(
                            [adb, "disconnect", serial],
                            capture_output=True, text=True, encoding="utf-8", errors="replace",
                            timeout=4, creationflags=cf,
                        )
                    except Exception:
                        pass
                    continue
                if state != "device":
                    continue
                try:
                    cp = subprocess.run(
                        [adb, "-s", serial, "shell", "getprop", "sys.boot_completed"],
                        capture_output=True, text=True, encoding="utf-8", errors="replace",
                        timeout=6, creationflags=cf,
                    )
                    if (cp.stdout or "").strip() == "1":
                        # 再确认一次 MuMu 侧仍 started，防止探测期间被关
                        if require_android_started:
                            try:
                                n2 = self._node(vmindex) or {}
                                if not bool(n2.get("is_android_started")):
                                    return False
                            except Exception:
                                return False
                        return True
                except Exception:
                    continue
        return False

    def create_and_launch(
        self,
        number: int,
        defaults: dict[str, Any] | None = None,
        name_prefix: str = "venmo",
        launch_workers: int = 2,
        boot_timeout: int = 240,
        log: LogFn = None,
        cancel_check=None,
    ) -> dict[str, Any]:
        """新建并多线程启动。create 串行，launch 并行。cancel_check 可中断。"""
        new_ids = self.create_configured(
            number,
            defaults=defaults,
            name_prefix=name_prefix,
            log=log,
            cancel_check=cancel_check,
        )
        results: dict[int, bool] = {}
        if not new_ids:
            return {"new_ids": [], "boot": results}

        def _cancelled() -> bool:
            try:
                return bool(cancel_check and cancel_check())
            except Exception:
                return False

        if _cancelled():
            self._log(log, "create_and_launch: 创建后已取消，跳过启动")
            return {"new_ids": new_ids, "boot": results, "cancelled": True}

        workers = max(1, min(int(launch_workers or 1), len(new_ids)))
        self._log(log, f"并行启动 {len(new_ids)} 台，线程={workers}")

        def _one(idx: int) -> tuple[int, bool]:
            if _cancelled():
                return idx, False
            ok = self.launch_and_wait(
                idx,
                timeout=boot_timeout,
                defaults=defaults,
                log=log,
                ensure_settings=True,
                cancel_check=cancel_check,
            )
            if _cancelled():
                return idx, False
            try:
                self.ensure_index_player_name(idx, str(int(idx)), retries=2, delay=0.2, log=log)
            except Exception as exc:
                self._log(log, f"VM={idx} 启动后写序号名失败: {exc}")
            try:
                self.set_player_window_title(idx, str(int(idx)))
            except Exception:
                pass
            return idx, ok

        # instant-stop-v2: wait 轮询，避免 as_completed 卡在已运行 future 上
        from concurrent.futures import wait, FIRST_COMPLETED
        ex = ThreadPoolExecutor(max_workers=workers)
        try:
            futs = [ex.submit(_one, i) for i in new_ids]
            pending = set(futs)
            while pending:
                if _cancelled():
                    self._log(log, "create_and_launch: 启动阶段已取消")
                    for f in list(pending):
                        try:
                            f.cancel()
                        except Exception:
                            pass
                    break
                done, pending = wait(pending, timeout=0.3, return_when=FIRST_COMPLETED)
                if not done:
                    continue
                for fut in done:
                    try:
                        idx, ok = fut.result(timeout=0)
                        results[idx] = ok
                    except Exception as exc:
                        self._log(log, f"启动任务异常: {exc}")
        finally:
            try:
                ex.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                ex.shutdown(wait=False)
        out = {"new_ids": new_ids, "boot": results}
        if _cancelled():
            out["cancelled"] = True
        return out

    def player_name(self, vmindex: int) -> str:
        node = self._node(vmindex)
        return str(node.get("name") or f"vm-{vmindex}")
