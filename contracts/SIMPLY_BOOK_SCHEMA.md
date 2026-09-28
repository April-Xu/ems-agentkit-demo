# simply_book 模块 Schema



## 0. 表索引

| 表 | 用途 | i18n |
|----|------|------|
| `simply_book_location` / `_lang` | 地点 | lang 表 1→2 |
| `partner_practitioner` / `_detail` | 导师 | lang 列（每语言一行） |
| `simply_book_category` | 分类主表 | 单语言 |
| `simply_book_class` / `_lang` | 课程 | lang 表 1→2 |
| `simply_book_work_calendar` | 排期 | 单语言 |
| `simply_book_work_calendar_tag_relation` | 排期标签 | — |
| `simply_book_work_calendar_favorite` | 收藏 | — |
| `simply_book_waiting_list` | 候补 | — |
| `simply_book_bookings` | 预定记录 | lang 列 + lang_related_id（EN/ZH 双行） |
| `partner_event_ticket_relation` | credits 余额行（锁对象） | — |
| `partner_event_credits_transaction` | credits 流水 | — |

---

## 1. 创建流程

创建顺序（前 4 阶段为主数据，排期聚合引用前 4 者）：

```
① 地点  simply_book_location            ── location_id
② 导师  partner_practitioner            ── practitioner_id
③ 分类  simply_book_category            ── cate_id
④ 课程  simply_book_class (+_lang)      ── class_id
                                          ▼
                  ⑤ 排期  simply_book_work_calendar
                  引用: class_id / location_id / class_cate_id / practitioner_id
                  (practitioner_id / host_ids / sponsor_ids 逗号分隔，FIND_IN_SET)
```

- ① 地点：主表 + `simply_book_location_lang`（location_id + lang，en/zh 双行）。
- ② 导师：`partner_practitioner` 单表 + `lang` 列（每语言一行，按 practitioner_id 聚合，软删除 `deleted_time`，排序 `practitioner_seq`）。`simply_book_provider` legacy 不用。
- ③ 分类：`simply_book_category`（主表，`cate_id`）。
- ④ 课程：`simply_book_class` 主表 + `simply_book_class_lang`（class_id + lang）。
- ⑤ 排期：`simply_book_work_calendar`，聚合上述软 FK；`class_cate_id` 即 `cate_id`，直接引用分类主表 `simply_book_category`。

---

## 2. 列定义

### simply_book_location

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| user_id | int(11) | YES | NULL | | |
| location_name | varchar(255) | YES | NULL | | |
| venue_city | varchar(191) | YES | NULL | | |
| venue_full_name | varchar(191) | YES | NULL | | |
| introduction | text | YES | NULL | | |
| venue_image | varchar(191) | YES | NULL | | |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`

### simply_book_location_lang

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| location_id | int(11) | NO | — | PK | → simply_book_location.id |
| lang | varchar(50) | NO | — | PK | en / zh |
| location_name | varchar(255) | YES | NULL | | |
| created_time | timestamp | NO | CURRENT_TIMESTAMP | | |
| updated_time | timestamp | NO | CURRENT_TIMESTAMP(ON UPDATE) | | |

索引：`PK(location_id, lang)`、`KEY idx_lang(lang)`

### partner_practitioner

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| ato_id | varchar(50) | YES | NULL | | |
| practitioner_id | varchar(50) | YES | NULL | KEY | 导师编号；排期.practitioner_id 指此 |
| practitioner_name | varchar(255) | YES | NULL | | 中文名 |
| practitioner_title | varchar(255) | YES | NULL | | |
| practitioner_org | varchar(255) | YES | NULL | | 所属组织/公司 |
| head_imgs | varchar(500) | YES | NULL | | 头像 json |
| avatar_badge | varchar(255) | YES | NULL | | 头像装饰标记 |
| nationality | varchar(100) | YES | NULL | | |
| work_exp | varchar(100) | YES | NULL | | 从业时间 |
| sex | varchar(10) | YES | NULL | | |
| birthday | date | YES | NULL | | |
| city_id / province_id / district_id | int(11) | YES | NULL | | 地区 |
| intro_self | text | YES | NULL | | 自我介绍中文 |
| intro_desc | text | YES | NULL | | 长文介绍 |
| intro_course_imgs | text | YES | NULL | | 课程介绍图片 |
| intro_course_video | varchar(500) | YES | NULL | | 课程介绍视频 |
| honer_desc | text | YES | NULL | | 荣誉介绍 |
| fans | varchar(255) | YES | NULL | | 自有媒体平台和粉丝数 |
| practitioner_remark | varchar(255) | YES | NULL | | |
| practitioner_status | tinyint(4) | YES | 1 | | |
| languages | varchar(80) | YES | NULL | | 授课语言 |
| lang | varchar(40) | YES | zh | | 本条记录的语言 |
| practitioner_seq | int(11) | YES | NULL | | 排序 |
| practitioner_bu_id | varchar(50) | YES | NULL | | BU ID |
| practitioner_poster | varchar(255) | YES | NULL | | |
| practitioner_poster_params | varchar(100) | YES | NULL | | |
| practitioner_email | varchar(50) | YES | NULL | | 邮箱 |
| practitioner_comwx | varchar(50) | YES | NULL | | 企微 ID |
| practitioner_country_code | varchar(20) | YES | 86 | | 手机国别号 |
| practitioner_phone | varchar(50) | YES | NULL | | 手机 |
| deleted_time | datetime | YES | NULL | | 软删除 |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_pracid(practitioner_id)`

