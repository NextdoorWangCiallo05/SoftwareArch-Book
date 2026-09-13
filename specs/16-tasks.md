# 实现任务拆解

> 输入：全部 specs（baseline 已冻结于 `experiment2-specs-baseline-v1`）
> 约定：**每个任务由 Agent 一次完成**；实现前先输出计划，实现后运行测试，人工 `git diff` 审查后再提交。
> 硬约束：**不得修改 `specs/` 下任何文件**。

---

## TASK-001 初始化四层目录结构与核心配置

- **目标**：在 `backend/app` 下建立 `core / presentation / application / domain / infrastructure / schemas` 目录骨架与核心配置。
- **输入规格**：`07-architecture.md` 第 3 节目录结构、`constitution.md` 第 5 条
- **允许修改**：`backend/app/**`（新建目录与 `__init__.py`）、`backend/app/core/config.py`、`core/response.py`、`core/exceptions.py`、`main.py`
- **禁止修改**：`specs/**`、`backend/app/models.py`、`backend/app/routes.py`（本任务不删除，后续迁移后移除）
- **实现要求**：
  - `APIResponse` 信封（`code/message/data`）；
  - 异常体系 `BusinessError(400)`、`PermissionDeniedError(403)`、`NotFoundError(404)`、`InfrastructureError(500)`；
  - 全局异常处理器注册；
  - 配置：端口 8001、数据库路径、令牌有效期 8 小时。
- **验收**：服务可启动，`GET /api/health` 返回 `{"status":"ok"}`。
- **建议测试**：启动冒烟。

## TASK-002 基础设施：ORM 模型、会话与种子数据

- **目标**：按 `13-database-design.md` 建立 14 张表的 ORM 模型与初始化逻辑。
- **输入规格**：`13-database-design.md`、`05-domain-model.md`
- **允许修改**：`backend/app/infrastructure/db/**`、`infrastructure/models/**`
- **禁止修改**：`specs/**`
- **实现要求**：
  - 单表继承：`readers`（鉴别列 `reader_type`）、`library_items`（鉴别列 `item_type`）；
  - 三个部分唯一索引：有效借阅证、在借记录、有效预约；
  - `book_reviews` 唯一约束 `(title_id, reader_id)`；
  - **初始化时删除旧 `library.db` 后重建**；
  - 种子数据：`borrow_policies` 5 条（含 ASSOCIATE 3/30）、`fine_rules` 5 条（含宽限期）、1 名 admin、2 名 librarian、3 名读者、若干标题与副本。
- **验收**：启动后建表成功，种子数据写入；`library.db` 结构符合设计。
- **建议测试**：查询种子数据条数。

## TASK-003 领域实体与枚举

- **目标**：实现领域层实体与值对象（不含持久化依赖）。
- **输入规格**：`05-domain-model.md`、`06-domain-class-diagram.puml`
- **允许修改**：`backend/app/domain/entities/**`、`domain/value_objects/**`
- **禁止修改**：`specs/**`、`infrastructure/**`
- **实现要求**：`Account`、`Reader`(+2 子类)、`Librarian`、`SystemAdmin`、`BorrowCard`、`BookTitle`、`LibraryItem`(+3 子类)、`Loan`、`Reservation`、`FineRecord`、`BookReview`；枚举 8 个；**领域层不得 import sqlalchemy**。
- **验收**：实体方法齐备（`is_valid`、`is_overdue`、`renew`、`is_effective`、`update/approve/reject`）。
- **建议测试**：UT-009～UT-016。

## TASK-004 策略对象与领域服务

- **目标**：实现 `BorrowPolicy`、`FineRule`、`FineCalculator`、`CirculationPolicyChecker`。
- **输入规格**：`05-domain-model.md`、`09-design-model.md` 第 4 节、`02-requirements.md` BR-002/004/005
- **允许修改**：`backend/app/domain/policies/**`、`domain/services/**`、`domain/repositories/**`（接口声明）
- **禁止修改**：`specs/**`
- **实现要求**：罚款公式 `max(0, 逾期天数 - grace_days) × amount_per_day`；禁止硬编码单价与数量。
- **验收**：策略可从配置读取；宽限期内返回 0。
- **建议测试**：UT-001～UT-008。

