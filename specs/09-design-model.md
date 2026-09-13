# 详细设计模型说明书

> 输入：`specs/02-requirements.md`、`specs/03-use-cases.md`、`specs/05-domain-model.md`、`specs/07-architecture.md`、`specs/13-database-design.md`
> 状态：草稿（Agent 生成，待人工审查）
> 方法：采用指导书推荐的**两步走**——先给出分析类（不含界面与持久化），再增强为设计类（加入 Controller、Repository 实现、DTO）。

---

## 1. 设计方法

| 步骤 | 产物 | 说明 |
|---|---|---|
| 第一步：分析类 | 领域实体、策略对象、领域服务及其交互 | 不考虑界面与持久化 |
| 第二步：设计类 | 在分析类基础上加入 Controller、Application Service、Repository 实现、DTO | 得到可编码的设计类图与顺序图 |

---

## 2. 分析类（第一步）

| 分析类 | 职责 | 关键方法 |
|---|---|---|
| `Account` | 身份与凭证 | `set_password`、`verify_password`、`has_role` |
| `Reader` / `StudentReader` / `TeacherReader` | 借阅主体 | `active_loans`、`has_overdue`、`has_unpaid_fine`、`can_borrow` |
| `BorrowCard` | 借书资格凭证 | `is_valid`、`revoke` |
| `BookTitle` | 书目信息 | `available_items`、`is_reservable` |
| `LibraryItem` / `Book` / `Magazine` / `Thesis` | 实体副本与状态 | `is_available`、`mark_borrowed`、`mark_available` |
| `Loan` | 借阅生命周期 | `is_overdue`、`renew`、`return_item` |
| `Reservation` | 预约与排队 | `is_effective`、`is_expired`、`cancel`、`fulfill` |
| `BorrowPolicy` | 数量与期限策略 | `get_max_borrow_count`、`get_borrow_days`、`can_borrow` |
| `FineRule` | 罚款策略 | `get_grace_days`、`calculate_fine` |
| `FineCalculator` | 罚款计算服务 | `calculate` |
| `CirculationPolicyChecker` | 借书前置校验服务 | `check_before_borrow` |
| `BookReview` | 评分与评论 | `update`、`approve`、`reject`、`is_visible` |

---

## 3. 设计类（第二步）

### 3.1 表现层（Controller）

| 设计类 | 端点前缀 | 依赖 |
|---|---|---|
| `auth_router` | `/api/auth` | `AuthService` |
| `catalog_router` | `/api/books` | `CatalogService` |
| `circulation_router` | `/api/circulation` | `CirculationService` |
| `reservation_router` | `/api/reservations` | `ReservationService` |
| `review_router` | `/api/reviews` | `ReviewService` |
| `admin_router` | `/api/admin` | `AdminService` |

公共依赖：`get_db`（会话）、`get_current_account`（令牌解析）、`require_role(...)`（角色校验）。

### 3.2 应用层（Service）

| 设计类 | 主要方法 |
|---|---|
| `AuthService` | `register`、`login`、`logout`、`get_current` |
| `CatalogService` | `search`、`get_detail` |
| `CirculationService` | `borrow`、`return_book`、`renew`、`list_loans` |
| `ReservationService` | `create`、`cancel`、`list_by_title` |
| `ReviewService` | `submit`、`list_approved`、`moderate` |
| `AdminService` | `issue_card`、`revoke_card`、`add_librarian`、`remove_librarian`、`add_title`、`deactivate_title`、`add_item`、`remove_item`、`upsert_borrow_policy`、`upsert_fine_rule` |

### 3.3 基础设施层（Repository 实现）

`SQLAlchemyReaderRepository`、`SQLAlchemyItemRepository`、`SQLAlchemyLoanRepository`、`SQLAlchemyReservationRepository`、`SQLAlchemyFineRepository`、`SQLAlchemyReviewRepository`、`SQLAlchemyPolicyRepository`，均实现领域层声明的抽象基类。

### 3.4 DTO（`schemas/`）

请求 DTO 不接收 `role`、`paid` 等敏感或派生字段；响应 DTO 不返回 `password_hash`、`salt`。

---

## 4. 类的数据结构与关键算法

### 4.1 密码与令牌（UC-002）

**数据结构**：`accounts(password_hash, salt)`、`auth_tokens(token, account_id, expires_at)`

**算法：设置密码**

```python
def set_password(raw: str) -> None:
    self.salt = os.urandom(16).hex()                       # 32 位十六进制
    self.password_hash = hashlib.pbkdf2_hmac(
        "sha256", raw.encode("utf-8"),
        bytes.fromhex(self.salt), 120_000                  # 迭代 12 万次
    ).hex()
```

