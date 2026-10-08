# 对话式演示记录（学生任务卡 第 5 节要求）

- 演示方式：在 CodeBuddy 中用自然语言对 `orchestrator-agent` 提需求，由 Agent 真实调用后端 REST API
- 后端：`http://localhost:8001`（`python main.py`，干净种子库）
- 演示账号：`lib01/123456`（图书管理员）、`zhangsan/123456`（读者·本科生）、`admin/admin123`（系统管理员）
- 接口级验证另见 `backend/scripts/e2e_report.md`（30 个场景全通过）

---

## 1. 演示一：借书（主线）

**用户**：我想借《三体》

**路由判断**：借书 → 流通类意图 → 委派 `circulation-agent`（参考 `borrow-book` skill）

**调用链路**：

| 步骤 | 请求 | 关键响应 |
|---|---|---|
| 1 | `POST /api/auth/login` `{lib01/123456}` | `token`，`role=librarian` |
| 2 | `POST /api/auth/login` `{zhangsan/123456}` | `token`，`role=reader`，`user_id=4` |
| 3 | `GET /api/auth/me`（读者令牌） | **`reader_id=1`**、**`card_no=CARD2026000001`**、`reader_type=UNDERGRADUATE` |
| 4 | `GET /api/books/search?keyword=三体` | `total=3`，《三体》`title_id=1`，`available_count=4` |
| 5 | `GET /api/books/1` | `items[]` 中 `ITEM2026000002` 状态 `AVAILABLE` |
| 6 | `POST /api/circulation/borrow` `{card_no, barcode}`（管理员令牌） | `loan_id=2`，`due_date=2026-10-25` |

**回复**：借阅成功！《三体》（刘慈欣）已借出，条码 ITEM2026000002，请于 **2026-10-25** 前归还。

---

## 2. 演示二：续借（任务卡 任务一）

**用户**：把我借的《三体》续借一下

**路由判断**：续借 → 流通类意图 → 委派 `circulation-agent`（参考 `renew-book` skill）

**调用链路**：

| 步骤 | 请求 | 关键响应 |
|---|---|---|
| 1 | `GET /api/circulation/records/1?status=BORROWED`（读者令牌，路径用 `reader_id`） | `total=2`，两本《三体》`loan_id=1` / `loan_id=2` |
| 2 | `POST /api/circulation/renew` `{loan_id: 2}` | **`new_due_date=2026-11-24`**，`renew_count=1` |

**回复**：续借成功！《三体》新的应还日期为 **2026-11-24**（已使用 1 次续借，每本限 1 次）。

**验收对照**：
- 续借成功并回复新应还日期 ✅
- 仅"在借（BORROWED）"记录可续借；已归还记录 → `400 该图书已归还，无法续借` ✅（见 `e2e_report.md` F-02）
- 续借上限 1 次 → `400 该图书已达续借上限（1 次）` ✅（E-02）

---

## 3. 演示三：图书评论与评分（任务卡 任务二）

**用户**：给《三体》打 5 分，写句评论：太好看了 → 看看《三体》的评论

**路由判断**：评论类意图与"找书"同层 → 编排层直接 `use_skill("book-review")`，**不**经 `circulation-agent`

**调用链路**：

| 步骤 | 请求 | 关键响应 |
|---|---|---|
| 1 | `POST /api/reviews` `{title_id:1, rating:5, comment:"太好看了"}`（读者令牌） | `review_id=1`，`status=PENDING` |
| 2 | `GET /api/reviews?title_id=1`（审核前） | `average_rating=0.0`，`total=0` ← **未审核不可见** |
| 3 | `POST /api/reviews/1/moderate` `{decision:"APPROVED"}`（admin 令牌） | `status=APPROVED` |
| 4 | `GET /api/reviews?title_id=1`（审核后） | **`average_rating=5.0`**，`total=1`，评论"太好看了" |

