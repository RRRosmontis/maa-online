# MAA Online 用户配置

`daily.example.toml` 是公开模板。执行 `install.sh` 后会复制为被 Git 忽略的 `daily.toml`，并建立以下链接：

```text
config/tasks/daily.toml
  -> user_config/daily.toml
```

## 使用前必须确认

下面这些参数会改变游戏资源或账号行为。首次运行前请逐项确认。

### 全局参数

| 参数 | 当前值 | 可填写值/作用 |
|---|---:|---|
| `client_type` | `Official` | 官服用 `Official`；B服用 `Bilibili` |
| `startup` | `true` | 运行任务前自动启动并进入游戏 |
| `closedown` | `true` | 全部任务结束后退出网易云游戏实例 |

### 清理理智 `Fight`

| 参数 | 当前值 | 说明 |
|---|---:|---|
| `stage` | `1-7` | 必填偏好。要刷的关卡，如 `1-7`、`CE-6`、`LS-6`、`AP-5`、活动关卡 |
| `medicine` | `0` | 最多使用多少瓶普通理智药；`0` 表示不用 |
| `medicine_expire_days` | `0` | 使用多少天内将过期的理智药；`0` 表示不用 |
| `stone` | `0` | 最多碎多少颗源石；强烈建议保持 `0` |
| `times` | `999` | 最大作战次数；理智不足时仍会停止 |
| `series` | `0` | `0` 自动选择最大代理倍率，`1` 单次代理，其他正数为指定倍率 |
| `report_to_penguin` | `false` | 是否匿名上报掉落至企鹅物流 |
| `report_to_yituliu` | `false` | 是否匿名上报至一图流 |

修改关卡示例：

```toml
stage = "CE-6"
```

只刷十次：

```toml
times = 10
```

### 自动公招 `Recruit`

| 参数 | 当前值 | 说明 |
|---|---:|---|
| `refresh` | `true` | 是否刷新低价值三星标签，会消耗游戏内免费刷新次数 |
| `select` | `[5, 4]` | 允许选择的标签组合等级 |
| `confirm` | `[4, 3]` | 允许自动确认的标签等级；高价值组合不自动确认 |
| `first_tags` | `高级资深干员` | 三星组合时优先考虑的标签；通常无需修改 |
| `extra_tags_mode` | `0` | `0` 默认；`1` 尽量选三个标签；`2` 尽量选择更多高星标签 |
| `times` | `4` | 本轮最多处理/发起多少次招募，会消耗招聘许可 |
| `set_time` | `true` | 是否自动设置招募时间 |
| `expedite` | `false` | 是否使用加急许可；建议保持 `false` |
| `preserve_tags` | 高资、资深、支援机械 | 识别到任一标签时保留槽位，留给人工确认 |
| `recruitment_time` | 540 分钟 | 三星和四星组合默认设置为 9 小时 |
| `server` | `CN` | 国服为 `CN`，国际服可为 `US`、`JP`、`KR` |

如果只想识别公招、不自动确认和发起招募：

```toml
confirm = []
times = 0
```

### 基建换班 `Infrast`

| 参数 | 当前值 | 说明 |
|---|---:|---|
| `mode` | `20000` | 已启用一键轮换；`0` 为自动计算换班，`10000` 为自定义排班 |
| `facility` | 七类常用设施 | 要处理的设施及顺序 |
| `drones` | `_NotUse` | 不使用无人机；也可填 `Money`、`CombatRecord`、`PureGold` 等 |
| `threshold` | `0.3` | 心情低于此比例时参与换班判断 |
| `dorm_notstationed_enabled` | `false` | 是否将未进驻干员放入宿舍 |
| `dorm_trust_enabled` | `false` | 是否优先安排需要提升信赖的干员进宿舍 |

设施名称：

```text
Mfg          制造站
Trade        贸易站
Power        发电站
Control      控制中枢
Reception    会客室
Office       办公室
Dorm         宿舍
Processing   加工站
Training     训练室
```

### 信用商店 `Mall`

| 参数 | 当前值 | 说明 |
|---|---:|---|
| `visit_friends` | `true` | 访问好友基建获取信用 |
| `shopping` | `true` | 是否自动购买信用商店商品 |
| `buy_first` | 招聘许可、龙门币 | 优先购买列表，按顺序购买 |
| `blacklist` | 家具零件、加急许可 | 第二轮购物时不购买的商品 |
| `force_shopping_if_credit_full` | `false` | 信用将溢出时是否无视黑名单；建议保持 `false` |
| `only_buy_discount` | `false` | 第二轮是否只购买折扣商品 |
| `reserve_max_credit` | `true` | 信用高于 300 时可继续购买其他非黑名单商品；降至 300 以下后停止第二轮购物 |
| `credit_fight` | `false` | 是否借助战打一局 OF-1 获取次日信用；会产生额外操作 |
| `formation_index` | `0` | 信用战使用的编队；`0` 当前编队，`1`～`4` 对应编队栏 |

完全禁止自动购物，但仍访问好友：

```toml
visit_friends = true
shopping = false
```

### 奖励领取 `Award`

| 参数 | 当前值 | 说明 |
|---|---:|---|
| `award` | `true` | 领取每日和每周任务奖励 |
| `mail` | `true` | 领取所有邮件奖励 |
| `recruit` | `false` | 是否领取限定池每日免费单抽 |
| `orundum` | `false` | 是否领取幸运墙等活动合成玉奖励 |

## 交互式编辑

运行：

```bash
bin/maa-online-config
```

使用数字选择“全局”或某个任务，再选择具体配置项。字符串可以直接输入；列表既可以输入完整 TOML，也可以用逗号分隔，例如：

```text
1-7
招聘许可,龙门币
5,4
```

在主菜单输入 `s` 保存。每次保存前会自动备份到 `user_config/backups/`，随后运行 MAA dry-run；若验证失败会自动回滚。输入 `q` 退出，`Ctrl+C` 会取消未保存的修改。

## 检查配置但不执行

每次修改后先运行：

```bash
bin/maa-online run daily --dry-run --batch
```

出现任务列表且没有 Error，表示 TOML 格式和参数能够被解析。

## 正式执行

终端一：

```bash
bin/maa-online-server
```

终端二：

```bash
curl -X POST http://127.0.0.1:22888/start
bin/maa-online run daily --batch -v \
  --log-file=maa-daily.log
```

## 紧急停止

停止当前 MAA：

```bash
pkill -INT -f '/runtime/bin/maa'
```

退出网易云游戏实例：

```bash
curl -X POST http://127.0.0.1:22888/exit
```

## 示例模板设置

公开示例模板会：

- 使用基建一键轮换模式；
- 最多处理四次公招，但保留高资、资深和支援机械标签；
- 刷 `1-7` 直到理智不足；
- 不吃理智药；
- 绝不碎石；
- 不使用加急许可；
- 访问好友；优先购买指定商品，信用高于 300 时不限折扣购买其他非黑名单商品；
- 不无视信用商店黑名单；
- 领取每日/每周任务奖励；
- 领取所有邮件；
- 任务结束后退出云游戏。
