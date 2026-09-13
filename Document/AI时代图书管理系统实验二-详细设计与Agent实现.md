# 实验二：AI时代图书管理系统的详细设计与 Agent 辅助实现

## 一、实验目的

在实验一的需求、用例、领域模型、架构设计和数据库设计基础上，完成图书管理系统的详细设计、接口设计、测试设计和代码实现。

通过本实验，学生应掌握：

1. 从用例场景推导设计类、接口和交互。
2. 使用 Agent 辅助生成详细设计。
3. 使用顺序图表达关键用例流程。
4. 使用设计模式实现借阅规则和罚款规则。
5. 使用数据库设计指导持久化实现。
6. 使用测试计划验证设计合理性。
7. 使用 Agent 按任务实现代码。
8. 使用 Git diff 审查 Agent 修改。

---

## 二、实验前提

学生应已经完成实验一，并至少拥有以下 baseline 文档：

```text
specs/02-requirements.md
specs/03-use-cases.md
specs/05-domain-model.md
specs/06-domain-class-diagram.puml
specs/07-architecture.md
specs/08-package-diagram.puml
specs/13-database-design.md
specs/constitution.md
```

确认 baseline：

```bash
git tag
```

应能看到：

```text
experiment1-specs-baseline-v1
```

---

## 三、实验二总体流程

```text
第 1 步：生成详细设计模型 design-model.md
第 2 步：生成关键用例顺序图
第 3 步：生成 API 或服务接口规范
第 4 步：生成测试计划
第 5 步：生成 Agent 编码任务拆解
第 6 步：人工审查详细设计 Specs
第 7 步：冻结实验二 Specs baseline
第 8 步：Agent 初始化项目代码
第 9 步：Agent 按任务实现代码
第 10 步：运行自动化测试
第 11 步：人工审查 Git diff
第 12 步：提交与复盘
```

---

## 四、步骤1：生成详细设计模型 design-model.md

Prompt：

```text
请根据以下文件生成 specs/09-design-model.md：

- specs/02-requirements.md
- specs/03-use-cases.md
- specs/05-domain-model.md
- specs/07-architecture.md
- specs/13-database-design.md

要求：
1. 以用例为基本单元进行详细设计。
2. 至少详细设计以下用例：
   - 办理借书
   - 办理还书
   - 预约图书
   - 查询借阅信息
   - 办理借阅证
   - 添加图书标题信息
   - 添加馆藏副本
   - 计算超期罚款
3. 对每个用例列出：
   - Controller 或界面入口
   - Application Service
   - Domain Service
   - Entity / Aggregate
   - Repository
   - DTO
   - 异常
   - 事务边界
4. 说明每个类的职责。
5. 说明设计模式使用位置。
6. 只修改 specs/09-design-model.md。
```

人工审查重点：

```text
1. Controller 是否只负责接收请求和返回响应？
2. 借书流程是否在 Application Service 中组织？
3. 借阅数量和期限检查是否在 BorrowPolicy 或服务中？
4. 罚款计算是否在 FineRule 或 FineService 中？
5. Repository 是否只负责持久化？
6. 是否为关键异常定义了错误类型？
```

提交：

```bash
git add specs/09-design-model.md
git commit -m "generate detailed design model"
```

---

## 五、步骤2：生成办理借书顺序图

Prompt：

```text
请根据 specs/03-use-cases.md 和 specs/09-design-model.md 生成办理借书用例的 PlantUML 顺序图，写入 specs/10-sequence-borrow-book.puml。

要求：
1. 参与对象至少包括：
   - LibrarianController
   - CirculationService
   - BorrowCardRepository
   - ReaderRepository
   - LoanRepository
   - LibraryItemRepository
   - BorrowPolicyService
   - Reader
   - LibraryItem
   - Loan
2. 表达正常流程。
3. 表达借阅证无效异常。
4. 表达超过借阅数量异常。
5. 表达存在超期未还异常。
6. 表达图书不可借异常。
7. 使用 alt/else 表达分支。
8. 不要修改其他文件。
```

提交：

```bash
git add specs/10-sequence-borrow-book.puml
git commit -m "generate borrow book sequence diagram"
```

---

## 六、步骤3：生成办理还书顺序图

Prompt：

