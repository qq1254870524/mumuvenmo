# Changelog

## 2026-08-12 — 11 开流畅并发、ADB 命令级调度与无运行截图正式版

- 每个勾选模拟器使用独立 Worker；启动按 8 秒间隔提前派发，慢代理或慢启动不再阻塞后续健康模拟器。
- 登录工作流并发与 `workers`/勾选数量对齐；`adb_command_limit` 只限制同时运行的 `adb.exe` 命令，不再限制可启动模拟器或登录线程数量。
- 当前配置实测 11 个 Worker、11 台 MuMu、11 个 ADB device 全部在线并持续登录，GUI 响应正常，未出现 ADB timeout/卡死/未响应。
- 完全删除软件运行期 PNG 截图、`screencap` 和 `pull` 链路，消除每条结果附带的大文件 ADB 开销；保留自动化定位和结果识别必需的 UI XML dump。
- SOCKS5 代理池支持 `proxy|refresh_url` 单行格式、GUI 动态 `+`/`-`、自动分配与可选复用；启动前测网，不通时按 180 秒冷却刷新并延迟复测。
- 日志明确记录每个模拟器/Worker 分配的代理编号；代理故障可隔离、刷新和重新分配，不阻塞其他健康线程。
- 停止分为等待当前任务完成的正常停止与立即打断的强制停止；全部 Worker 退出后才解除运行状态，停止后不再产生尾日志。
- 运行日志轮转后监控同时聚合当前文件和 `.log.1`，避免漏判启动阶段；账号输入与四类输出数量守恒检查通过。

## 2026-07-31 — 并发装包稳定 + 停止任务秒级生效

### 背景
MuMu 模拟器升级后，多开新建/装包出现：
- 设置了新建数量=10、启动线程=10，实际只有 3~4 台在走后半段流程
- 装包中途卡死 / adb install 超时后不恢复
- Magisk Direct Install 点完后掉回桌面，未点到 LET'S GO
- 【停止任务】/【停止登录】不会立刻生效，常卡在 adb install 或长 sleep

本次修复**不改变**原有业务装包流程（门禁 → kitsune/nekobox/venmo → Magisk Direct Install → GRANT → Settings → ih8 → restart → provision 完成）。

### 主要修复

#### 1) 多线程同步装包（全并行走完后半段）
- 启动未就绪的 VM 仍进入 provision 池二次等待，避免 10 开只剩 3~4 台
- 装包线程与新建数量对齐，真正并行安装
- adb 重负载（install/push）可中断排队，避免互相饿死

#### 2) 装包卡死自愈（install-heal-fast-v3/v4）
- adb install TIMEOUT / NEED_HEAL 时不再盲第二轮 install
- 跳过 TIMEOUT 后昂贵的多次 package_installed 探测（原先可空耗 40s+）
- 上层走 **MuMu restart** 自愈后重装（不用 adb reboot）
- 实测 E2E：**6/6** 台全部完成
  - Magisk v27.2-kitsune-4
  - u:r:magisk:s0
  - 模块 ih8SecureLock
  - kitsune / nekobox / venmo 三包齐全

#### 3) Magisk UI / Direct Install 掉桌面恢复（flash-desktop-recover-v1）
- Direct Install / LET'S GO 过程掉回桌面时，软拉回 Magisk 会话重走
- Magisk UI 槽位与授权弹窗逻辑保持既有 19 步流程，不跳步

#### 4) 停止任务立刻生效（instant-stop-v2）
根因：
- as_completed() 会死等已在跑的 future
- root_setup 大量裸 time.sleep，取消信号到了还在睡
- 取消异常被 except Exception 吞掉
- ADB 只杀一次，长 install 可能漏杀

修复：
- 新增 TaskCancelled(BaseException)，停止时不会被业务 except Exception 吞掉
- root_setup 约 160 处 time.sleep → 可取消 sleep（取消即抛出退出）
- 装包/启动线程池改为 wait(timeout=0.3s) 轮询取消，不再 as_completed 死等
- 【停止任务】立刻 request_cancel_all + interrupt_all，并脉冲杀 ADB ~12s
- 取消后跳过装包后收尾排列
- launch_and_wait / wait_android_started / create_and_launch 支持 cancel_check
- 【停止登录】同步强制短 join + 脉冲打断 ADB

单元实测：
- 单线程长 sleep 取消延迟 ≈ **0.10s**
- 6 线程模拟装包池全部 cancelled ≈ **0.10s**

### 涉及文件
- app_ui.py
- core/root_setup.py
- core/adb_client.py
- core/mumu_manager.py
- config.example.json（补充 stop_force_join_timeout_seconds 等）

### 使用注意
1. 更新代码后请**重启** GUI（start.cmd / python -B main.py）
2. assets/apk/venmo_bundle/base.apk（~161MB）仍需本地自备，不在 GitHub 仓库内
3. 不要提交真实账号、代理、日志、导出结果
4. 建议：create_count 与 create_launch_workers 设为相同，以实现同步并行装包

### 验证建议
1. 删除测试用新建 VM 后，新建 6 台并装包，确认 6/6 走完 Magisk + ih8 + 三包
2. 装包中途点【停止任务】，日志应秒级出现取消，UI 回空闲，无僵尸线程继续装
