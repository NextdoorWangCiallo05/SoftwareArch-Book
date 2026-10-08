# 数据库设计说明书

> 输入：`specs/05-domain-model.md`、`specs/07-architecture.md`、`specs/02-requirements.md`
> 状态：草稿（Agent 生成，待人工审查）
> 数据库：SQLite（`backend/app/library.db`），ORM：SQLAlchemy 2.x
> 约定：时间字段存 `DATETIME`，日期字段存 `DATE`（`YYYY-MM-DD`）；金额用 `NUMERIC(10,2)`。

---

## 1. 表清单

| # | 表名 | 说明 |
|---|---|---|
| 1 | `accounts` | 登录账户（认证） |
| 2 | `auth_tokens` | 访问令牌 |
| 3 | `readers` | 读者（单表继承：Student / Teacher） |
| 4 | `librarians` | 图书管理员 |
| 5 | `system_admins` | 系统管理员 |
| 6 | `borrow_cards` | 借阅证 |
| 7 | `book_titles` | 图书标题 |
| 8 | `library_items` | 馆藏副本（单表继承：Book / Magazine / Thesis） |
| 9 | `loans` | 借阅记录 |
| 10 | `reservations` | 预约 |
| 11 | `fine_records` | 罚款记录 |
| 12 | `borrow_policies` | 借阅规则（策略配置） |
| 13 | `fine_rules` | 罚款规则（策略配置） |
| 14 | `book_reviews` | 图书评论与评分 |
| 15 | `lost_items` | 丢失与赔偿记录 |
| 16 | `compensation_policies` | 赔偿策略（倍率） |

---

## 2. 表结构

### 2.1 accounts（登录账户）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | 账户 ID |
| username | VARCHAR(50) | N | UNIQUE, IDX | — | 登录名 |
| password_hash | VARCHAR(128) | N | | — | PBKDF2-HMAC 哈希 |
| salt | VARCHAR(64) | N | | — | 随机盐 |
| role | VARCHAR(20) | N | | 'reader' | reader / librarian / admin |
| is_active | BOOLEAN | N | | 1 | 是否启用 |
| created_at | DATETIME | N | | now | 创建时间 |

### 2.2 auth_tokens（访问令牌）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| token | VARCHAR(64) | N | PK, UNIQUE | — | 令牌串 |
| account_id | INTEGER | N | FK→accounts.id | — | 所属账户 |
| expires_at | DATETIME | N | | — | 过期时间 |
| created_at | DATETIME | N | | now | 签发时间 |

### 2.3 readers（读者 · 单表继承）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | 读者 ID |
| account_id | INTEGER | N | FK→accounts.id, UNIQUE | — | 关联账户 |
| name | VARCHAR(50) | N | | — | 姓名 |
| reader_type | VARCHAR(20) | N | IDX | — | 鉴别列：UNDERGRADUATE / GRADUATE / DOCTOR / TEACHER |
| grade | VARCHAR(50) | Y | | NULL | 学生读者扩展（StudentReader） |
| department | VARCHAR(100) | Y | | NULL | 教师读者扩展（TeacherReader） |
| email | VARCHAR(100) | Y | | NULL | 邮箱 |
| phone | VARCHAR(30) | Y | | NULL | 电话 |
| status | VARCHAR(20) | N | | 'active' | active / inactive |

> **继承映射策略**：单表继承（Single Table Inheritance），鉴别列 `reader_type`；子类专有列可空。

### 2.4 librarians（图书管理员）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| account_id | INTEGER | N | FK→accounts.id, UNIQUE | — | |
| name | VARCHAR(50) | N | | — | |
| employee_no | VARCHAR(30) | Y | UNIQUE | NULL | 工号 |

### 2.5 system_admins（系统管理员）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| account_id | INTEGER | N | FK→accounts.id, UNIQUE | — | |
| name | VARCHAR(50) | N | | — | |