```text
请根据 specs/03-use-cases.md 和 specs/09-design-model.md 生成办理还书用例的 PlantUML 顺序图，写入 specs/11-sequence-return-book.puml。

要求：
1. 参与对象至少包括：
   - LibrarianController
   - CirculationService
   - LibraryItemRepository
   - LoanRepository
   - FineService
   - FineRuleService
   - LibraryItem
   - Loan
   - FineRecord
2. 表达正常还书流程。
3. 表达图书不是本馆藏书异常。
4. 表达找不到借阅记录异常。
5. 表达超期罚款计算流程。
6. 使用 alt/else 表达分支。
```

提交：

```bash
git add specs/11-sequence-return-book.puml
git commit -m "generate return book sequence diagram"
```

---

## 七、步骤4：生成预约图书顺序图

Prompt：

```text
请根据 specs/03-use-cases.md 和 specs/09-design-model.md 生成预约图书用例的 PlantUML 顺序图，写入 specs/12-sequence-reserve-book.puml。

要求：
1. 参与对象至少包括：
   - ReaderController
   - ReservationService
   - ReaderRepository
   - BookTitleRepository
   - ReservationRepository
   - Reader
   - BookTitle
   - Reservation
2. 表达正常预约流程。
3. 表达读者不存在异常。
4. 表达标题不存在异常。
5. 表达重复预约异常。
6. 表达预约排队顺序。
```

提交：

```bash
git add specs/12-sequence-reserve-book.puml
git commit -m "generate reserve book sequence diagram"
```

---

## 八、步骤5：生成 API 或服务接口规范

如果项目实现为 Web 系统，建议生成 REST API 规范。  
如果项目实现为桌面程序，也应生成应用服务接口规范。

Prompt：

```text
请根据以下文件生成 specs/14-api-spec.md：

- specs/02-requirements.md
- specs/03-use-cases.md
- specs/09-design-model.md
- specs/13-database-design.md

要求：
1. 若采用 Web 实现，使用 REST API 格式。
2. 若采用非 Web 实现，也要列出 Application Service 方法签名。
3. 每个接口包含：
   - 方法或路径
   - 请求参数
   - 响应结果
   - 权限要求
   - 成功场景
   - 失败场景
4. 必须覆盖：
   - 注册读者
   - 办理借阅证
   - 查询图书
   - 办理借书
   - 办理还书
   - 查询借阅信息
   - 预约图书
   - 添加图书标题
   - 添加馆藏副本
   - 维护规则
5. 只修改 specs/14-api-spec.md。
```

REST API 示例：

```text
POST /api/circulation/borrow
POST /api/circulation/return
GET  /api/readers/{reader_id}/loans
POST /api/reservations
POST /api/admin/borrow-cards
POST /api/admin/book-titles
POST /api/admin/library-items
```

提交：

```bash
git add specs/14-api-spec.md
git commit -m "generate api spec"
```

---

## 九、步骤6：生成测试计划 test-plan.md

Prompt：

```text
请根据以下文件生成 specs/15-test-plan.md：

- specs/02-requirements.md
- specs/03-use-cases.md
- specs/09-design-model.md
- specs/14-api-spec.md

要求：
1. 每个测试用例编号为 TC-001、TC-002。
2. 每个测试用例包含：
   - 测试目标
   - 前置条件
   - 输入
   - 操作步骤
   - 预期结果
3. 至少覆盖：
   - 注册读者成功
   - 办理借阅证成功
   - 借阅证无效时借书失败
   - 借书成功
   - 超过借阅数量时借书失败
   - 存在超期未还图书时借书失败
   - 图书不可借时借书失败
   - 还书成功
   - 归还非本馆藏书失败
   - 超期还书生成罚款
   - 查询借阅信息成功
   - 预约图书成功
   - 重复预约失败
   - 普通读者不能执行管理员操作
4. 说明哪些测试是单元测试，哪些是集成测试。
5. 只修改 specs/15-test-plan.md。
```

提交：

```bash
git add specs/15-test-plan.md
git commit -m "generate test plan"
```

---

## 十、步骤7：生成任务拆解 tasks.md

Prompt：

```text
请根据所有 specs 生成 specs/16-tasks.md。

要求：
1. 任务粒度适合编码 Agent 一次完成。
2. 每个任务包含：
   - 任务编号
   - 任务目标
   - 输入规格
   - 允许修改文件
   - 不允许修改文件
   - 实现要求
   - 验收标准
   - 建议测试
3. 任务顺序建议：
   - 初始化项目结构
   - 实现领域实体
   - 实现 Repository
   - 实现借阅规则策略
   - 实现罚款规则策略
   - 实现读者和借阅证管理
   - 实现图书标题和馆藏管理
   - 实现借书
   - 实现还书
   - 实现预约
   - 实现查询
   - 实现管理员权限
   - 完善测试
4. 明确要求实现阶段不得修改 baseline specs。
5. 只修改 specs/16-tasks.md。
```

