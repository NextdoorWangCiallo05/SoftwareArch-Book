# AI时代《软件设计与体系结构》实验：图书管理系统

## 1. 实验主题

图书管理系统的 Spec-Driven 架构设计、详细设计与 Agent 辅助实现。

本实验是在传统“UML建模 + 简化统一过程 + 分层架构 + MVC + 数据库设计 + 代码实现”的基础上，结合 AI 编码 Agent 的新型软件开发范式进行重构。

本实验推荐使用：

```text
OpenSpec
Spec-Kit
UML-as-Spec
PlantUML / Mermaid
CodeBuddy CN/Claude Code / Codex / OpenCode
Git
JUnit / pytest / REST API 测试
```

---

## 2. 实验背景

原实验要求学生以图书管理系统为例，完成：

1. 用例分析；
2. 领域模型；
3. 分层架构设计；
4. 类图、顺序图设计；
5. 数据库设计；
6. 详细设计；
7. 代码实现。

在 AI Agent 流行之后，软件开发流程正在发生变化：

```text
传统流程：
人类分析需求 → 人类画UML → 人类设计架构 → 人类写代码 → 人类测试

AI时代流程：
人类提供目标与约束
→ Agent 辅助提出澄清问题
→ Agent 辅助生成需求规格、用例、UML、架构、数据库、测试计划
→ 人类审查和修订 Specs
→ 冻结 Specs Baseline
→ Agent 按任务实现代码
→ 测试验证
→ 人类审查 Git diff
→ 提交和复盘
```

因此，本实验的重点不再只是“画图”和“写代码”，而是训练学生：

```text
用规范指挥 Agent，
用 UML 表达设计，
用测试约束实现，
用 Git 审查变更，
用工程流程管理 AI。
```

---

## 3. 实验总体目标

通过本实验，学生应掌握：

1. 使用 Agent 辅助进行需求分析和澄清。
2. 使用 OpenSpec 组织需求、用例、领域模型、架构、数据库、API、测试和任务文档。
3. 使用 PlantUML 或 Mermaid 表达用例图、类图、包图、顺序图。
4. 使用 Spec-Kit 的“开发宪法”约束 Agent 行为。
5. 使用简化统一过程组织实验阶段。
6. 使用分层架构和 MVC 模式完成系统设计。
7. 使用 Agent 根据冻结后的 Specs 实现系统代码。
8. 使用自动化测试验证设计与实现的一致性。
9. 使用 Git 管理需求、设计、代码和测试的演进过程。
10. 理解 AI 时代架构师与开发者的新职责。

---

## 4. 新旧实验要求对照

| 原实验要求 | AI时代新实验要求 |
|---|---|
| 人工识别参与者和用例 | Agent 辅助提出澄清问题并生成用例规格，人类审查 |
| 用 UML 工具建立用例模型 | 用 PlantUML/Mermaid 生成可版本管理的 UML-as-Spec |
| 建立领域类图 | Agent 辅助生成领域模型和类图，人类校正业务概念 |
| 设计分层架构和 MVC | Agent 辅助生成 architecture.md 和包图 |
| 设计类、接口和交互 | Agent 辅助生成设计类图、顺序图、接口职责 |
| 数据库设计 | Agent 根据领域模型生成数据库设计，人类审查约束 |
| 详细设计 | Agent 辅助生成算法、流程、异常处理、DTO、服务方法 |
| 代码实现 | Agent 按任务实现，测试验证，人类审查 diff |
| 实验报告 | 提交 Specs、UML、代码、测试、AI 使用记录和复盘 |

---

## 5. 推荐技术路线

本实验可以选择 Java 或 Python 实现。

### 5.1 Java 推荐技术栈

```text
Java 17
Spring Boot 3.x
Spring Web
Spring Data JPA
H2 / MySQL
Validation
JUnit 5
MockMvc
PlantUML
Maven
Claude Code / Codex / OpenCode
```