### 2.6 borrow_cards（借阅证）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| card_no | VARCHAR(30) | N | UNIQUE, IDX | — | `CARD+年份+6位序号` |
| reader_id | INTEGER | N | FK→readers.id, IDX | — | 持证人 |
| status | VARCHAR(20) | N | | 'ACTIVE' | ACTIVE / LOST / REVOKED |
| issued_at | DATETIME | N | | now | 办理时间 |
| revoked_at | DATETIME | Y | | NULL | 注销时间 |

> **部分唯一索引**：`CREATE UNIQUE INDEX uq_card_active ON borrow_cards(reader_id) WHERE status='ACTIVE'` —— 保证同一读者最多一张有效证（BR-001）。

### 2.7 book_titles（图书标题）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| title | VARCHAR(200) | N | IDX | — | 题名 |
| author | VARCHAR(100) | N | IDX | — | 作者 |
| isbn | VARCHAR(20) | N | UNIQUE | — | ISBN |
| publisher | VARCHAR(100) | Y | | NULL | 出版社 |
| published_year | INTEGER | Y | | NULL | 出版年 |
| category | VARCHAR(50) | Y | IDX | NULL | 分类 |
| item_type | VARCHAR(20) | N | | 'BOOK' | BOOK / MAGAZINE / THESIS |
| price | NUMERIC(10,2) | Y | | NULL | 定价（仅记录，不参与罚款上限） |
| is_active | BOOLEAN | N | | 1 | 是否上架 |
| created_at | DATETIME | N | | now | |

### 2.8 library_items（馆藏副本 · 单表继承）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| barcode | VARCHAR(30) | N | UNIQUE, IDX | — | `ITEM+年份+6位序号` |
| title_id | INTEGER | N | FK→book_titles.id, IDX | — | 所属标题 |
| item_type | VARCHAR(20) | N | | — | 鉴别列：BOOK / MAGAZINE / THESIS |
| status | VARCHAR(20) | N | IDX | 'AVAILABLE' | AVAILABLE / BORROWED / RESERVED / REMOVED |
| location | VARCHAR(50) | Y | | NULL | 馆藏位置 |
| fine_category | VARCHAR(30) | N | | 'CHINESE_BOOK' | 罚款档位（5 类之一） |
| edition | VARCHAR(30) | Y | | NULL | Book 扩展 |
| pages | INTEGER | Y | | NULL | Book 扩展 |
| issue_no | VARCHAR(30) | Y | | NULL | Magazine 扩展 |
| period | VARCHAR(30) | Y | | NULL | Magazine 扩展 |
| degree | VARCHAR(30) | Y | | NULL | Thesis 扩展 |
| school | VARCHAR(100) | Y | | NULL | Thesis 扩展 |
| acquired_at | DATETIME | N | | now | 入藏时间 |

### 2.9 loans（借阅记录）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| reader_id | INTEGER | N | FK→readers.id, IDX | — | 借阅人 |
| item_id | INTEGER | N | FK→library_items.id, IDX | — | 馆藏副本 |
| borrow_date | DATE | N | | — | 借出日期 |
| due_date | DATE | N | IDX | — | 应还日期 |
| return_date | DATE | Y | | NULL | 实还日期 |
| status | VARCHAR(20) | N | IDX | 'BORROWED' | BORROWED / RETURN_REQUESTED / RETURNED / OVERDUE |
| renew_count | INTEGER | N | | 0 | 已续借次数（上限 1） |

> **部分唯一索引**：`CREATE UNIQUE INDEX uq_item_active_loan ON loans(item_id) WHERE status IN ('BORROWED','RETURN_REQUESTED')` —— 同一副本同时最多一条在借记录（含归还申请中，BR-020）。

### 2.10 reservations（预约）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| reader_id | INTEGER | N | FK→readers.id, IDX | — | 预约人 |
| title_id | INTEGER | N | FK→book_titles.id, IDX | — | 预约标题 |
| created_at | DATETIME | N | | now | 创建时间（排队依据） |
| expires_at | DATE | N | IDX | — | 有效期截止（created_at + 7 天） |
| status | VARCHAR(20) | N | | 'ACTIVE' | ACTIVE / CANCELLED / FULFILLED / EXPIRED |
| queue_position | INTEGER | Y | | NULL | 排队位次（读取时计算并回写） |

