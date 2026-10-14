# AI 时代《软件设计与体系结构》实验报告（实验一）

## 对话式图书管理系统的架构设计与 Spec 建模

| 项目 | 内容 |
|---|---|
| 课题 | 对话式图书管理系统（Spec-Driven + Agent 辅助实现） |
| 姓名 / 学号 | 王文硕/1024005279 |
| 班级 | 软件卓越2401 |
| 实验 | 实验一：应用系统的架构设计（Spec 建模） |
| 建模工具 | PlantUML（UML-as-Spec） |
| 开发方式 | CodeBuddy Agent / Skill 契约驱动，人工审查并冻结 baseline |
| 提交日期 | 2026-10-11 |
| 仓库 | 本目录（`README.md` 为仓库首页，`提交产物清单.md` 为交付物对照表） |

> 配套文档：实验二的详细设计与 Agent 实现见 `实验报告二-详细设计与Agent实现.md`。

---

## 一、实验目的

本实验在"UML 建模 + 简化统一过程 + 分层架构 + MVC + 数据库设计"的传统流程基础上，
引入 AI 编码 Agent 的协作范式。通过本实验掌握：

1. 使用 Agent 辅助进行需求分析与需求澄清；
2. 使用 OpenSpec 式的目录规范组织需求、用例、领域模型、架构、数据库、风险与审查文档；
3. 使用 PlantUML 表达用例图、类图、包图，使 UML 成为可版本管理的规格；
4. 使用"开发宪法"约束 Agent 行为；
5. 使用简化统一过程（Inception / Elaboration）组织实验阶段；
6. 使用分层架构与 MVC 模式完成系统设计；
7. 使用 Git 管理需求与设计文档的演进；
8. 理解 AI 时代架构师的新职责：**用规范指挥 Agent，用 UML 表达设计，用 Git 审查变更**。

---

## 二、实验环境与工具链

| 类别 | 选型 | 说明 |
|---|---|---|
| 建模 | PlantUML | 本实验 3 张图（用例图 / 类图 / 包图），文本入库 |
| Specs 组织 | OpenSpec 式目录 + 开发宪法 | `specs/` 编号化文档 |
| Agent | CodeBuddy（Agent + Skill 契约） | 生成 Specs 草案，人类审查修订 |
| 版本控制 | Git | 分阶段提交，`experiment1-specs-baseline-v1` 冻结 |
| 目标技术栈 | Python 3.14 · FastAPI · SQLAlchemy 2.0 · SQLite | 架构设计面向的技术选型（实现见实验二） |

**实验一 Specs 规模**：`specs/00`–`specs/08`、`specs/13`、`specs/17`、`specs/18` 共 12 份（含 3 张 `.puml`），
包含 FR-001–FR-030（30 条功能需求）、BR-001–BR-020（20 条业务规则）、NFR-001–NFR-006（6 条非功能需求）、
UC-001–UC-025（25 个用例）、R-01–R-24（24 条风险）。
详细设计（09–12）、API / 测试 / 任务（14–16）与 AI 记录（19）在实验二生成，见实验二报告。

---

## 三、实验流程与方法

实验采用"AI 增强的简化统一过程"，本实验对应 Inception 与 Elaboration 两个阶段的生成与冻结：

```text
Inception    项目愿景与范围 → 澄清问题 → 开发宪法
Elaboration  需求规格 → 用例模型 → 领域模型 → 架构与包图
             → 数据库设计 → 风险与审查清单
             → 人工审查 → 冻结 baseline
```

关键纪律（写入 `specs/constitution.md`，共 11 条）：

| # | 原则 | 在本项目中的落实 |
|---|---|---|
| 1 | Specs 优先 | 任何代码实现前先完成全部设计文档 |
| 2 | Agent 起草、人类确认 | 每份 Specs 都经过人工审查与修订提交（见第五章） |
| 3 | UML-as-Spec | PlantUML 文本图纳入 Git |
| 4 | Baseline 原则 | `experiment1-specs-baseline-v1` 冻结 Specs，实现阶段不改 specs |
| 5 | 分层架构 | `presentation / application / domain / infrastructure` 四层 |
| 6 | MVC | Controller 不写业务规则，View 由 DTO 承担 |
| 7 | 权限区分 | 读者 / 图书管理员 / 系统管理员三级权限矩阵 |
| 8 | 业务规则集中 | `BorrowPolicy` / `FineRule` / `CompensationPolicy` 策略对象 |
| 9 | 测试闭环 | 借书、还书、预约、超期罚款、权限失败均有自动化测试（实验二执行） |
| 10 | Git 审查 | Agent 每次改动均 `git diff` 审查后提交 |
| 11 | AI 使用记录 | 使用记录登记在 `specs/19-ai-usage-log.md` |

