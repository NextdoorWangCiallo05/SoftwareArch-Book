# 架构设计说明书

> 输入：`specs/02-requirements.md`、`specs/03-use-cases.md`、`specs/05-domain-model.md`、`specs/constitution.md`
> 状态：草稿（Agent 生成，待人工审查）
> 技术栈：Python 3.14 / FastAPI 0.141 / SQLAlchemy 2.0 / Pydantic v2 / SQLite / pytest + httpx

---

## 1. 架构总览

系统采用**分层架构 + MVC 分离**，并在最外层叠加**对话式 Agent 接入层**（本项目特色）。

```text
┌──────────────────────────────────────────────────────┐
│  对话式 Agent 层（.codebuddy/）                       │
│  orchestrator-agent → circulation-agent / skills      │
│  仅通过 REST API 访问系统，不直连数据库                │
└──────────────────────────────────────────────────────┘
                    ↓ HTTP :8001
┌──────────────────────────────────────────────────────┐
│  Presentation 表现层   FastAPI routers + 依赖注入      │
├──────────────────────────────────────────────────────┤
│  Application 应用层    用例编排服务 + 事务边界 + DTO    │
├──────────────────────────────────────────────────────┤
│  Domain 领域层         实体、值对象、策略、领域服务     │
├──────────────────────────────────────────────────────┤
│  Infrastructure 基础设施层  ORM、Repository 实现、安全 │
└──────────────────────────────────────────────────────┘
                    ↓
                 SQLite
```

### 1.1 MVC 映射

| MVC 角色 | 本项目实现 |
|---|---|
| Controller | `presentation/routers/*`：只做参数接收、调用应用服务、返回响应 |
| Model | `domain/*` + `application/*`：承载业务规则与用例流程 |
| View | `schemas/*`（Pydantic DTO）：对外数据结构的序列化视图 |

**硬约束**：Controller 不得直接依赖 Repository，不得编写业务规则（宪法第 5、6 条）。

---

## 2. 分层职责

### 2.1 Presentation 表现层

- 路由定义、请求参数校验（Pydantic）、OpenAPI 文档；
- **认证与授权依赖注入**：`get_current_account`、`require_role(...)`；
- 全局异常处理器：将领域/应用异常映射为统一信封 `code`；
- 不包含任何业务判断。

### 2.2 Application 应用层

- 每个用例一个服务方法（借书、还书、续借、预约、评论等）；
- 负责：加载领域对象 → 调用领域服务/策略 → 持久化 → 组装 DTO；
- **事务边界**在此层：一次用例对应一个数据库事务；
- 不做 HTTP 语义处理（不抛 HTTPException，而是抛领域异常）。

### 2.3 Domain 领域层

- 实体与聚合根、值对象/枚举、策略对象、领域服务；
- 声明仓储接口（抽象基类）；
- **不依赖** FastAPI、SQLAlchemy Session、HTTP 概念；
- 所有业务规则集中于此（BR-001～BR-018）。

### 2.4 Infrastructure 基础设施层

- SQLAlchemy ORM 模型与会话管理；
- Repository 接口实现；
- 密码哈希（`hashlib.pbkdf2_hmac` + 随机盐）与令牌存储；
- 数据库初始化与种子数据。

### 2.5 Test 测试层

- `tests/` 使用独立 SQLite 库（临时文件），pytest + httpx；
- 分层测试：领域层单元测试（策略、实体方法）+ API 集成测试（用例级）。

---

## 3. 目录结构

