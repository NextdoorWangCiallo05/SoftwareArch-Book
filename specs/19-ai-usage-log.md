# AI 使用记录

> 用途：记录每次使用 Agent 生成 specs、UML、代码或测试的过程与人工审查结果（宪法第 14 条）。
> 工具：CodeBuddy（IDE 内置 Agent）

---

## 第 1 次使用

### 使用工具
CodeBuddy

### 使用阶段
项目启动 / 现状梳理

### 输入 Prompt 摘要
"看一下这个项目目录，帮我整理一下头绪" —— 要求梳理工作区结构、现有后端接口、任务卡两个扩展任务的实现位置。

### Agent 修改文件
无（只读分析）

### 输出摘要
- 梳理出三层 Agent 架构（orchestrator-agent / circulation-agent / skills）与后端 FastAPI 的接口清单；
- 指出两个扩展任务的挂接位置：续借 → circulation-agent，评论 → 编排层 use_skill；
- 指出环境缺失（未安装 fastapi / uvicorn / sqlalchemy / pydantic，无 requirements.txt）。

### 人工审查结果
确认分析正确；决定先按课程实验文档推进 Specs，再实现功能。

### 测试结果
不适用（无代码改动）

### Git 提交
无

---

## 第 2 次使用

### 使用工具
CodeBuddy

### 使用阶段
项目启动 / 需求输入收集

### 输入 Prompt 摘要
"读一下 Document 文件夹里面的文档，项目即将启动" —— 要求阅读 5 份课程文档并梳理实验流程。

### Agent 修改文件
无（只读分析）

### 输出摘要
- 明确 5 份文档的角色：实验概述（总纲）、工具链说明书（环境）、Agent 提示词手册（Prompt 库）、实验一（架构与 Spec 建模）、实验二（详细设计与实现）；
- 指出文档要求（全量领域模型、分层架构、Git baseline）与现有简化骨架的差距；
- 指出端口不一致（8000 vs 8001）并建议统一为 8001；
- 提出三个关键决策（技术栈、领域范围、任务卡功能归属）。

### 人工审查结果
学生决策：**Python FastAPI**（复用现有骨架）、**全量领域模型**、**先主线后补续借与评论**。

### 测试结果
不适用

### Git 提交
无

---

## 第 3 次使用

### 使用工具
CodeBuddy

### 使用阶段
项目初始化 / 环境搭建

### 输入 Prompt 摘要
按实验一第 1 步与工具链说明书，创建 `specs/` 目录骨架、初始化 Git、安装依赖并跑通后端。

### Agent 修改文件
- `specs/`（新建 21 个规格文件骨架）
- `backend/requirements.txt`（新建）
- `.gitignore`（新建）
- `.git/`（初始化仓库）

### 输出摘要
- 建立 `specs/` 21 个文件（15 个 `.md` + 6 个 `.puml`，编号与实验文档一致）；
- 安装依赖：`fastapi 0.141.1`、`sqlalchemy 2.0.50`、`pydantic 2.13.4`、`pytest`、`httpx`（Python 3.14）；
- 用 `TestClient` 冒烟验证：`/api/health` 正常，登录返回 `user_id=1`，借阅记录查询返回 2 条在借。

### 人工审查结果
确认可用；中文路径导致 PowerShell `cd` 偶发失败，改用文件系统枚举定位目录绕过。

### 测试结果
后端可导入（15 条路由），冒烟通过。

### Git 提交
`init project with specs skeleton`

---

## 第 4 次使用

### 使用工具
CodeBuddy

### 使用阶段
需求分析：澄清问题、开发宪法

### 输入 Prompt 摘要
根据 `00-project-brief.md` 提出 20–30 个澄清问题并生成 `01-clarifying-questions.md` 与 `constitution.md`。

### Agent 修改文件
- `specs/00-project-brief.md`（新建）
- `specs/01-clarifying-questions.md`（新建，31 个问题）
- `specs/constitution.md`（新建，15 条）

### 输出摘要
- 澄清问题分 A–J 十类（权限、借阅证、借阅规则、馆藏、借还、预约、罚款、续借评论、架构数据、测试工具）；
- 宪法在原示例基础上补充：持久化抽象、API 契约（含 SKILL.md 一致性）、任务粒度。

### 人工审查结果
学生回答关键项：**真实登录认证**、**允许重构为四层目录并删库重建**、**LibraryItem 用继承体系**、**code 扩展 403/404**。宪法同步修订（新增 10.1 认证原则）。