---

## 四、Spec 建模与架构设计过程

> 产物：`specs/00`–`specs/08` + `specs/13`、`specs/17`、`specs/18` + `constitution.md`，
> 冻结于 tag `experiment1-specs-baseline-v1`

### 4.1 项目愿景与范围（`00-project-brief.md`）

明确系统定位为"对话式图书管理系统"：自然语言入口 + REST 后端；参与者包括学生、教师、图书管理员、系统管理员；
业务主线为"注册 → 办证 → 借书 → 还书 → 罚款 / 赔偿 → 预约 → 查询"；非目标包括复杂 OAuth/JWT、分布式部署、
真实支付、条码硬件与邮件通知等。

### 4.2 需求澄清（`01-clarifying-questions.md`）

Agent 就指导书中未明确之处提出澄清问题，人类逐条回答或采用默认值，典型项：

| 问题 | 结论 |
|---|---|
| 是否需要"专科生"读者类型？ | 按指导书修订为**五类**：专科 / 本科 / 研究生 / 博士 / 教师 |
| 各类型借阅数量与期限？ | 专科 3 本 30 天、本科 5/30、研究生 10/60、博士 15/90、教师 20/90 |
| 借阅规则是否需要按馆藏类型细分？ | 需要，扩展为 `(reader_type, item_type)` 二维策略 |
| 罚款是否含宽限期？ | 含，`max(0, 逾期天数 − grace_days) × 单价` |
| 读者类型变更时已借图书如何处理？ | 已借记录保持原 `due_date`，新借阅按新规则 |

### 4.3 需求规格（`02-requirements.md`）

30 条功能需求（FR-001–FR-030）、20 条业务规则（BR-001–BR-020）、6 条非功能需求（NFR-001–NFR-006），
每条功能需求均附**可验证的验收标准**。业务规则编号成为后续测试断言的引用锚点，例如：

- BR-002 借阅数量上限、BR-003 存在超期不可借、BR-004 借阅期限、BR-005 罚款单价；
- BR-011 权限矩阵、BR-012 续借条件、BR-017 借阅证注销条件；
- BR-020 两段式还书状态机（读者申请 + 馆员审核）。

### 4.4 用例模型（`03-use-cases.md`、`04-use-case-model.puml`）

25 个用例（UC-001–UC-025），覆盖指导书要求的 4 类参与者，用例文本包含编号、名称、主要 / 次要参与者、
前置 / 后置条件、基本事件流、备选事件流与异常事件流、关联需求编号。
用例图以 PlantUML 表达参与者泛化（Student / Teacher 继承 Reader）与 `include` 关系（借书、还书均包含身份校验）。

### 4.5 领域模型（`05-domain-model.md`、`06-domain-class-diagram.puml`）

- 继承体系：`Reader` ← `StudentReader` / `TeacherReader`；`LibraryItem` ← `Book` / `Magazine` / `Thesis`
- 核心实体：`Account`、`BorrowCard`、`Librarian`、`SystemAdmin`、`BookTitle`、`Loan`、`Reservation`、`FineRecord`、`BookReview`
- 策略对象：`BorrowPolicy`（读者类型 × 出借物二维规则）、`FineRule`（宽限期 + 单价）
- 类图只画领域概念，**不含 Controller / Repository / DTO**，避免设计类污染领域模型

### 4.6 架构设计（`07-architecture.md`、`08-package-diagram.puml`）

采用分层架构 + MVC 分离，并在最外层叠加"对话式 Agent 接入层"：

| MVC 角色 | 本项目实现 |
|---|---|
| Controller | `presentation/routers/*`：只接收参数、调用应用服务、返回响应 |
| Model | `domain/*` + `application/*`：业务规则与用例流程 |
| View | `schemas/*`（Pydantic DTO）：对外数据结构的序列化视图 |

包图表达 `presentation → application → domain ← infrastructure` 的依赖方向，
并声明硬约束：**Controller 不得直接依赖 Repository**。关键架构决策（ADR 摘要）：

| 编号 | 决策 | 理由 |
|---|---|---|
| ADR-01 | 认证身份（`Account`）与业务身份（`Reader`）分离 | 密码字段不混入领域实体，便于多身份扩展 |
| ADR-03 | 业务规则放在策略对象而非 Service 硬编码 | 满足宪法第 8 条，规则可配置化 |
| ADR-04 | 令牌存服务端映射而非 JWT | 免第三方依赖，符合教学定位 |
| ADR-06 | 预约失效采用读取时惰性判定 | 无需定时任务 |
| ADR-07 | 借阅 / 罚款 / 赔偿规则用**可配置策略表**替代策略继承体系 | 规则可运行时调整；语义等价于参考类图中的"本科生借书策略 / 书到期策略 / 杂志罚款策略"等 |

