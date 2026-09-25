# 实验二端到端验收记录

- 生成时间：2026-09-25
- 生成方式：`python scripts/e2e_acceptance.py`（对运行中的 http://localhost:8001 调用真实接口）
- 结果：**28 / 28 通过**

| 编号 | 验收场景 | 请求 | 预期与实际 | 结论 |
|---|---|---|---|---|
| A-01 | 三类角色登录（admin/lib01/zhangsan） | `POST /api/auth/login` | 返回 token<br>实际：admin/librarian/reader 令牌均已取得 | PASS |
| B-01 | 未登录调用借书 | `POST /api/circulation/borrow（无令牌）` | 403 未登录或令牌无效<br>实际：HTTP 403 code=403｜未登录或令牌无效 | PASS |
| B-02 | 读者调用管理员接口借书 | `POST /api/circulation/borrow（读者令牌）` | 403 权限不足（借书必须由管理员代理）<br>实际：HTTP 403 code=403｜权限不足 | PASS |
| C-01 | 借书：本科生（5 本 / 30 天） | `POST /api/circulation/borrow` | due_date = 今天+30 = 2026-10-25<br>实际：HTTP 200｜due_date=2026-10-25 | PASS |
| C-02 | 借书：研究生（10 本 / 60 天） | `POST /api/circulation/borrow` | due_date = 今天+60 = 2026-11-24<br>实际：HTTP 200｜due_date=2026-11-24 | PASS |
| C-03 | 借书：期刊（读者类型 × 出借物二维策略，7 天） | `POST /api/circulation/borrow` | due_date = 今天+7 = 2026-10-02<br>实际：HTTP 200｜due_date=2026-10-02 | PASS |
| C-04 | 借书：学位论文（二维策略，3 天） | `POST /api/circulation/borrow` | due_date = 今天+3 = 2026-09-28<br>实际：HTTP 200｜due_date=2026-09-28 | PASS |
| C-05 | 专科生连借 3 本（上限 3） | `POST /api/circulation/borrow ×3` | 3 次均成功<br>实际：3 次请求，全部成功=True | PASS |
| C-06 | 超过借阅数量上限（第 4 本） | `POST /api/circulation/borrow` | 400 借阅数量已达上限<br>实际：HTTP 400 code=400｜借阅已满（3/3），请先归还图书 | PASS |
| D-01 | 读者查询本人借阅记录 | `GET /api/circulation/records/1` | total ≥ 4（三体 + 3 本新借）<br>实际：HTTP 200｜total=4 | PASS |
| D-02 | 读者查询他人借阅记录 | `GET /api/circulation/records/2（张三令牌）` | 403 权限不足<br>实际：HTTP 403 code=403｜只能查询本人的借阅信息 | PASS |
| D-03 | 管理员查询任意读者借阅记录 | `GET /api/circulation/records/2` | 管理员可查他人<br>实际：HTTP 200｜total=1 | PASS |
| E-01 | 续借：读者本人续借在借图书 | `POST /api/circulation/renew` | new_due_date 后延、renew_count=1<br>实际：HTTP 200｜new_due_date=2026-11-24, renew_count=1 | PASS |
| E-02 | 重复续借（上限 1 次） | `POST /api/circulation/renew` | 400 已达续借上限<br>实际：HTTP 400 code=400｜该图书已达续借上限（1 次） | PASS |
| F-01 | 还书：按期归还 | `POST /api/circulation/return` | status=RETURNED，无罚款<br>实际：HTTP 200｜fine=0.00 | PASS |
| F-02 | 重复还书（已归还记录） | `POST /api/circulation/return` | 400 未找到借阅记录<br>实际：HTTP 400 code=400｜未找到该馆藏的借阅记录 | PASS |
| G-01 | 逾期还书：中文图书 0.50 元/天（宽限 0 天），逾期 10 天 | `POST /api/circulation/return` | fine = 5.00<br>实际：HTTP 200｜overdue_days=10, fine=5.00 | PASS |
| G-02 | 缴清罚款（未缴罚款会阻塞后续借书） | `POST /api/circulation/fines/1/pay` | paid = true<br>实际：HTTP 200｜amount=5.00, paid=True | PASS |
| G-03 | 逾期还书：学位论文 2.00 元/天，同样逾期 10 天 | `POST /api/circulation/return` | fine = 20.00（与图书 5.00 不同）<br>实际：HTTP 200｜overdue_days=10, fine=20.00 | PASS |
| H-01 | 预约图书（7 天有效期） | `POST /api/reservations` | queue_position≥1，expires_at = 今天+7 = 2026-10-02<br>实际：HTTP 200｜queue_position=1, expires_at=2026-10-02 | PASS |
| H-02 | 重复预约同一标题 | `POST /api/reservations` | 400 已预约过该书<br>实际：HTTP 400 code=400｜您已预约过该书 | PASS |
| H-03 | 取消预约 | `POST /api/reservations/1/cancel` | status = CANCELLED<br>实际：HTTP 200｜status=CANCELLED | PASS |
| I-01 | 提交评分与评论 | `POST /api/reviews` | status = PENDING（待审核）<br>实际：HTTP 200｜rating=5, status=PENDING | PASS |
| I-02 | 评分越界（6 分） | `POST /api/reviews` | 400 评分必须为 1-5 的整数<br>实际：HTTP 400 code=400｜评分必须为 1-5 的整数 | PASS |
| I-03 | 未审核评论不可见 | `GET /api/reviews?title_id=1` | total=0, average_rating=0.0（仅统计 APPROVED）<br>实际：HTTP 200｜total=0, average_rating=0.0 | PASS |
| I-04 | 读者审核评论 | `POST /api/reviews/1/moderate（读者令牌）` | 403 权限不足（仅系统管理员）<br>实际：HTTP 403 code=403｜权限不足 | PASS |
| I-05 | 系统管理员审核通过 | `POST /api/reviews/1/moderate` | status = APPROVED<br>实际：HTTP 200｜status=APPROVED | PASS |
| I-06 | 查看评论与平均分 | `GET /api/reviews?title_id=1` | total=1, average_rating=5.0<br>实际：HTTP 200｜total=1, average_rating=5.0 | PASS |

## 覆盖的实验二验收项

| 验收项 | 对应用例 |
|---|---|
| 9. 借书、还书、预约、查询可用 | C-01、F-01、H-01、D-01 |
| 10. 不同读者类型借阅规则可用 | C-01/C-02/C-05/C-06、C-03/C-04（出借物维度） |
| 11. 不同借出物类型罚款规则可用 | G-01（图书 5.00）vs G-02（论文 20.00） |
| 任务卡 任务一 续借 | E-01、E-02 |
| 任务卡 任务二 图书评论与评分 | I-01～I-06 |