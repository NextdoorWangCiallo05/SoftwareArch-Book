# AI 时代《软件设计与体系结构》实验报告（实验二）

## 对话式图书管理系统的详细设计与 Agent 辅助实现

| 项目 | 内容 |
|---|---|
| 课题 | 对话式图书管理系统（Spec-Driven + Agent 辅助实现） |
| 姓名 / 学号 | 王文硕/1024005279 |
| 班级 | 软件卓越2401 |
| 实验 | 实验二：详细设计与 Agent 实现 |
| 技术栈 | Python 3.14 · FastAPI 0.141 · SQLAlchemy 2.0 · Pydantic v2 · SQLite · pytest · Vue 3.5 + Vite 6 |
| 开发方式 | CodeBuddy Agent / Skill 契约驱动，按冻结后的 Specs 逐 TASK 实现 |
| 提交日期 | 2026-10-11 |
| 仓库 | 本目录（`README.md` 为仓库首页，`提交产物清单.md` 为交付物对照表） |

> 配套文档：实验一的架构设计与 Spec 建模见 `实验报告一-架构设计与Spec建模.md`。

---

## 一、实验目的

在实验一冻结的 Specs 基础上，完成系统的详细设计与 Agent 辅助实现，掌握：

1. 用两步法（分析类 → 设计类）生成详细设计模型，并以顺序图表达借书 / 还书 / 预约的交互与备选分支；
2. 编写 API 或服务接口规范、测试计划与任务拆解，使 Agent 可以"一任务一提交"地推进；
3. 按分层架构与 MVC 落地代码：Controller 不写业务规则、业务规则集中在领域策略对象；
4. 接入对话式 Agent：自然语言入口经编排层路由到流通执行者，再调用后端 REST API；
5. 使用自动化测试（单元 + 集成 + 端到端验收）验证"设计 — 实现"一致性；
6. 理解 AI 时代开发者的新职责：**用测试约束实现，用 Git 审查变更**。

---

## 二、实验前提

1. 实验一 Specs 已冻结于 tag `experiment1-specs-baseline-v1`；
2. 开发宪法 11 条生效（Specs 优先、Agent 起草人类确认、分层架构、业务规则集中等）；
3. 本实验在实现前先补齐详细设计 Specs（`09`–`12`、`14`–`16`），
   人工审查后追加 tag `experiment2-specs-baseline-v1`（与实验一 tag 同一提交 `679977d`）。

---

## 三、实验流程与方法

本实验对应 Construction 与 Transition 两个阶段：

```text
Design       详细设计（两步法）→ 借书 / 还书 / 预约顺序图
             → API 规范 → 测试计划 → 任务拆解
             → 人工审查 → 冻结实验二 Specs
Construction 骨架与数据模型 → 仓储 → 领域策略 → 各用例服务与路由 → Agent 契约同步 → 测试
Transition   端到端验收 → 提交产物整理 → AI 使用记录 → 报告与复盘
```

---

## 四、详细设计（`09-design-model.md`、`10`–`12` 顺序图、`14`–`16`）

### 4.1 详细设计模型（`09-design-model.md`）

采用指导书推荐的**两步法**：

1. **分析类**：领域实体、策略对象、领域服务及其交互（不考虑界面与持久化）；
2. **设计类**：加入 Controller、应用服务、Repository 实现与 DTO，并给出类职责、方法签名与异常映射。

`09-design-model.md` 第 6 节专门给出「展现层 → 领域层的消息设计」，为第五章界面元素设计提供依据。

### 4.2 三张顺序图（`10`–`12`）

三张顺序图分别描述**借书**、**还书**、**预约**，均含 `alt/else` 备选分支：

| 图 | 备选分支 |
|---|---|
| `10-sequence-borrow-book.puml` | 借阅证无效、超出可借册数、存在超期未还、副本不可借 |
| `11-sequence-return-book.puml` | 非本馆藏书、找不到借阅记录、超期生成罚款 |
| `12-sequence-reserve-book.puml` | 读者不存在、图书标题不存在、重复预约（排队） |

