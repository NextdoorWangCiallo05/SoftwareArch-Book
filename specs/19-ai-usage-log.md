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
