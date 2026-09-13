# AI时代图书管理系统 Agent 提示词手册

## 1. 使用原则

使用 Claude Code、Codex、OpenCode 等 Agent 时，必须遵守：

```text
1. 先读 specs，再行动。
2. 先输出计划，再修改文件。
3. 一次只做一个任务。
4. 不得擅自修改 baseline specs。
5. 修改后必须运行测试。
6. 测试失败先解释原因，再最小修复。
7. 人类必须审查 git diff。
```

---

## 2. Agent 初始化 Prompt

```text
你是本项目的编码 Agent。

请先阅读：
- specs/constitution.md
- specs/00-project-brief.md
- specs/02-requirements.md
- specs/03-use-cases.md
- specs/05-domain-model.md
- specs/07-architecture.md
- specs/09-design-model.md
- specs/13-database-design.md
- specs/15-test-plan.md
- specs/16-tasks.md

请不要修改任何文件。

请完成：
1. 总结项目目标。
2. 总结核心参与者和用例。
3. 总结核心领域对象。
4. 总结架构约束。
5. 总结测试要求。
6. 给出建议实现顺序。
7. 等待我确认后再开始修改代码。
```

---

## 3. 需求澄清 Prompt

```text
你是资深软件需求分析师。

请阅读 specs/00-project-brief.md。

现在不要生成正式需求文档，只提出澄清问题。

要求：
1. 问题覆盖参与者、用例、借阅规则、罚款规则、预约规则、权限、数据、异常场景、测试和教学复杂度。
2. 问题数量 20 到 30 个。
3. 按类别组织。
4. 写入 specs/01-clarifying-questions.md。
5. 文件末尾预留“人类回答”区域。
6. 不要修改其他文件。
```

---

## 4. 需求规格生成 Prompt

```text
请根据：
- specs/00-project-brief.md
- specs/01-clarifying-questions.md
- specs/constitution.md

生成 specs/02-requirements.md。

要求：
1. 包含项目目标、参与者、功能需求、非功能需求、业务规则。
2. 功能需求编号为 FR-001、FR-002。
3. 业务规则编号为 BR-001、BR-002。
4. 每个功能需求必须有可验证验收标准。
5. 不要加入明确暂不实现的功能。
6. 如果存在不确定点，写入“待确认问题”。
7. 只修改 specs/02-requirements.md。
```

---

## 5. 用例文本生成 Prompt

```text
请根据 specs/02-requirements.md 生成 specs/03-use-cases.md。

要求：
1. 识别所有参与者和核心用例。
2. 每个用例包含：
   - 用例编号
   - 用例名称
   - 主要参与者
   - 次要参与者
   - 前置条件
   - 后置条件
   - 基本事件流
   - 备选事件流
   - 异常事件流
   - 关联需求编号
3. 重点详细描述办理借书、办理还书、预约图书、办理借阅证和计算超期罚款。
4. 只修改 specs/03-use-cases.md。
```

---

## 6. 用例图生成 Prompt

```text
请根据 specs/03-use-cases.md 生成 PlantUML 用例图，写入 specs/04-use-case-model.puml。

要求：
1. 使用 @startuml 和 @enduml。
2. 参与者至少包括 Reader、Student、Teacher、Librarian、SystemAdmin。
3. Student 和 Teacher 泛化自 Reader。
4. 准确表达 include、extend、泛化关系。
5. 不要修改其他文件。
```

---

## 7. 领域模型生成 Prompt

```text
请根据 specs/02-requirements.md 和 specs/03-use-cases.md 生成 specs/05-domain-model.md。

要求：
1. 识别核心领域类。
2. 每个类包含职责、属性、行为、约束、关系。
3. 必须包含 Reader、BorrowCard、BookTitle、LibraryItem、Loan、Reservation、BorrowPolicy、FineRule、FineRecord。
4. 必须体现不同读者类型和不同借出物类型。
5. 区分实体、值对象、领域服务和策略对象。
6. 只修改 specs/05-domain-model.md。
```

---

## 8. 领域类图生成 Prompt

```text
请根据 specs/05-domain-model.md 生成 PlantUML 领域类图，写入 specs/06-domain-class-diagram.puml。

要求：
1. 表达类、属性、核心方法。
2. 表达继承、关联、聚合或组合。
3. 不要加入 Controller、Repository、DTO 等设计类。
4. 不要修改其他文件。
```

---

## 9. 架构设计 Prompt

```text
请根据 requirements、use-cases、domain-model 和 constitution 生成 specs/07-architecture.md。

要求：
1. 采用分层架构和 MVC。
2. 说明各层职责。
3. 说明主要模块。
4. 说明权限控制、异常处理、事务边界。
5. 说明业务规则放置位置。
6. 说明使用的设计模式。
7. 只修改 specs/07-architecture.md。
```

