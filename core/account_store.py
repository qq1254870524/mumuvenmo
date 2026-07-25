# -*- coding: utf-8 -*-
"""账号解析、线程安全分配、四类实时分类导出。

更新记录 2026-07-24:
- 支持 账号----密码 与 账号1----密码----账号2----残号----姓名（- 与 ---- 均可）
- 成功/失败终态跳过，不重复登录
- 四类文本实时导出（叠加）：
  1) correct.txt        : SUCCESS（验证码/掩码成功）
  2) risk_control.txt   : RISK_CONTROL（账密正确但风控红框）
  3) wrong_password.txt : WRONG_PASSWORD
  4) no_network.txt     : NO_NETWORK + 其它失败
- 导出：保持原始字段格式，用 TAB 或 ---- 连接，末尾追加识别到的红框/掩码（单行，不换行块）
- 账号2 登录成功时：正确账号放账号1，错误放账号2
- 2026-07-24 补 remaining()/stats() 供 GUI 与 smoke 使用
- 2026-07-24 风控单独第四个文本 risk_control.txt
- 2026-07-25 import-skip-v1:
  - 导入时按四类导出主键跳过已明确成功/失败账号
  - 同步从导入源文本删除这些行
  - load() 记录 last_load_stats，UI 只显示待处理
- 2026-07-25 realtime-import-prune-v1:
  - finish() 导出后立即同步导入源：只保留 pending/running
  - pending_source_text() 供 UI 实时刷新文本框
"""
from __future__ import annotations

import csv
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable, Optional

from paths import (
    EXPORT_CLASSIFIED_DIR,
    EXPORT_CORRECT_NAME,
    EXPORT_NONET_NAME,
    EXPORT_RISK_NAME,
    EXPORT_WRONG_NAME,
    resolve_export_dir,
)

# 分隔符：---- 或 单个 - 或 tab/多空白
SPLIT_RE = re.compile(r"(?:\t+|----+|-+|,|，|;|；|\|)")


