# 对话式图书管理系统 · AI 时代《软件设计与体系结构》实验

> **规格驱动开发（Spec-Driven Development）**：人类提供目标与约束 → Agent 辅助生成 Specs 与 UML →
> 人工审查并冻结 baseline → Agent 按任务实现代码 → 自动化测试验证 → 人工审查 Git diff → 提交与复盘。

| 规格文档 | UML 图（PlantUML） | 自动化测试 | 端到端验收 | AI 使用记录 | Git 演进 |
|---|---|---|---|---|---|
| 21 份（`00`–`19` + 开发宪法） | 6 张（用例图/类图/包图/顺序图×3） | `142 passed` | `30 / 30` 通过 | 20 次，含审查与纠偏 | 38 次提交（截至 2026-10-14）+ 2 个 baseline tag |

---

## 1. 项目简介

本仓库是一个**对话式图书管理系统**：用户用自然语言提需求（如"我想借《三体》"），
由 `.codebuddy/` 下的 Agent 把意图翻译成对后端 REST API 的调用，再把结果整理成自然语言回复。

系统同时提供两种入口，二者共用同一套后端契约：

| 入口 | 说明 |
|---|---|
| **对话式 Agent** | `.codebuddy/`：`orchestrator-agent`（唯一入口，只做意图识别、路由分发、结果聚合）→ 委派 `circulation-agent` 或调用 `skills` |
| **可视化 Web 界面** | `frontend/`：Vue 3 + Vite，按读者 / 图书管理员 / 系统管理员划分工作台 |

设计文档（需求、用例、领域模型、架构、详细设计、数据库、API、测试计划、任务拆解、风险、AI 使用记录）
全部位于 `specs/`，**实现阶段不修改 specs**，代码严格按 `specs/16-tasks.md` 的任务粒度推进。

---

## 2. 功能范围

| 角色 | 能力 |
|---|---|
| **读者** | 注册账号；检索图书、查看详情与评分；预约图书（7 天有效期）；查看本人借阅 / 预约记录；发起续借；发起归还申请；提交评分与评论 |
| **图书管理员** | 代理借书；现场办理还书；**审核读者提交的归还申请**（通过 / 驳回）；代理续借；查询任意读者借阅记录；登记丢失与赔偿；罚款与赔偿缴清 |
| **系统管理员** | 办理 / 吊销借阅证；停用读者；图书管理员账号增删；图书标题与馆藏副本增删；维护借阅规则与罚款规则；审核评论 |
| **对话式 Agent** | 意图识别 → 路由（`circulation-agent` / `skills`）→ 调用 REST API → 聚合自然语言回复 |

必做业务规则：不同读者类型（专科 / 本科 / 研究生 / 博士 / 教师）借阅数量与期限不同；
不同馆藏类型（中/外文图书、中/外文杂志、论文）罚款规则不同；超期罚款；预约；查询。

---

## 3. 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.14 · FastAPI 0.141 · SQLAlchemy 2.0 · Pydantic v2 · SQLite |
| 测试 | pytest · httpx（单元 + 集成）· 自研端到端验收脚本 |
| 前端 | Vue 3.5 · Vue Router 4 · Vite 6（开发服务器 `:5173`，`/api` 代理到 `:8001`） |
| 建模 | PlantUML（UML-as-Spec，文本入库、可版本管理） |
| 流程 | Git（分阶段提交 + baseline tag）· CodeBuddy Agent / Skill 契约 |

---

## 4. 系统架构

```text
浏览器（frontend/  Vue 3 + Vite，:5173 → /api 代理）
        ↓ HTTP :8001
对话式 Agent 层（.codebuddy/）  仅通过 REST 契约访问，不直连数据库
  orchestrator-agent → circulation-agent / skills
        ↓
┌──────────────────────────────────────────────────────┐
│ Presentation   表现层   FastAPI routers + 依赖注入    │  ← Controller
├──────────────────────────────────────────────────────┤
│ Application    应用层   用例编排服务 + 事务边界 + DTO  │  ← Model
├──────────────────────────────────────────────────────┤
│ Domain         领域层   实体、值对象、策略、领域服务    │  ← Model
├──────────────────────────────────────────────────────┤
│ Infrastructure 基础设施 ORM、Repository 实现、安全     │
└──────────────────────────────────────────────────────┘
        ↓
      SQLite
```