**算法：校验密码**

```python
def verify_password(raw: str) -> bool:
    calc = hashlib.pbkdf2_hmac("sha256", raw.encode(), bytes.fromhex(self.salt), 120_000).hex()
    return hmac.compare_digest(calc, self.password_hash)    # 常量时间比较，防时序攻击
```

**算法：登录**

```python
def login(username, password):
    acc = repo.find_by_username(username)
    if acc is None or not acc.verify_password(password):
        raise PermissionDeniedError("用户名或密码错误")     # 统一文案，不泄露用户是否存在
    token = secrets.token_urlsafe(32)
    token_store.save(token, acc.id, ttl_hours=8)
    return LoginDTO(token=token, user_id=acc.id, role=acc.role, username=acc.username)
```

> 令牌有效期默认 **8 小时**（OPEN-06 默认取值）；`get_current_account` 每次请求校验 `expires_at`，过期返回 `403`。

### 4.2 借书（UC-009）

**输入**：`card_no`、`barcode`
**输出**：`loan_id`、`barcode`、`title`、`due_date`

**算法（应用服务 `CirculationService.borrow`）**

```python
def borrow(card_no: str, barcode: str, operator: Account) -> BorrowResultDTO:
    require(operator.has_role(LIBRARIAN))              # 否则 PermissionDeniedError → 403

    card  = card_repo.find_by_no(card_no)
    if card is None:        raise NotFoundError("借阅证不存在")
    if not card.is_valid(): raise BusinessError("借阅证无效")

    reader = reader_repo.get(card.reader_id)
    item   = item_repo.find_by_barcode(barcode)
    if item is None:        raise NotFoundError("馆藏不存在")

    checker.check_before_borrow(reader, item)           # 四项前置校验，见 4.3

    # 二维策略：先 (reader_type, item_type) 精确匹配，未命中回退 (reader_type, ALL)
    due = today + timedelta(days=policy.get_borrow_days(reader.reader_type, item.item_type))
    loan = Loan(reader_id=reader.id, item_id=item.id,
                borrow_date=today, due_date=due, status=BORROWED, renew_count=0)
    item.mark_borrowed()                                # AVAILABLE → BORROWED
    loan_repo.add(loan)                                 # 同一事务提交
    return BorrowResultDTO(...)
```

**事务边界**：`loan_repo.add` 与 `item.mark_borrowed` 在同一事务，任一失败全部回滚。

### 4.3 借书前置校验（`CirculationPolicyChecker`）

```python
def check_before_borrow(reader, item) -> None:
    policy = policy_repo.get(reader.reader_type, item.item_type)   # 二维，未命中回退 ALL
    active = loan_repo.count_active(reader.id, item.item_type)
    if active >= policy.max_borrow_count:
        raise BusinessError(f"借阅已满（{active}/{policy.max_borrow_count}），请先归还图书")
    if loan_repo.count_overdue(reader.id) > 0:
        raise BusinessError("有超期未还图书，请先归还")
    if fine_repo.has_unpaid(reader.id):
        raise BusinessError("存在未缴罚款，请先缴清")
    if not item.is_available():
        raise BusinessError("该馆藏不可借")
```

### 4.4 还书与罚款计算（UC-010 / UC-015）

```python
def return_book(barcode: str, operator: Account) -> ReturnResultDTO:
    require(operator.has_role(LIBRARIAN))
    item = item_repo.find_by_barcode(barcode)
    if item is None or not item.belongs_to_library:
        raise BusinessError("非本馆藏书")
    loan = loan_repo.find_active_by_item(item.id)
    if loan is None:
        raise BusinessError("未找到该馆藏的借阅记录")

    overdue_days = loan.return_item(today)              # 设置 return_date，状态 → RETURNED
    item.mark_available()                               # BORROWED → AVAILABLE

    fine = 0
    if overdue_days > 0:
        fine = calculator.calculate(loan, today)        # 见下，宽限期内返回 0
    return ReturnResultDTO(loan_id=loan.id, return_date=today,
                           overdue_days=overdue_days, fine=fine)
```

**罚款算法（含宽限期）**