### 4.3 API 规范（`14-api-spec.md`）

每个接口含方法路径、请求参数、响应结果、权限要求、成功场景与失败场景；
实现后共 7 个路由模块、45 个端点（清单见附录 A）。

### 4.4 测试计划（`15-test-plan.md`）

TC 编号用例共 102 条，覆盖"注册成功、办证成功、证无效借书失败、借书成功、超数量失败、有超期失败、
图书不可借失败、还书成功、归还非本馆藏书失败、超期生成罚款、查询借阅信息、预约成功、重复预约失败、
普通读者执行管理员操作失败"等场景，并区分单元测试与集成测试。

### 4.5 任务拆解（`16-tasks.md`）

TASK-001–TASK-016，每个任务明确目标、输入规格、允许修改文件、禁止修改文件、实现要求、
验收标准与建议测试，使 Agent 可以"一任务一提交"地推进。

### 4.6 实验二 Specs 冻结

详细设计 Specs 经人工审查后追加 tag `experiment2-specs-baseline-v1`。
实现阶段若需变更规格，必须先提交**变更影响分析**（`19-ai-usage-log.md` 第 19、20 次记录即为两次变更的记录）。

---

## 五、代码实现

> 产物：`backend/`（四层架构）、`frontend/`（Vue 3 界面）、`demo/`（curl 记录与对话演示）

### 5.1 技术选型与工程落地

按 `specs/16-tasks.md` 的顺序实施：前两个任务先搭骨架（分层目录、`core` 配置、ORM 模型、种子数据），
其余任务按"领域 → 基础设施 → 应用 → 表现 → 契约"的顺序推进。实现规模：

| 部分 | 规模 |
|---|---|
| 后端 | `backend` 71 个 Python 文件、约 5,548 行 |
| 表现层 | 7 个路由模块、45 个 REST 端点 |
| 前端 | `frontend/src` 28 个文件、约 3,613 行 |
| 测试 | 7 个测试文件（单元 + 集成），142 个测试用例通过 |

### 5.2 领域层实现（业务规则集中）

| 规则 | 落点 |
|---|---|
| BR-002 / BR-004 数量与期限 | `BorrowPolicy.get_max_borrow_count()` / `get_borrow_days()`，支持 `(reader_type, item_type)` 二维查找并回退 `ALL` |
| BR-001 借阅证有效 | `BorrowCard.is_valid()` + `CirculationPolicyChecker` |
| BR-003 超期检查 | `Reader.has_overdue()` |
| BR-005 罚款计算 | `FineRule.calculate_fine()`：`max(0, 逾期天数 − grace_days) × 单价` |
| BR-012 续借条件 | `Loan.renew()`：仅 `BORROWED`、限 1 次、逾期拦截、有他人有效预约拦截 |
| BR-010 副本状态机 | `LibraryItem` 状态方法（可借 / 借出 / 下架 / 丢失） |
| BR-020 两段式还书 | `Loan` 状态机 `BORROWED → RETURN_REQUESTED → RETURNED`，驳回退回 `BORROWED` |

领域层不依赖 FastAPI / SQLAlchemy Session，可脱离框架独立单元测试。

### 5.3 应用层与表现层实现

- **应用层**：`auth / catalog / circulation / reservation / review / admin` 六个服务，一个用例方法对应一个事务边界；
  只抛领域异常，不抛 `HTTPException`；
- **表现层**：7 个路由模块对外提供 45 个端点，统一响应信封 `{code, message, data}`；
  认证与角色校验由 `get_current_account` / `require_role(...)` 依赖注入完成，**角色只从令牌解析**，忽略请求体中的角色字段；
  全局异常处理器把领域异常映射为 `400 / 403 / 404 / 500`；
- **数据级权限**（读者只能查本人借阅记录）在应用服务中校验，越权返回 `403`。

### 5.4 基础设施层实现