### partner_practitioner_detail

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| practitioner_id | varchar(50) | YES | NULL | | → partner_practitioner.practitioner_id |
| title | varchar(255) | YES | NULL | | |
| type | varchar(50) | YES | NULL | | 元素类型 |
| value | text | YES | NULL | | 元素的值 |
| value_extend | varchar(255) | YES | NULL | | 元素值拓展 |
| sort | tinyint(4) | YES | 0 | | 排序 |
| lang | varchar(50) | YES | NULL | | 语言 |
| click_action | varchar(50) | YES | NULL | | 点击动作 |
| click_value | varchar(255) | YES | NULL | | 点击动作的值 |
| click_value_extend | varchar(255) | YES | NULL | | 点击动作值拓展 |
| margin | varchar(100) | YES | NULL | | 元素边距 |
| update_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| create_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`

### simply_book_category

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| user_id | int(11) | YES | NULL | | |
| cate_id | int(11) | YES | NULL | KEY | 分类业务 id（软 FK 目标） |
| cate_name | varchar(255) | YES | NULL | KEY | 分类名 |
| cate_show_name | varchar(255) | YES | NULL | | |
| cate_icon | varchar(255) | YES | NULL | | |
| cate_color | varchar(50) | YES | NULL | | |
| cate_is_public | tinyint(4) | YES | NULL | | |
| update_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| create_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_catename(cate_name)`、`KEY idx_cateid(cate_id)`

### simply_book_class

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment；simplybook 的 class id |
| user_id | int(11) | YES | NULL | | |
| name | varchar(500) utf8 | YES | NULL | | simplybook 的 event name（已拆 lang 表） |
| description | text utf8 | YES | NULL | | event 描述（已拆 lang 表） |
| description_short | varchar(500) | YES | NULL | | 短描述（已拆 lang 表） |
| position | varchar(100) utf8 | YES | NULL | | |
| picture_path | varchar(500) utf8 | YES | NULL | | 图片路径 |
| bookings_limit | int(11) | YES | NULL | | 预订限制 |
| is_publish | tinyint(4) | YES | NULL | | |
| min_group_booking | int(11) | YES | NULL | | 最小组预订数量 |
| finish_points | int(11) | YES | NULL | | 完课分数 |
| is_online | tinyint(4) | YES | 0 | | 是否线上课 |
| delivery_mode | varchar(20) | YES | NULL | | private/group/workshop/hybrid |
| multi_booking | tinyint(4) | YES | 0 | | 多次预约 |
| remark | text | YES | NULL | | 备注 |
| length_of_activity | varchar(191) utf8 | YES | NULL | | |
| venue_id | int(11) | YES | NULL | | |
| category_id | int(11) | YES | NULL | | |
| provider_type | varchar(191) utf8 | YES | NULL | | |
| assign_provider | varchar(191) utf8 | YES | NULL | | |
| jump_link | varchar(255) | YES | NULL | | 需要跳转的链接 |
| class_price | int(11) | YES | NULL | | 价格 |
| class_credits | int(11) | YES | NULL | | 价格-积分型；null=不走 credits |
| currency_type | varchar(50) | YES | NULL | | |
| create_time | timestamp | NO | CURRENT_TIMESTAMP | | |
| update_time | timestamp | NO | CURRENT_TIMESTAMP(ON UPDATE) | | |

