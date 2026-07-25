# -*- coding: utf-8 -*-
"""no-tun: refresh bound change-ip (3min), wait 5s host check, reconnect; else reassign."""
from __future__ import annotations
from pathlib import Path
import py_compile

WE = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\worker_engine.py")
t = WE.read_text(encoding="utf-8")

# header note
if "no-tun-refresh-ip-v1" not in t:
    t = t.replace(
        "# 2026-07-25 stop-wait-login-v1:",
        "# 2026-07-25 no-tun-refresh-ip-v1: NekoBox无tun时刷绑定刷新链接(3分钟限频)+等5s主机测通后重连/换绑\n# 2026-07-25 stop-wait-login-v1:",
        1,
    )

helper = '''
    def _recover_nekobox_after_no_tun(
        self,
        worker_id: str,
        vmindex: int,
        rs: "RootSetup",
        proxy: ProxyProfile,
    ) -> tuple[ProxyProfile, bool]:
        """NekoBox 已 Connect 仍无 tun：按规则处理绑定代理。

        1) 用当前 profile 的刷新链接刷 IP（3 分钟限频）
        2) 等待 5 秒后主机测 SOCKS5 连通
        3) 关闭再开启 NekoBox（强制 reimport + Connect）
        4) 仍无 tun：整包换绑（SOCKS5 + change-ip 一起换）再导入连接
        返回 (proxy, tun_ok)
        """
        if proxy is None:
            return proxy, False

        # 1+2) 刷绑定刷新链接并主机测通
        ref = self._refresh_proxy_if_needed(
            worker_id,
            proxy,
            reason="nekobox_no_tun",
        )
        net_ok = bool(ref.get("network_ok") or ref.get("ok"))
        if not net_ok:
            try:
                net_ok = bool(check_proxy_profile_host(proxy, timeout=10.0))
            except Exception:
                net_ok = False
            self.log(
                f"{worker_id} 刷IP后主机复测 profile={proxy.profile_name} "
                f"proxy_ok={net_ok} status={ref.get('status')}"
            )
        else:
            self.log(
                f"{worker_id} 刷IP/主机测通完成 profile={proxy.profile_name} "
                f"status={ref.get('status')} network_ok={ref.get('network_ok')}"
            )

        def _stop_vpn() -> None:
            try:
                msg = rs.stop_nekobox_vpn_ui(log=lambda m: self.log(f"{worker_id} {m}"))
                self.log(f"{worker_id} 刷IP前/换绑前已停 VPN: {str(msg)[:160]}")
            except Exception as exc:
                self.log(f"{worker_id} 停 VPN 异常: {exc}")

        def _reimport_connect(p: ProxyProfile, tag: str) -> bool:
            _stop_vpn()
            try:
                msg = rs.ensure_auth_then_connect(
                    p.profile_name,
                    p.host,
                    int(p.port),
                    p.username,
                    p.password,
                    log=lambda m: self.log(f"{worker_id} {m}"),
                    verify_vpn=True,
                    vpn_wait_seconds=25.0,
                    force_reimport=True,
                )
                self.log(f"{worker_id} {tag} NekoBox reimport+connect: {str(msg)[:300]}")
            except Exception as exc:
                self.log(f"{worker_id} {tag} NekoBox reimport+connect 失败: {exc}")
            try:
                ok = bool(rs.is_vpn_active(skip_ui=True))
            except Exception:
                ok = False
            self.log(f"{worker_id} {tag} tun_active={ok} profile={p.profile_name}")
            return ok

        # 3) 当前绑定代理：关再开
        if _reimport_connect(proxy, "刷IP后"):
            return proxy, True

        # 4) 整包换绑
        tried = {str(getattr(proxy, "profile_name", "") or "")}
        max_try = max(1, len(getattr(self.proxy_pool, "proxies", []) or []))
        for _i in range(max_try):
            if self._stop.is_set():
                break
            try:
                alt = self.proxy_pool.reassign(
                    f"vm-{vmindex}",
                    exclude_names=tried,
                )
            except Exception as rexc:
                self.log(f"{worker_id} no_tun 换绑失败: {rexc}")
                break
            if alt is None:
                self.log(
                    f"{worker_id} no_tun 无空闲代理可换绑，保留 profile="
                    f"{proxy.profile_name} 再刷一次自己的 change-ip"
                )
                ref2 = self._refresh_proxy_if_needed(
                    worker_id,
                    proxy,
                    reason="nekobox_no_tun_keep",
                )
                if ref2.get("network_ok") or ref2.get("ok"):
                    if _reimport_connect(proxy, "保留代理再刷后"):
                        return proxy, True
                break

            old_name = str(getattr(proxy, "profile_name", "") or "")
            old_cip = str(getattr(proxy, "change_ip_url", "") or "")
            proxy = alt
            tried.add(str(proxy.profile_name or ""))
            try:
                with self._lock:
                    self._vm_proxy[int(vmindex)] = proxy
            except Exception:
                pass
            cip = str(getattr(proxy, "change_ip_url", "") or "")
            self.log(
                f"{worker_id} no_tun 整包换绑 {old_name} -> {proxy.profile_name} "
                f"endpoint={proxy.host}:{proxy.port} "
                f"cip_changed={old_cip != cip} (SOCKS5+刷新链接一起换)"
            )
            pre = self._ensure_proxy_ready_before_import(worker_id, proxy)
            if not pre.get("ok"):
                self.log(
                    f"{worker_id} 换绑后主机仍不通 profile={proxy.profile_name} "
                    f"status={pre.get('status')}，继续尝试下一条"
                )
                continue
            if _reimport_connect(proxy, "换绑后"):
                return proxy, True

        return proxy, False

'''