- SQLAlchemy ORM 共 16 张表（与 `13-database-design.md` 一致），读者与馆藏采用单表继承 + 鉴别列；
- Repository 接口在领域层声明、在基础设施层实现，实现依赖倒置；
- 密码使用 PBKDF2-HMAC-SHA256 + 随机盐；令牌为随机串并持久化到 `auth_tokens` 表，服务重启不影响已登录会话；
- 启动装配：建表 + 灌种子数据（五类借阅策略、五类罚款规则、图书与馆藏、各角色测试账号）。

---

## 六、界面元素的设计

按指导书实验二"以用例文本和交互图为基础，重点考虑从展现层进入领域层的消息"的要求，本项目以 REST API 作为展现层入口
（`09-design-model.md` 第 6 节），并实现 Vue 3 可视化界面：

| 工作台 | 页面能力 |
|---|---|
| 读者 | 图书检索、图书详情与评分、我的借阅（状态筛选、申请归还、续借）、我的预约、登录 |
| 图书管理员 | 借书、现场还书、**归还申请审核**、读者借阅记录查询、罚款与赔偿（缴清） |
| 系统管理员 | 图书标题与馆藏副本维护、读者与借阅证管理、图书管理员账号管理、借阅与罚款规则维护、评论审核 |

界面只调用统一信封的 REST 接口，不承载任何业务规则（符合宪法第 6、8 条）。

---

## 七、对话式 Agent 接入层的实现

```text
用户自然语言
  → orchestrator-agent（意图识别 + 路由 + 聚合，自己不调 API）
      ├─ 借 / 还 / 续借 / 预约 / 查记录 → circulation-agent（真正调 API）
      ├─ 找书 / 评论评分                → book-search / book-review skill
      └─ 登录                           → user-manage skill
  → REST API :8001
```

- 6 个 skill 契约：`book-search`、`book-review`、`borrow-book`、`renew-book`、`return-book`、`user-manage`；
- 遵守任务卡"三条铁律"：契约文件是提示词而非代码；穿过 API 边界的名字（`reader_id`、`card_no`、`loan_id`、
  `new_due_date`、`average_rating` 等）与后端严格一致；仅描述流程的措辞用自然语言；
- 界面与 Agent 两条入口共用同一套后端契约，任何接口变更必须同步契约，否则视为破坏性变更；
- 4 段真实对话演示（借书 / 续借 / 评论 / 还书）见 `demo/chat-demo.md`，含路由判断、调用链路与验收对照，
  并内嵌任务卡 5.3 实测截图（`ScreenShots/`）。

---

## 八、扩展任务实现

| 扩展 | 实现要点 | 验收证据 |
|---|---|---|
| **任务一：续借** | `POST /api/circulation/renew`（body 用真实主键 `loan_id`，不传天数，借期由 `BorrowPolicy` 推算）；`Loan.renew()` 限 1 次 | `demo/curl-tests.md` §1、`demo/chat-demo.md` 演示二 |
| **任务二：评论与评分** | 新增 `book_reviews` 表；`POST /api/reviews`（评分 1–5 由领域层校验）、`GET /api/reviews?title_id=`（平均分仅统计 `APPROVED`）、审核端点；挂接位置为**编排层 `use_skill`** 而非 circulation-agent | `demo/curl-tests.md` §2、`demo/chat-demo.md` 演示三 |
| **扩展：BR-020 两段式还书** | 读者发起归还申请 → 馆员审核通过 / 驳回；申请期间仍占借阅配额；罚款按实际归还日结算 | `demo/return-flow-curl-test.md`、集成测试 TC-083–TC-095 |
| **扩展：丢失赔偿** | `lost_items` + `compensation_policies`，登记丢失与赔偿、缴清 | `backend/scripts/e2e_report.md` |

---

## 九、测试与验收

```powershell
# 单元 + 集成测试（独立内存库，不污染运行库）
cd backend
$env:PYTHONIOENCODING="utf-8"
python -m pytest tests -q            # 142 passed

# 端到端验收（对真实运行的服务调用 30 个场景）
python scripts/e2e_acceptance.py     # 生成 scripts/e2e_report.md，30 / 30 通过
```

