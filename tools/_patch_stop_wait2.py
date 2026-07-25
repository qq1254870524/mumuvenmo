from pathlib import Path
import py_compile
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\worker_engine.py")
t = p.read_text(encoding="utf-8")
old = 'if shutdown_vms and vms and (not result["joined"]) and (not force):'
new = 'if (not result["joined"]) and (not force):'
if old not in t:
    if new in t:
        print("already ok")
    else:
        raise SystemExit("target if not found")
else:
    t = t.replace(old, new, 1)
    # improve log for shutdown_vms false case if still single log only
    old_log = '''            self.log(
                "当前登录任务尚未完成：跳过关闭模拟器，保持停止信号"
                "（不再领新号；当前号继续跑完后可再点停止，或点【强制停止】打断）"
            )
            # 保持 running=True / _stopping=True / threads，便于继续等或强制停止
            return result'''
    new_log = '''            if shutdown_vms and vms:
                self.log(
                    "当前登录任务尚未完成：跳过关闭模拟器，保持停止信号"
                    "（不再领新号；当前号继续跑完后可再点停止，或点【强制停止】打断）"
                )
            else:
                self.log(
                    "当前登录任务尚未完成：保持 worker 继续跑完"
                    "（不再领新号；可再点【强制停止】打断）"
                )
            # 保持 running=True / _stopping=True / threads
            return result'''
    if old_log in t:
        t = t.replace(old_log, new_log, 1)
        print("log branch updated")
    else:
        print("condition updated; log branch already different or missing")
    p.write_text(t, encoding="utf-8")
    print("wrote")
py_compile.compile(str(p), doraise=True)
t2 = p.read_text(encoding="utf-8")
assert 'if (not result["joined"]) and (not force):' in t2
assert 'if shutdown_vms and vms and (not result["joined"]) and (not force):' not in t2
print("VERIFY OK")