if "_recover_nekobox_after_no_tun" not in t:
    anchor = "        return result\n\n\n    def _update_active_index("
    if anchor not in t:
        raise SystemExit("insert anchor not found")
    t = t.replace(anchor, "        return result\n" + helper + "\n    def _update_active_index(", 1)
    print("helper inserted")
else:
    print("helper already present")

old = '''                        if not tun:
                            self.log(f"{worker_id} 致命: 仍无 tun0，本 worker 不进入登录")
                            return
'''
new = '''                        if not tun:
                            self.log(
                                f"{worker_id} 无 tun0：按规则刷绑定刷新链接"
                                f"(3分钟限频)+等5s主机测通后重连；仍失败则整包换绑"
                            )
                            proxy, tun = self._recover_nekobox_after_no_tun(
                                worker_id,
                                vmindex,
                                rs,
                                proxy,
                            )
                            try:
                                with self._lock:
                                    self._vm_proxy[int(vmindex)] = proxy
                            except Exception:
                                pass
                            if not tun:
                                self.log(
                                    f"{worker_id} 致命: 刷IP/换绑后仍无 tun0，"
                                    f"本 worker 不进入登录 profile="
                                    f"{getattr(proxy, 'profile_name', '')}"
                                )
                                return
                            self.log(
                                f"{worker_id} 恢复 tun 成功 profile="
                                f"{getattr(proxy, 'profile_name', '')}，继续登录"
                            )
'''
if old not in t:
    if "_recover_nekobox_after_no_tun(" in t and "无 tun0：按规则刷绑定刷新链接" in t:
        print("call site already patched")
    else:
        # show context
        i = t.find("仍无 tun0")
        print(repr(t[i-120:i+180]))
        raise SystemExit("call site not found")
else:
    t = t.replace(old, new, 1)
    print("call site patched")

WE.write_text(t, encoding="utf-8")
py_compile.compile(str(WE), doraise=True)
print("COMPILE OK")
# sanity
tt = WE.read_text(encoding="utf-8")
assert "_recover_nekobox_after_no_tun" in tt
assert "nekobox_no_tun" in tt
assert "致命: 刷IP/换绑后仍无 tun0" in tt
print("VERIFY OK")