| 验收维度 | 覆盖内容 | 结果 |
|---|---|---|
| 单元测试 | 借阅策略（含二维与回退）、罚款计算、预约有效期、续借上限、评分校验 | 通过 |
| 集成测试 | 注册 / 办证 / 借书（含四类拒绝）/ 还书（含超期罚款）/ 续借 / 预约 / 评论审核 / 权限失败 / BR-020 全流程 | 通过 |
| 端到端验收 | 借还预约查询、三种读者类型借期与上限、杂志 7 天与论文 3 天、续借与上限、评论校验与审核后可见、权限收口、同样逾期 10 天下"图书 5.00 元 vs 论文 20.00 元"的罚款差异 | **30 / 30 通过** |
| 接口 curl 记录 | 任务一、任务二接口（含请求 / 响应 / 结论） | 通过 |
| 对话演示 | 借书 / 续借 / 评论 / 还书 四段，含路由判断与验收对照 | 完成 |

### 9.1 实验二小结

| 检查项 | 结果 |
|---|---|
| 分层架构落地（Controller 不碰 Repository） | ✅ 依赖方向与包图一致 |
| 业务规则集中在策略对象 | ✅ 策略表可运行时调整 |
| 45 个端点均有权限要求与错误码语义 | ✅ 统一信封 + 全局异常映射 |
| 界面元素设计（展现层 → 领域层消息） | ✅ `09-design-model.md` §6 + Vue 3 三类工作台 |
| 对话式 Agent 三层路由 | ✅ 编排层只路由、流通执行者调 API |
| 自动化测试闭环 | ✅ 142 个用例 + 30 个端到端场景 |

---

## 十、AI 使用记录（实验二阶段）

`specs/19-ai-usage-log.md` 全量共 **21 次**，其中本实验阶段为第 16–21 次：

| 阶段 | 次数 | 典型任务 |
|---|---|---|
| Construction | 第 16–18 次 | 按 TASK 分批实现领域层 / 基础设施层 / 应用与表现层、同步 Agent 契约 |
| Transition 与变更 | 第 19–20 次 | 新增接口（附**变更影响分析**）、BR-020 两段式还书（规格 + 后端 + 前端同步修改） |
| 迭代优化 | 第 21 次 | 前端玻璃拟态视觉重构（仅 `styles.css`，零结构与类名变更） |

**人工审查发挥作用的典型事例**（说明"Agent 起草、人类确认"不是形式）：

1. **契约缺口**：对话演示时发现 Agent 拿到的是 `user_id`，而借书 / 查记录需要 `reader_id`，且 `card_no` 无法直接取得；
   据此新增 `GET /api/auth/me` 并在 `GET /api/admin/readers` 暴露 `card_no`，同步修订 skill 契约
   （提交 `0ce0b9e fix agent contract gap: add /api/auth/me and expose card_no`）。
2. **规则编号误用**：两段式还书的规则编号一度被写成 BR-013（该编号实为"评分范围"），
   审查后全局校正为 **BR-020**，并同步修正后端与前端注释、测试类 docstring 中的用例编号。
3. **超出 baseline 的变更管控**：第 19、20 次使用超出了已冻结的 Specs，因此记录中额外增加
   "变更影响分析"小节（列出受影响的规格、接口、前端页面与测试），而不是直接改代码。

---

## 十一、Git 演进过程（实验二阶段）

共 **42 次提交**（截至 2026-10-14），本实验阶段的提交按"逐 TASK 实现 → 验收与提交产物 → 交付完善"推进，
每个提交都保持可运行、可回溯：