```python
def calculate(self, loan, return_date) -> Decimal:
    overdue = (return_date - loan.due_date).days
    if overdue <= 0:
        return Decimal("0.00")
    rule = fine_rule_repo.get(item.fine_category)
    chargeable = overdue - rule.grace_days
    if chargeable <= 0:
        return Decimal("0.00")                          # 宽限期内：判定超期但不计费
    amount = Decimal(chargeable) * rule.amount_per_day
    fine_repo.add(FineRecord(loan_id=loan.id, amount=amount.quantize(Decimal("0.01")), paid=False))
    return amount
```

### 4.5 续借（UC-011）

```python
def renew(self, policy, has_other_active_reservation: bool, today) -> date:
    if self.status != BORROWED:  raise BusinessError("该图书已归还，无法续借")
    if self.is_overdue(today):   raise BusinessError("该图书已逾期，请归还后重新借阅")
    if self.renew_count >= 1:    raise BusinessError("该图书已达续借上限（1 次）")
    if has_other_active_reservation:
        raise BusinessError("该图书已被预约，暂不可续借")
    self.due_date = self.due_date + timedelta(
        days=policy.get_borrow_days(reader_type, self.item.item_type))  # 二维策略
    self.renew_count += 1
    return self.due_date
```

> 续借基数为**原 `due_date`** 而非今天，避免逾期前突击续借造成期限损失；延长天数取该读者类型借阅期限。

### 4.6 预约排队与有效期（UC-013）

```python
def create_reservation(reader_id, title_id) -> ReservationDTO:
    title = title_repo.get(title_id)                    # 不存在 → 404
    if reservation_repo.has_effective(reader_id, title_id):
        raise BusinessError("您已预约过该书")
    if loan_repo.has_active_loan_of_title(reader_id, title_id):
        raise BusinessError("您已借有该书，无需预约")

    resv = Reservation(reader_id=reader_id, title_id=title_id,
                       created_at=now, expires_at=(now + timedelta(days=7)).date(),
                       status=ACTIVE)
    resv.queue_position = reservation_repo.count_effective_before(title_id, resv.created_at) + 1
    reservation_repo.add(resv)
    return ...
```

**有效预约判定（惰性失效）**

```python
def is_effective(self, today) -> bool:
    return self.status == ACTIVE and not self.is_expired(today)

def is_expired(self, today) -> bool:
    return today > self.expires_at
```

### 4.7 评论评分与审核（UC-017 / 018 / 021）

```python
def submit(title_id, reader_id, rating, comment):
    if not (isinstance(rating, int) and 1 <= rating <= 5):
        raise BusinessError("评分必须为 1-5 的整数")
    review = review_repo.find_by_reader_and_title(title_id, reader_id)
    if review is None:
        review = BookReview(title_id=title_id, reader_id=reader_id, status=PENDING)
    review.update(rating, comment)      # 更新后 status 重置为 PENDING（BR-014）
    review_repo.save(review)
    return ...

def list_approved(title_id):
    reviews = review_repo.list_by_status(title_id, APPROVED)
    avg = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0.0
    return ReviewListDTO(title_id=title_id, average_rating=avg,
                         total=len(reviews), reviews=[...])
```

### 4.8 借阅规则与罚款规则维护（UC-019 / 020）

写入前校验：`max_borrow_count > 0`、`borrow_days > 0`、`amount_per_day >= 0`、`grace_days >= 0`；非法值抛 `BusinessError`。修改**仅对新借阅生效**，已有 Loan 的 `due_date` 不变。

### 4.9 登记丢失与赔偿（UC-022）

```python
def report_lost(barcode: str, operator: Account) -> LostResultDTO:
    require(operator.has_role(LIBRARIAN))                 # 否则 403

    item = item_repo.find_by_barcode(barcode)
    if item is None:      raise NotFoundError("馆藏不存在")
    loan = loan_repo.find_active_by_item(item.id)
    if loan is None:      raise BusinessError("未找到该馆藏的借阅记录")

    title = title_repo.get(item.title_id)
    if title.price is None:
        raise BusinessError("请先维护该图书定价")            # BR-018a

    amount = compensation_policy.calculate_compensation(item.item_type, title.price)
    lost = LostItem(loan_id=loan.id, item_id=item.id,
                    lost_date=today, amount=amount, paid=False)
    loan.close_as_lost()                                   # 结束借阅
    item.mark_removed()                                    # 丢失副本不可再借
    lost_repo.add(lost)                                    # 同一事务
    return LostResultDTO(...)
```

赔偿倍率由 `CompensationPolicy` 提供（`BOOK=2.0`、`MAGAZINE=1.5`、`THESIS=3.0`），可配置，禁止硬编码。

---

## 5. 用例 × 设计元素映射