- **MVC 映射**：Controller = `presentation/routers/*`；Model = `domain/*` + `application/*`；View = `schemas/*`（Pydantic DTO）
- **硬约束**：Controller 不直接依赖 Repository，不写业务规则；业务规则集中在 `BorrowPolicy` / `FineRule` / `CompensationPolicy` 策略对象
- **设计模式**：Strategy、Repository、Service Layer、DTO、Factory、单表继承、依赖注入
- 架构决策与指导书参考架构的逐项映射见 `specs/07-architecture.md` 第 11、12 节

---

## 5. 目录结构

```text
仓库根目录/
├─ README.md                  # 本文件（仓库首页）
├─ run.ps1                    # 一键运行脚本：启动前后端 + 健康检查（见 §6.1）
├─ 实验报告一-架构设计与Spec建模.md   # 实验一报告：Spec 建模与架构设计
├─ 实验报告二-详细设计与Agent实现.md  # 实验二报告：详细设计、代码实现与验收
├─ 提交产物清单.md            # 交付物逐项对照表（提交入口）
├─ 学生任务卡.md              # 课程下发的扩展任务卡
├─ specs/                     # 实验一 Spec 建模：需求 / 用例 / 领域 / 架构 / 详细设计 / 数据库 / API / 测试 / 任务 / 风险 / AI 记录
├─ backend/                   # 四层架构后端（FastAPI），说明见 backend/README.md
│  ├─ app/                    # core / presentation / application / domain / infrastructure / schemas
│  ├─ tests/                  # unit（领域与策略）+ integration（用例级 API）
│  └─ scripts/                # e2e_acceptance.py + e2e_report.md（30/30 场景）
├─ frontend/                  # Vue 3 界面：读者 / 馆员 / 管理员三类工作台
├─ .codebuddy/                # Agent / Skill 契约（提示词，非可执行代码）
│  ├─ agents/                 # orchestrator-agent（编排）、circulation-agent（流通执行者）
│  └─ skills/                 # book-search / book-review / borrow-book / renew-book / return-book / user-manage
├─ demo/                      # 提交产物：curl 测试记录、对话演示、复现脚本
├─ UML/                       # 6 张建模图的 PlantUML 源文件（.puml）与导出 PNG
├─ ScreenShots/               # 任务卡 5.3 实测截图：任务一续借 2 张 + 任务二评论 4 张
├─ .specify/                  # Spec-Kit 工具链产物：开发宪法副本、脚本与模板
└─ Document/                  # 课程提供的实验指导书与参考资料（非本项目交付物）
```

---

## 6. 快速开始

运行环境（开发与验收实测版本）：

| 组件 | 最低要求 | 实测版本 |
|---|---|---|
| Python | 3.11+ | 3.14.7 |
| Node.js | 18+ | 24.21.0（npm 11.19.0） |

**API 基址（前后端约定）**

| 场景 | 前端请求 | 实际到达 |
|---|---|---|
| 开发（`npm run dev`） | 相对路径 `/api/...` | Vite 开发服务器代理转发到 `http://localhost:8001`（见 `frontend/vite.config.js`） |
| 生产构建（`npm run build`） | 相对路径 `/api/...` | 由部署时的同源反向代理转发到后端 |

后端监听端口由 `backend/app/core/config.py` 的 `API_PORT` 控制（默认 8001），数据库地址、CORS 来源、令牌有效期等同样可用环境变量覆盖。

### 6.1 一键运行（推荐）

```powershell
powershell -ExecutionPolicy Bypass -File run.ps1              # 启动后端 :8001 + 前端 :5173
powershell -ExecutionPolicy Bypass -File run.ps1 -Reset       # 先重置演示数据再启动
powershell -ExecutionPolicy Bypass -File run.ps1 -BackendOnly # 只启动后端（跑 pytest / 验收脚本）
powershell -ExecutionPolicy Bypass -File run.ps1 -Open        # 启动后自动打开浏览器
powershell -ExecutionPolicy Bypass -File run.ps1 -Detach      # 启动后脚本退出，服务留在后台
powershell -ExecutionPolicy Bypass -File run.ps1 -Stop        # 停止后台残留的进程
```

脚本会检查 Python / Node 是否可用、按需安装依赖、等待健康检查通过；前台运行时按 `Ctrl+C` 一并停止前后端，
运行日志写入 `logs/`（`backend.log` / `frontend.log` 等，已被 `.gitignore` 忽略）。

### 6.2 手动启动后端

