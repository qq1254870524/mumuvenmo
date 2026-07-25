# -*- coding: utf-8 -*-
"""入口：MuMu Venmo 登录器。所有产物仅限本目录。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

from app_ui import main

if __name__ == "__main__":
    main()