| 用例 | Controller | Application Service | 领域对象 / 策略 | Repository | 请求 DTO | 响应 DTO | 异常 | 事务 |
|---|---|---|---|---|---|---|---|---|
| UC-001 注册 | auth_router | `AuthService.register` | `Account`、`Reader` | ReaderRepo | `RegisterRequest` | `ReaderDTO` | Business(400) | 写 |
| UC-002 登录 | auth_router | `AuthService.login` | `Account` | AccountRepo、TokenStore | `LoginRequest` | `LoginDTO` | Permission(403) | 写 |
| UC-003 办证 | admin_router | `AdminService.issue_card` | `BorrowCard` | CardRepo、ReaderRepo | `IssueCardRequest` | `CardDTO` | Permission/NotFound/Business | 写 |
| UC-004 注销证 | admin_router | `AdminService.revoke_card` | `BorrowCard`、`Loan` | CardRepo、LoanRepo | `RevokeCardRequest` | `CardDTO` | Business(400)、NotFound | 写 |
| UC-005 加管理员 | admin_router | `AdminService.add_librarian` | `Account`、`Librarian` | AccountRepo | `CreateStaffRequest` | `StaffDTO` | Business(400) | 写 |
| UC-006 加标题 | admin_router | `AdminService.add_title` | `BookTitle` | TitleRepo | `TitleRequest` | `TitleDTO` | Business(400) | 写 |
| UC-007 加副本 | admin_router | `AdminService.add_item` | `LibraryItem` 子类（Factory） | ItemRepo | `ItemRequest` | `ItemDTO` | NotFound(404) | 写 |
| UC-008 检索 | catalog_router | `CatalogService.search` | `BookTitle` | TitleRepo | query params | `BookListDTO` | — | 读 |
| UC-009 借书 | circulation_router | `CirculationService.borrow` | `Loan`、`BorrowPolicy`、`CirculationPolicyChecker` | LoanRepo、ItemRepo、CardRepo | `BorrowRequest` | `BorrowResultDTO` | Permission/NotFound/Business | **写（同一事务）** |
| UC-010 还书 | circulation_router | `CirculationService.return_book` | `Loan`、`FineRule`、`FineCalculator` | LoanRepo、ItemRepo、FineRepo | `ReturnRequest` | `ReturnResultDTO` | Permission/Business | **写（同一事务）** |
| UC-011 续借 | circulation_router | `CirculationService.renew` | `Loan`、`BorrowPolicy`、`Reservation` | LoanRepo、ReservationRepo | `RenewRequest` | `RenewResultDTO` | Business/NotFound | 写 |
| UC-012 查借阅 | circulation_router | `CirculationService.list_loans` | `Loan` | LoanRepo | path + query | `LoanListDTO` | Permission(403) | 读 |
| UC-013 预约 | reservation_router | `ReservationService.create` | `Reservation` | ReservationRepo、LoanRepo、TitleRepo | `ReserveRequest` | `ReservationDTO` | NotFound/Business | 写 |
| UC-014 取消预约 | reservation_router | `ReservationService.cancel` | `Reservation` | ReservationRepo | path | `ReservationDTO` | NotFound/Business | 写 |
| UC-015 计罚款 | （UC-010 内含） | — | `FineRule`、`FineCalculator` | FineRepo | — | — | Business(500 未配置) | 随还书事务 |
| UC-016 缴清罚款 | circulation_router | `CirculationService.mark_fine_paid` | `FineRecord` | FineRepo | path | `FineDTO` | Permission/NotFound/Business | 写 |
| UC-017 提交评论 | review_router | `ReviewService.submit` | `BookReview` | ReviewRepo、TitleRepo | `ReviewRequest` | `ReviewDTO` | NotFound/Business | 写 |
| UC-018 看评论 | review_router | `ReviewService.list_approved` | `BookReview` | ReviewRepo | query | `ReviewListDTO` | NotFound(404) | 读 |
| UC-019 借阅规则 | admin_router | `AdminService.upsert_borrow_policy` | `BorrowPolicy` | PolicyRepo | `PolicyRequest` | `PolicyDTO` | Permission/Business | 写 |
| UC-020 罚款规则 | admin_router | `AdminService.upsert_fine_rule` | `FineRule` | PolicyRepo | `FineRuleRequest` | `FineRuleDTO` | Permission/Business | 写 |
| UC-021 审核评论 | review_router | `ReviewService.moderate` | `BookReview` | ReviewRepo | `ModerateRequest` | `ReviewDTO` | Permission/NotFound/Business | 写 |
| UC-022 处理赔偿 | circulation_router | `CirculationService.report_lost` | `LostItem`、`CompensationPolicy` | ItemRepo、LoanRepo、LostRepo、PolicyRepo | `LostRequest` | `LostResultDTO` | Permission/NotFound/Business | **写（同一事务）** |
| UC-023 管理借阅者 | admin_router | `AdminService.manage_reader` | `Account`、`Reader` | ReaderRepo | `ReaderManageRequest` | `ReaderDTO` / `ReaderListDTO` | Permission/NotFound/Business | 写 |
| UC-024 管理图书管理员 | admin_router | `AdminService.manage_librarian` | `Librarian` | LibrarianRepo | `StaffManageRequest` | `StaffDTO` / `StaffListDTO` | Permission/NotFound/Business | 写 |
| UC-025 修改图书信息 | admin_router | `AdminService.update_title` | `BookTitle` | TitleRepo | `TitleUpdateRequest` | `TitleDTO` | Permission/NotFound/Business | 写 |