```text
backend/
├─ app/
│  ├─ main.py                      # FastAPI 应用装配
│  ├─ core/
│  │  ├─ config.py                 # 端口、数据库路径、令牌有效期
│  │  ├─ response.py               # 统一响应信封 APIResponse
│  │  ├─ exceptions.py             # 领域异常体系
│  │  └─ security.py               # 依赖注入：当前账户、角色校验
│  ├─ presentation/
│  │  ├─ deps.py
│  │  └─ routers/
│  │     ├─ auth_router.py         # 注册、登录、注销
│  │     ├─ catalog_router.py      # 检索、详情
│  │     ├─ circulation_router.py  # 借书、还书、续借、借阅记录
│  │     ├─ reservation_router.py  # 预约、取消
│  │     ├─ review_router.py       # 评论提交、列表、审核
│  │     └─ admin_router.py        # 借阅证、馆藏、规则维护
│  ├─ application/
│  │  ├─ auth_service.py
│  │  ├─ catalog_service.py
│  │  ├─ circulation_service.py
│  │  ├─ reservation_service.py
│  │  ├─ review_service.py
│  │  └─ admin_service.py
│  ├─ domain/
│  │  ├─ entities/                 # account, reader, borrow_card, book_title,
│  │  │                            # library_item, loan, reservation,
│  │  │                            # fine_record, book_review, librarian, admin
│  │  ├─ value_objects/enums.py
│  │  ├─ policies/                 # borrow_policy, fine_rule
│  │  ├─ services/                 # fine_calculator, circulation_policy_checker
│  │  └─ repositories/             # 仓储抽象基类
│  ├─ infrastructure/
│  │  ├─ db/                       # base, session, seed
│  │  ├─ models/                   # SQLAlchemy ORM（单表继承）
│  │  ├─ repositories/             # 仓储实现
│  │  └─ security/                 # password_hasher, token_store
│  └─ schemas/                     # Pydantic DTO
└─ tests/
   ├─ unit/                        # 策略与实体方法
   └─ integration/                 # 用例级 API 测试
```

---

## 4. 模块划分

| 模块 | 职责 | 主要类 |
|---|---|---|
| `auth` | 注册、登录、令牌、角色 | `AuthService`、`Account`、`PasswordHasher`、`TokenStore` |
| `reader` | 读者信息与类型 | `Reader`、`StudentReader`、`TeacherReader` |
| `card` | 借阅证办理与注销 | `BorrowCard`、`AdminService` |
| `catalog` | 图书标题与馆藏副本、检索 | `BookTitle`、`LibraryItem` 子类、`CatalogService` |
| `circulation` | 借书、还书、续借、查询 | `Loan`、`CirculationService`、`CirculationPolicyChecker` |
| `reservation` | 预约排队与有效期 | `Reservation`、`ReservationService` |
| `fine` | 罚款计算与缴清 | `FineRule`、`FineCalculator`、`FineRecord` |
| `review` | 评论评分与审核 | `BookReview`、`ReviewService` |
| `admin` | 管理员、规则维护 | `AdminService`、`Librarian`、`SystemAdmin` |

---

## 5. 权限控制策略

1. 登录成功后颁发令牌（随机串，服务端存储映射 `token → account_id`），响应 `data.token`；
2. 受保护路由通过依赖注入 `get_current_account` 解析令牌；未携带/无效 → `403`；
3. 角色校验通过 `require_role(Role.LIBRARIAN)` 等装饰器式依赖完成；角色不匹配 → `403`；
4. **角色只从令牌解析**，请求体中的角色字段一律忽略；
5. 数据级权限（读者只能查本人借阅信息）在**应用服务**中校验，返回 `403`。

---

## 6. 异常处理策略

领域异常体系（`core/exceptions.py`）：

| 异常类 | 语义 | 映射 `code` |
|---|---|---|
| `BusinessError` | 业务规则不满足 | `400` |
| `PermissionDeniedError` | 未认证或权限不足 | `403` |
| `NotFoundError` | 资源不存在 | `404` |
| `InfrastructureError` | 数据库等底层故障 | `500` |

- 领域层与应用层**只抛领域异常**，不抛 `HTTPException`；
- 表现层注册全局异常处理器，统一转换为 `{code, message, data}`；
- `message` 必须是可直接呈现给用户的中文文案。

---

## 7. 事务边界

- **事务边界 = 应用服务的一个用例方法**（一次请求一个事务）；
- 借书：创建 Loan + 更新副本状态，必须同一事务；
- 还书：更新 Loan + 更新副本状态 + 生成 FineRecord，必须同一事务；
- 续借：更新 `due_date` 与 `renew_count`，单表更新；
- 评论审核：单表更新；
- 只读用例（检索、查询、评论列表）不开启写事务。

