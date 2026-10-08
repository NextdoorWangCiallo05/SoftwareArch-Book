# 领域模型说明书

> 输入：`specs/02-requirements.md`、`specs/03-use-cases.md`、`specs/constitution.md`
> 状态：草稿（Agent 生成，待人工审查）
> 说明：本文件描述**领域概念**，不引入 Controller、Repository 实现、DTO 等设计类（那些属于 `09-design-model.md`）。

---

## 1. 领域对象总览

| 类别 | 对象 |
|---|---|
| 实体（Entity） | `Account`、`Reader` / `StudentReader` / `TeacherReader`、`Librarian`、`SystemAdmin`、`BorrowCard`、`BookTitle`、`LibraryItem` / `Book` / `Magazine` / `Thesis`、`Loan`、`Reservation`、`FineRecord`、`LostItem`、`BookReview` |
| 值对象 / 枚举 | `Role`、`ReaderType`、`ItemType`、`ItemStatus`、`LoanStatus`、`CardStatus`、`ReservationStatus`、`ReviewStatus` |
| 策略对象（Strategy） | `BorrowPolicy`（二维）、`FineRule`（含宽限期）、`CompensationPolicy` |
| 领域服务 | `CirculationPolicyChecker`、`FineCalculator` |
| 仓储接口（领域层声明） | `ReaderRepository`、`ItemRepository`、`LoanRepository`、`ReservationRepository`、`FineRepository`、`ReviewRepository`、`PolicyRepository` |

---

## 2. 身份与账户

### 2.1 Account（账户 · 实体 · 聚合根）

- **职责**：承载登录认证信息，是系统内所有人类参与者的身份载体。
- **关键属性**：`id`、`username`（唯一）、`password_hash`、`salt`、`role`（`Role`）、`created_at`、`is_active`
- **关键方法**：
  - `set_password(raw)`：生成随机盐并计算哈希；
  - `verify_password(raw) -> bool`：校验密码；
  - `has_role(role) -> bool`：角色判定。
- **约束**：
  - 系统中**不存在明文密码**（宪法 10.1）；
  - `username` 全局唯一；
  - 角色从 `Account.role` 解析，业务层不信任请求体中的角色字段。
- **关系**：与 `Reader` / `Librarian` / `SystemAdmin` 各为 **1 : 0..1**（一个账户最多对应一个业务身份）。

> 设计说明：认证（`Account`）与业务身份（`Reader` 等）分离，避免把密码字段混入领域实体，也便于同一自然人兼具多种身份的扩展。

### 2.2 Role（枚举 · 值对象）
`READER` / `LIBRARIAN` / `ADMIN`

---

## 3. 读者与借阅证

### 3.1 Reader（读者 · 实体 · 聚合根）

- **职责**：表示可借书的人，持有借阅证，承担借阅配额与期限的载体。
- **关键属性**：`id`、`account_id`、`name`、`reader_type`（`ReaderType`）、`email`、`phone`、`status`
- **关键方法**：
  - `active_loans()`：当前未归还的借阅记录；
  - `has_overdue()`：是否存在超期未还；
  - `has_unpaid_fine()`：是否存在未缴罚款；
  - `can_borrow(policy) -> bool`：委托 `BorrowPolicy` 判定。

**子类（继承）**

| 子类 | 语义 | 差异化行为 |
|---|---|---|
| `StudentReader` | 学生读者（本科 / 研究生 / 博士） | 按 `UNDERGRADUATE` / `GRADUATE` / `DOCTOR` 取借阅规则 |
| `TeacherReader` | 教师读者 | 按 `TEACHER` 取借阅规则 |

- **约束**：`reader_type` 与子类保持一致（单表继承 + 鉴别列）；一个 Reader 最多一张 `ACTIVE` 借阅证。
- **关系**：`Reader 1 ── 0..1 BorrowCard`；`Reader 1 ── * Loan`；`Reader 1 ── * Reservation`；`Reader 1 ── * FineRecord`（经 Loan 间接）；`Reader 1 ── * BookReview`。

### 3.2 ReaderType（枚举 · 值对象）
`ASSOCIATE`（专科生，3 本 / 30 天）、`UNDERGRADUATE`（5 / 30）、`GRADUATE`（10 / 60）、`DOCTOR`（15 / 90）、`TEACHER`（20 / 90）

### 3.3 Librarian（图书管理员 · 实体）