| 阶段 | 关键提交 |
|---|---|
| Construction | `189183c` TASK-001/002 骨架与数据模型 → `577d1a4` TASK-003/004 领域实体与策略 → `6d50ef2` TASK-005 仓储 → `38b72cf` TASK-006 认证与权限 → `93d74a7` TASK-007/008 检索与管理端 → `8645018` TASK-009~011 借书/还书/续借/赔偿 → `679ee69` TASK-012~016 预约/评论/规则/契约同步 |
| Transition | `37b4341` 端到端验收脚本与报告 → `0ce0b9e` 修复契约缺口 → `0aed0c5` 接口 curl 记录 → `b144f1f` 前端源码与两段式还书、提交产物 |
| 交付完善 | `4561d41` specs 与实现对齐 → `edfbee4` 后端组合根重构 → `108d71f` 前端分页与防御性处理 → `bc552a0` PlantUML 模型与本地产物忽略 → `153093a` 文档状态与接口路径修正 → `d21666d` 一键运行脚本 → `20c17d6` 任务卡 5.3 截图 → `9cad275` 提交前检查收尾 |

两个 tag 标记了两次规格冻结：

| Tag | 含义 |
|---|---|
| `experiment1-specs-baseline-v1` | 实验一 Specs 审查通过并冻结（提交 `679977d`） |
| `experiment2-specs-baseline-v1` | 实验二实现前的最终规格基线（与上一 tag 同点追加） |

---

## 十二、交付物对照（指导书实验二最终验收）

| # | 验收要求 | 本仓库证据 | 状态 |
|---|---|---|---|
| 1 | 实验一 specs 已 baseline | tag `experiment1-specs-baseline-v1` | ✅ |
| 2 | 实验二详细设计 specs 已 baseline | tag `experiment2-specs-baseline-v1` | ✅ |
| 3 | 至少有借书、还书、预约三个顺序图 | `specs/10`、`11`、`12` | ✅ |
| 4 | 有 API 或服务接口规范 | `specs/14-api-spec.md`（45 个端点） | ✅ |
| 5 | 有测试计划 | `specs/15-test-plan.md`（102 条 TC） | ✅ |
| 6 | 有按任务拆解的 tasks.md | `specs/16-tasks.md`（TASK-001–016） | ✅ |
| 7 | 代码可以运行 | `run.ps1` 一键启动（前后端 + 健康检查） | ✅ |
| 8 | 自动化测试通过 | `backend/tests/`（142 个用例）+ `e2e_acceptance.py`（30/30） | ✅ |
| 9 | 借书、还书、预约、查询至少可用 | 集成测试 + `e2e_report.md` 全覆盖 | ✅ |
| 10 | 不同读者类型借阅规则可用 | 五类读者二维策略（专科 3/30 … 教师 20/90） | ✅ |
| 11 | 不同借出物类型罚款规则可用 | 五类罚款规则（`fine_category` 可配置） | ✅ |
| 12 | ai-usage-log.md 完整 | `specs/19-ai-usage-log.md`（21 次记录） | ✅ |
| 13 | Git commit 能体现按任务逐步开发 | 本报告第十一章 TASK 分批提交 | ✅ |

---

## 十三、功能验收结果

| 需求范围（指导书） | 实现与验证 |
|---|---|
| 读者注册账号、由系统管理员办理借阅证 | `POST /api/auth/register`（不自动发证）+ `POST /api/admin/cards` |
| 读者：查询图书 / 查询本人借阅信息 / 网络预约 | 检索与详情接口、`GET /api/circulation/records/{reader_id}`、预约接口（7 天有效） |
| 图书管理员：借书 / 还书 / 查询读者借阅信息 | 借书四重校验、现场还书 + 归还申请审核、记录查询 |
| 系统管理员：办证 / 删证 / 增删管理员 / 增删图书 / 增删标题 | `admin_router` 全量提供，并在前端管理员工作台提供入口（逻辑删除，保留历史） |
| 不同读者类型不同借阅数量与期限 | 五类读者二维策略：专科 3/30、本科 5/30、研究生 10/60、博士 15/90、教师 20/90 |
| 不同馆藏类型不同罚款规则 | 中/外文图书、中/外文杂志、论文五类罚款规则（`fine_category` 可配置） |
| 超期罚款 | `FineRule` 按天计费（含宽限期），图书与论文单价不同 |
| 预约与查询 | 预约排队 + 7 天有效期；可查询当前 / 历史 / 超期状态的借阅记录 |