### 5.2 Python 推荐技术栈

```text
Python 3.10+
FastAPI
SQLAlchemy
SQLite
Pydantic
pytest
httpx
PlantUML / Mermaid
Claude Code / Codex / OpenCode
```

如果本课程更强调面向对象设计、分层架构、接口、类图和设计模式，推荐使用 Java Spring Boot。

---

## 6. 项目推荐目录结构

```text
library-management-ai/
  specs/
    00-project-brief.md
    01-clarifying-questions.md
    02-requirements.md
    03-use-cases.md
    04-use-case-model.puml
    05-domain-model.md
    06-domain-class-diagram.puml
    07-architecture.md
    08-package-diagram.puml
    09-design-model.md
    10-sequence-borrow-book.puml
    11-sequence-return-book.puml
    12-sequence-reserve-book.puml
    13-database-design.md
    14-api-spec.md
    15-test-plan.md
    16-tasks.md
    17-risk-analysis.md
    18-review-checklist.md
    19-ai-usage-log.md
    constitution.md
  src/
  tests/
  README.md
```

说明：

| 文件 | 作用 |
|---|---|
| 00-project-brief.md | 人类提供的项目背景和约束 |
| 01-clarifying-questions.md | Agent 提出的需求澄清问题及人类回答 |
| 02-requirements.md | 功能需求和非功能需求 |
| 03-use-cases.md | 用例文本 |
| 04-use-case-model.puml | 用例图 |
| 05-domain-model.md | 领域模型说明 |
| 06-domain-class-diagram.puml | 领域类图 |
| 07-architecture.md | 架构设计 |
| 08-package-diagram.puml | 包图 |
| 09-design-model.md | 详细设计说明 |
| 10-12 sequence diagrams | 关键用例顺序图 |
| 13-database-design.md | 数据库设计 |
| 14-api-spec.md | API 或服务接口规范 |
| 15-test-plan.md | 测试计划 |
| 16-tasks.md | Agent 可执行任务拆解 |
| 17-risk-analysis.md | 风险分析 |
| 18-review-checklist.md | 人工审查清单 |
| 19-ai-usage-log.md | AI 使用记录 |
| constitution.md | Agent 行为约束和开发宪法 |

---

## 7. 实验总体流程

本实验采用“AI增强的简化统一过程”。

```text
初始阶段 Inception
  → 项目愿景、范围、参与者、主要用例、非目标

细化阶段 Elaboration
  → 需求规格、用例模型、领域模型、架构设计、风险分析

构造阶段 Construction
  → 详细设计、数据库设计、任务拆解、Agent编码实现、自动化测试

交付阶段 Transition
  → 验收测试、文档整理、AI使用记录、答辩复盘
```

对应操作：

```text
第 1 步：创建项目和 specs 目录
第 2 步：编写 Project Brief
第 3 步：让 Agent 提出澄清问题
第 4 步：人类回答澄清问题
第 5 步：Agent 生成需求规格
第 6 步：Agent 生成用例文本和用例图
第 7 步：Agent 生成领域模型和领域类图
第 8 步：Agent 生成架构设计和包图
第 9 步：Agent 生成详细设计和顺序图
第 10 步：Agent 生成数据库设计
第 11 步：Agent 生成 API/服务接口规范
第 12 步：Agent 生成测试计划
第 13 步：Agent 生成任务拆解
第 14 步：人类审查全部 Specs
第 15 步：冻结 Specs Baseline
第 16 步：Agent 按任务实现代码
第 17 步：运行测试
第 18 步：人工审查 Git diff
第 19 步：提交代码
第 20 步：实验报告与答辩
```

---

## 8. 图书管理系统需求范围

### 8.1 基础业务

图书馆服务对象包括：

- 学生；
- 教师；
- 图书管理员；
- 系统管理员。

读者需要先注册账号，并由系统管理员办理借阅证。

读者可以：

- 查询图书；
- 查询自己的借阅信息；
- 通过网络预约图书。