- **职责**：代理读者办理借书、续借、标记罚款缴清；**审核读者提交的归还申请并确认收书**（或凭条码现场办理还书）；可查询任意读者借阅信息。
- **关键属性**：`id`、`account_id`、`name`、`employee_no`
- **关键方法**：`borrow_book(...)`、`return_book(...)`、`mark_fine_paid(...)`（均为应用服务编排入口，领域对象只提供状态变更方法）。
- **约束**：不可办理借阅证与图书维护（BR-011）。

### 3.4 SystemAdmin（系统管理员 · 实体）

- **职责**：办理/注销借阅证、维护管理员、维护图书标题与馆藏副本、维护借阅规则与罚款规则、审核评论。
- **关键属性**：`id`、`account_id`、`name`

### 3.5 BorrowCard（借阅证 · 实体）

- **职责**：证明读者的借书资格。
- **关键属性**：`id`、`card_no`（唯一，格式 `CARD + 年份 + 6 位序号`）、`reader_id`、`status`（`CardStatus`）、`issued_at`
- **关键方法**：`is_valid() -> bool`（`status == ACTIVE`）、`revoke()`
- **约束**：
  - `card_no` 全局唯一（BR-001）；
  - 同一读者最多一张 `ACTIVE` 借阅证；
  - 存在未归还图书时不得注销（BR-017）。
- **CardStatus**：`ACTIVE` / `LOST` / `REVOKED`

---

## 4. 馆藏与借出物

### 4.1 BookTitle（图书标题 · 实体 · 聚合根）

- **职责**：描述一类出版物的书目信息，是检索、预约、评论的对象。
- **关键属性**：`id`、`title`、`author`、`isbn`（唯一）、`publisher`、`published_year`、`category`、`item_type`（`ItemType`）、`price`、`is_active`
- **关键方法**：`available_items()`、`is_reservable()`
- **约束**：ISBN 唯一；存在未归还副本时不可下架。

### 4.2 LibraryItem（馆藏资源 · 抽象实体）

- **职责**：表示一本可被借阅的**实体副本**，承载状态机与条码。
- **关键属性**：`id`、`barcode`（唯一，格式 `ITEM + 年份 + 6 位序号`）、`title_id`、`status`（`ItemStatus`）、`location`、`acquired_at`
- **关键方法**：`mark_borrowed()`、`mark_available()`、`mark_removed()`、`is_available()`
- **约束**：`barcode` 全局唯一；状态迁移遵循 BR-010。

**子类（继承体系，Q-D1 已确认）**

| 子类 | 扩展属性 | 罚款归属类型 |
|---|---|---|
| `Book` | `edition`、`pages` | `CHINESE_BOOK` / `FOREIGN_BOOK` |
| `Magazine` | `issue_no`、`period` | `CHINESE_MAGAZINE` / `FOREIGN_MAGAZINE` |
| `Thesis` | `degree`、`school` | `THESIS` |

- **ItemType（枚举）**：`BOOK` / `MAGAZINE` / `THESIS`（单表继承鉴别列）
- **ItemStatus（枚举）**：`AVAILABLE` / `BORROWED` / `RESERVED` / `REMOVED`
- **关系**：`BookTitle 1 ── * LibraryItem`

> 罚款单价按**借出物类型**（`CHINESE_BOOK` 等 5 类）配置；领域实现上由 `LibraryItem` 的子类 + 语种标记共同决定，为简化配置，在 `LibraryItem` 上保留 `fine_category` 字段取值 5 种类型之一。

---

## 5. 流通

### 5.1 Loan（借阅记录 · 实体）

- **职责**：记录一次借出与归还的完整生命周期，是续借、归还申请审核与罚款计算的载体。
- **关键属性**：`id`、`reader_id`、`item_id`、`borrow_date`、`due_date`、`return_date`、`status`（`LoanStatus`）、`renew_count`
- **关键方法**：
  - `is_overdue(today) -> bool`：**在借状态**（`BORROWED` / `RETURN_REQUESTED`）且 `due_date < today` 时为真；
  - `renew(policy)`：校验"未逾期 + 次数未满 + 无他人有效预约"后延长 `due_date`，`renew_count += 1`，返回新的 `due_date`；
  - `request_return()`：读者发起归还申请，`BORROWED → RETURN_REQUESTED`（BR-020），**不改变副本状态**；
  - `reject_return_request()`：馆员驳回申请，`RETURN_REQUESTED → BORROWED`，不产生罚款、不改副本状态；
  - `return_item(today)`：设置 `return_date`，状态置 `RETURNED`，返回逾期天数。仅在**馆员审核通过或现场办理**时调用。