class LoginResult(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    RISK_CONTROL = "risk_control"  # 账密正确但风控
    WRONG_PASSWORD = "wrong_password"
    NO_NETWORK = "no_network"
    ERROR = "error"
    SKIPPED = "skipped"


MSG_RISK = (
    "We're having some trouble completing your request right now. "
    "Please try again shortly, and if it persists let us know."
)
# 兼容无空格粘连写法（用户要求导出用此文案）
MSG_RISK_COMPACT = (
    "We're having some trouble completing your requestright now. "
    "Please try again shortly, and if it persistslet us know."
)
MSG_WRONG = "Incorrect login Check your info and try again."
MSG_NO_NET = "Something went wrong. Try again."

# 明确成功/失败：claim 时跳过
TERMINAL_STATUSES = frozenset(
    {
        LoginResult.SUCCESS.value,
        LoginResult.RISK_CONTROL.value,
        LoginResult.WRONG_PASSWORD.value,
        LoginResult.NO_NETWORK.value,
        LoginResult.ERROR.value,
        LoginResult.SKIPPED.value,
    }
)

# 四类导出桶
BUCKET_CORRECT = "correct"  # SUCCESS only
BUCKET_RISK = "risk_control"  # RISK_CONTROL 风控
BUCKET_WRONG = "wrong_password"
BUCKET_NO_NET = "no_network"

# 明确终态导出文件名（叠加，导入时据此跳过）
FINISHED_EXPORT_NAMES = (
    EXPORT_CORRECT_NAME,
    EXPORT_RISK_NAME,
    EXPORT_WRONG_NAME,
    EXPORT_NONET_NAME,
)


def account_key_of_line(s: str) -> str:
    """账号主键：行首字段（账号1），用于跳过/去重。"""
    s = (s or "").replace("\ufeff", "").replace("\u200b", "").strip()
    if not s or s.startswith("#"):
        return ""
    for sep in ("\t", "----", "—", " - ", "-"):
        if sep in s:
            return s.split(sep, 1)[0].strip().lower()
    parts = s.split()
    return (parts[0] if parts else s).strip().lower()


def load_finished_account_keys(export_dir: str | Path | None = None) -> set[str]:
    """从四类导出文本读取已明确成功/失败的账号主键（跳过用）。"""
    d = resolve_export_dir(export_dir)
    keys: set[str] = set()
    for name in FINISHED_EXPORT_NAMES:
        path = d / name
        if not path.exists() or not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                k = account_key_of_line(line)
                if k:
                    keys.add(k)
        except Exception:
            continue
    return keys



@dataclass
class Account:
    account1: str
    password: str
    account2: str = ""
    residual: str = ""  # 残号
    name: str = ""
    masked_phone: str = ""
    status: str = LoginResult.PENDING.value
    message: str = ""
    used_account: str = ""  # 最终正确/尝试成功的账号
    wrong_account: str = ""
    worker_id: str = ""
    vm_index: int = -1
    profile: str = ""
    updated_at: str = ""
    raw_line: str = ""
    line_no: int = 0
    extra: dict = field(default_factory=dict)

    def export_line(self) -> str:
        """兼容旧逻辑的单行摘要（live 日志用）。"""
        return format_export_oneline(self)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("extra", None)
        return d


def _normalize_risk_text(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()



def _strip_bidi(s: str) -> str:
    if not s:
        return ""
    drop = {
        "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
        "\u200e", "\u200f", "\u2066", "\u2067", "\u2068", "\u2069",
    }
    out = "".join(ch for ch in s if ch not in drop)
    out = out.replace("\u2018", "'").replace("\u2019", "'")
    out = out.replace("\u201c", '"').replace("\u201d", '"')
    out = out.replace("\u00a0", " ")
    return out


def _is_login_loading_text(ui_text: str) -> bool:
    """提交后加载中：表单可能仍可见，但禁止 resubmit，应等待红框/验证页。

    更新 2026-07-25 loading-no-resubmit-v2:
    - 识别 This may take a few seconds / please wait / submitting 等
    - 修复上一轮补丁字符串未闭合导致 SyntaxError
    """
    t = _normalize_risk_text(ui_text or "")
    if not t:
        return False
    keys = (
        "this may take a few seconds",
        "may take a few seconds",
        "please wait",
        "just a moment",
        "one moment",
        "loading",
        "submitting",
        "checking your info",
        "securing your account",
    )
    if any(k in t for k in keys):
        return True
    # 部分 dump 会把 "Password entered" 与 submit 态并排出现
    compact = t.replace(" ", "")
    if "passwordentered" in compact and "submit" in compact:
        return True
    return False


def _still_on_login_form_text(ui_text: str) -> bool:
    """登录表单仍在前台（邮箱/密码/Log in），此时不得判 SUCCESS。

    更新 2026-07-25 loading-no-resubmit-v1:
    - 加载中仍算在登录流程，禁止 SUCCESS
    - 加载中由 _is_login_loading_text 单独识别，避免反复点 Log in
    """
    t = _normalize_risk_text(ui_text or "")
    if not t:
        return False
    has_email = ("email, username" in t) or ("email username or phone" in t.replace(",", ""))
    has_password = "password" in t
    has_login = ("log in" in t) or ("forgot password" in t)
    strong = (
        "verify it's you",
        "verify it is you",
        "we'll text you a code",
        "we will text you a code",
        "text you a code",
        "text me a code",
        "enter the code",
        "verification code",
        "remember this device",
        "choose a way to verify",
        "how do you want to verify",
        "security code",
        "we sent a code",
        "sent you a code",
        "two-step",
        "two step",
        "confirm it's you",
        "confirm it is you",
    )
    if any(k in t for k in strong):
        return False
    return bool(has_email and has_password and has_login)


def _is_verification_or_masked_ui(ui_text: str) -> bool:
    """验证页 / 掩码手机邮箱页 = 账密正确。

    2026-07-24 fix-false-success-v1:
    - 登录表单仍在（Email+Password+Log in）时一律不算成功
    - 去掉过宽的单独 "verification"/"to verify"/"get a code" 关键词
    - 掩码手机/邮箱正则仍有效，但同样受登录表单门禁约束
    """
    raw = _strip_bidi(ui_text or "")
    t = _normalize_risk_text(raw)
    if not t:
        return False
    if _still_on_login_form_text(raw):
        return False
    keys = (
        "verify it's you",
        "verify it is you",
        "we'll text you a code",
        "we will text you a code",
        "text you a code",
        "text me a code",
        "send a code",
        "enter the code",
        "enter code",
        "verification code",
        "confirm it's you",
        "confirm it is you",
        "two-step",
        "two step",
        "remember this device",
        "choose a way to verify",
        "how do you want to verify",
        "security code",
        "we sent a code",
        "sent you a code",
        "we'll email you a code",
        "we will email you a code",
        "email you a code",
    )
    if any(k in t for k in keys):
        return True
    if re.search(r"\(\s*[\d*xX]{1,3}\s*\)\s*[\d*xX*\-\s]{3,}\d{2,}", raw):
        return True
    if re.search(r"\b\d{0,3}\*{2,}[\d\-*]{2,}\d{2,}\b", raw):
        return True
    if re.search(r"[A-Za-z0-9._%+\-]*\*+[A-Za-z0-9._%+\-]*@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", raw):
        return True
    return False
def classify_ui_text(ui_text: str) -> tuple[LoginResult, str]:
    """识别登录红框/验证页/掩码联系方式。mask-timeout-retry-v2"""
    t = _normalize_risk_text(ui_text)
    compact = t.replace(" ", "")

    if (
        "having some trouble completing your request" in t
        or "havingsometroublecompletingyourrequest" in compact
        or "if it persists" in t
        or "ifitpersists" in compact
    ):
        return LoginResult.RISK_CONTROL, MSG_RISK_COMPACT

    if "incorrect login" in t or "check your info and try again" in t:
        return LoginResult.WRONG_PASSWORD, MSG_WRONG

    if "something went wrong" in t and "try again" in t:
        return LoginResult.NO_NETWORK, MSG_NO_NET

    # WebView / 代理无网：Webpage not available、net::ERR、连接失败
    if (
        "webpage not available" in t
        or "webpagenotavailable" in compact
        or "net::err" in t
        or "err_connection" in t
        or "err_proxy" in t
        or "err_name_not_resolved" in t
        or "err_timed_out" in t
        or "err_internet_disconnected" in t
        or "unable to connect" in t
        or "could not connect" in t
        or ("the webpage at" in t and ("venmo.com" in t or "http" in t))
    ):
        return LoginResult.NO_NETWORK, "webpage_not_available"

    if "too many login attempts" in t or "try again a little later" in t:
        return LoginResult.ERROR, "too_many_login_attempts"

    if _is_verification_or_masked_ui(ui_text or ""):
        return LoginResult.SUCCESS, "verification_or_masked_contact"

    if any(k in t for k in ("search people", "your balance", "pay or request", "scan")):
        if not _still_on_login_form_text(ui_text or ""):
            return LoginResult.SUCCESS, "login_success"

    return LoginResult.PENDING, ""

def _looks_like_masked_phone(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    if re.search(r"\*+|•+|·+|\(\*+\)|\(\d\*|\(\d+\)\s*\*+", s):
        return True
    if re.search(r"\*+\d|\d\*+\d|\*+\d{2,}", s):
        return True
    if s.startswith("*") or "xxx" in s.lower():
        return True
    # (3**) ***-**80
    if re.search(r"\(\d?\*+\)|\*{2,}.*\d{2,}", s):
        return True
    return False


def _looks_like_message_note(s: str) -> bool:
    low = (s or "").lower()
    return any(
        k in low
        for k in (
            "incorrect login",
            "something went wrong",
            "having some trouble",
            "too_many",
            "login_success",
            "verification",
            "cannot_reach",
            "login_timeout",
        )
    )


def split_account_fields(raw: str) -> list[str]:
    """拆分账号行：优先 ----，再 tab，再 手机-密码，再多空白。"""
    raw = (raw or "").strip()
    if not raw:
        return []

    if "----" in raw:
        parts = [p.strip() for p in raw.split("----")]
    elif "\t" in raw:
        parts = [p.strip() for p in raw.split("\t")]
    else:
        # 纯数字账号-密码（3106343580-Volvo5318）
        m = re.match(r"^(\+?\d{6,20})-(.+)$", raw)
        if m:
            # 密码段若仍含 ---- 再拆
            rest = m.group(2)
            if "----" in rest:
                parts = [m.group(1)] + [p.strip() for p in rest.split("----")]
            else:
                parts = [m.group(1), rest.strip()]
        elif re.search(r"\s{2,}", raw):
            parts = [p.strip() for p in re.split(r"\s{2,}", raw) if p.strip()]
        else:
            # 邮箱/用户名 + 空白 + 密码（至少两段）
            parts = [p.strip() for p in re.split(r"\s+", raw) if p.strip()]
            if len(parts) < 2 and "-" in raw and "@" not in raw:
                # 非邮箱的 a-b-c：按 - 拆（用户明确 - 也可识别）
                parts = [p.strip() for p in raw.split("-") if p.strip()]
            elif len(parts) < 2 and "@" in raw and "-" in raw:
                # email-password 少见：最后一个 - 分割
                left, right = raw.rsplit("-", 1)
                if "@" in left and right:
                    parts = [left.strip(), right.strip()]

    # 去掉尾部空段
    while parts and parts[-1] == "":
        parts.pop()
    return parts


def parse_account_line(line: str, line_no: int = 0) -> Optional[Account]:
    # 更新 2026-07-24: 去掉 UTF-8 BOM / 零宽字符，避免注释行被当成账号
    raw = (line or "").replace("\ufeff", "").replace("\u200b", "").strip()
    if not raw or raw.startswith("#") or raw.startswith("//"):
        return None

    parts = split_account_fields(raw)
    if len(parts) < 2:
        return None

    account1 = parts[0]
    password = parts[1]
    account2 = ""
    residual = ""
    name = ""
    masked = ""
    message = ""
    status = LoginResult.PENDING.value

    # 尾部已知文案 → 终态（重导历史结果时跳过）
    if len(parts) >= 3 and _looks_like_message_note(parts[-1]):
        message = parts[-1]
        tail = parts[-1].lower().replace(" ", "")
        if "incorrectlogin" in tail or "checkyourinfo" in tail:
            status = LoginResult.WRONG_PASSWORD.value
        elif "havingsometrouble" in tail or "ifitpersists" in tail:
            status = LoginResult.RISK_CONTROL.value
        elif "somethingwentwrong" in tail:
            status = LoginResult.NO_NETWORK.value
        else:
            status = LoginResult.ERROR.value
        parts = parts[:-1]

    # 格式1: 账号 密码 [掩码]
    # 格式2: 账号1 密码 账号2 残号 姓名 [掩码]
    if len(parts) == 2:
        pass
    elif len(parts) == 3:
        if _looks_like_masked_phone(parts[2]):
            masked = parts[2]
        else:
            account2 = parts[2]
    elif len(parts) == 4:
        account2, residual = parts[2], parts[3]
        if _looks_like_masked_phone(parts[3]) and not parts[2]:
            residual = ""
            masked = parts[3]
        elif _looks_like_masked_phone(parts[3]) and _looks_like_masked_phone(parts[2]):
            # 少见：密码后两段都是掩码
            residual, masked = parts[2], parts[3]
            account2 = ""
    elif len(parts) >= 5:
        account2 = parts[2]
        residual = parts[3]
        name = parts[4]
        if len(parts) >= 6:
            if _looks_like_masked_phone(parts[5]):
                masked = parts[5]
            else:
                # 第6段非掩码时并入 message 备查
                if not message:
                    message = parts[5]

    return Account(
        account1=account1,
        password=password,
        account2=account2,
        residual=residual,
        name=name,
        masked_phone=masked,
        status=status,
        message=message,
        raw_line=raw,
        line_no=line_no,
    )


def load_accounts_from_text(text: str) -> list[Account]:
    accounts: list[Account] = []
    for i, line in enumerate(text.splitlines(), start=1):
        acc = parse_account_line(line, i)
        if acc:
            accounts.append(acc)
    return accounts


def load_accounts_from_file(path: str | Path) -> list[Account]:
    p = Path(path)
    # utf-8-sig 自动去掉文件 BOM
    text = p.read_text(encoding="utf-8-sig", errors="replace")
    return load_accounts_from_text(text)


def result_bucket(status: str | LoginResult) -> str | None:
    """映射到四类导出桶；RUNNING/PENDING 不入桶。"""
    if isinstance(status, LoginResult):
        status = status.value
    if status == LoginResult.SUCCESS.value:
        return BUCKET_CORRECT
    if status == LoginResult.RISK_CONTROL.value:
        return BUCKET_RISK
    if status == LoginResult.WRONG_PASSWORD.value:
        return BUCKET_WRONG
    if status in (LoginResult.NO_NETWORK.value, LoginResult.ERROR.value):
        return BUCKET_NO_NET
    return None


def format_export_oneline(acc: Account) -> str:
    """单行摘要：沿用 TAB/----，末尾备注。"""
    return format_classified_block(acc).rstrip("\n")


def _detect_field_sep(raw: str) -> str:
    """优先沿用导入行分隔：TAB 或 ----，默认 ----。"""
    s = raw or ""
    if "\t" in s and "----" not in s:
        return "\t"
    if "----" in s:
        return "----"
    if "\t" in s:
        return "\t"
    return "----"


def _export_base_parts(acc: Account) -> list[str]:
    """导出基础字段：尽量保持原始字段，去掉尾部历史红框文案。"""
    raw = (acc.raw_line or "").strip()
    parts: list[str] = []
    if raw:
        parts = split_account_fields(raw)
        # 去掉已有结果文案
        while parts and _looks_like_message_note(parts[-1]):
            parts.pop()
        # 若 raw 末尾是掩码手机，保留；后面 success 再补
    if len(parts) < 2:
        parts = [(acc.account1 or "").strip(), (acc.password or "").strip()]
        if (acc.account2 or acc.residual or acc.name):
            parts.extend([
                (acc.account2 or "").strip(),
                (acc.residual or "").strip(),
                (acc.name or "").strip(),
            ])
        phone0 = (acc.masked_phone or "").strip()
        if phone0:
            parts.append(phone0)
    # 账号2 登录成功后 account1/account2 可能已调换：以当前 account 字段为准重建
    # 仅当字段与 raw 解析明显不一致时覆盖前两段
    a1 = (acc.account1 or "").strip()
    pw = (acc.password or "").strip()
    if a1 and pw:
        if not parts:
            parts = [a1, pw]
        else:
            parts[0] = a1
            if len(parts) >= 2:
                parts[1] = pw
            else:
                parts.append(pw)
        # 双号：同步 account2/residual/name
        if acc.account2 or acc.residual or acc.name:
            while len(parts) < 5:
                parts.append("")
            parts[2] = (acc.account2 or "").strip()
            parts[3] = (acc.residual or "").strip()
            parts[4] = (acc.name or "").strip()
            # 掩码若在第6段
            phone = (acc.masked_phone or "").strip()
            if phone:
                if len(parts) >= 6 and _looks_like_masked_phone(parts[5]):
                    parts[5] = phone
                elif len(parts) == 5:
                    parts.append(phone)
                elif len(parts) > 6:
                    # 保持长度，替换第一个像掩码的
                    for i in range(5, len(parts)):
                        if _looks_like_masked_phone(parts[i]):
                            parts[i] = phone
                            break
                    else:
                        parts.append(phone)
    # 去掉末尾空段（但中间空段保留以对齐双号格式时尽量不丢）
    while parts and parts[-1] == "":
        parts.pop()
    return parts


def format_classified_block(acc: Account) -> str:
    """单行导出：原始字段 + TAB/---- + 红框文案或掩码手机。

    例:
      3106343580----Volvo5318----We're having some trouble...
      8148440612\tNanataty12!\tIncorrect login Check your info and try again.
      3106343580----Volvo5318----(3**) ***-**80
    """
    sep = _detect_field_sep(acc.raw_line or "")
    parts = _export_base_parts(acc)
    status = acc.status
    phone = (acc.masked_phone or "").strip()
    msg = (acc.message or "").strip()

    def _append_unique(token: str) -> None:
        token = (token or "").strip()
        if not token:
            return
        if parts and parts[-1] == token:
            return
        # 避免重复追加同一红框
        if any(token == p for p in parts[-2:]):
            return
        parts.append(token)

    if status == LoginResult.RISK_CONTROL.value:
        _append_unique(msg or MSG_RISK_COMPACT)
    elif status == LoginResult.WRONG_PASSWORD.value:
        _append_unique(msg or MSG_WRONG)
    elif status == LoginResult.NO_NETWORK.value:
        _append_unique(msg or MSG_NO_NET)
    elif status == LoginResult.SUCCESS.value:
        if phone:
            # 若末段已是掩码则替换，否则追加
            if parts and _looks_like_masked_phone(parts[-1]):
                parts[-1] = phone
            else:
                _append_unique(phone)
    elif status in (LoginResult.PENDING.value, LoginResult.RUNNING.value, LoginResult.SKIPPED.value, ""):
        # 未完成：只保留原始字段，不追加状态
        pass
    else:
        # ERROR 等
        _append_unique(msg or status or "error")

    # 再清一次尾空
    while parts and parts[-1] == "":
        parts.pop()
    return sep.join(parts) + "\n"



def apply_account_order(acc: Account, used_account: str = "", wrong_account: str = "") -> None:
    """正确账号放账号1，错误放账号2。"""
    original_a1 = acc.account1
    original_a2 = acc.account2

    if used_account:
        acc.used_account = used_account
    if wrong_account:
        acc.wrong_account = wrong_account

    # 成功/风控：used 为正确账号
    if used_account:
        correct = used_account
        wrong = wrong_account or ""
        if not wrong:
            if correct == original_a1:
                wrong = original_a2
            elif correct == original_a2:
                wrong = original_a1
            else:
                wrong = original_a1 if original_a1 != correct else original_a2
        acc.account1 = correct
        acc.account2 = wrong if wrong != correct else ""
        if wrong and wrong != correct:
            acc.wrong_account = wrong
        return

    # 仅密码错误：wrong_account 标记失败的那个
    if wrong_account:
        # 双号都错时 keep a1/a2 原值，wrong_account 记最后失败
        if original_a2 and wrong_account == original_a2:
            # a1 已失败后试 a2 也失败：保持 a1=原a1, a2=原a2
            acc.account1 = original_a1
            acc.account2 = original_a2
            acc.wrong_account = wrong_account
        else:
            acc.wrong_account = wrong_account


class AccountStore:
    """线程安全账号池 + 固定四类文本叠加导出。"""

    FIXED_NAMES = {
        BUCKET_CORRECT: EXPORT_CORRECT_NAME,
        BUCKET_RISK: EXPORT_RISK_NAME,
        BUCKET_WRONG: EXPORT_WRONG_NAME,
        BUCKET_NO_NET: EXPORT_NONET_NAME,
    }

    def __init__(self, export_dir: str | Path | None = None):
        self._lock = threading.RLock()
        self.accounts: list[Account] = []
        self.last_load_stats: dict[str, int] = {
            "imported": 0,
            "skipped": 0,
            "pending": 0,
            "pruned": 0,
        }
        self._cursor = 0
        self._in_use: set[int] = set()
        self.source_path: Path | None = None  # 导入源文件，出结果后删除对应行
        self._finished_callbacks: list = []
        self.set_export_dir(export_dir)

    def add_finished_callback(self, cb) -> None:
        if cb and cb not in self._finished_callbacks:
            self._finished_callbacks.append(cb)

    def set_export_dir(self, export_dir: str | Path | None = None) -> None:
        """设置导出目录（可自由选择）；四类固定文件名，已有内容叠加不覆盖。"""
        with self._lock:
            self.export_dir = resolve_export_dir(export_dir)
            self.export_classified_dir = self.export_dir
            # 兼容旧字段
            self.export_live_dir = self.export_dir
            self.export_results_dir = self.export_dir
            self.export_all_dir = self.export_dir
            self.stamp = "fixed"
            self.correct_path = self.export_dir / EXPORT_CORRECT_NAME
            self.risk_control_path = self.export_dir / EXPORT_RISK_NAME
            self.wrong_password_path = self.export_dir / EXPORT_WRONG_NAME
            self.no_network_path = self.export_dir / EXPORT_NONET_NAME
            self.live_export_path = self.export_dir / "_live_unused.txt"
            self.result_csv_path = self.export_dir / "_csv_unused.csv"
            self._bucket_paths = {
                BUCKET_CORRECT: self.correct_path,
                BUCKET_RISK: self.risk_control_path,
                BUCKET_WRONG: self.wrong_password_path,
                BUCKET_NO_NET: self.no_network_path,
            }
            self._init_files()

    def _init_files(self) -> None:
        # 固定四文件：不存在才创建空文件，已有数据保留叠加
        for path in self._bucket_paths.values():
            if not path.exists():
                path.write_text("", encoding="utf-8")

    def set_source_path(self, path: str | Path | None) -> None:
        with self._lock:
            self.source_path = Path(path) if path else None

    def load(self, accounts: Iterable[Account], source_path: str | Path | None = None) -> int:
        """加载账号。

        规则：
        - 四类导出里已有明确成功/失败的账号：跳过登录，不重复导出
        - 导入源文本里同步删掉这些已出结果的行
        - 返回待处理（pending）数量
        - last_load_stats: imported/skipped/pending/pruned
        """
        acc_list = list(accounts)
        with self._lock:
            if source_path is not None:
                self.source_path = Path(source_path)
            finished = load_finished_account_keys(self.export_dir)
            kept: list[Account] = []
            skipped_keys: set[str] = set()
            skipped_count = 0
            for acc in acc_list:
                raw = (acc.raw_line or "").strip()
                k1 = account_key_of_line(raw) or account_key_of_line(acc.account1 or "")
                k2 = account_key_of_line(acc.account2 or "")
                hit = bool(k1 and k1 in finished) or bool(k2 and k2 in finished)
                # 也认 used/wrong
                ku = account_key_of_line(acc.used_account or "")
                kw = account_key_of_line(acc.wrong_account or "")
                if (ku and ku in finished) or (kw and kw in finished):
                    hit = True
                if hit or acc.status in TERMINAL_STATUSES:
                    acc.status = LoginResult.SKIPPED.value
                    if not acc.message:
                        acc.message = "already_finished_in_export"
                    if k1:
                        skipped_keys.add(k1)
                    if k2:
                        skipped_keys.add(k2)
                    skipped_count += 1
                    # 不进入待登录队列（直接丢弃，避免 UI 仍显示）
                    continue
                acc.status = LoginResult.PENDING.value
                kept.append(acc)
            self.accounts = kept
            self._cursor = 0
            self._in_use.clear()
            pruned = 0
            # 从导入源文本删除已出结果账号（按主键）
            if self.source_path is not None and (finished or skipped_keys):
                pruned = self._prune_source_keys(finished | skipped_keys)
            self.last_load_stats = {
                "imported": len(acc_list),
                "skipped": skipped_count,
                "pending": len(kept),
                "pruned": int(pruned or 0),
            }
            return len(self.accounts)

    def _prune_source_keys(self, keys: set[str]) -> int:
        """按账号主键从导入源文件删除已明确成功/失败的行。返回删除行数。"""
        path = self.source_path
        if path is None or not keys:
            return 0
        try:
            path = Path(path)
            if not path.exists() or not path.is_file():
                return 0
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            return 0
        lines = text.splitlines(keepends=True)
        new_lines: list[str] = []
        removed = 0
        keyset = {k.strip().lower() for k in keys if k}
        for line in lines:
            s = line.replace("\ufeff", "").replace("\u200b", "").strip()
            if not s:
                new_lines.append(line)
                continue
            k = account_key_of_line(s)
            if k and k in keyset:
                removed += 1
                continue
            new_lines.append(line)
        if removed:
            try:
                path.write_text("".join(new_lines), encoding="utf-8")
            except Exception:
                return 0
        return removed

    def total(self) -> int:
        with self._lock:
            return len(self.accounts)

    def counts(self) -> dict[str, int]:
        with self._lock:
            c: dict[str, int] = {}
            for a in self.accounts:
                c[a.status] = c.get(a.status, 0) + 1
            c["in_use"] = len(self._in_use)
            c["pending"] = sum(
                1 for a in self.accounts if a.status == LoginResult.PENDING.value
            )
            return c

    def stats(self) -> dict[str, int]:
        with self._lock:
            st = {
                "total": len(self.accounts),
                "pending": 0,
                "running": 0,
                "success": 0,
                "risk_control": 0,
                "wrong_password": 0,
                "no_network": 0,
                "error": 0,
                "skipped": 0,
                "in_use": len(self._in_use),
            }
            for a in self.accounts:
                if a.status in st:
                    st[a.status] += 1
                elif a.status == LoginResult.PENDING.value:
                    st["pending"] += 1
            st["pending"] = sum(
                1 for a in self.accounts if a.status == LoginResult.PENDING.value
            )
            st["running"] = sum(
                1 for a in self.accounts if a.status == LoginResult.RUNNING.value
            )
            return st

    def remaining(self) -> int:
        with self._lock:
            return sum(1 for a in self.accounts if a.status == LoginResult.PENDING.value)

    def claim_next(
        self,
        worker_id: str = "",
        vm_index: int = -1,
        profile: str = "",
    ) -> Optional[Account]:
        """领取下一个待处理账号；明确成功/失败终态一律跳过。"""
        with self._lock:
            n = len(self.accounts)
            if n == 0:
                return None

            def _try_claim(i: int) -> Optional[Account]:
                if i in self._in_use:
                    return None
                acc = self.accounts[i]
                if acc.status in TERMINAL_STATUSES:
                    return None
                if acc.status == LoginResult.RUNNING.value:
                    return None
                if acc.status not in (LoginResult.PENDING.value, ""):
                    return None
                self._in_use.add(i)
                acc.status = LoginResult.RUNNING.value
                acc.worker_id = worker_id
                acc.vm_index = vm_index
                acc.profile = profile
                acc.updated_at = datetime.now().isoformat(timespec="seconds")
                self._cursor = i + 1
                return acc

            for i in range(self._cursor, n):
                acc = _try_claim(i)
                if acc:
                    return acc
            for i in range(0, n):
                acc = _try_claim(i)
                if acc:
                    return acc
            return None

    def release_without_result(self, acc: Account) -> None:
        with self._lock:
            idx = self._index_of(acc)
            if idx is not None:
                self._in_use.discard(idx)
            if acc.status == LoginResult.RUNNING.value:
                acc.status = LoginResult.PENDING.value

    def finish(
        self,
        acc: Account,
        status: LoginResult | str,
        message: str = "",
        used_account: str = "",
        wrong_account: str = "",
        masked_phone: str = "",
    ) -> None:
        cbs = []
        with self._lock:
            if isinstance(status, LoginResult):
                status = status.value
            acc.status = status
            if message:
                acc.message = message
            if masked_phone:
                acc.masked_phone = masked_phone

            apply_account_order(acc, used_account=used_account, wrong_account=wrong_account)

            if status == LoginResult.RISK_CONTROL.value:
                acc.message = MSG_RISK_COMPACT
            elif status == LoginResult.WRONG_PASSWORD.value:
                if not acc.message or "incorrect" not in acc.message.lower():
                    acc.message = MSG_WRONG
            elif status == LoginResult.NO_NETWORK.value:
                acc.message = MSG_NO_NET

            acc.updated_at = datetime.now().isoformat(timespec="seconds")
            idx = self._index_of(acc)
            if idx is not None:
                self._in_use.discard(idx)
            # 主输出：四类固定文本叠加
            self._append_classified(acc)
            # 导入源文本：出结果后删除该账号行
            self._remove_done_from_source(acc)
            cbs = list(self._finished_callbacks)
        for cb in cbs:
            try:
                cb(acc)
            except Exception:
                pass

    def _index_of(self, acc: Account) -> Optional[int]:
        for i, a in enumerate(self.accounts):
            if a is acc:
                return i
            if a.line_no == acc.line_no and a.raw_line == acc.raw_line:
                return i
            if a.line_no == acc.line_no and a.account1 == acc.account1:
                return i
        return None

    def _append_classified(self, acc: Account) -> None:
        bucket = result_bucket(acc.status)
        if not bucket:
            return
        path = self._bucket_paths[bucket]
        block = format_classified_block(acc)
        if not (block or "").strip():
            # 防止写出空行导致“像没导出”
            a1 = (acc.account1 or "").strip()
            pw = (acc.password or "").strip()
            tail = (acc.masked_phone or acc.message or acc.status or "").strip()
            block = "%s----%s----%s\n" % (a1, pw, tail)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(block)
            f.flush()
            try:
                import os
                os.fsync(f.fileno())
            except Exception:
                pass
        # 轻量校验：文件应包含账号
        try:
            data = path.read_text(encoding="utf-8", errors="ignore")
            key = (acc.account1 or "").strip()
            if key and key not in data:
                with path.open("a", encoding="utf-8") as f2:
                    f2.write(block)
                    f2.flush()
        except Exception:
            pass

    def _remove_done_from_source(self, acc: Account) -> None:
        """出结果后从导入源删除该账号；以 pending 全量回写为准。"""
        self._sync_source_pending()

    def _sync_source_pending(self) -> int:
        """把导入源文件重写为当前待处理/进行中账号（实时删除已导出成功/失败）。

        返回写入行数。无 source_path 时返回 0。
        调用方通常已持有 self._lock。
        """
        path = self.source_path
        if path is None:
            return 0
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            return 0

        lines: list[str] = []
        for acc in self.accounts:
            if acc.status not in (
                LoginResult.PENDING.value,
                LoginResult.RUNNING.value,
                "",
            ):
                continue
            line = (acc.raw_line or "").strip()
            if not line:
                line = f"{acc.account1}----{acc.password}"
                if acc.account2:
                    line += f"----{acc.account2}"
                if acc.residual:
                    line += f"----{acc.residual}"
                if acc.name:
                    line += f"----{acc.name}"
            if line:
                lines.append(line)

        content = ('\n'.join(lines) + ('\n' if lines else ''))
        try:
            path.write_text(content, encoding="utf-8")
        except Exception:
            return 0
        return len(lines)

    def pending_source_text(self) -> str:
        """待处理账号原文，用于刷新 UI 文本框。"""
        with self._lock:
            lines: list[str] = []
            for acc in self.accounts:
                if acc.status in (
                    LoginResult.PENDING.value,
                    LoginResult.RUNNING.value,
                    "",
                ):
                    line = (acc.raw_line or "").strip()
                    if not line:
                        line = f"{acc.account1}----{acc.password}"
                        if acc.account2:
                            line += f"----{acc.account2}"
                        if acc.residual:
                            line += f"----{acc.residual}"
                        if acc.name:
                            line += f"----{acc.name}"
                    lines.append(line)
            return ("\n".join(lines) + ("\n" if lines else ""))

    def export_all(self, path: str | Path | None = None) -> Path:
        with self._lock:
            if path is None:
                path = self.export_dir / "export_all_snapshot.txt"
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                for acc in self.accounts:
                    f.write(format_export_oneline(acc) + "\n")
            return path

    def export_classified_snapshot(self) -> dict[str, Path]:
        """全量重写四类固定文件（会覆盖叠加内容，慎用）。默认不在实时路径调用。"""
        with self._lock:
            buffers = {
                BUCKET_CORRECT: [],
                BUCKET_RISK: [],
                BUCKET_WRONG: [],
                BUCKET_NO_NET: [],
            }
            for acc in self.accounts:
                b = result_bucket(acc.status)
                if b:
                    buffers[b].append(format_classified_block(acc))
            for b, path in self._bucket_paths.items():
                with path.open("w", encoding="utf-8") as f:
                    for block in buffers[b]:
                        f.write(block)
            return dict(self._bucket_paths)

    def snapshot_lines(self, limit: int = 200) -> list[str]:
        with self._lock:
            return [format_export_oneline(a) for a in self.accounts[:limit]]

    def classified_paths(self) -> dict[str, str]:
        return {
            "correct": str(self.correct_path),
            "risk_control": str(self.risk_control_path),
            "wrong_password": str(self.wrong_password_path),
            "no_network": str(self.no_network_path),
            "export_dir": str(self.export_dir),
        }
