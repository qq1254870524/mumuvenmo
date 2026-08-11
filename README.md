# mumuvenmo

MuMu 多开 + Venmo 装包/登录 GUI 自动化工具。

## 2026-08-12 正式版

- 勾选多少台模拟器，就为多少台创建独立登录 Worker；先就绪的模拟器立即开始。
- `adb_command_limit` 只限制同时执行的 ADB 子进程，不限制多开数量或登录线程数量。
- 运行期 PNG 截图、`adb screencap` 和图片 `pull` 已删除；保留登录控件定位与结果识别必需的 UI XML dump。
- SOCKS5 使用 `proxy|refresh_url` 单行格式，GUI 可通过 `+`/`-` 动态增删。
- 代理启动前多轮测网；不通时遵守 180 秒刷新冷却，刷新后等待并复测；日志记录 VM、Worker 和代理编号。
- 实机验证 11 个 Worker、VM0–VM10、11/11 ADB device 持续并发运行，无 ADB timeout、卡死或 GUI 未响应。

完整更新见 [CHANGELOG.md](CHANGELOG.md) 与 [docs/UPDATE_2026-08-12.md](docs/UPDATE_2026-08-12.md)。

## 快速开始

```bat
cd mumuvenmo
copy config.example.json config.json
copy proxies\cocks5.txt.example proxies\cocks5.txt
copy accounts\input\accounts.example.txt accounts\input\import_active.txt
start.cmd
```

发布包已包含 NekoBox、Kitsune、Aurora、Venmo split APK 和 ih8 模块；`assets/apk/venmo_bundle/base.apk` 约 161MB，需自行放入（GitHub 单文件大小限制）。

## SOCKS5 代理格式

每行一套代理和刷新链接：

```text
HOST:PORT:USERNAME:PASSWORD|https://refresh.example/action
```

GUI 中点 `+` 新增一行，新增行点 `-` 删除。刷新链接可留空；同一链接默认 180 秒最多刷新一次。

## 并发配置

```json
{
  "workers": 11,
  "adb_workflow_limit": 11,
  "adb_command_limit": 4,
  "startup_wave_size": 1,
  "startup_wave_settle_seconds": 8,
  "allow_proxy_reuse": true
}
```

- `workers`：登录线程数。
- `adb_workflow_limit`：兼容字段，GUI 会与 `workers` 对齐。
- `adb_command_limit`：同时执行的 ADB 命令数，范围 1–4；它不是模拟器数量上限。
- `allow_proxy_reuse`：代理少于 Worker 时允许自动均衡复用。

## 账号格式

```text
账号----密码
账号1----密码----账号2----残号----姓名
```

四类实时导出位于 `export/classified/`：

- `correct.txt`
- `risk_control.txt`
- `wrong_password.txt`
- `no_network.txt`

处理完成后，账号从输入源原子移出并写入对应结果文件；输入剩余数与四类结果累计数保持守恒。

## 目录结构

- `app_ui.py` / `main.py`：GUI 与入口
- `core/`：MuMu、ADB、代理、装包、登录与 Worker
- `assets/`：小型 APK、Venmo splits 与模块
- `config.example.json`：无真实数据的配置模板
- `proxies/cocks5.txt.example`：代理格式模板
- `accounts/input/accounts.example.txt`：账号格式模板

## 发布包排除项

- `config.json`
- 真实账号与真实代理
- 日志、导出结果、运行状态
- `__pycache__`、`.pyc`、临时文件
- `assets/apk/venmo_bundle/base.apk`

## License

仅供本地授权自动化与自用测试。