---

## 十四、遇到的问题与解决

| # | 问题 | 原因 | 解决方式 |
|---|---|---|---|
| 1 | 对话演示时 Agent 拿不到借书所需的 `card_no`，且混淆 `user_id` 与 `reader_id` | 契约中引用了不存在的字段；两个编号体系在提示词里未区分 | 新增 `GET /api/auth/me` 返回 `reader_id` / `card_no` / `reader_type`，管理员读者列表暴露 `card_no`，并同步修订 `.codebuddy/` 契约（提交 `0ce0b9e`） |
| 2 | 两段式还书的规则编号被写成 BR-013 | Agent 生成时的编号笔误，而 BR-013 实为"评分范围" | 全局校正为 BR-020，同步修正后端 / 前端注释与测试 docstring 中的用例编号 |
| 3 | 旧 `library.db` 结构残留导致建表冲突 | 领域模型演进后旧库仍有旧表 | 首次启动建库灌种子；重复启动不清空数据，需要重置时以 `RESET_DB_ON_START=1` 启动重建；`*.db` 加入 `.gitignore` 不入库 |
| 4 | 令牌存在内存中，服务重启即失效 | 初版实现简单 | 改为 `auth_tokens` 表持久化，重启后已登录会话仍有效（对应风险 R-11） |
| 5 | curl 记录中携带真实会话令牌 | 直接粘贴原始输出 | 全部脱敏为 `<TOKEN>`，并在记录中注明 |
| 6 | 金额计算可能出现浮点误差 | 初版使用浮点 | 数据库用 `NUMERIC(10,2)`，领域层用 `Decimal` 计算（对应风险 R-14） |
| 7 | 前端原本不在 Brief 范围内，但实验二要求"界面元素的设计" | 范围扩展 | 以 Vue 3 实现三类工作台作为可视化验收入口，并在 ai-usage-log 的变更记录中登记；根目录 README 说明该扩展 |

---

## 十五、总结与改进方向

### 15.1 收获

1. **设计先行、规格冻结再实现的流程**，使 Agent 的产出自始至终受 `specs/` 约束，
   代码结构与包图、类图保持一致（差异仅在 ADR 记录的决策处，如策略表替代策略继承体系）；
2. **业务规则集中在领域层策略对象后**，规则调整（数量、期限、单价、宽限期）无需改动控制器与前端；
3. **测试是 Agent 协作的合同**：142 个用例 + 30 个端到端场景，使"看起来改对了"必须变成"实测通过"。
4. **人工审查不可省**：本项目最有价值的三处修正（契约缺口、规则编号、规格与指导书对齐）都来自人工审查与实测，
   而非 Agent 自查。
5. **Git 是 AI 时代的过程证据**：逐 TASK 提交把"冻结 → 实现 → 验收 → 交付完善"完整保留下来，复盘时有据可依。
6. **契约即接口**：对话式 Agent 层与 Web 界面共用同一套契约，两条入口的改动必须同步，避免了前后端漂移。

### 15.2 待改进

| # | 改进点 | 说明 |
|---|---|---|
| 1 | 补充博士生读者种子账号 | 策略表中已有博士 15 本 / 90 天规则且被单元测试覆盖，但种子账号未包含博士生，现场演示时可操作性不足 |
| 2 | 顺序图对象命名与指导书列举完全对齐 | 现用 `CirculationController` / `FineCalculator` 等实现类名，指导书列举为 `LibrarianController` / `FineService`，语义一致但名称不同 |
| 3 | 部分测试计划条目补齐字段 | 部分集成测试条目的"前置条件 / 操作步骤"可进一步补全 |
| 4 | 演示材料 | 对话演示目前为文字调用链记录（另附任务卡 5.3 实测截图），可再补录屏 |
| 5 | Agent 团队模式演示 | 当前演示环境未组队，`circulation-agent` 以"编排层自执行"降级通道运行（见 `demo/chat-demo.md` §6），可在组队环境下补一次真实委派演示 |

### 15.3 结语