**回复**：评论已提交，待管理员审核后公开。系统管理员已审核通过：《三体》当前平均分 **5.0** 分，共 **1** 条评论 —— 张三打 5 分："太好看了"。

**验收对照**：
- 评分评论保存成功 ✅
- 列出评论列表与平均评分 ✅
- 评分超出 1–5 被后端拒绝 → `400 评分必须为 1-5 的整数` ✅（I-02）

---

## 4. 演示四：还书（读者申请 + 馆员审核，BR-020）

**用户**：我要还《三体》 → 馆员帮我确认一下这笔归还申请

**路由判断**：还书 → 流通类意图 → 委派 `circulation-agent`（参考 `return-book` skill）

**调用链路**：

| 步骤 | 请求 | 关键响应 |
|---|---|---|
| 1 | `GET /api/circulation/records/1?status=BORROWED`（读者令牌） | 取到 `loan_id=2`、`barcode=ITEM2026000002` |
| 2 | `POST /api/circulation/return-request {"loan_id":2}`（读者令牌） | `status=RETURN_REQUESTED`（书仍在读者手上，副本状态不变） |
| 3 | `GET /api/circulation/return-requests`（馆员令牌） | `total=1`，含读者"张三"、书名《三体》、条码、应还日期、是否逾期 |
| 4 | `POST /api/circulation/return-requests/2/approve`（馆员令牌） | `status=RETURNED`、`overdue_days=0`、`fine=0.00`；副本回架；待审清单清空 |

**回复**：归还申请已提交，请将图书交至馆台等待审核 —— 馆员已确认收书，归还完成，本次无逾期罚款。

**验收对照**：
- 读者发起归还申请 ✅（`BORROWED → RETURN_REQUESTED`，对应 TC-083）
- 馆员审核通过完成归还 ✅（`RETURN_REQUESTED → RETURNED`，对应 TC-089）
- 驳回通道：`POST /api/circulation/return-requests/{loan_id}/reject` → `BORROWED` ✅（TC-090）
- 现场办理（读者未先申请，馆员凭条码直办）：`POST /api/circulation/return {"barcode":..}` ✅（TC-027）
- 申请期间不可续借 → `400 该图书已提交归还申请，审核通过前无法续借` ✅（TC-095）
- 越权发起申请 → `403 只能申请归还本人的图书` ✅（TC-084）

---

## 5. 演示中发现并修复的契约缺口

首轮演示暴露出两个会真实卡住 Agent 的问题，均已修复并复验：

| # | 问题 | 后果 | 修复 |
|---|---|---|---|
| 1 | 登录返回 `user_id`（账户 ID），而借书/续借/查记录用 `reader_id`（读者 ID），两者编号独立；Agent 无从解析 | 用 `user_id=4` 查记录 → `403 只能查询本人的借阅信息` | 新增 `GET /api/auth/me`，返回 `reader_id`、`card_no`、`reader_type` |
| 2 | 后端没有任何只读接口能查到 `card_no` | Agent 借书时只能猜证号 | ① `GET /api/auth/me` 带 `card_no`；② `GET /api/admin/readers` 的每位读者补 `card_no` |

复验结果：`user_id=4 ≠ reader_id=1`，`card_no=CARD2026000001`，与管理员侧 `/api/admin/readers` 口径一致（双源交叉校验通过）。

同步修改的提示词：`user-manage`(2.1)、`borrow-book`(2.1)、`renew-book`(1.1)、`book-review`(1.1)、`book-search`(2.1)、`orchestrator-agent`(3.1)、`circulation-agent`(2.1)。

## 6. 环境说明

当前会话未组队，`circulation-agent` 无法作为独立 Agent 被委派（工具返回 "Not in a team."）。
按 `orchestrator-agent` 硬约束第 6 条降级：由编排层严格按 `circulation-agent/SKILL.md` 及其引用的 skill 契约自执行，接口路径与字段名未凭记忆编造。