- **约束**：
  - `due_date = borrow_date + BorrowPolicy.get_borrow_days(reader_type)`；
  - 续借上限 1 次（BR-012）；
  - 已归还、已逾期或已提交归还申请（`RETURN_REQUESTED`）不可续借；
  - `RETURN_REQUESTED` 仍属**在借**：占用借阅数量配额、参与超期检查（BR-003）。
- **状态机（BR-020）**：`BORROWED → RETURN_REQUESTED → RETURNED`（审核通过）；`RETURN_REQUESTED → BORROWED`（审核驳回）
- **LoanStatus（枚举）**：`BORROWED` / `RETURN_REQUESTED` / `RETURNED` / `OVERDUE`
- **关系**：`Reader 1 ── * Loan`；`LibraryItem 1 ── * Loan`（同一副本历史上可有多条记录，同时最多一条**在借**记录 `BORROWED` / `RETURN_REQUESTED`）

### 5.2 Reservation（预约 · 实体）

- **职责**：表达读者对某一图书标题的排队请求。
- **关键属性**：`id`、`reader_id`、`title_id`、`created_at`、`expires_at`、`status`（`ReservationStatus`）、`queue_position`
- **关键方法**：
  - `is_expired(today) -> bool`（`today > expires_at`）；
  - `is_effective(today) -> bool`（`ACTIVE` 且未过期）；
  - `cancel()`、`fulfill()`、`expire()`
- **约束**：
  - 有效期 7 天：`expires_at = created_at + 7 天`（BR-008）；
  - 同一读者对同一标题最多一条**有效**（未过期）预约（BR-007）；
  - `EXPIRED` 不占排队位次，不阻塞续借；失效判定为读取时惰性判定。
- **ReservationStatus（枚举）**：`ACTIVE` / `CANCELLED` / `FULFILLED` / `EXPIRED`
- **关系**：`Reader 1 ── * Reservation`；`BookTitle 1 ── * Reservation`

---

## 6. 规则与策略

### 6.1 BorrowPolicy（借阅规则 · 策略对象）

- **职责**：按 **`(reader_type, item_type)` 二维策略键**提供"最大借阅数量"与"借阅期限"，集中承载 BR-002 / BR-004。
  语义等价于指导书参考类图中的"本科生借书策略 / 研究生借书策略 / 本科生借杂志策略 / 研究生杂志借阅策略"与"书到期策略 / 杂志到期策略"，本系统以**可配置策略表 + 策略对象**实现，规则可运行时调整，无需新增子类。
- **关键属性**：`reader_type`、`item_type`（`ALL | BOOK | MAGAZINE | THESIS`）、`max_borrow_count`、`borrow_days`
- **关键方法**：
  - `get_max_borrow_count(reader_type, item_type) -> int`
  - `get_borrow_days(reader_type, item_type) -> int`
  - `can_borrow(reader, item_type, active_loan_count) -> (bool, reason)`
- **约束**：
  - 查找顺序：先按 `(reader_type, item_type)` 精确匹配，未命中则回退 `(reader_type, ALL)`；
  - 规则**可配置**（FR-025 持久化），禁止硬编码在 Controller 或路由中（宪法第 8 条）。

### 6.2 FineRule（罚款规则 · 策略对象）

- **职责**：按借出物类型提供**宽限期**与**每日罚款金额**，集中承载 BR-005（指导书：超期时间的规定和罚金都不同）。
- **关键属性**：`item_category`、`grace_days`、`amount_per_day`
- **关键方法**：
  - `get_grace_days(item_category) -> int`
  - `calculate_fine(item_category, overdue_days) -> Decimal`
- **约束**：
  - `overdue_days <= 0` 返回 0；
  - `0 < overdue_days <= grace_days` 返回 0（宽限期内不计费，但仍判定为超期）；
  - 计费公式：`max(0, overdue_days - grace_days) × amount_per_day`；
  - 规则可配置（FR-026），实现为可替换策略，禁止硬编码。

### 6.3 FineCalculator（罚款计算 · 领域服务）

- **职责**：在还书流程（馆员审核通过 / 现场办理）中，根据 `Loan` 与对应副本的 `fine_category` 委托 `FineRule` 计算金额并生成 `FineRecord`。
- **关键方法**：`calculate(loan, return_date) -> FineRecord | None`
- **约束**：本身不持有单价，只做编排与结果封装。