---

## 8. 业务规则的落点

| 规则 | 落点类 | 层 |
|---|---|---|
| BR-001 借阅证有效 | `BorrowCard.is_valid()`、`CirculationPolicyChecker` | Domain |
| BR-002 数量上限 | `BorrowPolicy.get_max_borrow_count()` | Domain |
| BR-003 超期检查 | `Reader.has_overdue()` | Domain |
| BR-004 借阅期限 | `BorrowPolicy.get_borrow_days()`、`Loan.renew()` | Domain |
| BR-005 罚款单价 | `FineRule.calculate_fine()` | Domain |
| BR-006 未缴罚款 | `Reader.has_unpaid_fine()` | Domain |
| BR-007/008/009 预约 | `Reservation` + `ReservationService` | Domain / Application |
| BR-010 副本状态机 | `LibraryItem` 状态方法 | Domain |
| BR-011 权限矩阵 | `core.security.require_role` + 应用服务 | Presentation / Application |
| BR-012 续借条件 | `Loan.renew()` | Domain |
| BR-013/014/018 评论 | `BookReview` | Domain |
| BR-015 认证 | `Account`、`PasswordHasher`、`TokenStore` | Domain / Infrastructure |
| BR-016 状态码 | `core.response` + 全局异常处理器 | Presentation |
| BR-017 注销条件 | `BorrowCard` + `AdminService` | Domain / Application |

---

## 9. 设计模式

| 模式 | 应用位置 |
|---|---|
| **Strategy** | `BorrowPolicy`（读者类型规则）、`FineRule`（借出物类型罚款），规则可配置、可替换 |
| **Repository** | `domain/repositories` 声明接口，`infrastructure/repositories` 实现 |
| **Service Layer** | `application/*_service.py` 组织用例流程与事务 |
| **DTO** | `schemas/*` 隔离接口层与领域层，领域实体不直接序列化到响应 |
| **Factory** | 按 `reader_type` 创建 `StudentReader`/`TeacherReader`；按 `item_type` 创建 `Book`/`Magazine`/`Thesis` |
| **Template Method / 单表继承** | `Reader` 与 `LibraryItem` 的继承体系（SQLAlchemy 单表继承 + 鉴别列） |
| **Dependency Injection** | FastAPI `Depends` 注入会话、当前账户、仓储实现 |
| **MVC** | routers（C）+ schemas（V）+ domain/application（M） |

---

## 10. 对话式 Agent 接入层

```text
用户自然语言
  → orchestrator-agent（意图识别 + 路由 + 聚合，不直接调 API）
      ├─ 借 / 还 / 预约 / 续借 / 查记录 → circulation-agent
      ├─ 检索 / 评论评分                → 对应 skill
      └─ 登录                           → user-manage skill
  → REST API :8001
```

- Agent 层与后端**只通过 HTTP 契约**耦合；
- `.codebuddy/skills/*/SKILL.md` 中出现的路径与字段名必须与后端实现逐字一致（宪法第 10 条）；
- 后端变更接口时，必须同步更新对应 `SKILL.md`，否则视为破坏性变更。

---

## 11. 关键架构决策记录（ADR 摘要）

| 编号 | 决策 | 理由 |
|---|---|---|
| ADR-01 | 认证与业务身份分离（`Account` 独立于 `Reader`） | 避免密码字段混入领域实体，便于多身份扩展 |
| ADR-02 | 继承体系用单表继承 + 鉴别列 | SQLite 下查询简单、无需 join，满足教学可读性 |
| ADR-03 | 业务规则放在策略对象而非 Service 硬编码 | 满足宪法第 8 条，便于规则配置化（FR-025/026） |
| ADR-04 | 令牌存服务端映射而非 JWT | 免第三方依赖，符合"不强制完整 OAuth/JWT"的教学定位 |
| ADR-05 | 跨聚合只引用 ID | 避免大聚合，控制事务范围 |
| ADR-06 | 预约失效采用读取时惰性判定 | 无需定时任务，教学项目复杂度可控 |
