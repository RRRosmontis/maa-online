# maa-online

在 Linux 无图形服务器上，通过网易云游戏运行《明日方舟》，并让官方 MAA/maa-cli 执行日常任务的实验性适配层。

> 本项目调用网易云游戏未公开的 HTTP、WebSocket 与 WebRTC 协议，可能随平台更新失效，也可能不符合平台服务条款。请仅用于个人研究，自行承担账号及服务风险；禁止多账号、商业代练或规避平台限制。

## 上游项目

本仓库是在以下开源项目及实验原型基础上整理的适配代码，不包含完整第三方源码、官方 MAA 二进制或任何用户凭据：

- **MAA 官方仓库（AGPL-3.0）**  
  https://github.com/MaaAssistantArknights/MaaAssistantArknights
- **maa-cli 官方仓库**  
  https://github.com/MaaAssistantArknights/maa-cli
- **网易云游戏后端原型（Apache-2.0）**  
  https://github.com/Tokisaki-Galaxy/netease_cloud_game_server
- **后端使用的网易云游戏 SDK fork（Apache-2.0）**  
  https://github.com/Tokisaki-Galaxy/netease_cloud_game_sdk
- **MAA 云游戏实验分支**  
  https://github.com/Tokisaki-Galaxy/MaaAssistantArknights/tree/support-cloudgame
- **最初的网易云游戏 SDK 原型（Apache-2.0）**  
  https://github.com/wupco/netease_cloud_game_sdk
- **MAA 社区实验讨论**  
  https://github.com/orgs/MaaAssistantArknights/discussions/14404

`backend/` 与 `backend/sdk/` 分别保留了相应上游的 Apache-2.0 LICENSE。MAA 和 maa-cli 由安装脚本从官方渠道下载，其许可证仍以各自上游为准。

## 工作原理

```text
官方 maa-cli / MaaCore
        │ 标准 ADB 命令
        ▼
  bin/adb-cloud
        │ loopback HTTP
        ▼
backend/server.py
        │ 网易 HTTP + WebSocket + WebRTC
        ▼
  网易云游戏中的明日方舟
```

没有修改官方 MaaCore。`adb-cloud` 将 MaaCore 的截图、点击、滑动、文字输入和启动/停止命令转换成本地 HTTP 请求，因此官方 `maa self update`、`maa update` 与 `maa hot-update` 仍可使用。

## 环境要求

- Linux x86_64（其他架构需自行验证）
- Python 3.10+
- `python3-venv`、Git、curl
- 可访问网易云游戏和 GitHub
- 已完成实名认证的网易云游戏账号
- 已有或可登录的《明日方舟》官服账号

## 安装

```bash
git clone https://git.rrrosmontis.icu/RoyirinRosmontis/maa-online.git
cd maa-online
./install.sh
```

安装脚本会在仓库内部创建被 Git 忽略的 `runtime/`，安装 Python 依赖、官方 maa-cli、官方 MaaCore 和资源；不会下载或保存本仓库维护者的账号数据。

## 登录网易云游戏

```bash
runtime/venv/bin/python backend/login.py request <手机号>
runtime/venv/bin/python backend/login.py verify <短信验证码>
```

生成的 token 位于 `backend/token`，权限为 `0600`，且已被 `.gitignore` 排除。不要将 token、手机号、验证码、身份证信息、游戏截图或日志提交到 Git。

实名认证请在网易云游戏网页或 App 中自行完成，不要通过 Issue、聊天或配置文件提供身份证信息。

## 启动与运行

终端一：

```bash
bin/maa-online-server
```

终端二：

```bash
curl -X POST http://127.0.0.1:22888/start
bin/maa-online startup Official --batch -v
```

编辑日常配置：

```bash
bin/maa-online-config
```

验证配置：

```bash
bin/maa-online run daily --dry-run --batch
```

执行日常：

```bash
bin/maa-online run daily --batch -v
```

退出云游戏：

```bash
curl -X POST http://127.0.0.1:22888/exit
```

服务默认仅监听 `127.0.0.1:22888`，不要直接暴露到公网。

## 默认日常模板

`user_config/daily.example.toml` 是脱敏示例。首次安装时复制为被 Git 忽略的 `user_config/daily.toml`，包括：

