# -*- coding: utf-8 -*-
"""项目内日志，禁止写到外部目录。"""
from __future__ import annotations

import logging
import os
import re
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
    now = datetime.now()
    log_file = ensure_under_root(LOG_RUN_DIR / f"run_{now.strftime('%Y%m%d')}.log")
    # 日志文件可能由另一权限级别的进程创建，Windows 会在 import 阶段抛
    # PermissionError。主日志打不开时改用当前用户/进程独立文件；两者都失败
    # 时保留控制台日志，禁止因为日志权限导致 GUI 无法启动。
    safe_user = re.sub(
        r"[^A-Za-z0-9_.-]+",
        "_",
        str(os.environ.get("USERNAME") or "user"),
    ).strip("._") or "user"
    fallback_file = ensure_under_root(
        LOG_RUN_DIR
        / f"run_{now.strftime('%Y%m%d')}_{safe_user}_{now.strftime('%H%M%S')}_{os.getpid()}.log"
    )
    fh = None
    file_errors: list[str] = []
    for candidate in (log_file, fallback_file):
        try:
            fh = RotatingFileHandler(
                candidate,
                maxBytes=5 * 1024 * 1024,
                backupCount=5,
                encoding="utf-8",
            )
            if candidate != log_file:
                sys.stderr.write(
                    f"主日志无写权限，已切换到独立日志: {candidate}\n"
                )
            break
        except OSError as exc:
            file_errors.append(f"{candidate}: {type(exc).__name__}: {exc}")
    if fh is not None:
        fh.setLevel(logging.DEBUG)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(threadName)s %(message)s")
    if fh is not None:
        fh.setFormatter(fmt)
    sh.setFormatter(fmt)
    if fh is not None:
        logger.addHandler(fh)
    elif file_errors:
        sys.stderr.write(
            "日志文件不可写，当前仅输出到控制台: " + " | ".join(file_errors) + "\n"
        )
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