实验的核心不是"让 AI 写代码"，而是**用规范指挥 Agent、用 UML 表达设计、用测试约束实现、用 Git 审查变更**。
本项目中人类负责目标与约束、审查与决策，Agent 负责生成与实现，两者通过 Specs、契约与测试形成闭环，
最终交付了一个可运行、可复现、可追溯的系统。

---

## 附录 A. 接口清单（按模块）

| 模块 | 端点 | 说明 |
|---|---|---|
| `auth` | `POST /api/auth/register`、`/login`、`/logout`；`GET /api/auth/me` | 注册、登录、注销、当前身份 |
| `catalog` | `GET /api/books/search`、`GET /api/books/{title_id}` | 检索、详情 |
| `circulation` | `POST /borrow`、`/return`、`/return-request`、`/return-requests/{loan_id}/approve`、`/reject`、`/renew`、`/lost`、`/fines/{id}/pay`、`/lost/{id}/pay`；`GET /records/{reader_id}`、`/return-requests`、`/fines`、`/lost` | 借书、还书、两段式审核、续借、记录查询、丢失赔偿、罚款缴清 |
| `reservation` | `POST /api/reservations`、`/{id}/cancel`；`GET /api/reservations` | 预约、取消、查询 |
| `review` | `POST /api/reviews`；`GET /api/reviews`、`/pending`；`POST /api/reviews/{id}/moderate` | 评论提交、查询、待审清单、审核 |
| `admin` | `/api/admin/cards`、`/readers`、`/librarians`、`/titles`、`/items`、`/policies/borrow`、`/policies/fine` | 借阅证、读者、管理员、标题与馆藏、规则维护 |
| `system` | 健康检查与初始化相关端点 | 服务状态 |

合计 7 个路由模块、45 个端点，统一响应信封 `{code, message, data}`。

## 附录 B. 测试账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 系统管理员 |
| `lib01` / `lib02` | `123456` | 图书管理员 |
| `zhangsan`（本科生）/ `lisi`（研究生）/ `wangwu`（教师）/ `zhaoliu`（专科生） | `123456` | 读者 |

## 附录 C. 复现步骤

```powershell
# 1) 启动后端（首次启动建库灌种子；需重置时先 $env:RESET_DB_ON_START=1）
cd backend
pip install -r requirements.txt
python main.py                       # http://localhost:8001/docs

# 2) 单元 + 集成测试
$env:PYTHONIOENCODING="utf-8"
python -m pytest tests -q            # 142 passed

# 3) 端到端验收（30 个真实接口场景）
python scripts/e2e_acceptance.py     # 生成 scripts/e2e_report.md

# 4) 接口 curl 记录（任务一续借 / 任务二评论评分）
cd ..
powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1

# 5) 两段式还书完整状态流转（自包含，自动启停后端）
powershell -ExecutionPolicy Bypass -File demo/return-flow-curl-verify.ps1

# 6) 前端界面
cd frontend
npm install
npm run dev                          # http://localhost:5173
```

## 附录 D. 文档索引

| 文档 | 内容 |
|---|---|
| `specs/09`–`12` | 详细设计、借书 / 还书 / 预约顺序图 |
| `specs/14`–`16` | API 规范、测试计划、任务拆解 |
| `specs/19-ai-usage-log.md` | AI 使用记录（21 次，含两次变更影响分析） |
| `README.md` | 仓库首页：功能、架构、启动、接口、测试、规格导航 |
| `backend/README.md` | 后端细节：目录结构、启动、测试、账号、完整接口清单 |
| `提交产物清单.md` | 任务卡第 5 节四要素对照、任务一 / 任务二实现位置与验收证据 |
| `demo/chat-demo.md` | 4 段对话演示（借书 / 续借 / 评论 / 还书） |
| `demo/curl-tests.md` | 任务一 + 任务二接口 curl 测试记录 |
| `demo/return-flow-curl-test.md` | BR-020 两段式还书 curl 记录 |
| `backend/scripts/e2e_report.md` | 端到端验收报告（30 / 30 场景） |
