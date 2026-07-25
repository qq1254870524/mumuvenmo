from pathlib import Path
p = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\root_setup.py")
src = p.read_text(encoding="utf-8")
old_cfg = (
    "        if not su_ok:\n"
    "            try:\n"
    "                if reuse_session:\n"
    "                    g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=True)\n"
    "                else:\n"
    "                    g = self.grant_shell_superuser(log=log)\n"
    "                outs.append(f\"grant={g[:80]}\")\n"
    "            except Exception as exc:\n"
    "                outs.append(f\"grant_err={exc}\")\n"
)
new_cfg = (
    "        if not su_ok:\n"
    "            try:\n"
    "                # always GRANT popup first; Superuser only fallback\n"
    "                popup = self.grant_shell_prefer_popup(log=log)\n"
    "                outs.append(f\"popup={str(popup)[:100]}\")\n"
    "                popup_ok = str(popup).startswith(\"popup_grant_ok\") or \"uid=0\" in str(popup)\n"
    "                if popup_ok:\n"
    "                    g = popup\n"
    "                    self._log(log, f\"configure_flags Shell GRANT弹窗成功，跳过 Superuser: {str(popup)[:120]}\")\n"
    "                else:\n"
    "                    self._log(log, f\"configure_flags Shell GRANT未确认，Superuser兜底 reuse={reuse_session}\")\n"
    "                    g = self.grant_shell_via_kitsune_superuser(log=log, reuse_session=bool(reuse_session))\n"
    "                outs.append(f\"grant={str(g)[:80]}\")\n"
    "            except Exception as exc:\n"
    "                outs.append(f\"grant_err={exc}\")\n"
)
if old_cfg not in src:
    raise SystemExit("configure block missing")
src = src.replace(old_cfg, new_cfg, 1)
p.write_text(src, encoding="utf-8")
print("configure_flags patched")