索引：`PK(id)`、`KEY idx_osbc_classid(id)`

### simply_book_class_lang

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| class_id | int(11) | NO | — | PK | → simply_book_class.id |
| lang | varchar(50) | NO | — | PK | en / zh |
| name | varchar(500) | YES | NULL | | |
| description | text | YES | NULL | | |
| description_short | varchar(500) | YES | NULL | | |
| created_time | timestamp | NO | CURRENT_TIMESTAMP | | |
| updated_time | timestamp | NO | CURRENT_TIMESTAMP(ON UPDATE) | | |

索引：`PK(class_id, lang)`、`KEY idx_lang(lang)`

### simply_book_work_calendar

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment；alias calendar_id |
| class_id | int(11) | YES | NULL | | → simply_book_class.id |
| date | varchar(50) utf8 | YES | NULL | KEY | 排期日期；与 bookings.booking_day(date) 类型不一致 |
| from_time | tinytext utf8 | YES | NULL | | |
| to_time | tinytext utf8 | YES | NULL | | |
| calendar_sort | tinyint(4) | YES | 0 | | |
| is_day_off | tinytext utf8 | YES | NULL | | |
| location | varchar(255) utf8 | YES | NULL | | |
| location_id | int(11) | YES | NULL | | → simply_book_location.id |
| booking_left | int(11) | YES | 0 | | 剩余可订库存（原子 ±） |
| booking_limit | int(11) | YES | 0 | | per-user 额度，联动 sangha_learning_booking_limit |
| finish_points | int(11) | YES | 0 | | |
| class_cate_id | int(11) | YES | 0 | KEY | 即 cate_id（→ simply_book_category.cate_id） |
| practitioner_id | varchar(100) utf8 | YES | NULL | | 逗号分隔；FIND_IN_SET |
| host_ids | varchar(100) | YES | NULL | | 主持人；逗号分隔 |
| sponsor_ids | varchar(100) | YES | NULL | | 赞助方；逗号分隔 |
| outlook_id | varchar(255) | YES | NULL | | 发送 outlook id |
| remark | text | YES | NULL | | 备注 |
| create_time | timestamp | YES | CURRENT_TIMESTAMP | | |
| update_time | timestamp | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |

索引：`PK(id)`、`KEY idx_date_cateid(date, class_cate_id)`

### simply_book_work_calendar_tag_relation

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| calendar_id | int(11) | YES | NULL | | → simply_book_work_calendar.id |
| tag_id | varchar(50) | YES | NULL | | 无 tag 主表 |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`

### simply_book_work_calendar_favorite

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| ato_id | varchar(64) | NO | '' | UK/KEY | 用户 ATO_ID |
| calendar_id | int(11) | NO | 0 | UK | → simply_book_work_calendar.id |
| created_time | datetime | NO | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`UNIQUE uk_ato_calendar(ato_id, calendar_id)`、`KEY idx_ato_id(ato_id)`

### simply_book_waiting_list

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| calendar_id | int(11) | YES | NULL | KEY | → simply_book_work_calendar.id |
| ato_id | varchar(50) | YES | NULL | | |
| is_deleted | tinyint(4) | YES | 0 | | 用户删掉了 |
| event_id | varchar(50) | YES | NULL | | |
| course_id | varchar(50) | YES | NULL | | |
| status | tinyint(4) | YES | 1 | | 用户排上队 状态设成 0 |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_calendarid(calendar_id)`