提交：

```bash
git add specs/16-tasks.md
git commit -m "generate implementation tasks"
```

---

## 十一、步骤8：人工审查详细设计 Specs

执行：

```bash
git diff HEAD~6..HEAD
```

重点审查：

```text
1. 顺序图是否与用例文本一致？
2. API 是否覆盖核心用例？
3. 测试计划是否覆盖异常流程？
4. 任务拆解是否过大？
5. 是否将业务规则放在了正确层？
6. 是否体现了 Strategy、Repository、Service Layer 等设计模式？
7. 是否与数据库设计一致？
```

修订 Prompt：

```text
请根据以下人工审查意见修订详细设计 specs，不要修改代码：

1. 办理借书顺序图缺少检查超期未还图书分支。
2. test-plan.md 缺少图书不可借时借书失败测试。
3. tasks.md 中“实现借阅模块”任务太大，请拆成借书、还书、查询三个任务。
4. api-spec.md 中缺少权限说明。

请说明修改了哪些文件和原因。
```

提交：

```bash
git add specs
git commit -m "revise detailed design specs after review"
```

---

## 十二、步骤9：冻结实验二 Specs

```bash
git add specs
git commit -m "baseline experiment 2 detailed design specs"
git tag experiment2-specs-baseline-v1
```

---

## 十三、步骤10：创建代码项目

### Java Spring Boot 版本

使用 Spring Initializr：

```text
Project: Maven
Language: Java
Spring Boot: 3.x
Java: 17
Dependencies:
- Spring Web
- Spring Data JPA
- H2 Database
- Validation
- Spring Security Crypto
```

推荐包结构：

```text
src/main/java/com/example/library/
  LibraryApplication.java
  presentation/
  application/
  domain/
    reader/
    card/
    catalog/
    circulation/
    reservation/
    fine/
    admin/
  infrastructure/
  dto/
  exception/
src/test/java/com/example/library/
```

### Python FastAPI 版本

```text
app/
  main.py
  database.py
  routers/
  services/
  domain/
  repositories/
  schemas/
tests/
```

---

## 十四、步骤11：Agent 初始化代码项目

Prompt：

```text
你是本项目的编码 Agent。

请先阅读：
- specs/constitution.md
- specs/02-requirements.md
- specs/03-use-cases.md
- specs/05-domain-model.md
- specs/07-architecture.md
- specs/09-design-model.md
- specs/13-database-design.md
- specs/14-api-spec.md
- specs/15-test-plan.md
- specs/16-tasks.md

请不要修改任何文件。

请完成：
1. 总结项目目标。
2. 总结核心架构约束。
3. 总结核心领域对象。
4. 总结关键用例流程。
5. 总结任务实现顺序。
6. 等待我确认后再开始编码。
```

学生检查 Agent 是否提到：

```text
1. 分层架构
2. MVC
3. 借书必须由图书管理员代理
4. 借书前验证借阅证
5. 借书前检查借阅数量和超期未还
6. 还书时计算超期罚款
7. 不同读者类型规则不同
8. 不同借出物类型罚款不同
9. specs baseline 后不得修改
```

---

## 十五、步骤12：实现 TASK-001 初始化项目结构

Prompt：

```text
请根据 specs/16-tasks.md 中的 TASK-001 初始化项目结构。

要求：
1. 开始前先输出实现计划，不要修改代码。
2. specs 已经 baseline，不得修改 specs。
3. 只创建架构要求的包和基础启动类。
4. 不要实现业务逻辑。
5. 实现后运行基础测试命令。
```

确认后：

```text
计划可以。请实现 TASK-001，并运行测试。
```

Java：

```bash
mvn test
```

Python：

```bash
pytest
```

提交：

```bash
git add .
git commit -m "complete TASK-001 initialize project structure"
```

---

## 十六、步骤13：实现领域实体

Prompt：