`07-architecture.md` 第 12 节给出与指导书参考架构（Dispatcher / Controller / Service / DAO / Hibernate）的逐项映射，
说明本项目是同一套分层思想的 Python 技术实现。

### 4.7 数据库设计（`13-database-design.md`）

共 16 张表，与领域模型一一对应（含单表继承的鉴别列）：

```text
accounts      auth_tokens      readers        borrow_cards
librarians    system_admins    book_titles    library_items
loans         reservations     borrow_policies    fine_rules
fine_records  compensation_policies  lost_items  book_reviews
```

要点：借阅策略表以 `UNIQUE(reader_type, item_type)` 承载二维规则；金额使用 `NUMERIC(10,2)` 并在领域层用 `Decimal` 计算；
业务数据一律逻辑删除；为"有效借阅证 / 在借记录"建立部分唯一索引。

### 4.8 风险分析与人工审查（`17-risk-analysis.md`、`18-review-checklist.md`）

24 条风险按需求 / 建模 / 架构 / 数据库 / 权限 / 测试 / Agent 使用七类登记并给出缓解措施。
高风险项包括"领域层被 SQLAlchemy 污染""业务规则散落到路由层""Agent 编造字段名导致前后端不一致"
"Agent 擅自修改已冻结 Specs"等；`18-review-checklist.md` 把风险转化为逐项可勾选的审查清单，
用于每次 Agent 产出后的人工审查。

### 4.9 Specs baseline 冻结

全部实验一 Specs 经人工审查后打 tag `experiment1-specs-baseline-v1`。后续实现阶段若需变更规格，
必须先提交**变更影响分析**（`19-ai-usage-log.md` 第 19、20 次记录即为两次变更的记录）。
实验二实现前的最终规格快照另打 tag `experiment2-specs-baseline-v1`（详见实验二报告）。

### 4.10 实验一小结

| 检查项 | 结果 |
|---|---|
| 实验一 Specs 文件齐全（00–08、13、17、18 + 宪法） | ✅ 12 份 |
| 用例图 / 类图 / 包图 | ✅ 3 张 PlantUML |
| 需求可追溯（FR ↔ UC ↔ BR） | ✅ 编号互相引用 |
| 人工审查记录 | ✅ `18-review-checklist.md` + `19-ai-usage-log.md` 的"人工审查结果"字段 |
| Baseline | ✅ `experiment1-specs-baseline-v1` |

---

## 五、AI 使用记录（实验一阶段）

全部 Agent 使用登记在 `specs/19-ai-usage-log.md`。本实验阶段共 **15 次**（第 1–15 次），
每次记录包含：使用工具、使用阶段、输入 Prompt 摘要、Agent 修改文件、输出摘要、人工审查结果、测试结果、Git 提交。

| 阶段 | 次数 | 典型任务 |
|---|---|---|
| Inception | 第 1–3 次 | 生成项目 Brief、提出澄清问题、生成开发宪法 |
| Elaboration | 第 4–12 次 | 需求规格、用例文本与用例图、领域模型与类图、架构与包图、数据库设计、风险与审查清单 |
| Elaboration 修订 | 第 13–15 次 | 对照指导书修订（新增专科生类型、罚款宽限期）、人工审查后修订（评论审核、预约有效期）、对照参考图修订 |

**人工审查发挥作用的典型事例**：

**规格与指导书对齐**：对照指导书发现缺少"专科生"类型与罚款宽限期，先改 Specs（提交 `b18d7f6`），再改实现。

---

## 六、Git 演进过程（实验一阶段）

按"Specs 生成 → 人工修订 → baseline"的顺序推进，每个提交都保持可回溯：

| 阶段 | 关键提交 |
|---|---|
| 初始化 | `44d327c` init project: add gitignore and python dependencies；`f70977c` add baseline code, course documents and agent skills |
| Inception | `9f72aa6` add project brief → `75804af` answer clarifying questions → `24847b3` add development constitution |
| Elaboration（生成） | `96ddf6b` requirements → `199ba11` use case texts → `df2fa20` use case diagram → `544ab1c` domain model → `8977dd1` domain class diagram → `d056561` architecture → `2d29a8b` package diagram → `11bfc6d` database design → `6175276` risk analysis and review checklist |
| Elaboration（人工修订） | `58d8de2` revise specs after human review: comment moderation and reservation expiry；`b18d7f6` revise specs according to lab manual: associate reader type and fine grace period；`679977d` revise specs after comparing with lab manual reference diagrams |

