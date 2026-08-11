# mumuvenmo

MuMu 多开 + Venmo 装包/登录自动化（本地工具）。

## 2026-08-11 更新摘要

- GUI SOCKS5 代理池改为每行 `代理|刷新链接`，支持 `+` 新增、`-` 删除并持久化
- 每个 Worker 启动前独立检测绑定代理；不通时刷新一次，等待 10 秒后最多复测 5 轮
- 同一刷新链接固定 180 秒冷却；健康代理对应的线程立即启动，不等待慢代理
- 多选模拟器保持独立并发：首次缺包的 VM 会先自愈安装，完成后自动进入登录循环
- 模拟器窗口固定从左上角按 360x640 紧凑一行排列；数量过多时只缩小，不再放大占满屏幕
- 日志文件遇到占用/权限问题时自动切换到进程专用日志，不再阻止 GUI 启动
- 停止登录后，当前登录调用栈会在约 0.1 秒内收到取消；只有 `workers=0` 才显示停止完成，模拟器关闭后不再持续刷 ADB 尾日志
- 强停取消的账号会退回待处理，新任务会自动清理上一轮 ADB 取消标记

代理行示例：

```text
host:port:user:pass|https://example.com/change-ip/TOKEN
```

完整说明见 [docs/UPDATE_2026-08-11.md](docs/UPDATE_2026-08-11.md)。

## 2026-07-31 更新摘要

- 多开同步装包：新建 N 台可 N 台并行走完后半段（不再只剩 3~4 台）
- 装包卡死自愈：adb install 超时后 MuMu restart 再装，E2E 实测 6/6
- Magisk Direct Install 掉桌面可软恢复
- 【停止任务】/【停止登录】秒级取消（instant-stop-v2，约 0.1s）
- **不改变**原有业务装包流程

完整说明见 [CHANGELOG.md](CHANGELOG.md) 与 [docs/UPDATE_2026-07-31.md](docs/UPDATE_2026-07-31.md)。

## 快速开始

```bat
cd mumuvenmo
copy config.example.json config.json
copy proxies\cocks5.txt.example proxies\cocks5.txt
copy accounts\input\accounts.example.txt accounts\input\import_active.txt
```

1. 小型 APK（NekoBox / Kitsune / Aurora / Venmo splits）已随仓库提供；仅需自行放入 `assets/apk/venmo_bundle/base.apk`（约 161MB，超 GitHub 单文件限制）
2. 在 GUI 代理池逐行填写 `代理|刷新链接`，或编辑 `proxies\cocks5.txt`
3. 编辑 `accounts\input\import_active.txt` 写入账号
4. 启动：

```bat
start.cmd
```

或：

```bat
python -B main.py
```

## 推荐并行参数

为了「新建几台就几台同时装包」，建议：

```json
{
  "create_count": 6,
  "create_launch_workers": 6,
  "workers": 6,
  "stop_force_join_timeout_seconds": 8
}
```

`create_launch_workers` 应 **>= create_count**，否则会串行排队，看起来像只有 3~4 台在动。

## 账号格式

```text
账号----密码
账号1----密码----账号2----残号----姓名
```

导出分类（默认 `export/classified/`）：

- correct.txt
- wrong_password.txt
- locked.txt
- captcha_or_review.txt
- residual.txt
- other_fail.txt

## 目录结构（摘要）

- `app_ui.py` / `main.py`：GUI 与入口
- `core/`：MuMu / ADB / 装包 / Magisk / 登录 / worker
- `assets/apk/`：小型 APK 与模块（`base.apk` 需自备）
- `config.example.json`：配置模板（本地复制为 `config.json`）
- `proxies/cocks5.txt.example`：代理模板
- `accounts/input/accounts.example.txt`：账号模板

## 安全与仓库约定

**禁止提交：**

- 真实 `config.json`
- 真实账号文件
- 真实代理凭据
- 日志 / 导出结果 / state
- `assets/apk/venmo_bundle/base.apk`（过大）

## License

仅供本地授权自动化与自用测试。