```text
请根据 specs/05-domain-model.md 和 specs/13-database-design.md 实现领域实体。

要求：
1. 开始前先输出实现计划。
2. 只实现领域实体和必要枚举。
3. 不要实现 Controller。
4. 不要实现业务流程。
5. 必须体现：
   - Reader
   - BorrowCard
   - BookTitle
   - LibraryItem
   - Loan
   - Reservation
   - BorrowPolicy
   - FineRule
   - FineRecord
6. 如采用 Java，可使用 JPA Entity。
7. 如采用 Python，可使用 SQLAlchemy Model。
8. 实现后运行测试。
```

审查重点：

```text
1. 是否有借阅证唯一号？
2. 是否有馆藏副本唯一条码？
3. Loan 是否有 dueDate、returnDate、status？
4. Reservation 是否有 createdAt 和 status？
5. BorrowPolicy 是否能表达不同读者类型规则？
6. FineRule 是否能表达不同借出物类型规则？
```

提交：

```bash
git add .
git commit -m "complete domain entities"
```

---

## 十七、步骤14：实现借阅规则策略

Prompt：

```text
请根据 specs/09-design-model.md 实现借阅规则策略。

要求：
1. 使用 Strategy 或可替换策略对象实现不同读者类型借阅规则。
2. 至少支持：
   - UNDERGRADUATE：最多 5 本，30 天
   - GRADUATE：最多 10 本，60 天
   - DOCTOR：最多 15 本，90 天
   - TEACHER：最多 20 本，90 天
3. 提供方法：
   - getMaxBorrowCount(readerType)
   - getBorrowDays(readerType)
   - canBorrow(reader, currentLoans)
4. 添加单元测试。
```

提交：

```bash
git add .
git commit -m "complete borrow policy strategy"
```

---

## 十八、步骤15：实现罚款规则策略

Prompt：

```text
请根据 specs/09-design-model.md 实现罚款规则策略。

要求：
1. 使用 Strategy 或规则表实现不同借出物类型罚款规则。
2. 至少支持：
   - CHINESE_BOOK
   - FOREIGN_BOOK
   - CHINESE_MAGAZINE
   - FOREIGN_MAGAZINE
   - THESIS
3. 提供方法：
   - calculateFine(itemType, overdueDays)
4. overdueDays <= 0 时罚款为 0。
5. 添加单元测试。
```

提交：

```bash
git add .
git commit -m "complete fine rule strategy"
```

---

## 十九、步骤16：实现办理借阅证

Prompt：

```text
请根据用例“办理借阅证”和 api-spec 实现借阅证管理功能。

要求：
1. 只有系统管理员可以办理借阅证。
2. 读者必须存在。
3. 同一读者不能拥有多个有效借阅证。
4. 借阅证号必须唯一。
5. 添加集成测试：
   - 办理成功
   - 读者不存在失败
   - 重复办理失败
   - 非系统管理员失败
```

提交：

```bash
git add .
git commit -m "complete borrow card management"
```

---

## 二十、步骤17：实现图书标题和馆藏管理

Prompt：

```text
请根据用例“添加图书标题信息”和“添加馆藏副本”实现图书管理功能。

要求：
1. 只有系统管理员可以添加标题和馆藏副本。
2. BookTitle 表示题名、作者、ISBN、出版社、类型。
3. LibraryItem 表示具体馆藏副本，有唯一 barcode。
4. 副本状态至少包括 AVAILABLE、BORROWED、RESERVED、REMOVED。
5. 添加测试：
   - 添加标题成功
   - 添加副本成功
   - 重复 barcode 失败
   - 普通读者无权限失败
```

提交：

```bash
git add .
git commit -m "complete catalog management"
```

---

## 二十一、步骤18：实现办理借书

Prompt：

```text
请根据以下 specs 实现办理借书功能：

- specs/03-use-cases.md 中办理借书
- specs/10-sequence-borrow-book.puml
- specs/09-design-model.md
- specs/15-test-plan.md

要求：
1. 只有图书管理员可以办理借书。
2. 输入借阅证号和馆藏条码。
3. 验证借阅证存在且有效。
4. 检查读者当前未归还数量是否超过规则。
5. 检查读者是否有超期未还图书。
6. 验证馆藏副本存在且可借。
7. 创建 Loan。
8. 设置 dueDate。
9. 更新 LibraryItem 状态为 BORROWED。
10. 添加测试：
    - 借书成功
    - 借阅证无效失败
    - 超过数量失败
    - 有超期未还失败
    - 图书不可借失败
```

提交：

```bash
git add .
git commit -m "complete borrow book use case"
```

---

## 二十二、步骤19：实现办理还书

Prompt：