### 测试结果
不适用

### Git 提交
`add project brief, clarifying questions and constitution`

---

## 第 5 次使用

### 使用工具
CodeBuddy

### 使用阶段
需求分析：需求规格与用例建模

### 输入 Prompt 摘要
根据 brief、澄清回答与宪法生成 `02-requirements.md`、`03-use-cases.md`、`04-use-case-model.puml`。

### Agent 修改文件
- `specs/02-requirements.md`（新建：25 条 FR、17 条 BR、6 条 NFR）
- `specs/03-use-cases.md`（新建：20 个用例 + UC-009A 子用例）
- `specs/04-use-case-model.puml`（新建）

### 输出摘要
- FR 覆盖注册、认证、借阅证、管理员、馆藏、检索、借、还、续借、查询、预约、罚款、规则；
- 重点用例（借书、还书、续借、预约、办证、罚款）写了完整异常流；
- 用例图含参与者泛化、include（验证借阅证、计算罚款）、extend（不可借转预约）。

### 人工审查结果
学生追加决策：**评论需审核后可见**、**预约设 7 天有效期**。已同步修订 FR-022/023/024、BR-008/014/018、UC-011/013/017/018/021 与用例图。

### 测试结果
不适用

### Git 提交
`add requirements, use cases and use case diagram`

---

## 第 6 次使用

### 使用工具
CodeBuddy

### 使用阶段
架构设计：领域模型、类图、架构、包图

### 输入 Prompt 摘要
根据需求与用例生成 `05-domain-model.md`、`06-domain-class-diagram.puml`、`07-architecture.md`、`08-package-diagram.puml`。

### Agent 修改文件
- `specs/05-domain-model.md`（新建）
- `specs/06-domain-class-diagram.puml`（新建）
- `specs/07-architecture.md`（新建）
- `specs/08-package-diagram.puml`（新建）

### 输出摘要
- 领域模型：13 个实体、8 个枚举、2 个策略对象、2 个领域服务、5 个聚合边界；
- `Account` 与业务身份分离（密码不进领域实体）；
- 架构：四层目录、9 个模块、权限/异常/事务策略、BR 落点表、8 个设计模式、6 条 ADR；
- 包图：依赖自上而下，Controller 不直连 Repository。

### 人工审查结果
确认继承体系（Reader / LibraryItem 单表继承）与罚款档位落在副本（`fine_category`）的设计。

### 测试结果
不适用

### Git 提交
`add domain model, class diagram, architecture and package diagram`

---

## 第 7 次使用

### 使用工具
CodeBuddy

### 使用阶段
架构设计：数据库设计、风险分析、审查清单、AI 使用记录

### 输入 Prompt 摘要
"语言与框架改为 Python 3.14，继续完成实验一要求" —— 生成 `13-database-design.md`、`17-risk-analysis.md`、`18-review-checklist.md`、`19-ai-usage-log.md`，并冻结实验一 baseline。

### Agent 修改文件
- `specs/13-database-design.md`（新建：14 张表）
- `specs/17-risk-analysis.md`（新建：24 条风险）
- `specs/18-review-checklist.md`（新建：9 组 60 项）
- `specs/19-ai-usage-log.md`（本文件）
- `specs/00-project-brief.md`、`specs/07-architecture.md`（技术栈更新为 Python 3.14）

### 输出摘要
- 数据库设计含 3 个部分唯一索引（有效借阅证、在借记录、有效预约）与单表继承映射策略；
- 风险分析识别 8 项高风险（领域层污染、重构破坏可运行性、规则散落、旧库残留、越权查数据、伪造 role、Agent 改 specs、Agent 编造字段）；
- 技术栈统一为 Python 3.14 / FastAPI 0.141 / SQLAlchemy 2.0 / Pydantic v2。

### 人工审查结果
待审查（依据 `18-review-checklist.md` 逐项核对）

### 测试结果
不适用

### Git 提交
`baseline experiment 1 architecture specs`

---

## 第 8 次使用

### 使用工具
CodeBuddy

### 使用阶段
需求修订 / 基线重建

### 输入 Prompt 摘要
"语言与框架：Python 3.14 + FastAPI + SQLAlchemy + Pydantic，然后继续完成实验1要求" —— 更新技术栈、完成实验一剩余步骤（AI 使用记录、人工审查、冻结 baseline）。