### simply_book_bookings

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| booking_id | int(11) | YES | NULL | | 订单 id |
| course_id | varchar(50) | YES | NULL | | 课程 ID |
| event_id | varchar(50) | YES | NULL | KEY | 活动 ID |
| booking_day | date | YES | NULL | | 预订天 |
| booking_simplybook_id | int(11) | YES | NULL | | 预订日期 |
| ato_id | varchar(40) | YES | NULL | KEY | |
| booking_begin_datetime | datetime | YES | NULL | KEY | 预订开始时间 |
| booking_end_datetime | datetime | YES | NULL | KEY | 预订结束时间 |
| booking_event_name | varchar(255) | YES | NULL | KEY | 预订事件名 |
| booking_img | varchar(255) | YES | NULL | | 预订图片地址 |
| booking_description | text | YES | NULL | | 预订描述 |
| booking_unit | varchar(255) | YES | NULL | | 预订业务组 |
| booking_location | varchar(255) | YES | NULL | | 预订地点名称 |
| booking_providers | varchar(100) | YES | NULL | | 预订服务提供者 ID |
| booking_categories | varchar(255) | YES | NULL | | |
| booking_class_id | varchar(50) | YES | NULL | | |
| booking_practitioner_id | varchar(50) | YES | NULL | | |
| booking_location_id | varchar(50) | YES | NULL | | |
| booking_calendar_id | int(11) | YES | NULL | KEY | → simply_book_work_calendar.id |
| booking_outlook_id | varchar(255) | YES | NULL | | outlook 编辑 id |
| booking_canceled | tinyint(4) | YES | 0 | KEY | |
| booking_notify_status | tinyint(4) | YES | 1 | KEY | 推送状态 |
| booking_app_notify_status | tinyint(4) | YES | 0 | KEY | APP 推送状态 |
| lang | varchar(50) | YES | NULL | KEY | en / zh |
| lang_related_id | int(11) | YES | NULL | | EN/ZH 互指 |
| pre_calendar_id | int(11) | YES | NULL | | |
| booking_source | varchar(50) | YES | BACKEND | | 预定渠道 |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_date(booking_begin_datetime, booking_end_datetime)`、`KEY dix_eventname(booking_event_name)`、`KEY idx_calendarid(booking_calendar_id)`、`KEY idx_user(ato_id, booking_begin_datetime, booking_end_datetime)`、`KEY idx_remind(event_id, lang, booking_canceled, booking_app_notify_status, booking_begin_datetime)`

### partner_event_ticket_relation

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| event_id | varchar(50) | YES | NULL | KEY | 活动 ID |
| ticket_id | varchar(100) | YES | NULL | KEY | |
| ticket_credits_balance | int(11) | YES | 0 | | 消费点；FOR UPDATE 锁对象 |
| ato_id | varchar(50) | YES | NULL | KEY | |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_eventid_ticketid(event_id, ticket_id)`、`KEY idx_eventid_atoid(event_id, ato_id)`

### partner_event_credits_transaction

| 列 | 类型 | Null | 默认 | Key | 说明 |
|----|------|------|------|-----|------|
| id | int(11) | NO | — | PK | auto_increment |
| ato_id | varchar(50) | NO | — | KEY | |
| event_id | varchar(50) | NO | — | KEY | |
| transaction_booking_id | int(11) | YES | NULL | | 预定 id（EN 行） |
| transaction_name | varchar(255) | YES | NULL | | 流水名称 |
| transaction_type | varchar(50) | YES | NULL | | 签到/兑换/调整等 |
| transaction_amount | int(11) | NO | 0 | | 流水值（正=增，负=减） |
| transaction_balance | int(11) | NO | 0 | | 操作后余额快照 |
| transaction_relation_id | int(11) | YES | NULL | | 流水关联 ID |
| transaction_operator | varchar(255) | YES | NULL | | 操作者 |
| transaction_operator_id | int(11) | YES | NULL | | 操作者 ID |
| transaction_remark | varchar(255) | YES | NULL | | 备注 |
| updated_time | datetime | YES | CURRENT_TIMESTAMP(ON UPDATE) | | |
| created_time | datetime | YES | CURRENT_TIMESTAMP | | |

索引：`PK(id)`、`KEY idx_ato_event(ato_id, event_id)`

---

## 3. 关键关系与软外键

- **分类链**：`simply_book_work_calendar.class_cate_id` 即 `cate_id`，软 FK → `simply_book_category.cate_id`（排期直接引用分类主表），用于权限校验与 per-user 预订额度维度。
- **排期→课程/地点/导师**：`work_calendar.class_id` → `simply_book_class.id`；`location_id` → `simply_book_location.id`；`practitioner_id` / `host_ids` / `sponsor_ids` 均为**逗号分隔字符串**，查询用 `FIND_IN_SET`（`practitioner_id` 与 `host_ids` 同语义，OR 合并匹配）。
- **预定 EN/ZH 双行**：每次预定产 2 行（`lang=en` / `lang=zh`），由 `lang_related_id` 互指。**credits 流水只在 EN 行记账**。
- **Credits 双表 ledger**：`partner_event_ticket_relation`（余额行，`(event_id, ato_id)` → `ticket_credits_balance`）是扣减/退还的锁对象；`partner_event_credits_transaction` 每笔带 `transaction_balance` 余额快照。
- **日期列类型不统一**：`work_calendar.date` varchar(50)、`bookings.booking_day` date。