```text
请根据以下 specs 实现办理还书功能：

- specs/03-use-cases.md 中办理还书
- specs/11-sequence-return-book.puml
- specs/09-design-model.md
- specs/15-test-plan.md

要求：
1. 只有图书管理员可以办理还书。
2. 输入馆藏条码。
3. 验证馆藏副本存在。
4. 查找未归还 Loan。
5. 设置 returnDate。
6. 更新 Loan 状态为 RETURNED。
7. 更新 LibraryItem 状态。
8. 如果超期，生成 FineRecord。
9. 添加测试：
   - 还书成功
   - 非本馆藏书失败
   - 未找到借阅记录失败
   - 超期还书生成罚款
```

提交：

```bash
git add .
git commit -m "complete return book use case"
```

---

## 二十三、步骤20：实现预约图书

Prompt：

```text
请根据以下 specs 实现预约图书功能：

- specs/03-use-cases.md 中预约图书
- specs/12-sequence-reserve-book.puml
- specs/09-design-model.md
- specs/15-test-plan.md

要求：
1. 读者可以预约图书标题。
2. 读者必须存在。
3. 图书标题必须存在。
4. 同一读者不能重复预约同一标题的有效预约。
5. 预约按 createdAt 排队。
6. 添加测试：
   - 预约成功
   - 重复预约失败
   - 读者不存在失败
   - 标题不存在失败
```

提交：

```bash
git add .
git commit -m "complete reservation use case"
```

---

## 二十四、步骤21：实现查询借阅信息

Prompt：

```text
请根据用例“查询借阅信息”实现查询功能。

要求：
1. 读者可以查询自己的借阅信息。
2. 图书管理员可以查询任意读者借阅信息。
3. 返回当前借阅、历史借阅和超期状态。
4. 添加测试：
   - 读者查询自己成功
   - 图书管理员查询成功
   - 普通读者查询他人失败
```

提交：

```bash
git add .
git commit -m "complete loan query use case"
```

---

## 二十五、步骤22：完善测试

Prompt：

```text
请根据 specs/15-test-plan.md 检查当前测试覆盖情况。

请先输出测试覆盖分析，不要修改代码。

要求：
1. 列出已覆盖测试用例。
2. 列出未覆盖测试用例。
3. 给出补充测试计划。
4. 等我确认后再补充测试。
```

确认后：

```text
请补充未覆盖测试，并运行完整测试。
```

提交：

```bash
git add .
git commit -m "complete test coverage"
```

---

## 二十六、步骤23：生成 README

Prompt：

```text
请根据当前项目和 specs 生成 README.md。

要求包含：
1. 项目简介。
2. 技术栈。
3. 架构说明。
4. 目录结构。
5. 启动方式。
6. 测试方式。
7. 核心用例。
8. 核心 API 或服务接口。
9. UML 文档说明。
10. Agent 使用说明。
11. 不要编造不存在的功能。
```

提交：

```bash
git add README.md
git commit -m "add README"
```

---

## 二十七、步骤24：填写 ai-usage-log.md

模板：

```markdown
## 第 X 次使用

### 使用工具

Claude Code / Codex / OpenCode

### 使用阶段

详细设计 / 代码实现 / 测试生成

### 使用任务

实现办理借书用例

### 输入 Prompt 摘要

要求 Agent 根据用例文本、顺序图、详细设计和测试计划实现办理借书。

### Agent 修改文件

- CirculationService
- LoanRepository
- LibraryItemRepository
- BorrowBookRequest
- BorrowBookTest

### 测试结果

全部通过 / 部分失败后修复通过。

### 人工审查结果

发现 Agent 最初未检查超期未还，已要求修复。

### Git 提交

complete borrow book use case
```

提交：

```bash
git add specs/19-ai-usage-log.md
git commit -m "update AI usage log"
```

---

## 二十八、实验二最终验收

必须满足：

```text
1. 实验一 specs 已 baseline。
2. 实验二详细设计 specs 已 baseline。
3. 至少有办理借书、办理还书、预约图书三个顺序图。
4. 有 API 或服务接口规范。
5. 有测试计划。
6. 有按任务拆解的 tasks.md。
7. 代码可以运行。
8. 自动化测试通过。
9. 借书、还书、预约、查询至少可用。
10. 不同读者类型借阅规则可用。
11. 不同借出物类型罚款规则可用。
12. ai-usage-log.md 完整。
13. Git commit 能体现按任务逐步开发。
```