> **部分唯一索引**：`CREATE UNIQUE INDEX uq_resv_active ON reservations(reader_id, title_id) WHERE status='ACTIVE'` —— 有效预约唯一（BR-007）。

### 2.11 fine_records（罚款记录）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| loan_id | INTEGER | N | FK→loans.id, IDX | — | 关联借阅 |
| amount | NUMERIC(10,2) | N | | — | 罚款金额 |
| paid | BOOLEAN | N | | 0 | 是否已缴 |
| created_at | DATETIME | N | | now | |
| paid_at | DATETIME | Y | | NULL | 缴清时间 |

### 2.12 borrow_policies（借阅规则）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| reader_type | VARCHAR(20) | N | UNIQUE | — | ASSOCIATE / UNDERGRADUATE / GRADUATE / DOCTOR / TEACHER |
| item_type | VARCHAR(20) | N | UNIQUE | 'ALL' | ALL / BOOK / MAGAZINE / THESIS（二维策略键） |
| max_borrow_count | INTEGER | N | | — | 最大借阅数量 |
| borrow_days | INTEGER | N | | — | 借阅期限（天） |

**唯一约束**：`UNIQUE(reader_type, item_type)`

**初始数据（主规则）**：`(ASSOCIATE,ALL,3,30)`、`(UNDERGRADUATE,ALL,5,30)`、`(GRADUATE,ALL,10,60)`、`(DOCTOR,ALL,15,90)`、`(TEACHER,ALL,20,90)`

**初始数据（出借物维度覆盖）**：`(ASSOCIATE,MAGAZINE,2,7)`、`(UNDERGRADUATE,MAGAZINE,2,7)`、`(GRADUATE,MAGAZINE,2,7)`、`(DOCTOR,MAGAZINE,2,7)`、`(TEACHER,MAGAZINE,2,7)`、`(ASSOCIATE,THESIS,2,3)`、`(UNDERGRADUATE,THESIS,2,3)`、`(GRADUATE,THESIS,2,3)`、`(DOCTOR,THESIS,2,3)`、`(TEACHER,THESIS,2,3)`

> 查找顺序：先按 `(reader_type, item_type)` 精确匹配，未命中回退 `(reader_type, 'ALL')`。

### 2.13 fine_rules（罚款规则）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| item_category | VARCHAR(30) | N | UNIQUE | — | 借出物罚款档位 |
| grace_days | INTEGER | N | | 0 | 宽限期（天），超出后才计费 |
| amount_per_day | NUMERIC(10,2) | N | | — | 每日金额 |

**初始数据**：`CHINESE_BOOK (0, 0.50)`、`FOREIGN_BOOK (3, 1.00)`、`CHINESE_MAGAZINE (0, 0.20)`、`FOREIGN_MAGAZINE (2, 0.50)`、`THESIS (0, 2.00)`

### 2.14 book_reviews（图书评论与评分）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| title_id | INTEGER | N | FK→book_titles.id, IDX | — | 评论对象 |
| reader_id | INTEGER | N | FK→readers.id | — | 评论人 |
| rating | INTEGER | N | | — | 1–5 |
| comment | VARCHAR(1000) | Y | | NULL | 评论内容 |
| status | VARCHAR(20) | N | IDX | 'PENDING' | PENDING / APPROVED / REJECTED |
| created_at | DATETIME | N | | now | |
| updated_at | DATETIME | N | | now | |

> **唯一约束**：`UNIQUE(title_id, reader_id)` —— 同一读者对同一标题仅一条（BR-014）。

### 2.15 lost_items（丢失与赔偿记录）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| loan_id | INTEGER | N | FK→loans.id, IDX | — | 关联的借阅记录 |
| item_id | INTEGER | N | FK→library_items.id | — | 丢失的馆藏副本 |
| lost_date | DATE | N | | — | 登记丢失日期 |
| amount | NUMERIC(10,2) | N | | — | 赔偿金额 = 定价 × 倍率 |
| paid | BOOLEAN | N | | 0 | 是否已缴 |
| paid_at | DATETIME | Y | | NULL | 缴清时间 |

