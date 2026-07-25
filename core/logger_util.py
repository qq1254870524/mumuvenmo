# -*- coding: utf-8 -*-
"""项目内日志，禁止写到外部目录。"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Optional

from paths import LOG_RUN_DIR, ensure_under_root

LogCallback = Optional[Callable[[str], None]]


def setup_logger(name: str = "mumuvenmo") -> logging.Logger:
    LOG_RUN_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    log_file = ensure_under_root(LOG_RUN_DIR / f"run_{datetime.now().strftime('%Y%m%d')}.log")
    fh = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(threadName)s %(message)s")
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


class UiLogBridge(logging.Handler):
    def __init__(self, callback: LogCallback):
        super().__init__(level=logging.INFO)
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        if not self.callback:
            return
        try:
            self.callback(self.format(record))
        except Exception:
            pass
