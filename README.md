# mumuvenmo

MuMu 模拟器 Venmo 登录器（本地 GUI 工具）。

- 多线程启动/管理 MuMu 模拟器
- 账号导入、自动分配、实时分类导出
- 可选 NekoBox SOCKS5 代理
- Kitsune Mask / ih8 模块初始化流程
- 所有运行产物默认限制在项目目录内

## 环境要求

- Windows
- Python 3.10+
- 已安装 [MuMu Player](https://www.mumuplayer.com/)
- 本机 ADB（默认使用 MuMu 自带 `nx_main\adb.exe`）

## 快速开始

```bat
cd mumuvenmo
copy config.example.json config.json
copy proxies\cocks5.txt.example proxies\cocks5.txt
copy accounts\input\accounts.example.txt accounts\input\import_active.txt
```

1. 小型 APK（NekoBox / Kitsune / Aurora / Venmo splits）已随仓库提供；仅需自行放入 ssets/apk/venmo_bundle/base.apk（约 161MB，超 GitHub 单文件限制）
2. 编辑 `proxies\cocks5.txt` 写入 SOCKS5
3. 编辑 `accounts\input\import_active.txt` 写入账号
4. 启动：

```bat
start.cmd
```

或：

```bat
python -B main.py
```

## 账号格式

```text
账号----密码
账号1----密码----账号2----残号----姓名
```

导出分类（默认 `export/classified/`）：

- `correct.txt`
- `wrong_password.txt`
- `risk_control.txt`
- `no_network.txt`

## 目录结构

```text
mumuvenmo/
  main.py / app_ui.py / paths.py / start.cmd
  core/                 # 核心逻辑
  tools/                # 调试与补丁脚本
  assets/apk/           # 本地 APK（不入库）
  assets/modules/       # Magisk 模块
  accounts/             # 账号输入
  proxies/              # 代理列表
  export/               # 实时导出
  logs/                 # 运行日志
  data/                 # 运行状态
  screenshots/          # 调试截图
  docs/                 # 设计说明
```

## 安全说明

本仓库**不包含**：

- 真实账号/密码
- 真实代理凭据
- 运行日志、截图、导出结果
- 超大 Venmo ase.apk（需自行准备；其余小型 APK 已随仓库提供）

请勿把含真实凭据的文件提交到 Git。

## License

Private use / source snapshot. Third-party APKs and modules remain under their original licenses.