### 2.16 compensation_policies（赔偿策略）

| 字段 | 类型 | 空 | 键 | 默认 | 说明 |
|---|---|---|---|---|---|
| id | INTEGER | N | PK | 自增 | |
| item_type | VARCHAR(20) | N | UNIQUE | — | BOOK / MAGAZINE / THESIS |
| rate | NUMERIC(4,2) | N | | — | 赔偿倍率 |

**初始数据**：`BOOK 2.00`、`MAGAZINE 1.50`、`THESIS 3.00`

---

## 3. ER 关系总览

```text
accounts 1 ── 0..1 readers
accounts 1 ── 0..1 librarians
accounts 1 ── 0..1 system_admins
accounts 1 ── *    auth_tokens
readers  1 ── 0..1 borrow_cards
readers  1 ── *    loans
readers  1 ── *    reservations
readers  1 ── *    book_reviews
book_titles 1 ── * library_items
book_titles 1 ── * reservations
book_titles 1 ── * book_reviews
library_items 1 ── * loans
loans 1 ── 0..1 fine_records
loans 1 ── 0..1 lost_items
library_items 1 ── 0..1 lost_items
```

---

## 4. 索引设计

| 索引 | 表 | 字段 | 目的 |
|---|---|---|---|
| `ix_readers_type` | readers | reader_type | 按类型统计 |
| `ix_book_titles_title` | book_titles | title | 检索 |
| `ix_book_titles_author` | book_titles | author | 检索 |
| `ix_book_titles_category` | book_titles | category | 检索 |
| `ix_items_status` | library_items | status | 可借副本筛选 |
| `ix_loans_reader_status` | loans | (reader_id, status) | 在借数量、超期检查 |
| `ix_loans_due_date` | loans | due_date | 超期扫描 |
| `ix_reservations_title_created` | reservations | (title_id, created_at) | 排队计算 |
| `ix_reviews_title_status` | book_reviews | (title_id, status) | 已通过评论列表 |

---

## 5. 继承映射策略

| 领域继承 | 映射方式 | 鉴别列 | 子类专有列 |
|---|---|---|---|
| `Reader` → `StudentReader` / `TeacherReader` | 单表继承 | `reader_type` | `grade` / `department` |
| `LibraryItem` → `Book` / `Magazine` / `Thesis` | 单表继承 | `item_type` | `edition,pages` / `issue_no,period` / `degree,school` |

选择单表继承的理由：SQLite 下无需 join、查询简单、教学可读性高；子类列允许为空，由应用层保证一致性。

---

## 6. 数据完整性约束汇总

| 约束 | 实现 |
|---|---|
| 同一读者最多一张有效借阅证 | `borrow_cards` 部分唯一索引（status='ACTIVE'） |
| 同一副本同时最多一条在借记录 | `loans` 部分唯一索引（status IN ('BORROWED','RETURN_REQUESTED')，BR-020） |
| 同一读者对同一标题最多一条有效预约 | `reservations` 部分唯一索引（status='ACTIVE'） |
| 同一读者对同一标题仅一条评论 | `book_reviews` 唯一约束 (title_id, reader_id) |
| 证号/条码/ISBN/用户名唯一 | 各表 UNIQUE |

> 注：SQLite 支持部分索引（Partial Index），可直接使用；若未来迁移到 MySQL，需改写为生成列 + 唯一索引方案。

---

## 7. 初始化与迁移策略

- 采用 SQLAlchemy `Base.metadata.create_all()` 建表，**每次启动执行**；
- 由于本项目领域模型与旧版（三表：users / books / borrow_records）差异过大，**初始化时删除旧 `library.db` 后重建**（Q-I2 已确认）；
- 种子数据：4 类读者规则的 `borrow_policies`、5 类 `fine_rules`、1 名系统管理员、2 名图书管理员、3 名读者、若干图书标题与副本；
- 后续若需演进，引入 Alembic 管理迁移（当前阶段不引入，避免过度工程）。
