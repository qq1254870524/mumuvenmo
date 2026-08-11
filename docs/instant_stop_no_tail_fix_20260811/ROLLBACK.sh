#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-E:/mumuvenmo}"
ARTIFACT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT/core"
cp -f "$ARTIFACT_DIR/original/app_ui.py" "$ROOT/app_ui.py"
cp -f "$ARTIFACT_DIR/original/core/venmo_login.py" "$ROOT/core/venmo_login.py"
cp -f "$ARTIFACT_DIR/original/core/worker_engine.py" "$ROOT/core/worker_engine.py"
PYTHONDONTWRITEBYTECODE=1 python -B -c "import ast,pathlib; files=[pathlib.Path(r'$ROOT/app_ui.py'),pathlib.Path(r'$ROOT/core/venmo_login.py'),pathlib.Path(r'$ROOT/core/worker_engine.py')]; [ast.parse(p.read_text(encoding='utf-8-sig')) for p in files]; print('ROLLBACK_AST_OK=3')"
echo "ROLLBACK_RESTORED=app_ui.py,core/venmo_login.py,core/worker_engine.py"