---

## 10. 包图 Prompt

```text
请根据 specs/07-architecture.md 生成 PlantUML 包图，写入 specs/08-package-diagram.puml。

要求：
1. 表达分层架构。
2. 表达 presentation、application、domain、infrastructure、dto、test。
3. Controller 不得直接依赖 Repository。
4. Infrastructure 可以实现 Repository 接口。
```

---

## 11. 数据库设计 Prompt

```text
请根据 specs/05-domain-model.md 和 specs/07-architecture.md 生成 specs/13-database-design.md。

要求：
1. 找出需要持久化的类。
2. 转换为关系模型。
3. 每张表列出字段、类型、主键、外键、唯一约束、默认值。
4. 说明索引设计。
5. 说明继承映射策略。
6. 只修改 specs/13-database-design.md。
```

---

## 12. 详细设计 Prompt

```text
请根据 requirements、use-cases、domain-model、architecture 和 database-design 生成 specs/09-design-model.md。

要求：
1. 以用例为基本单元进行详细设计。
2. 每个用例列出 Controller、Application Service、Domain Service、Entity、Repository、DTO、异常和事务边界。
3. 说明设计模式使用位置。
4. 只修改 specs/09-design-model.md。
```

---

## 13. 顺序图 Prompt：办理借书

```text
请根据用例文本和详细设计生成办理借书顺序图，写入 specs/10-sequence-borrow-book.puml。

要求：
1. 使用 PlantUML。
2. 包含 Controller、Service、Repository、Policy、Entity。
3. 表达正常流程和异常流程。
4. 使用 alt/else 表达借阅证无效、超过数量、有超期未还、图书不可借等分支。
```

---

## 14. 顺序图 Prompt：办理还书

```text
请根据用例文本和详细设计生成办理还书顺序图，写入 specs/11-sequence-return-book.puml。

要求：
1. 表达正常还书流程。
2. 表达非本馆藏书、未找到借阅记录、超期罚款分支。
3. 使用 alt/else。
```

---

## 15. API 规范 Prompt

```text
请根据 requirements、use-cases、design-model 和 database-design 生成 specs/14-api-spec.md。

要求：
1. 使用 REST API 或 Application Service 方法签名。
2. 每个接口包含请求、响应、权限、成功场景、失败场景。
3. 覆盖注册、办证、查询、借书、还书、预约、管理维护。
```

---

## 16. 测试计划 Prompt

```text
请根据 requirements、use-cases 和 api-spec 生成 specs/15-test-plan.md。

要求：
1. 每个测试用例包含编号、目标、前置条件、输入、步骤、预期结果。
2. 覆盖正常路径、异常路径、权限失败、业务规则失败。
3. 区分单元测试和集成测试。
```

---

## 17. 任务拆解 Prompt

```text
请根据所有 specs 生成 specs/16-tasks.md。

要求：
1. 每个任务适合 Agent 一次完成。
2. 每个任务包含目标、输入规格、允许修改文件、不允许修改文件、实现要求、验收标准、建议测试。
3. 不要生成“实现整个系统”这种大任务。
4. baseline 后不得修改 specs。
```

---

## 18. 编码任务 Prompt 模板

```text
请根据 specs/16-tasks.md 中的 TASK-XXX 实现本任务。

开始前请阅读：
- specs/constitution.md
- specs/03-use-cases.md
- specs/05-domain-model.md
- specs/09-design-model.md
- specs/13-database-design.md
- specs/15-test-plan.md

要求：
1. 先输出实现计划，不要修改代码。
2. specs 已 baseline，不得修改 specs。
3. 只允许修改 TASK-XXX 指定文件。
4. 实现后运行测试。
5. 测试失败时先解释原因，再最小修复。
```

---

## 19. Git 审查命令

```bash
git status
git diff
git log --oneline
```

如果 Agent 修改了不该修改的文件：

```bash
git checkout -- path/to/file
```

如果需要完全回退本次修改：

```bash
git reset --hard HEAD
```

---

## 20. AI 使用记录模板

```markdown
## 第 X 次使用

### 使用工具

Claude Code / Codex / OpenCode

### 使用阶段

需求分析 / UML建模 / 架构设计 / 详细设计 / 编码实现 / 测试生成

### 输入 Prompt 摘要

简述本次给 Agent 的任务。

### Agent 修改文件

- specs/xxx.md
- src/xxx.java

### 输出摘要

Agent 生成或修改了哪些内容。

### 人工审查结果

发现的问题和确认结果。

### 测试结果

通过 / 未通过 / 修复后通过。

### Git 提交

commit message
```