### Agent 修改文件
- `specs/00-project-brief.md`、`specs/07-architecture.md`（技术栈更新为 Python 3.14 / FastAPI 0.141 / SQLAlchemy 2.0 / Pydantic v2）
- `specs/19-ai-usage-log.md`（新建）
- 仓库重建：删除因中文路径编码错误生成的目录，在真实项目目录重新 `git init`

### 输出摘要
- 完成 15 次分阶段提交并打标签 `experiment1-specs-baseline-v1`；
- 读取 `软件设计与体系结构实验指导书2026.docx` 后**发现两处需求偏差**并修订：
  1. **读者类型缺专科生** → 新增 `ASSOCIATE`（3 本 / 30 天），同步修订 BR-002、BR-004、领域模型、类图与数据库初始数据；
  2. **罚款规则缺宽限期** → `FineRule` 增加 `grace_days`，计费公式改为 `max(0, 逾期天数 - 宽限期) × 每日金额`，同步修订 BR-005、FR-020、FR-026、UC-015、数据库 `fine_rules` 表；
  3. 还书"删除借阅信息"差异：保留历史记录（状态置 `RETURNED`），已在 FR-015 记录设计说明。

### 人工审查结果
待审查（指导书带来的两处修订建议值：专科生 3 本/30 天；宽限期 0/3/0/2/0 天，可调整）

### 测试结果
不适用

### Git 提交
`revise specs according to lab manual: associate reader type and fine grace period`

---

## 第 9 次使用

### 使用工具
CodeBuddy + Git

### 使用阶段
详细设计 / 版本管理

### 输入 Prompt 摘要
"git 换成我自己的用户；建立仓库 SoftwareArch-Book"；随后继续完成实验二详细设计 Specs。

### Agent 修改文件
- `specs/09-design-model.md`（新建：分析类 → 设计类两步走、关键算法、用例 × 设计元素映射、设计模式落点）
- `specs/10-sequence-borrow-book.puml`、`11-sequence-return-book.puml`、`12-sequence-reserve-book.puml`（新建）
- `specs/14-api-spec.md`（新建：26 个接口）
- `specs/15-test-plan.md`（新建：16 个单元测试 + 68 个集成测试）
- `specs/16-tasks.md`（新建：TASK-001～016）
- `specs/19-ai-usage-log.md`（本记录）

### 输出摘要
- 详细设计采用指导书推荐的**两步走**：先分析类（不含界面与持久化），再增强为设计类（Controller / Service / Repository / DTO）；
- 关键算法以伪代码固定：密码 PBKDF2-HMAC-SHA256（12 万次迭代 + 随机盐）、令牌 `secrets.token_urlsafe(32)`（8 小时）、借书四项前置校验、还书罚款含宽限期 `max(0, overdue - grace) × amount`、续借以原 `due_date` 为基数、预约排队与 7 天有效期惰性失效、评论平均分仅统计 APPROVED；
- 仓库关联 GitHub：`origin = https://github.com/NextdoorWangCiallo05/SoftwareArch-Book.git`，主分支 `main`，已推送 17 个提交与 `experiment1-specs-baseline-v1` 标签。

### 人工审查结果
待审查（`18-review-checklist.md` 的实验二部分待补充）

### 测试结果
不适用（尚无代码）

### Git 提交
`baseline experiment 2 detailed design specs`

---

## 第 10 次使用

### 使用工具
CodeBuddy

### 使用阶段
需求与设计修订（对照指导书参考图）

### 输入 Prompt 摘要
提供指导书中的 9 张参考图（用例图、借出书目结构化规格、领域类图、MVC 架构图、数据库 ER），要求对照检查并完善。