### 6.4 CirculationPolicyChecker（流通前置校验 · 领域服务）

- **职责**：集中执行借书前的四项检查——借阅证有效、未超数量、无超期、无未缴罚款（BR-001～BR-006）。
- **关键方法**：`check_before_borrow(reader, item) -> (bool, reason)`
- **约束**：供应用服务调用，不直接返回 HTTP 错误码（错误码映射在表现层完成）。

---

## 7. 罚款

### 7.1 FineRecord（罚款记录 · 实体）

- **职责**：记录一次超期产生的罚款金额与缴纳状态。
- **关键属性**：`id`、`loan_id`、`amount`、`paid`、`created_at`、`paid_at`
- **关键方法**：`mark_paid()`
- **约束**：`amount` 保留 2 位小数；已缴清不可重复缴纳；存在 `paid = false` 的记录时禁止借书（BR-006）。

### 7.2 LostItem（丢失与赔偿 · 实体）

- **职责**：记录馆藏遗失事件与赔偿金额（对应参考类图的「丢失书项」）。
- **关键属性**：`id`、`loan_id`、`item_id`、`lost_date`、`amount`、`paid`、`paid_at`
- **关键方法**：`mark_paid()`
- **约束**：
  - 赔偿金额由 `CompensationPolicy` 计算，实体不自行计算；
  - 登记丢失后对应 `LibraryItem` 状态置为 `REMOVED`，不再可借；
  - 存在未缴赔偿时禁止借书（BR-006）。

### 7.3 CompensationPolicy（赔偿规则 · 策略对象）

- **职责**：按出借物类型提供赔偿倍率（对应参考类图的「图书赔偿策略 / 杂志赔偿策略」）。
- **关键属性**：`item_type`、`rate`
- **关键方法**：`calculate_compensation(item_type, price) -> Decimal`
- **约束**：`amount = price × rate`（`BOOK=2.0`、`MAGAZINE=1.5`、`THESIS=3.0`）；定价缺失时抛 `BusinessError`；倍率可配置，禁止硬编码。

---

## 8. 评论与评分（P2）

### 8.1 BookReview（图书评论 · 实体）

- **职责**：承载读者对图书标题的评分与评论文本，需经审核方可公开。
- **关键属性**：`id`、`title_id`、`reader_id`、`rating`（1–5 整数）、`comment`、`status`（`ReviewStatus`）、`created_at`、`updated_at`
- **关键方法**：`update(rating, comment)`（更新后状态重置为 `PENDING`）、`approve()`、`reject()`、`is_visible()`
- **约束**：
  - 同一读者对同一标题仅保留一条记录（BR-014）；
  - 仅 `APPROVED` 计入平均分并对外可见（BR-018）；
  - 评分越界为业务错误（BR-013）。
- **ReviewStatus（枚举）**：`PENDING` / `APPROVED` / `REJECTED`
- **关系**：`BookTitle 1 ── * BookReview`；`Reader 1 ── * BookReview`

---

## 9. 聚合与一致性边界

| 聚合根 | 聚合内对象 | 一致性规则 |
|---|---|---|
| `Reader` | `BorrowCard` | 借阅证状态与读者借书资格强一致；注销借阅证需校验无未归还 |
| `BookTitle` | `LibraryItem` | 副本状态由标题聚合内统一维护；下架需校验无未归还副本 |
| `Loan` | （引用 `Reader`、`LibraryItem` 的 ID） | 借书时需同时更新 Loan 与副本状态，**同一事务** |
| `Reservation` | （引用 `Reader`、`BookTitle` 的 ID） | 排队位次在标题维度计算 |
| `FineRecord` | （引用 `Loan` 的 ID） | 随还书事务一并生成 |

跨聚合引用**一律通过 ID**，不通过对象引用，避免大聚合导致的性能与一致性问题。

---

## 10. 领域层与基础设施层的边界

- 领域层只声明仓储接口（`ReaderRepository` 等），不依赖 SQLAlchemy Session（宪法第 9 条）；
- 继承映射（`Reader` 子类、`LibraryItem` 子类）采用 **SQLAlchemy 单表继承 + 鉴别列**，由基础设施层实现，领域层只见子类语义；
- 枚举值以字符串持久化，便于 SQLite 中直接阅读与调试。