## TASK-005 仓储实现

- **目标**：实现 7 个仓储接口的 SQLAlchemy 实现与依赖注入。
- **输入规格**：`07-architecture.md`、`13-database-design.md`
- **允许修改**：`backend/app/infrastructure/repositories/**`、依赖注入模块
- **禁止修改**：`specs/**`、`domain/**`
- **实现要求**：`get_db` 会话注入；仓储只做持久化，不含业务判断。
- **验收**：可通过仓储完成基本 CRUD。
- **建议测试**：配合 TASK-006 起用。

## TASK-006 认证：注册、登录、注销

- **目标**：实现 FR-001～FR-003 与密码哈希、令牌。
- **输入规格**：`14-api-spec.md` 第 1 节、`09-design-model.md` 4.1
- **允许修改**：`application/auth_service.py`、`presentation/routers/auth_router.py`、`infrastructure/security/**`、`schemas/auth.py`
- **禁止修改**：`specs/**`
- **实现要求**：PBKDF2-HMAC-SHA256 + 随机盐；`secrets.token_urlsafe(32)`；`auth_tokens` 持久化；`get_current_account` / `require_role` 依赖。
- **验收**：登录返回 token；无效令牌 403。
- **建议测试**：TC-001～TC-006、UT-015/016。

## TASK-007 馆藏与检索

- **目标**：实现 FR-008、FR-012、FR-013 及管理端标题/副本维护（FR-006～FR-011）。
- **输入规格**：`14-api-spec.md` 第 2、6 节
- **允许修改**：`application/catalog_service.py`、`application/admin_service.py`、`presentation/routers/catalog_router.py`、`admin_router.py`、相关 schemas
- **禁止修改**：`specs/**`
- **实现要求**：条码/ISBN 唯一校验；逻辑删除；副本 Factory 按 `item_type` 创建。
- **验收**：检索分页正确；重复 ISBN/条码返回 400。
- **建议测试**：TC-013～TC-016。

## TASK-008 借阅证与人员管理

- **目标**：实现 FR-004、FR-005、FR-006、FR-007。
- **输入规格**：`14-api-spec.md` 6.1～6.4、`03-use-cases.md` UC-003/004/005
- **允许修改**：`application/admin_service.py`、`presentation/routers/admin_router.py`
- **禁止修改**：`specs/**`
- **实现要求**：证号 `CARD+年份+6位序号`；注销校验无未归还；仅 SystemAdmin。
- **验收**：TC-007～TC-012 通过。
- **建议测试**：TC-007～TC-012。

## TASK-009 办理借书

- **目标**：实现 FR-014（UC-009）。
- **输入规格**：`09-design-model.md` 4.2/4.3、`10-sequence-borrow-book.puml`
- **允许修改**：`application/circulation_service.py`、`presentation/routers/circulation_router.py`
- **禁止修改**：`specs/**`
- **实现要求**：四项前置校验；`due_date = 今天 + 借阅期限`；Loan 与副本状态在同一事务更新。
- **验收**：TC-017～TC-026 通过。
- **建议测试**：TC-017～TC-026。

## TASK-010 办理还书与超期罚款

- **目标**：实现 FR-015、FR-020、FR-021（UC-010、UC-015、UC-016）。
- **输入规格**：`09-design-model.md` 4.4、`11-sequence-return-book.puml`
- **允许修改**：`application/circulation_service.py`、`domain/services/fine_calculator.py`、路由与 schemas
- **禁止修改**：`specs/**`
- **实现要求**：宽限期逻辑；仅超期且超出宽限期才生成 FineRecord；缴清操作。
- **验收**：TC-027～TC-036 通过。
- **建议测试**：TC-027～TC-036。

## TASK-011 续借（P2）