---

## 6. 展现层 → 领域层的消息设计

指导书要求"界面元素的设计，重点考虑从展现层进入领域层的消息"。本项目以 REST API 作为展现层入口，消息设计如下：

```text
POST /api/auth/register   {username, password, name, reader_type}
POST /api/auth/login      {username, password}                  → {token, user_id, role, username}
POST /api/auth/logout     (Header: Authorization)

GET  /api/books/search?keyword=&author=&category=&page=
GET  /api/books/{title_id}

POST /api/circulation/borrow       {card_no, barcode}           → {loan_id, title, barcode, due_date}
POST /api/circulation/return       {barcode}                    → {loan_id, return_date, overdue_days, fine}
POST /api/circulation/renew        {loan_id}                    → {loan_id, new_due_date, renew_count}
GET  /api/circulation/records/{reader_id}?status=
POST /api/circulation/fines/{fine_id}/pay

POST /api/reservations             {title_id}                   → {reservation_id, queue_position, expires_at}
POST /api/reservations/{id}/cancel

POST /api/reviews                  {title_id, rating, comment}  → {review_id, status}
GET  /api/reviews?title_id=                                     → {average_rating, total, reviews}
POST /api/reviews/{id}/moderate    {decision}                   → {review_id, status}

POST /api/admin/cards              {reader_id}                  → {card_no}
POST /api/admin/cards/{id}/revoke
POST /api/admin/librarians         {username, password, name}
DELETE /api/admin/librarians/{id}
POST /api/admin/titles             {...}
POST /api/admin/titles/{id}/deactivate
POST /api/admin/items              {title_id, count, location}
POST /api/admin/items/{id}/remove
PUT  /api/admin/policies/borrow    {reader_type, max_borrow_count, borrow_days}
PUT  /api/admin/policies/fine      {item_category, grace_days, amount_per_day}
```

所有响应统一信封 `{code, message, data}`；完整字段定义见 `14-api-spec.md`。

---

## 7. 设计模式落点

| 模式 | 落点 | 解决的问题 |
|---|---|---|
| Strategy | `BorrowPolicy`、`FineRule` | 读者类型/借出物类型规则可配置、可替换 |
| Repository | `domain/repositories` 接口 + `infrastructure/repositories` 实现 | 领域层与持久化解耦 |
| Service Layer | `application/*_service.py` | 用例编排与事务边界 |
| DTO | `schemas/*` | 隔离接口层与领域层，防止过度暴露 |
| Factory | `ReaderFactory`、`ItemFactory` | 按鉴别列创建子类实例 |
| Dependency Injection | FastAPI `Depends` | 注入会话、当前账户、仓储实现 |
| Template Method（继承） | `Reader` / `LibraryItem` 单表继承 | 区分读者类型与借出物类型 |
| Facade | `CirculationPolicyChecker` | 封装借书四项前置校验 |

---

## 8. 异常与事务汇总

| 场景 | 异常 | code | 事务 |
|---|---|---|---|
| 未携带/无效令牌 | `PermissionDeniedError` | 403 | — |
| 角色不符 | `PermissionDeniedError` | 403 | — |
| 资源不存在 | `NotFoundError` | 404 | — |
| 业务规则不满足 | `BusinessError` | 400 | 回滚 |
| 底层故障 | `InfrastructureError` | 500 | 回滚 |

写事务用例：注册、登录、办证、注销证、加管理员、加标题、加副本、借书、还书、续借、预约、取消预约、缴清罚款、提交评论、审核评论、规则维护。
读用例不开启写事务。