借阅和归还操作由图书管理员代理完成。

图书管理员可以：

- 办理借书；
- 办理还书；
- 查询读者借阅信息。

系统管理员可以：

- 办理借阅证；
- 删除借阅证；
- 添加管理员；
- 删除管理员；
- 添加图书；
- 删除图书；
- 添加标题信息；
- 删除标题信息。

系统需要支持：

- 不同读者类型有不同借阅数量和期限；
- 不同馆藏类型有不同罚款规则；
- 超期罚款；
- 预约；
- 查询。

---

## 9. 推荐核心领域对象

初步建议包括：

```text
Account
Reader
Student
Teacher
BorrowCard
Librarian
SystemAdmin
BookTitle
LibraryItem
BookCopy
Magazine
Thesis
Loan
Reservation
FineRule
FineRecord
BorrowPolicy
```

可以根据教学复杂度适当简化，但至少应保留：

```text
Reader
BorrowCard
Librarian
SystemAdmin
BookTitle
LibraryItem
Loan
Reservation
FineRule
```

---

## 10. 推荐核心用例

### 10.1 读者相关

```text
UC-001 注册账号
UC-002 查询图书
UC-003 查询借阅信息
UC-004 预约图书
```

### 10.2 图书管理员相关

```text
UC-101 办理借书
UC-102 办理还书
UC-103 查询读者借阅信息
```

### 10.3 系统管理员相关

```text
UC-201 办理借阅证
UC-202 删除借阅证
UC-203 添加图书管理员
UC-204 删除图书管理员
UC-205 添加图书标题信息
UC-206 删除图书标题信息
UC-207 添加馆藏副本
UC-208 删除馆藏副本
UC-209 维护借阅规则和罚款规则
```

---

## 11. 开发宪法 constitution.md 示例

```markdown
# 图书管理系统开发宪法

## 1. Specs 优先原则

任何代码实现前，必须先完成需求、用例、领域模型、架构、数据库、测试和任务拆解文档。

## 2. Agent 起草，人类确认原则

Agent 可以生成规格初稿，但所有规格必须经过学生人工审查后才能作为实现依据。

## 3. UML-as-Spec 原则

用例图、类图、包图、顺序图必须使用 PlantUML 或 Mermaid 文本格式保存到 specs 目录，纳入 Git 管理。

## 4. Baseline 原则

Specs 审查通过后必须建立 baseline。实现阶段 Agent 不得擅自修改 specs。

## 5. 分层架构原则

系统必须采用分层架构，至少包括表现层、应用服务层、领域层、基础设施层或持久化层。

## 6. MVC 原则

Web 或界面层应遵循 MVC 或类似分离思想，不得把业务规则写入 Controller。

## 7. 权限原则

图书管理员、系统管理员和读者权限必须区分。

## 8. 业务规则集中原则

借阅数量、借阅期限、超期罚款等规则应集中在 Policy 或 Service 中实现，不得散落在界面层。

## 9. 测试闭环原则

核心用例必须有自动化测试，至少覆盖借书、还书、预约、超期罚款和权限失败场景。

## 10. Git 审查原则

Agent 修改代码后，学生必须查看 git diff，再决定是否提交。

## 11. AI 使用记录原则

每次使用 Agent 生成 specs、UML、代码或测试，都必须记录在 ai-usage-log.md 中。
```

---

## 12. 实验交付物

学生最终提交：

```text
1. specs 全部文档
2. PlantUML/Mermaid 图文件
3. 源代码
4. 自动化测试
5. README.md
6. ai-usage-log.md
7. Git commit 记录
8. 实验报告
```

---

## 13. AI时代实验核心理念

本实验不是取消 UML，也不是让 AI 代替学生完成设计，而是让学生学会：

```text
用 Agent 辅助分析，
用 UML 表达结构，
用 Specs 固化设计，
用测试约束实现，
用 Git 管理演进，
用人工审查承担责任。
```