### Agent 修改文件
- `specs/00-project-brief.md`、`specs/02-requirements.md`：借阅规则扩展为 `(reader_type, item_type)` 二维；新增 FR-027 处理赔偿、FR-028 管理借阅者、FR-029 管理图书管理员、FR-030 修改图书信息；新增 BR-018a 赔偿规则；BR-006 扩展为含未缴赔偿
- `specs/03-use-cases.md`：新增 UC-022～UC-025；UC-009 补「结构化规格」（基本路径 7 步 + 4a/6a/6b/6c/6d/1a 异常路径，对齐参考格式）
- `specs/04-use-case-model.puml`、`specs/06-domain-class-diagram.puml`：新增用例与 `LostItem`、`CompensationPolicy` 类
- `specs/05-domain-model.md`：新增 `LostItem`、`CompensationPolicy`；`BorrowPolicy` 改为二维
- `specs/07-architecture.md`：新增第 12 节「与指导书参考架构的映射」（Dispatcher/Controller/Service/DAO 对照表 + 参考类图策略体系对照表）、ADR-07
- `specs/09-design-model.md`：算法加二维策略与赔偿伪代码；用例映射加 4 行
- `specs/13-database-design.md`：`borrow_policies` 加 `item_type` 二维键；新增 `lost_items`、`compensation_policies` 表
- `specs/14-api-spec.md`：新增 3.6 登记丢失、3.7 缴清赔偿
- `specs/15-test-plan.md`：新增 TC-026A～026D（二维策略）、TC-069～TC-082（赔偿与管理）
- `specs/16-tasks.md`：TASK-004 加二维策略；TASK-008 加管理功能；TASK-010 纳入赔偿
- `specs/19-ai-usage-log.md`（本记录）

### 输出摘要
对照 9 张参考图识别出 3 个缺口并全部补齐：① 处理赔偿 / 丢失书项（参考图 1/6/9 有，指导书正文未提）；② 管理借阅者、管理图书管理员、修改图书（参考图 1）；③ 借阅期限的出借物维度（参考类图的「书到期策略 / 杂志到期策略」）。另补齐 2 项文档形式：用例结构化规格、与参考架构的映射对照表。

### 人工审查结果
待审查

### 测试结果
不适用（尚无代码）

### Git 提交
`revise specs after comparing with lab manual reference diagrams`

---

## 第 11 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-001 四层目录与核心配置、TASK-002 ORM 与种子数据

### 输入 Prompt 摘要
"开始编码" —— 按 `16-tasks.md` 顺序实现，先建 `backend/app` 四层目录骨架与核心配置，再按 `13-database-design.md` 建 ORM 与种子数据；不得修改 `specs/`。

### Agent 修改文件
- `backend/app/{core,presentation/routers,application,domain,infrastructure,schemas}/`（新建四层目录与 `__init__.py`）
- `backend/app/core/config.py`、`core/response.py`、`core/exceptions.py`
- `backend/app/infrastructure/db/{base,seed}.py`、`infrastructure/models/orm.py`
- `backend/main.py`（装配 FastAPI + 全局异常处理器）

### 输出摘要
- `APIResponse` 信封 `code/message/data`；异常体系 `BusinessError(400)`、`PermissionDeniedError(403)`、`NotFoundError(404)`、`InfrastructureError(500)`；
- 16 张表建成，含 4 个部分唯一索引（`uq_borrow_card_active`、`uq_item_active_loan`、`uq_reservation_active`、`uq_review_reader_title`），已用 `sqlite_master` 验证实际生效；
- 种子数据：7 账户 / 4 读者 / 2 管理员 / 4 借阅证 / 9 标题 / 29 副本 / 15 条借阅策略 / 5 条罚款规则 / 3 条赔偿策略；
- 密码 PBKDF2-HMAC-SHA256（12 万次迭代 + 32 位随机盐），库中无明文。

### 人工审查结果
确认目录分层与 `specs/07-architecture.md` 一致；确认旧 `library.db` 已删库重建。

### 测试结果
`GET /api/health` 返回 `{"status":"ok"}`；OpenAPI 可生成。

### Git 提交
`complete TASK-001 and TASK-002: layered structure, core config, ORM models and seed data`（`189183c`）

---

## 第 12 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-003 领域实体与枚举、TASK-004 策略对象与领域服务

### 输入 Prompt 摘要
按 `05-domain-model.md` 与 `06-domain-class-diagram.puml` 实现领域实体；按 `09-design-model.md` 第 4 节实现 `BorrowPolicy`、`FineRule`、`FineCalculator`、`CirculationPolicyChecker`。

### Agent 修改文件
- `backend/app/domain/entities/**`、`domain/value_objects/**`
- `backend/app/domain/policies/**`、`domain/services/**`、`domain/repositories/protocols.py`

