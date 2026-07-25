from pathlib import Path
import py_compile

p = Path("core/root_setup.py")
t = p.read_text(encoding="utf-8")

old_doc = '''        """检查/安装 Kitsune Magisk Direct Install。

        新建硬规则（create-direct-kill-reopen-v1）：
        1) 打开 Kitsune Mask
        2) 弹窗 Remember choice forever → Allow
        3) Hide 后立刻点 Install
        4) 检查第3项 Direct Install (modify /system directly)
        5) 找不到 → 结束 Kitsune 进程 → 再打开 → 直接点 Install → 再查第3项（最多杀进程1次）
        6) 找到 → 选第3项 → LET'S GO → MuMu restart device
        7) 重启后：GRANT → Settings(Zygisk/MagiskHide/Enforce SuList) 只 BACK 一次
           → Modules → Install from storage 装 ih8SecureLock-v8.zip → restart
        - 见到 Uninstall Magisk → 已安装，不点 Install
        - 绝不可选第2项 Direct Install (Recommended)
        - configure_settings=True（仅新建）：重启后 Shell 授权 + Settings 三项 + 可选 ih8
        - configure_settings=False（登录复用）：只确认 Uninstall / 必要时 Direct Install，不进 Settings
        """'''

new_doc = '''        """检查/安装 Kitsune Magisk Direct Install。

        新建硬规则 19 步（create-19steps-v1，禁止擅自改序）：
        1) 打开 Kitsune Mask
        2) 弹出框点 Remember choice forever
        3) 再点 Allow（永久授权；临时授权不会出现第3项）
        4) 点击 Hide
        5) 直接点 Install
        6) 检查 Direct Install (modify /system directly)
        7) 找不到 → 结束 Kitsune Mask 进程
        8) 再打开 Kitsune Mask
        9) 直接点 Install
        10) 再检查；找到第3项 Direct Install (modify /system directly) 就选第3项
            （绝不可选第2项 Direct Install (Recommended)）
        11) 点 LET'S GO
        12) 模拟器 restart device
        13) 再打开 Kitsune Mask
        14) 发起 shell 后，弹出窗口点 GRANT（不点 Deny）
        15) Settings 打开 Zygisk / MagiskHide / Enforce SuList
        16) 直接返回一次（只 BACK 一次，不进 Configure MagiskHide）
        17) 点 Modules
        18) 点 Install from storage
        19) 加载 ih8SecureLock-v8.zip 后 restart device

        其它：
        - 见到 Uninstall Magisk → 已安装，不点 Install
        - configure_settings=True（仅新建）：走 13–19
        - configure_settings=False（登录复用）：只确认 Uninstall / 必要时 Direct Install，不进 Settings/Modules
        """'''

if old_doc not in t:
    print("DOC_NOT_FOUND")
    # try find start of docstring
    i = t.find("def ensure_kitsune_magisk_direct_install")
    j = t.find('"""', i)
    k = t.find('"""', j+3)
    print(repr(t[j:k+3][:500]))
    raise SystemExit(1)

t = t.replace(old_doc, new_doc, 1)

# step markers (log only, no logic change)
replacements = [
    (
        'self._log(log, f"VM={vmindex} 已点完 Install，开始检查 Direct Install (modify /system directly)")',
        'self._log(log, f"VM={vmindex} [STEP5-6] 已点完 Install，开始检查 Direct Install (modify /system directly)")',
    ),
    (
        'f"VM={vmindex} round={round_i} 无第3项 Direct Install "\n'
        '                    f"({why}) visible={last_opts!r} → 结束Kitsune进程再开再点Install "\n'
        '                    f"({reopen_used+1}/{max_kill})"',
        'f"VM={vmindex} [STEP7-9] round={round_i} 无第3项 Direct Install "\n'
        '                    f"({why}) visible={last_opts!r} → 结束Kitsune进程再开再点Install "\n'
        '                    f"({reopen_used+1}/{max_kill})"',
    ),
    (
        'self._log(log, f"VM={vmindex} Magisk Direct Install 后 MuMu restart device")',
        'self._log(log, f"VM={vmindex} [STEP11-12] LETS GO 后 MuMu restart device")',
    ),
    (
        'self._log(log, f"VM={vmindex} first restart done, start shell for GRANT")',
        'self._log(log, f"VM={vmindex} [STEP13-14] first restart done, open Kitsune + shell for GRANT")',
    ),
    (
        'self._log(log, f"VM={vmindex} 一次会话 Settings: {str(flags)[:160]}")',
        'self._log(log, f"VM={vmindex} [STEP15-16] Settings三项+BACK一次: {str(flags)[:160]}")',
    ),
    (
        'self._log(log, f"VM={vmindex} 一次会话 ih8: {str(ih)[:160]}")',
        'self._log(log, f"VM={vmindex} [STEP17-19] Modules/Install from storage/ih8: {str(ih)[:160]}")',
    ),
]

for a,b in replacements:
    if a not in t:
        print("MISS:", a[:80])
    else:
        t = t.replace(a, b, 1)
        print("OK:", b[:60])

# header note
if "create-19steps-v1" not in t[:500]:
    # add near top if version comments exist
    pass

p.write_text(t, encoding="utf-8")
py_compile.compile(str(p), doraise=True)
print("DOC_AND_MARKERS_OK")