```powershell
cd backend
pip install -r requirements.txt
python main.py          # http://localhost:8001
```

- 接口文档：`http://localhost:8001/docs`
- 首次启动自动建库并灌入种子数据；重复启动**不会**清空已有数据。
  需要重置演示数据时，设置 `$env:RESET_DB_ON_START="1"` 后重启（或删除 `backend/app/library.db`）

### 6.3 手动启动前端

```powershell
cd frontend
npm install
npm run dev             # http://localhost:5173，/api 自动代理到 :8001
```

> 需先启动后端，前端才能取到数据。

---

## 7. 测试账号（种子数据）

| 用户名 | 密码 | 角色 |
|---|---|---|
| `admin` | `admin123` | 系统管理员 |
| `lib01` / `lib02` | `123456` | 图书管理员 |
| `zhangsan`（本科生） | `123456` | 读者 |
| `lisi`（研究生） | `123456` | 读者 |
| `wangwu`（教师） | `123456` | 读者 |
| `zhaoliu`（专科生） | `123456` | 读者 |

---

## 8. 核心接口

统一响应信封：`{"code": 200|400|403|404|500, "message": "...", "data": {...}}`。

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` · `/login` · `/logout` | 公开 / 登录 | 注册、登录、注销 |
| GET | `/api/auth/me` | 登录 | 当前身份（`reader_id`、`card_no`、`reader_type`） |
| GET | `/api/books/search` · `/api/books/{title_id}` | 登录 | 检索（关键词/作者/分类/类型/分页）、详情与副本 |
| POST | `/api/circulation/borrow` | 管理员 | 借书（`card_no` + `barcode`） |
| POST | `/api/circulation/return` | 管理员 | 现场办理还书（含超期罚款） |
| POST | `/api/circulation/return-request` | 读者 / 管理员 | 两段式还书·读者发起申请（BR-020） |
| GET/POST | `/api/circulation/return-requests[/{loan_id}/approve\|/reject]` | 管理员 | 归还申请清单、审核通过、驳回 |
| POST | `/api/circulation/renew` | 读者本人 / 管理员 | 续借 |
| GET | `/api/circulation/records/{reader_id}` | 本人 / 管理员 | 借阅记录（可选 `?status=`） |
| POST | `/api/circulation/lost` · `.../fines/{id}/pay` · `.../lost/{id}/pay` | 管理员 | 登记丢失赔偿、缴清罚款 / 赔偿 |
| GET | `/api/circulation/fines` · `/api/circulation/lost` | 管理员 | 罚款 / 赔偿清单（`?paid=false` 待缴） |
| POST | `/api/reservations` · `/{id}/cancel`，GET `/api/reservations` | 读者（管理员可代查） | 预约、取消、查询（7 天有效） |
| POST | `/api/reviews`，GET `/api/reviews?title_id=` | 读者 / 登录 | 提交评分评论、查看已通过评论与平均分 |
| GET/POST | `/api/reviews/pending` · `/api/reviews/{id}/moderate` | 系统管理员 | 待审核清单、审核 |
| ALL | `/api/admin/**` | 系统管理员 | 借阅证、图书管理员、读者、图书标题与馆藏、借阅与罚款规则维护 |

完整接口规范（请求 / 响应 / 权限 / 成功与失败场景）见 `specs/14-api-spec.md` 与 `backend/README.md`。

---

## 9. 关键业务规则

| 规则 | 内容 |
|---|---|
| 借阅策略 | 二维 `(reader_type, item_type)`：专科 3 本/30 天、本科 5/30、研究生 10/60、博士 15/90、教师 20/90；杂志 2 本/7 天、论文 2 本/3 天；未命中回退 `(reader_type, ALL)` |
| 罚款 | `max(0, 逾期天数 − grace_days) × amount_per_day`，含宽限期；图书与论文单价不同（同样逾期 10 天：图书 5.00 元 / 论文 20.00 元） |
| 借书前置校验 | 借阅证有效、未超可借册数、无超期未还、无未缴罚款、副本可借 |
| 续借 | 仅 `BORROWED` 可续借，每本限 1 次，逾期或存在他人有效预约时拒绝 |
| 预约 | 有效期 7 天，过期惰性失效，不占排队位次、不阻塞续借 |
| 评论 | 评分 1–5，需系统管理员审核；`average_rating` 仅统计 `APPROVED` |
| 两段式还书（BR-020） | `BORROWED --读者申请--> RETURN_REQUESTED --馆员通过--> RETURNED`；驳回退回 `BORROWED`；申请期间仍占借阅配额，罚款在审核通过时按实际归还日结算 |

---

## 10. 测试与验收结果

```powershell
# 1) 单元 + 集成测试（独立内存库，不污染运行库）
cd backend
$env:PYTHONIOENCODING="utf-8"
python -m pytest tests -q            # 142 passed

# 2) 端到端验收（对正在运行的服务调用真实接口，30 个场景）
python scripts/e2e_acceptance.py     # 生成 scripts/e2e_report.md，当前 30 / 30 通过

# 3) 接口 curl 记录复现（任务一续借 / 任务二评论评分）
powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1

# 4) 两段式还书完整状态流转（自包含：自动启停后端并重写报告）
powershell -ExecutionPolicy Bypass -File demo/return-flow-curl-verify.ps1
```

| 验收维度 | 结果 | 证据 |
|---|---|---|
| 单元测试（策略、实体方法） | 通过 | `backend/tests/unit/` |
| 集成测试（用例级 API，含 BR-020） | 通过 | `backend/tests/integration/` |
| 端到端真实接口验收 | 30 / 30 | `backend/scripts/e2e_report.md` |
| 接口 curl 记录 | 通过 | `demo/curl-tests.md`、`demo/return-flow-curl-test.md` |
| 对话链路演示 | 4 段 | `demo/chat-demo.md` |
| 任务卡 5.3 实测截图 | 6 张 | `ScreenShots/`（内嵌于 `demo/chat-demo.md` 演示二 / 演示三） |

---

## 11. 规格文档导航（`specs/`）

| 文件 | 作用 | 阶段 |
|---|---|---|
| `00-project-brief.md` | 人类提供的项目背景与约束 | Inception |
| `01-clarifying-questions.md` | Agent 澄清问题与人类回答 | Inception |
| `02-requirements.md` | FR-001–030 / BR-001–020 / NFR-001–006 | Elaboration |
| `03-use-cases.md` | 用例文本 UC-001–025（事件流、备选流） | Elaboration |
| `04-use-case-model.puml` | 用例图（参与者泛化与 include 关系） | Elaboration |
| `05-domain-model.md` | 领域模型说明 | Elaboration |
| `06-domain-class-diagram.puml` | 领域类图（继承、关联、策略对象） | Elaboration |
| `07-architecture.md` | 分层架构、MVC 映射、设计模式、ADR | Elaboration |
| `08-package-diagram.puml` | 包图与依赖方向 | Elaboration |
| `09-design-model.md` | 详细设计（两步法：分析类 → 设计类）+ 展现层→领域层消息 | Construction |
| `10`–`12` `sequence-*.puml` | 借书 / 还书 / 预约顺序图（含 alt 备选分支） | Construction |
| `13-database-design.md` | 数据库设计（16 张表、约束、索引） | Construction |
| `14-api-spec.md` | 接口规范（方法、参数、响应、权限、成功/失败场景） | Construction |
| `15-test-plan.md` | 测试计划 TC-xxx（单元 / 集成） | Construction |
| `16-tasks.md` | TASK 拆解（目标、输入规格、允许修改文件、验收标准） | Construction |
| `17-risk-analysis.md` | 风险分析 R-01–R-24 与缓解措施 | Elaboration |
| `18-review-checklist.md` | 人工审查清单 | Transition |
| `19-ai-usage-log.md` | AI 使用记录（20 次：Prompt、改动文件、测试结果、审查、提交） | 全程 |
| `constitution.md` | 开发宪法（11 条 Agent 行为约束） | Inception |

### 11.1 核心用例（标注"重点用例"的端到端链路）

| 用例 | 名称 | 覆盖要点 |
|---|---|---|
| UC-009 | 办理借书 | 读者类型 / 馆藏类型差异化借期与配额；含对齐指导书参考格式的结构化规格 |
| UC-010 | 申请还书与审核归还 | 读者发起申请（010.1）→ 馆员审核（010.2）；保留馆员现场办理通道（010.3）；审核通过时结算超期罚款 |
| UC-011 | 续借图书 | 续借次数上限、超期阻塞、被预约阻塞（OPEN-02）等规则校验 |
| UC-013 | 预约图书 | 无在架副本时可预约，预约有效期 7 天；被预约馆藏不可续借 |
| UC-015 | 计算超期罚款 | 由 UC-010 包含（include）；按馆藏类型套用差异化罚款规则并生成罚款记录 |

---

## 12. AI 协作方式（本实验的关键）

```text
人类提供目标与约束 → Agent 澄清与生成 Specs/UML → 人类审查并冻结 baseline
→ Agent 按 TASK 实现 → 测试验证 → 人类审查 git diff → 提交与复盘
```

- **开发宪法** `specs/constitution.md`：Specs 优先、Agent 起草人类确认、UML-as-Spec、Baseline 冻结、
  分层架构、MVC、权限区分、业务规则集中、测试闭环、Git 审查、AI 使用记录 —— 共 11 条
- **Baseline tag**：`experiment1-specs-baseline-v1`（实验一 Specs 冻结）、`experiment2-specs-baseline-v1`（代码实现前冻结）
- **实现阶段不得修改 specs**；确需变更时先提交变更影响分析（`19-ai-usage-log.md` 第 19、20 次记录即为示例，完整变更清单见 `提交产物清单.md` §9）
- **Agent 契约三条铁律**：`SKILL.md` 是提示词不是代码；穿过 API 边界的名字必须与后端一致；只描述流程的措辞用自然语言

---

## 13. 实验交付物对照（指导书 §12）

| # | 指导书要求 | 本仓库位置 |
|---|---|---|
| 1 | specs 全部文档 | `specs/`（21 份） |
| 2 | PlantUML / Mermaid 图文件 | `specs/04`、`06`、`08`、`10`、`11`、`12`（6 张 `.puml`） |
| 3 | 源代码 | `backend/`（四层架构）+ `frontend/`（Vue 3） |
| 4 | 自动化测试 | `backend/tests/`（单元 + 集成）+ `backend/scripts/e2e_acceptance.py` |
| 5 | README.md | 根目录 `README.md` + `backend/README.md` |
| 6 | ai-usage-log.md | `specs/19-ai-usage-log.md`（20 次记录） |
| 7 | Git commit 记录 | 38 次提交（截至 2026-10-14）+ 2 个 baseline tag（含 Specs 生成、审查修订、逐 TASK 实现、交付完善） |
| 8 | 实验报告 | `实验报告一-架构设计与Spec建模.md`（实验一）+ `实验报告二-详细设计与Agent实现.md`（实验二） |

---

## 14. 相关文档

| 文档 | 内容 |
|---|---|
| `实验报告一-架构设计与Spec建模.md` | 实验一：Spec 建模与架构设计（Brief → 需求 → 用例 → 领域 → 架构 → 数据库 → 风险审查 → 冻结 baseline） |
| `实验报告二-详细设计与Agent实现.md` | 实验二：详细设计、代码实现、Agent 接入层、测试验收、AI 使用复盘 |
| `提交产物清单.md` | 任务卡第 5 节四要素逐项对照、任务一/任务二的实现位置与验收证据、复现步骤 |
| `backend/README.md` | 后端技术细节：目录结构、启动、测试、账号、完整接口清单、业务规则速查 |
| `demo/chat-demo.md` | 4 段对话演示（借书 / 续借 / 评论 / 还书），逐条对齐验收标准与路由判断，内嵌任务卡 5.3 实测截图 |
| `ScreenShots/` | 任务卡 5.3 实测截图：任务一续借 2 张、任务二评论 4 张 |
| `demo/curl-tests.md` | 任务一 + 任务二接口 curl 测试记录（含复现脚本与原始输出） |
| `demo/return-flow-curl-test.md` | 扩展功能 BR-020 两段式还书 curl 记录（申请 → 驳回 → 再审 → 通过） |
| `Document/` | 课程提供的实验指导书、实验一/二详细要求、Agent 提示词手册、工具链说明书 |

---

## 15. 说明与约定

- 脚本会改变库状态；需要从清洁状态复现时，设置 `$env:RESET_DB_ON_START="1"` 后重启后端（默认重启**不清空**数据）。
- 文档中的令牌均已脱敏为 `<TOKEN>`；记录中的具体日期随运行日变化（借期由运行当日推算），属正常现象。
- 运行日志（`logs/`、`server*.log` / `server*.err`）、`*.db`、`__pycache__`、`node_modules/`、`dist/` 均已由 `.gitignore` 忽略，不随提交带出。
- `Document/` 为课程下发资料，不属于本项目交付内容。