### 输出摘要
- 实体：`Account`、`Reader`（+Student/Teacher 子类分支）、`Librarian`、`SystemAdmin`、`BorrowCard`、`BookTitle`、`LibraryItem`（+3 子类）、`Loan`、`Reservation`、`FineRecord`、`LostItem`、`BookReview`；领域层不 import sqlalchemy；
- 罚款公式 `max(0, 逾期天数 - grace_days) × amount_per_day`；
- `BorrowPolicy` 采用 `(reader_type, item_type)` 二维键，未命中回退 `(reader_type, ALL)`。

### 人工审查结果
发现枚举用 `(str, Enum)` 导致 `str()` 返回 `ReaderType.UNDERGRADUATE`（而非 `UNDERGRADUATE`），会使 API 返回串与 SKILL.md 契约不一致，要求改用 `StrEnum` 修复。

### 测试结果
UT-001～UT-016 通过（38 个单元测试全绿）。

### Git 提交
`complete TASK-003 and TASK-004: domain entities, enums, policies and domain services`（`577d1a4`）

---

## 第 13 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-005 仓储接口与实现

### 输入 Prompt 摘要
按 `07-architecture.md` 与 `13-database-design.md` 实现 7 个仓储的 SQLAlchemy 实现与依赖注入；仓储只做持久化，不含业务判断。

### Agent 修改文件
- `backend/app/infrastructure/repositories/**`（7 个实现文件）
- `backend/app/domain/repositories/protocols.py`（12 个仓储 Protocol）

### 输出摘要
- 领域层只依赖 Protocol 抽象，应用服务不接触 ORM；
- 集成测试实测三个部分唯一索引真的会拦截：同一副本重复在借、同一读者两张有效证。

### 人工审查结果
确认异常在 `flush` 而非 `commit` 时抛出，据此修正了测试写法（原先断言位置错误导致误判索引未生效）。

### 测试结果
58 个测试通过。

### Git 提交
`complete TASK-005: repository interfaces and SQLAlchemy implementations`（`6d50ef2`）

---

## 第 14 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-006 认证（注册、登录、注销）

### 输入 Prompt 摘要
按 `14-api-spec.md` 第 1 节实现 FR-001～FR-003；密码哈希 + 随机盐；令牌持久化；`get_current_account` / `require_role` 依赖。

### Agent 修改文件
- `backend/app/application/auth_service.py`
- `backend/app/presentation/routers/auth_router.py`
- `backend/app/infrastructure/security/{password_hasher,security}.py`
- `backend/app/schemas/auth.py`

### 输出摘要
- 注册在同一事务创建 Account + Reader；
- 登录令牌 `secrets.token_urlsafe(32)`，有效期 8 小时，写入 `auth_tokens`；
- `require_role` 的角色**只从令牌解析**，不信任请求体中的 role 字段（对应风险分析中"伪造 role"一项）。

### 人工审查结果
确认密码错误与用户不存在返回统一文案，不泄露用户是否存在。

### 测试结果
TC-001～TC-006 通过（68 个测试全绿），含"库中无明文密码"断言。

### Git 提交
`complete TASK-006: authentication, token and role dependencies`（`38b72cf`）

---

## 第 15 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-007 馆藏与检索、TASK-008 借阅证与人员管理

### 输入 Prompt 摘要
实现 FR-004～FR-013 及管理端维护：`/api/books/search`、`/api/admin/*`；条码/ISBN 唯一校验；借阅证号 `CARD+年份+6位序号`；补充 FR-028～FR-030 管理功能。

### Agent 修改文件
- `backend/app/application/{catalog_service,admin_service}.py`
- `backend/app/presentation/routers/{catalog_router,admin_router}.py`
- `backend/app/schemas/{catalog,admin}.py`

### 输出摘要
- 检索支持书名/作者/分类与分页；副本 Factory 按 `item_type` 创建；标题与副本逻辑删除；
- 借阅证注销校验无未归还；仅 SystemAdmin 可办证/注销/维护；
- 补齐读者增删改查（删除=停用）、管理员查询与修改、图书信息修改（ISBN 不可改）。

### 人工审查结果
测试 fixture 与种子账号重名冲突，要求让种子账号使用真实密码哈希、测试复用种子账号，避免重复造账号。

### 测试结果
TC-007～TC-016、TC-077～TC-082 通过。

### Git 提交
`complete TASK-007 and TASK-008: catalog search and admin management`（`93d74a7`）

---

## 第 16 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-009 借书、TASK-010 还书与罚款赔偿、TASK-011 续借