- **目标**：实现 FR-016（UC-011）。
- **输入规格**：`09-design-model.md` 4.5、`03-use-cases.md` UC-011
- **允许修改**：`application/circulation_service.py`、`circulation_router.py`
- **禁止修改**：`specs/**`
- **实现要求**：四条前置条件；延长期限按读者类型；`renew_count` 上限 1；他人有效预约（未过期）阻塞。
- **验收**：TC-037～TC-042 通过。
- **建议测试**：TC-037～TC-042。

## TASK-012 预约

- **目标**：实现 FR-018、FR-019（UC-013、UC-014）。
- **输入规格**：`09-design-model.md` 4.6、`12-sequence-reserve-book.puml`
- **允许修改**：`application/reservation_service.py`、`reservation_router.py`
- **禁止修改**：`specs/**`
- **实现要求**：7 天有效期；排队位次；惰性失效判定；仅本人可取消。
- **验收**：TC-043～TC-050 通过。
- **建议测试**：TC-043～TC-050。

## TASK-013 评论评分与审核（P2）

- **目标**：实现 FR-022、FR-023、FR-024（UC-017、018、021）。
- **输入规格**：`09-design-model.md` 4.7、`14-api-spec.md` 第 5 节
- **允许修改**：`application/review_service.py`、`review_router.py`、schemas
- **禁止修改**：`specs/**`
- **实现要求**：评分 1–5 校验；同一读者同标题仅一条；提交即 PENDING；仅 SystemAdmin 审核；平均分只统计 APPROVED。
- **验收**：TC-055～TC-063 通过。
- **建议测试**：TC-055～TC-063。

## TASK-014 借阅规则与罚款规则维护

- **目标**：实现 FR-025、FR-026（UC-019、UC-020）。
- **输入规格**：`14-api-spec.md` 6.9、6.10
- **允许修改**：`application/admin_service.py`、`admin_router.py`
- **禁止修改**：`specs/**`
- **实现要求**：数值合法性校验；仅 SystemAdmin；修改对新借阅生效。
- **验收**：TC-064～TC-068 通过。
- **建议测试**：TC-064～TC-068。

## TASK-015 查询借阅信息、权限收口与旧代码清理

- **目标**：实现 FR-017，完成权限收口，移除旧 `models.py` / `routes.py`。
- **输入规格**：`02-requirements.md` BR-011、`14-api-spec.md` 3.4
- **允许修改**：`circulation_service.py`、`circulation_router.py`、删除 `backend/app/models.py`、`backend/app/routes.py`
- **禁止修改**：`specs/**`
- **实现要求**：读者仅本人、管理员任意；删除旧文件后服务仍可启动。
- **验收**：TC-051～TC-054 通过；旧接口全部下线。
- **建议测试**：TC-051～TC-054 + 全量回归。

## TASK-016 测试完善、Agent 提示词同步与 README

- **目标**：补齐 `15-test-plan.md` 全部用例；同步 `.codebuddy` 提示词；编写 README。
- **输入规格**：`15-test-plan.md`、`14-api-spec.md`
- **允许修改**：`tests/**`、`.codebuddy/**`、`README.md`、`specs/19-ai-usage-log.md`
- **禁止修改**：其余 `specs/**`
- **实现要求**：
  - 测试使用临时库，全量 `pytest` 通过；
  - `SKILL.md` 中路径/字段名与 `14-api-spec.md` 逐字一致；
  - README 含架构、目录、启动、测试、核心 API。
- **验收**：`pytest` 全绿；对话"我想借《三体》"端到端可用。
- **建议测试**：全量。

---

## 任务依赖与顺序

```text
TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005
                                              ↓
   TASK-006 → TASK-007 → TASK-008 → TASK-009 → TASK-010
                                              ↓
        TASK-011 → TASK-012 → TASK-013 → TASK-014 → TASK-015 → TASK-016
```

主线（P1）为 TASK-001～010、012、014～016；TASK-011（续借）与 TASK-013（评论）为 P2，按用户决策放在主线之后，但任务单已预留位置。