Baseline tag：

| Tag | 含义 |
|---|---|
| `experiment1-specs-baseline-v1` | 实验一 Specs 审查通过并冻结（位于提交 `679977d`） |
| `experiment2-specs-baseline-v1` | 实验二实现前的最终规格基线（与上一 tag 同点追加，见实验二报告） |

---

## 七、交付物对照（指导书实验一提交物）

| # | 指导书要求 | 本仓库位置 | 状态 |
|---|---|---|---|
| 1 | `00-project-brief.md` | `specs/00-project-brief.md` | ✅ |
| 2 | `01-clarifying-questions.md` | `specs/01-clarifying-questions.md` | ✅ |
| 3 | `02-requirements.md` | `specs/02-requirements.md` | ✅ |
| 4 | `03-use-cases.md` | `specs/03-use-cases.md` | ✅ |
| 5 | `04-use-case-model.puml` | `specs/04-use-case-model.puml`（另有 `UML/` 导出 PNG） | ✅ |
| 6 | `05-domain-model.md` | `specs/05-domain-model.md` | ✅ |
| 7 | `06-domain-class-diagram.puml` | `specs/06-domain-class-diagram.puml` | ✅ |
| 8 | `07-architecture.md` | `specs/07-architecture.md` | ✅ |
| 9 | `08-package-diagram.puml` | `specs/08-package-diagram.puml` | ✅ |
| 10 | `13-database-design.md` | `specs/13-database-design.md` | ✅ |
| 11 | `17-risk-analysis.md` | `specs/17-risk-analysis.md` | ✅ |
| 12 | `18-review-checklist.md` | `specs/18-review-checklist.md` | ✅ |
| 13 | `19-ai-usage-log.md` | `specs/19-ai-usage-log.md`（第 1–15 次记录，后 6 次在实验二续记） | ✅ |
| 14 | Git commit 记录 | 本报告第六章（初始化 → baseline） | ✅ |

---

## 八、遇到的问题与解决

| # | 问题 | 原因 | 解决方式 |
|---|---|---|---|
| 1 | Specs 与指导书参考图不一致（缺少"专科生"类型、罚款无宽限期） | 首版规格依据 Brief 的简化假设 | 先修订 Specs（`b18d7f6`）再改实现，并按指导书参考图复核领域模型与架构映射（`679977d`） |

---

## 九、总结与改进方向

### 9.1 收获

1. **规格是可执行的资产**：把需求编号（FR/BR）、用例编号（UC）与测试编号（TC）、任务编号（TASK）互相引用后，
   Agent 产出的每一段代码都能追溯到具体规格，人工审查也有了可对照的清单。
2. **分层与策略对象是"抗 AI 漂移"的结构**：业务规则集中在 `BorrowPolicy` / `FineRule` / `CompensationPolicy` 后，
   Agent 即使在多处生成代码，也很难把规则散落到控制器里；测试断言直接引用 BR 编号，规则被放宽会立即暴露。
3. **Git 是 AI 时代的过程证据**：分阶段提交把"澄清 → 建模 → 冻结"完整保留下来，复盘时有据可依。

### 9.2 待改进

| # | 改进点 | 说明 |
|---|---|---|
| 1 | 顺序图对象命名与指导书列举完全对齐 | 指导书列举为 `LibrarianController` / `FineService` 等，本项目改用实现类名，语义一致但名称不同（详见实验二报告） |
| 2 | 部分用例条目补齐字段 | 少数用例的"次要参与者 / 备选事件流"可进一步补全 |
| 3 | 包图补充独立 DTO 包 | 现把 DTO 归入 `schemas` 并在架构文档中说明，可在包图里显式画出 |

---

## 附录 A. Specs 文档索引（实验一）

| 文档 | 内容 |
|---|---|
| `specs/00`–`01` | 项目 Brief、需求澄清问答 |
| `specs/02`–`04` | 需求规格（FR/BR/NFR）、用例文本、用例图 |
| `specs/05`–`06` | 领域模型、领域类图 |
| `specs/07`–`08` | 架构设计（含 ADR 与参考架构映射）、包图 |
| `specs/13` | 数据库设计（16 张表） |
| `specs/17`–`18` | 风险分析（24 条）、审查清单 |
| `specs/constitution.md` | 开发宪法（11 条原则） |
| `UML/` | 6 张图的 PlantUML 源与导出 PNG（本实验 3 张：用例图 / 类图 / 包图） |

## 附录 B. 实验二入口

实验二的详细设计（`specs/09`–`12`、`14`–`16`）与 Agent 实现见 `实验报告二-详细设计与Agent实现.md`。