---

## 4. 预定/取消与 Credits 流程

### 预定（扣库存 + 扣 credits）
事务内锁定排期行 → 校验剩余库存 ≥ 预定数 → 原子扣减 `booking_left`（条件更新 `WHERE booking_left >= N` 防超卖）→ 循环 N 次各插 EN/ZH 一对预定行（互写 `lang_related_id`）→ 扣 per-user 预订额度。若课程为 credits 型，预定前先校验 credits 总额（单价 × N），预定后**逐笔**在 EN 行记 redeem 流水。

### 取消（释库存 + 退 credits）
事务内释放 `booking_left`、标记 `booking_canceled = 1`、恢复 per-user 预订额度。取消时不加锁。credits 退还仅对 EN 行处理。

### Credits 机制
- 余额行 `partner_event_ticket_relation.ticket_credits_balance` 为扣减/退还的锁对象，事务内 `FOR UPDATE`。
- 每笔增减在 `partner_event_credits_transaction` 记一行，带操作后余额快照 `transaction_balance`；无余额行时自动创建并初始化。
- 流水类型：签到 / 兑换(redeem) / 取消 / 充值 / 调整 / 下单 / 后台扣减。
- **逐笔对称**：预定 N 条则记 N 笔 redeem（每条 EN 行一笔）；取消时每条 EN 行各查各退，`transaction_booking_id` 是 redeem↔cancel 关联键。
- **防误退三件套**：① ZH 行经 `lang_related_id` 归一到 EN id（流水存 EN id）；② 已有 cancel 流水则跳过（防重复退还）；③ 汇总此前 adjust 已退部分，`退还额 = |redeem| − 已adjust退还`，≤0 跳过。

---

## 5. 运维场景

### 场景 A：批量预定
防重复提交锁 → 时间/权限校验 → 校验 credits 总额（单价 × N）→ 校验库存 ≥ N → 扣库存、产 N 对 EN/ZH 预定行 → 逐笔扣 credits（每条 EN 行一笔 redeem）→ 触发 SMS / 日历 / 预定流水。

### 场景 B：批量取消
防重复提交锁 → 权限校验 → 取该排期全部预定行（EN+ZH 配对，**释放数 = 总行数 / 2**）→ 释放库存、标记取消 → 逐笔退 credits（仅 EN 行）→ 触发 SMS / 邮件 / Outlook 删除。单条取消同构（N=1）。

### 场景 C：查询某排期下的预定人数
按 `booking_calendar_id` 取该排期全部预定行 → 批量水化用户信息 → 仅当前语言行挂用户信息塞列表。**人数 = 列表行数**；只要总数直接 count 查询结果。

### 场景 D：批量增加 credits
无专用批量入口。循环对每个 `(ato_id, event_id)` 调充值或调整流水，每笔独立事务 + FOR UPDATE + 余额快照；无余额行自动创建。

### 场景 E：批量增加某个排期的库存
对 `simply_book_work_calendar.booking_left` 原子加 N（`UPDATE ... SET booking_left = booking_left + N WHERE id = ?`）。单排期加 N 座位传 N；跨排期逐个处理。只动 `booking_left`，**不动 `booking_limit`**（后者是 per-user 预订额度，语义见 `sangha_learning_booking_limit`）。对称的扣库存操作带 `WHERE booking_left >= N` 条件，不足不执行。操作自身不加事务/锁，调用方按需自包。

### 场景 F：批量退 credits
无专用批量入口。两条路径：

1. **绑预定 id 的安全退还**（推荐，防重复 + adjust-aware）：取排期下所有 EN 预定行，逐条走取消退还流程。已退跳过，adjust 已退自动扣减。
2. **裸调整（无 booking 绑定）**：循环记调整/取消流水。

> 降价差价自动退 credits 走 adjust 路径，会被安全退还的「已 adjust 退还」扣除以免多退。
