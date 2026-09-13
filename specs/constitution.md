# 图书管理系统 开发宪法

> 本文件约束 Agent（以及学生本人）在生成 Specs、UML、代码和测试时的行为。
> 任何与本宪法冲突的产出都必须被人工审查否决。

## 1. Specs 优先原则

任何代码实现前，必须先完成需求、用例、领域模型、架构、数据库、API、测试和任务拆解文档。
`specs/` 是唯一事实来源；代码与 specs 冲突时，**改代码，不改 specs**。

## 2. Agent 起草，人类确认原则

Agent 可以生成规格初稿，但所有规格必须经过人工审查后，才能作为实现依据。
未经审查的 specs 不得进入 baseline。

## 3. UML-as-Spec 原则

用例图、类图、包图、顺序图必须使用 PlantUML（`.puml`）文本格式保存到 `specs/` 目录，纳入 Git 管理。
禁止只提交截图或仅存在图形工具中的图。

## 4. Baseline 原则

Specs 审查通过后必须打 Git tag 建立 baseline：
- 实验一：`experiment1-specs-baseline-v1`
- 实验二：`experiment2-specs-baseline-v1`

实现阶段 Agent 不得擅自修改 specs。确需变更时，必须先提交"变更影响分析"，由人类决定是否解冻。

## 5. 分层架构原则

系统必须采用分层架构，至少包括：

```text
presentation（FastAPI 路由 / Controller）
application  （用例编排 Service）
domain       （实体、值对象、领域服务、策略）
infrastructure（Repository 实现、ORM、数据库）
test         （pytest）
```

依赖方向必须自上而下：Controller → Application Service → Domain。
**Controller 不得直接依赖 Repository。**

## 6. MVC 原则

界面 / 接口层应遵循 MVC 或类似分离思想，**不得把业务规则写入 Controller**。
Controller 只负责：接收请求、参数校验转发、调用 Application Service、返回响应。

## 7. 权限原则

图书管理员、系统管理员和读者权限必须区分：

- 借书、还书：仅 Librarian；
- 借阅证、图书、规则维护：仅 SystemAdmin；
- 查询自己的借阅信息：Reader 本人；
- 查询任意读者的借阅信息：Librarian。

## 8. 业务规则集中原则

借阅数量、借阅期限、超期罚款等规则必须集中在 `BorrowPolicy` / `FineRule` 等策略对象中实现，
**不得散落在界面层或路由函数里**，不得硬编码魔法数字。

## 9. 持久化抽象原则

领域层不得直接依赖 SQLAlchemy Session。
持久化通过 Repository 接口访问，由 infrastructure 层实现。

## 10. API 契约原则

- 所有接口统一返回信封：`{"code": 200|400|403|404|500, "message": "...", "data": {...}}`；
- 状态码语义：
  - `200` 成功；
  - `400` 业务错误（message 可直接呈现给用户，如"借阅已满，请先归还"）；
  - `403` 未认证或权限不足（未携带令牌、令牌无效、角色不允许）；
  - `404` 资源不存在（读者、图书、借阅记录等未找到）；
  - `500` 系统错误；
- 日期格式统一 `YYYY-MM-DD`；
- 服务基址：`http://localhost:8001`；
- 接口路径、字段名一经确定，**后端实现与 `.codebuddy/skills/*/SKILL.md` 中的描述必须逐字一致**。

## 10.1 认证原则（真实登录认证）

- 系统必须实现**真实登录认证**：用户名 + 密码校验，密码不得以明文存储（使用加盐哈希）；
- 登录成功后返回访问令牌 `token`，受保护接口通过请求头 `Authorization: Bearer <token>` 携带；
- 未携带、过期或无效令牌一律返回 `403`，不得泄露"用户是否存在"之外的敏感信息；
- 角色（`reader` / `librarian` / `admin`）从令牌解析，业务层不得信任请求体中的角色字段；
- 认证逻辑属于基础设施/应用服务层，不得散落在各路由函数中。

## 11. 测试闭环原则

核心用例必须有自动化测试（pytest + httpx），至少覆盖：

- 借书成功 / 借阅证无效 / 超过数量 / 有超期未还 / 图书不可借；
- 还书成功 / 非本馆藏书 / 未找到借阅记录 / 超期生成罚款；
- 预约成功 / 重复预约失败；
- 权限失败场景（普通读者执行管理员操作）。

测试失败时，Agent 必须先解释原因，再做**最小修复**，禁止大规模重写。

## 12. 任务粒度原则

`16-tasks.md` 中每个任务必须适合 Agent 一次完成，
每个任务明确：目标、输入规格、允许修改文件、禁止修改文件、验收标准、建议测试。
禁止出现"实现整个系统"这类任务。

## 13. Git 审查原则

Agent 修改代码后，必须查看 `git diff` 再决定是否提交。
提交信息按任务组织，例如 `complete TASK-005 borrow book use case`。

## 14. AI 使用记录原则

每次使用 Agent 生成 specs、UML、代码或测试，都必须记录在 `specs/19-ai-usage-log.md` 中，
包含：工具、阶段、输入 Prompt 摘要、修改文件、输出摘要、人工审查结果、测试结果、commit。

## 15. 安全原则

- API Key 不得写入仓库，`.gitignore` 必须包含 `.env`；
- 不得让 Agent 无限制修改文件，每次任务必须限定文件范围；
- 不得让 Agent 通过修改 specs 来"适配"错误的代码。
