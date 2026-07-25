from pathlib import Path
p2 = Path(r"C:\Users\zhang\Desktop\mumuvenmo\core\adb_client.py")
t2 = p2.read_text(encoding="utf-8")
o2 = t2
if "shareduid-grant-fastpath-v2" not in t2:
    t2 = t2.replace(
        "# 2026-07-25 shareduid-grant-click-v1:",
        "# 2026-07-25 shareduid-grant-fastpath-v2: Magisk SharedUID GRANT immediate click\n# 2026-07-25 shareduid-grant-click-v1:",
        1,
    )
marker = "        # -------- MuMu SuperUser 专用快路径：resource-id 点 Forever → Allow --------\n        nemu = False\n"
if marker not in t2:
    raise SystemExit("marker missing")
fast_lines = [
"        # -------- Magisk SharedUID Shell GRANT fast path --------",
"        def _magisk_grant_fast(cur_xml: str, cur_low: str) -> str:",
"            if not cur_xml or not cur_low:",
"                return \"\"",
"            if any(k in cur_low for k in (",
"                \"com.android.settings:id/remember_forever\",",
"                \"com.android.settings:id/this_time_only\",",
"                \"com.nemu.superuser\",",
"                \"remember choice forever\",",
"                \"requesting superuser access\",",
"            )):",
"                return \"\"",
"            has_grant_btn = any(k in cur_low for k in (",
"                \"io.github.huskydg.magisk:id/grant\",",
"                \"com.topjohnwu.magisk:id/grant\",",
"                'text=\"grant\"', 'text=\"Grant\"', 'text=\"GRANT\"',",
"                'content-desc=\"grant\"', 'content-desc=\"Grant\"',",
"            ))",
"            has_shell_ctx = any(k in cur_low for k in (",
"                \"shareduid\", \"shell\", \"surequest\", \"superuser request\",",
"                \"wants to access\", \"root access\",",
"            ))",
"            if not (has_grant_btn and has_shell_ctx):",
"                if not (has_grant_btn and any(k in cur_low for k in (\"io.github.huskydg.magisk\", \"com.topjohnwu.magisk\", \"magisk\")) and any(k in cur_low for k in ('text=\"deny\"', 'text=\"Deny\"', \"拒绝\"))):",
"                    return \"\"",
"            for lab in (\"Forever\", \"永久\", \"Always\", \"始终\", \"Always allow\"):",
"                try:",
"                    b = self.find_node_bounds(text_substr=lab, xml=cur_xml)",
"                except Exception:",
"                    b = None",
"                if b:",
"                    try:",
"                        self.tap_bounds(b)",
"                        time.sleep(0.15)",
"                    except Exception:",
"                        pass",
"                    break",
"            for rid in (\"io.github.huskydg.magisk:id/grant\", \"com.topjohnwu.magisk:id/grant\"):",
"                b = self.find_node_bounds(resource_id=rid, xml=cur_xml)",
"                if b:",
"                    self.tap_bounds(b)",
"                    time.sleep(0.25)",
"                    return f\"magisk_grant_fast_rid={rid.split('/')[-1]}\"",
"            hit = self.tap_any([\"Grant\", \"GRANT\", \"Allow\", \"ALLOW\", \"允许\", \"同意\"], xml=cur_xml, match_desc=True, match_text=True)",
"            if hit:",
"                time.sleep(0.25)",
"                return f\"magisk_grant_fast_text={hit}\"",
"            deny_b = self.find_node_bounds(text_substr=\"Deny\", xml=cur_xml) or self.find_node_bounds(text_substr=\"拒绝\", xml=cur_xml)",
"            if deny_b:",
"                x1, y1, x2, y2 = deny_b",
"                w = max(40, x2 - x1)",
"                self.tap(x2 + w // 2 + 50, (y1 + y2) // 2)",
"                time.sleep(0.25)",
"                return \"magisk_grant_fast_via_deny_right\"",
"            return \"\"",
"",
"        try:",
"            mg = _magisk_grant_fast(xml, low)",
"            if mg:",
"                return mg",
"        except Exception:",
"            pass",
"",
"        # -------- MuMu SuperUser 专用快路径：resource-id 点 Forever → Allow --------",
"        nemu = False",
"",
]
t2 = t2.replace(marker, "\n".join(fast_lines) + "\n", 1)
old_missing = "                # MuMu SuperUser：未选 Forever 绝不点临时 Allow（否则没有 Direct Install 第3项）\n                return \"forever_missing_no_temp_allow\"\n"
new_missing = "                # MuMu SuperUser：未选 Forever 绝不点临时 Allow（否则没有 Direct Install 第3项）\n                try:\n                    mg2 = _magisk_grant_fast(xml, low)\n                    if mg2:\n                        return mg2\n                except Exception:\n                    pass\n                return \"forever_missing_no_temp_allow\"\n"
if old_missing not in t2:
    raise SystemExit("missing block not found")
t2 = t2.replace(old_missing, new_missing, 1)
if t2 == o2:
    raise SystemExit("no change")
p2.write_text(t2, encoding="utf-8")
print("adb_client patched")
