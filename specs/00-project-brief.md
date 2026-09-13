# Project Brief：AI 时代图书管理系统

## 1. 项目背景

本项目是《软件设计与体系结构》课程实验项目，用于训练需求分析、UML 建模、架构设计、数据库设计、详细设计和代码实现能力。

与传统的"人工画图 + 人工编码"不同，本项目采用 **Spec-Driven（规格驱动）+ Agent 辅助实现** 的方式：

- 需求、用例、领域模型、架构、数据库、API、测试计划全部以开放文本（Markdown / PlantUML）形式放在 `specs/` 目录；
- 由 Git 管理版本，冻结 baseline 后作为实现与测试的唯一依据；
- 由编码 Agent（CodeBuddy）按 `16-tasks.md` 中的任务逐个实现；
- 所有 Agent 产出必须经过人工审查（`git diff`）后才提交。

## 2. 项目目标

开发一个**可运行的图书管理系统**，支持：

- 读者注册与借阅证办理；
- 图书标题与馆藏副本管理；
- 图书检索；
- 借阅、归还、续借；
- 借阅信息查询；
- 图书预约；
- 图书评论与评分；
- 超期罚款计算；
- 系统维护（借阅证、管理员、图书、规则）。

并通过 **对话式 Agent 入口** 完成上述操作：用户用自然语言提出需求，由编排 Agent 识别意图并调用后端 REST API。

## 3. 目标用户与参与者

| 参与者 | 说明 |
|---|---|
| Reader（读者） | 抽象基类，持有借阅证 |
| StudentReader（学生读者） | 本科生 / 研究生 / 博士生 |
| TeacherReader（教师读者） | 教师 |
| Librarian（图书管理员） | **代理**读者完成借书、还书，可查询任意读者借阅信息 |
| SystemAdmin（系统管理员） | 办理/删除借阅证、维护管理员、维护图书标题与馆藏副本、维护借阅与罚款规则 |

## 4. 主要业务

```text
注册读者账号
办理/删除借阅证
添加、删除图书管理员
添加/删除图书标题信息
添加/删除馆藏副本
查询图书
办理借书（管理员代理）
办理还书（管理员代理）
续借图书
查询借阅信息
预约图书
图书评论与评分
计算超期罚款
维护借阅规则与罚款规则
```

## 5. 业务规则（初稿，待 `01-clarifying-questions.md` 确认）

### 5.1 读者类型：借阅数量与期限

| 读者类型 | 最大借阅数量 | 借阅期限（天） |
|---|---|---|
| UNDERGRADUATE（本科生） | 5 | 30 |
| GRADUATE（研究生） | 10 | 60 |
| DOCTOR（博士生） | 15 | 90 |
| TEACHER（教师） | 20 | 90 |

### 5.2 借出物类型：罚款规则

| 借出物类型 | 罚款规则 |
|---|---|
| CHINESE_BOOK（中文图书） | 0.5 元/天 |
| FOREIGN_BOOK（外文图书） | 1.0 元/天 |
| CHINESE_MAGAZINE（中文杂志） | 0.2 元/天 |
| FOREIGN_MAGAZINE（外文杂志） | 0.5 元/天 |
| THESIS（论文） | 2.0 元/天 |

借阅规则与罚款规则必须实现为**可替换的策略对象**（Strategy 模式），不得硬编码在 Controller 中。

### 5.3 通用规则

- 借书前必须验证借阅证存在且有效；
- 借书前必须检查当前未归还数量是否超过该读者类型的上限；
- 借书前必须检查是否存在超期未还图书；
- 同一读者对同一图书标题的有效预约不可重复；
- 预约按创建时间排队；
- 只有系统管理员可办理借阅证、维护图书与规则；
- 只有图书管理员可办理借书与还书。

## 6. 核心领域对象

```text
Reader / StudentReader / TeacherReader
BorrowCard
Librarian
SystemAdmin
BookTitle
LibraryItem（Book / Magazine / Thesis）
Loan
Reservation
BorrowPolicy
FineRule
FineRecord
BookReview（图书评论与评分，第二阶段附加）
```

## 7. 技术要求

- 语言与框架：**Python 3.14 + FastAPI + SQLAlchemy 2.x + Pydantic v2**（复用现有 `backend/` 骨架）；
  - 已验证可用版本：`fastapi 0.141.1`、`sqlalchemy 2.0.50`、`pydantic 2.13.4`、`uvicorn`、`pytest`、`httpx`；
- 数据库：SQLite（`backend/app/library.db`）；
- 测试：pytest + httpx；
- 架构：分层架构（presentation / application / domain / infrastructure）+ MVC；
- UML：PlantUML（`.puml`，纳入 Git），必要时辅以 Mermaid；
- 服务端口：`http://localhost:8001`；
- 统一响应信封：`{"code": 200|400|500, "message": "...", "data": {...}}`；
- Agent：CodeBuddy，按 `specs/16-tasks.md` 分任务实现；
- 所有 Agent 生成内容必须人工审查。

### 7.1 对话式 Agent 分层（本项目特色，沿用现有 `.codebuddy` 结构）

```text
用户自然语言
  → orchestrator-agent（唯一入口：意图识别 + 路由分发 + 结果聚合，不直接调 API）
      ├─ 借/还/预约/续借/查记录 → circulation-agent（流通执行者，真正调 API）
      ├─ 找书/评论评分         → 对应 skill（编排层参考 skill 调 API）
      └─ 登录                  → user-manage skill
  → 后端 REST API
```

`SKILL.md` 是给大模型看的**接口契约说明书**，其中出现的字段名、路径必须与后端实现逐字一致。

## 8. 实施节奏

| 阶段 | 内容 |
|---|---|
| 第一阶段（主线） | 借阅证、馆藏、借书、还书、预约、查询、罚款、权限 |
| 第二阶段（附加） | 续借、图书评论与评分（对应《学生任务卡》两项扩展任务） |

## 9. 暂不实现（Non-Goals）

- 支付系统真实扣款；
- 图书条码扫描硬件；
- 复杂全文检索；
- 多校区馆藏调拨；
- 微信 / 统一身份认证登录；
- 复杂前端框架（本项目以 API + 对话式 Agent 为入口）。