- 基建一键轮换；
- 自动公招；
- 刷 `1-7` 清理理智；
- 信用商店与好友访问；
- 日常、周常及邮件奖励；
- 完成后退出云游戏。

示例默认不吃理智药、不碎石、不使用加急许可。运行前务必检查 `stage`、公招次数、信用商店列表和邮件领取选项。全部参数说明见 [`user_config/README.md`](user_config/README.md)。

## 更新

```bash
bin/maa-online-update
```

该脚本更新官方 maa-cli、MaaCore、基础资源和热更新资源。适配代码位于官方管理目录之外，不会被 `maa update` 清理。

## 自动定时执行

仓库自带 systemd 单元模板（`systemd/`）。以 root 执行：

```bash
sudo bin/maa-online-install-systemd
```

脚本会把单元渲染到 `/etc/systemd/system/`（`__ROOT__` 替换为当前检出路径）并启用：

| 单元 | 作用 |
|---|---|
| `maa-online-server.service` | 云游戏 API 常驻服务（`Restart=always`，启动前清除代理环境变量，限制 malloc arena 数量） |
| `maa-daily.timer` | 每天 04:00 起随机 0–2 小时触发日常任务 |
| `maa-online-recycle.timer` | 每天 03:59（游戏每日刷新前）重启 API 服务，回收内存 |
| `maa-update.timer` | 每周日 03:20 起随机 30 分钟执行更新 |

日常任务由 `bin/maa-online-daily-run` 驱动：等待 API 就绪 → 启动云游戏 → 在停滞看门狗下执行
`config/tasks/daily.toml` → 失败则释放云会话并重试。定时器使用 `Persistent=true`，机器重启
错过触发时间后会自动补跑；同一单元不会并发执行。

**内存回收**：一次流媒体会话会在 glibc 的 malloc arena 里留下大量不归还操作系统的冷匿名内存
（实测单个服务可累积到 2.5 GB 并填满 swap），因此有两层回收：`maa-daily.service` 在结束时
重启 API 服务（`ExecStopPost`），`maa-online-recycle.timer` 每天再独立回收一次。回收服务带
`ExecCondition=bin/maa-online-can-recycle` 守卫，日常任务运行期间会被自动跳过，不会打断任务。

重试采用**断点续跑**：`bin/maa-resume-tasks.py` 读取前几次尝试的日志，跳过已出现
`<任务类型> Completed` 的任务，只运行剩余任务；若全部完成则直接判定成功，不再开启新会话。
`StartUp` 永不跳过，因为每次 `/start` 都是全新的云实例。详见
[`user_config/README.md`](user_config/README.md#自动定时与断点续跑)。

查看运行情况：

```bash
systemctl list-timers maa-daily.timer maa-update.timer maa-online-recycle.timer
journalctl -u maa-daily.service -n 50
journalctl -u maa-online-server.service -n 50
```

## 离线测试

启动假后端：

```bash
runtime/venv/bin/python tests/fake_backend.py
```

另一个终端验证官方 MaaCore → ADB 适配层：

```bash
LD_LIBRARY_PATH="$PWD/runtime/home/.local/share/maa/lib" \
  runtime/venv/bin/python tests/smoke_maa_connect.py
```

预期：

```text
MaaCore -> adb-cloud -> fake backend: PASS
```

## 已知限制

- 网易私有协议可能随时变化；
- 云视频压缩与网络抖动会降低 MAA 图像识别稳定性；
- 高频截图在低性能服务器上较慢，基建换班可能耗时较长；
- Home/ESC 等键值尚未完整验证；
- 云端会主动断开会话（信令 WebSocket close、视频流停滞）。后端会在检测到这类情况时自动拆除
  会话并释放云端实例，日常包装脚本另有停滞看门狗与最多 3 次断点续跑重试，但仍无法保证每次都跑完；
- 云游戏免费额度通常有限（常见为每天 30 分钟），一次完整日常约 24 分钟，重试会进一步消耗额度；
- 后端可能出现少量 H.264 解码丢包警告；
- 游戏自动化会真实消耗招聘许可、理智、信用等资源，请先 dry-run 并审阅配置。


## 许可证

本仓库自有代码按 Apache License 2.0 发布，详见 [`LICENSE`](LICENSE)。派生文件及第三方组件同时受对应上游许可证约束。
