#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:?usage: ROLLBACK.sh TARGET_ROOT}"
BASE="$(cd "$(dirname "$0")" && pwd)"
cp "$BASE/rollback_source/app_ui.py" "$TARGET/app_ui.py"
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
else
  PYTHON_BIN=python
fi
"$PYTHON_BIN" -B - "$TARGET/app_ui.py" <<'PY'
from pathlib import Path
import ast,hashlib,sys
p=Path(sys.argv[1]); ast.parse(p.read_text('utf-8-sig'))
print('ROLLBACK_APP_SHA256='+hashlib.sha256(p.read_bytes()).hexdigest().upper())
print('ROLLBACK_AST_OK=True')
PY
echo "RESTORED_BEHAVIOR=refresh prefers existing 11 checked VMs and can drop newly typed VM11"