### 输入 Prompt 摘要
按 `10/11-sequence-*.puml` 与 `09-design-model.md` 实现借书四项前置校验、还书逾期罚款与赔偿（FR-027）、续借四条前置条件。

### Agent 修改文件
- `backend/app/application/circulation_service.py`
- `backend/app/presentation/routers/circulation_router.py`
- `backend/app/domain/services/fine_calculator.py`
- `backend/app/schemas/circulation.py`

### 输出摘要
- 借书：`due_date = 今天 + 二维策略借期`，Loan 与副本状态在同一事务更新；
- 还书：仅超期且超出宽限期才生成 `FineRecord`；支持缴清；
- 赔偿：`POST /api/circulation/lost` 按 `CompensationPolicy` 计费；
- 续借：`renew_count` 上限 1，逾期与他人有效预约阻塞。

### 人工审查结果
确认"未缴罚款"纳入借书前置校验（该约束是端到端验收时才暴露出来的联动关系）。

### 测试结果
TC-017～TC-042 通过。

### Git 提交
`complete TASK-009 to TASK-011: borrow, return with fine, renew and compensation`（`8645018`）

---

## 第 17 次使用

### 使用工具
CodeBuddy

### 使用阶段
代码实现：TASK-012 预约、TASK-013 评论审核、TASK-014 规则维护、TASK-015 权限收口与旧代码清理、TASK-016 测试与提示词同步

### 输入 Prompt 摘要
"继续往下推，把实验1做完" —— 补齐剩余任务：预约 7 天有效期、评论提交即 PENDING 且仅管理员审核、规则维护、删除旧 `models.py`/`routes.py`、同步 `.codebuddy` 提示词与 README。

### Agent 修改文件
- `backend/app/application/{reservation_service,review_service,admin_service,circulation_service}.py`
- `backend/app/presentation/routers/{reservation_router,review_router,admin_router,circulation_router}.py`
- 删除 `backend/app/models.py`、`backend/app/routes.py`（旧单层代码下线）
- `.codebuddy/agents/**`、`backend/README.md`

### 输出摘要
- 预约惰性失效 + 排队位次；评论平均分只统计 APPROVED；
- 权限收口：读者仅本人、管理员任意；旧接口全部下线，服务仍可启动；
- `.codebuddy` 的 6 个 skill 与 2 个 agent 的字段名逐字对齐 `14-api-spec.md`。

### 人工审查结果
确认旧文件删除后无残留 import；确认 SKILL.md 中路径与字段名与 api-spec 一致。

### 测试结果
全量 `pytest`：131 通过。

### Git 提交
`complete TASK-012 to TASK-016: reservation, review, policies, cleanup and agent skills sync`（`679ee69`）

---

## 第 18 次使用

### 使用工具
CodeBuddy

### 使用阶段
端到端验收 / 测试生成

### 输入 Prompt 摘要
"继续完成实验2" —— 对照实验二最终验收清单第 9/10/11 条与学生任务卡两个扩展任务，对运行中的服务跑真实接口验证，并生成可提交的验收记录。

### Agent 修改文件
- `backend/scripts/e2e_acceptance.py`（新建：28 个端到端验收场景）
- `backend/scripts/e2e_report.md`（新建：自动生成的验收记录）
- `specs/19-ai-usage-log.md`（本记录）
- `.gitignore`（新增 `~$*`、日志忽略）

### 输出摘要
- 28 个场景全部通过，覆盖：借书（本科生 30 天 / 研究生 60 天 / 专科生上限 3）、二维策略（期刊 7 天、论文 3 天）、还书、续借与续借上限、预约 7 天有效期与重复预约、评论评分 1–5 校验与审核后可见、权限收口；
- 罚款对比：同样逾期 10 天，中文图书 5.00 元 vs 学位论文 20.00 元，证明"不同借出物类型罚款规则可用"。

### 人工审查结果
两次失败均由脚本自身假设错误引起，已修正后通过：
1. 取可借副本时用 `OFFSET` 递增，但借走后可用行会减少 → 改为每次取第一个可用副本；
2. 制造逾期罚款后未缴清，导致后续借书被"存在未缴罚款"阻塞 → 补 `G-02 缴清罚款` 用例。
另发现需在重启服务后再运行（脚本会改库状态，依赖干净的种子库）。

### 测试结果
端到端 28/28 通过；回归 `pytest` 131 通过。

### Git 提交
`add end-to-end acceptance script and report for experiment 2`
