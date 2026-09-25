# 图书管理系统（AI 时代软件设计与体系结构实验）

基于 **Spec-Driven + Agent 辅助实现** 的图书管理系统后端，采用 Python FastAPI 四层架构。
所有设计文档位于仓库根目录的 `specs/`，代码严格按 `specs/16-tasks.md` 的任务拆解实现。

## 1. 技术栈

| 项 | 版本 |
|---|---|
| Python | 3.14 |
| Web 框架 | FastAPI 0.141 |
| ORM | SQLAlchemy 2.0 |
| 数据校验 | Pydantic v2 |
| 数据库 | SQLite |
| 测试 | pytest + httpx |

## 2. 架构

```text
对话式 Agent 层（.codebuddy/）
  orchestrator-agent → circulation-agent / skills
        ↓ HTTP :8001
presentation   FastAPI 路由 + 依赖注入（认证/角色）
application    用例编排服务 + 事务边界
domain         实体、值对象、策略对象、领域服务（不依赖框架）
infrastructure ORM、Repository 实现、密码哈希、令牌存储
        ↓
     SQLite
```

约束：**Controller 不直接依赖 Repository**，业务规则集中在 `BorrowPolicy` / `FineRule` / `CompensationPolicy` 策略对象，禁止硬编码。

## 3. 目录结构

```text
backend/
├─ main.py                    # 应用装配（路由 + 全局异常处理器）
├─ app/
│  ├─ core/                   # 配置、异常体系、响应信封、认证依赖
│  ├─ presentation/routers/   # auth / catalog / circulation / reservation / review / admin / system
│  ├─ application/            # auth_service、catalog_service、circulation_service、
│  │                          # reservation_service、review_service、admin_service
│  ├─ domain/
│  │  ├─ entities/            # 领域实体
│  │  ├─ value_objects/       # 枚举
│  │  ├─ policies/            # BorrowPolicy / FineRule / CompensationPolicy
│  │  ├─ services/            # CirculationPolicyChecker / FineCalculator
│  │  └─ repositories/        # 仓储接口（Protocol）
│  ├─ infrastructure/
│  │  ├─ db/                  # 引擎、会话、建表、种子数据
│  │  ├─ models/              # ORM（16 张表）
│  │  ├─ repositories/        # 仓储实现
│  │  └─ security/            # PBKDF2 密码哈希
│  └─ schemas/                # Pydantic DTO
├─ scripts/
│  ├─ e2e_acceptance.py       # 端到端验收脚本（28 个真实接口场景）
│  └─ e2e_report.md           # 自动生成的验收记录
└─ tests/                     # unit（领域与策略）+ integration（API）
```

## 4. 启动

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

- 服务监听 `http://localhost:8001`
- 接口文档：http://localhost:8001/docs
- 启动时若开启初始化会**删除旧 `library.db` 并重建**（领域模型变更后需要）

## 5. 测试

```powershell
# Windows 控制台需设置 UTF-8，否则中文输出会触发 GBK 解码错误
$env:PYTHONIOENCODING="utf-8"
python -m pytest tests -q
```

测试使用独立内存 SQLite，不污染运行库。

## 6. 测试账号（种子数据）

| 用户名 | 密码 | 角色 |
|---|---|---|
| admin | admin123 | 系统管理员 |
| lib01 / lib02 | 123456 | 图书管理员 |
| zhangsan（本科生）、lisi（研究生）、wangwu（教师）、zhaoliu（专科生） | 123456 | 读者 |

## 7. 核心 API

| 方法 | 路径 | 权限 | 说明 |
|---|---|---|---|
| POST | `/api/auth/register` / `/login` / `/logout` | 公开 / 登录 | 注册、登录、注销 |
| GET | `/api/books/search` | 登录 | 检索（关键词/作者/分类/类型/分页） |
| GET | `/api/books/{title_id}` | 登录 | 详情（副本列表 + 平均分） |
| POST | `/api/circulation/borrow` | 管理员 | 借书（card_no + barcode） |
| POST | `/api/circulation/return` | 管理员 | 还书（含超期罚款） |
| POST | `/api/circulation/renew` | 读者本人 / 管理员 | 续借 |
| GET | `/api/circulation/records/{reader_id}` | 本人 / 管理员 | 借阅记录 |
| POST | `/api/circulation/lost` | 管理员 | 登记丢失与赔偿 |
| POST | `/api/reservations` | 读者 | 预约（7 天有效期） |
| POST | `/api/reviews` | 读者 | 评分评论（需审核） |
| GET | `/api/reviews?title_id=` | 登录 | 已通过评论 + 平均分 |
| POST | `/api/reviews/{id}/moderate` | 系统管理员 | 审核 |
| `/api/admin/**` | — | 系统管理员 | 借阅证、管理员、图书、规则维护 |

统一响应信封：`{"code": 200|400|403|404|500, "message": "...", "data": {...}}`。

## 8. 业务规则速查

- **二维借阅策略** `(reader_type, item_type)`：专科 3/30、本科 5/30、研究生 10/60、博士 15/90、教师 20/90；杂志 2 本 7 天、论文 2 本 3 天；未命中回退 `(reader_type, ALL)`
- **罚款含宽限期**：`max(0, 逾期天数 - grace_days) × amount_per_day`，宽限期内不计费
- **预约有效期 7 天**，过期惰性失效，不占排队位次、不阻塞续借
- **续借**每本限 1 次，以原 `due_date` 为基数延长，存在他人有效预约时不可续借
- **评论**需审核，`average_rating` 仅统计 `APPROVED`

## 9. 端到端验收

对**正在运行的**服务调用真实接口，覆盖实验二最终验收第 9/10/11 条与任务卡两个扩展任务：

```powershell
# 1）重启服务以获得干净的种子库（脚本会改变库状态）
python main.py
# 2）另开一个终端执行
$env:PYTHONIOENCODING="utf-8"
python scripts/e2e_acceptance.py
```

- 通过后生成 `scripts/e2e_report.md`（含每个场景的请求、预期与实际、结论）
- 失败时以非 0 退出码结束，并打印失败用例编号
- 覆盖：借还预约查询、三种读者类型借期与数量上限、出借物维度（杂志 7 天 / 论文 3 天）、
  续借与续借上限、评论 1–5 校验与审核后可见、权限收口，
  以及同样逾期 10 天下图书 5.00 元 vs 论文 20.00 元的罚款差异

## 10. 规格文档

完整需求、用例、领域模型、架构、数据库、详细设计、API、测试计划见 `specs/`（编号 00–19）。
实验一 baseline：`experiment1-specs-baseline-v1`；实验二 baseline：`experiment2-specs-baseline-v1`。
实现阶段**不得修改 specs**，如需变更请先提交变更影响分析。
