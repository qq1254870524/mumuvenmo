from pathlib import Path
import sys
sys.dont_write_bytecode = True
root = Path(r"C:/Users/zhang/Desktop/mumuvenmo")
sys.path.insert(0, str(root))
from paths import DATA_SETUP_DIR, DATA_STATE_DIR, ensure_under_root

idx = 999
flag = ensure_under_root(DATA_SETUP_DIR / f"setup_vm_{idx}.flag")
state = ensure_under_root(DATA_STATE_DIR / f"kitsune_ok_vm{idx}.json")
flag.parent.mkdir(parents=True, exist_ok=True)
state.parent.mkdir(parents=True, exist_ok=True)
flag.write_text("ok\n", encoding="utf-8")
state.write_text('{"ok": true, "settings_ok": false}', encoding="utf-8")
print("before", flag.exists(), state.exists())

for p in (flag, state):
    if p.exists():
        p.unlink()
print("after", flag.exists(), state.exists())
print("is_first_setup", not flag.exists())

# import modules
from core import worker_engine, root_setup
print("import_ok", hasattr(worker_engine.WorkerEngine, "_clear_vm_setup_state"))
src = Path(root / "core/root_setup.py").read_text(encoding="utf-8")
assert "install_ih8=bool(configure_settings)" in src
assert "Settings+ih8" in src
we = Path(root / "core/worker_engine.py").read_text(encoding="utf-8")
assert "recycle_old" in we
print("ASSERT_OK")
