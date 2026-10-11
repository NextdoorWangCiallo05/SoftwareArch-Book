# 图书管理系统（AI 时代软件设计与体系结构实验）

基于 **Spec-Driven + Agent 辅助实现** 的对话式图书管理系统：后端为 Python FastAPI 四层架构，
前端为 Vue 3 + Vite 可视化界面，对话入口由 `.codebuddy/` 下的 Agent / Skill 契约驱动。
所有设计文档位于仓库根目录的 `specs/`，代码严格按 `specs/16-tasks.md` 的任务拆解实现。
提交物与任务卡第 5 节的逐项对照见仓库根目录 `提交产物清单.md`。

## 1. 技术栈

| 项 | 版本 |
|---|---|
| Python | 3.14 |
| Web 框架 | FastAPI 0.141 |
| ORM | SQLAlchemy 2.0 |
| 数据校验 | Pydantic v2 |
| 数据库 | SQLite |
| 测试 | pytest + httpx |
| 前端框架 | Vue 3.5 + Vue Router 4 |
| 前端构建 | Vite 6（开发服务器 :5173，`/api` 代理到 :8001） |

## 2. 架构

```text
浏览器（frontend/  Vue 3 + Vite，:5173 → /api 代理）
        ↓
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
仓库根目录/
├─ backend/                   # 后端（本 README 所在目录）
│  ├─ main.py                 # 应用装配（路由 + 全局异常处理器）
│  ├─ app/
│  │  ├─ core/                # 配置、异常体系、响应信封、认证依赖
│  │  ├─ presentation/routers/# auth / catalog / circulation / reservation / review / admin / system
│  │  ├─ application/         # auth、catalog、circulation、reservation、review、admin 服务
│  │  ├─ domain/
│  │  │  ├─ entities/         # 领域实体
│  │  │  ├─ value_objects/    # 枚举
│  │  │  ├─ policies/         # BorrowPolicy / FineRule / CompensationPolicy
│  │  │  ├─ services/         # CirculationPolicyChecker / FineCalculator
│  │  │  └─ repositories/     # 仓储接口（Protocol）
│  │  ├─ infrastructure/
│  │  │  ├─ db/               # 引擎、会话、建表、种子数据
│  │  │  ├─ models/           # ORM（16 张表）
│  │  │  ├─ repositories/     # 仓储实现
│  │  │  └─ security/         # PBKDF2 密码哈希
│  │  └─ schemas/             # Pydantic DTO
│  ├─ scripts/
│  │  ├─ e2e_acceptance.py    # 端到端验收脚本（30 个真实接口场景）
│  │  └─ e2e_report.md        # 自动生成的验收记录（30 / 30 通过）
│  └─ tests/                  # unit（领域与策略）+ integration（API，含 BR-020 还书）
├─ frontend/                  # Vue 3 界面：读者 / 馆员 / 管理员三类工作台
├─ demo/                      # ★ 提交产物：curl 测试记录 + 对话演示 + 复现脚本
├─ .codebuddy/                # Agent / Skill 契约（编排层与流通执行者）
├─ specs/                     # 实验一设计文档（00–19）
└─ 提交产物清单.md            # 提交入口对照表
```

## 4. 启动

### 4.1 后端

```powershell
cd backend
pip install -r requirements.txt
python main.py
```

- 服务监听 `http://localhost:8001`
- 接口文档：http://localhost:8001/docs
- 首次启动自动建库并灌入种子数据；重复启动**不会**清空已有数据。
  需要重置演示数据时，设置 `$env:RESET_DB_ON_START="1"` 后重启（或删除 `app/library.db`）
- 数据库地址、端口、CORS 来源、令牌有效期等均可用环境变量覆盖，见 `app/core/config.py`

### 4.2 前端（可视化验收用）

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173，/api 自动代理到 :8001
```

- 前端按角色划分工作台：读者（检索、我的借阅 / 预约、图书详情与评分）、
  馆员（借书、还书、归还审核、读者记录、罚款与赔偿）、管理员（图书、借阅证、管理员、借阅规则、评论审核）
- 需**先启动后端**，前端才能取到数据；接口统一走 `/api` 相对路径，由 Vite 代理避免跨域

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
| GET | `/api/auth/me` | 登录 | 当前身份：`reader_id`、`card_no`、`reader_type` |
| GET | `/api/books/search` | 登录 | 检索（关键词/作者/分类/类型/分页） |
| GET | `/api/books/{title_id}` | 登录 | 详情（副本列表 + 平均分） |
| POST | `/api/circulation/borrow` | 管理员 | 借书（card_no + barcode） |
| POST | `/api/circulation/return` | 管理员 | **现场办理**还书（条码直办，含超期罚款） |
| POST | `/api/circulation/return-request` | 读者本人 / 管理员代理 | **两段式还书·读者发起申请**（body：`loan_id`，BR-020） |
| GET | `/api/circulation/return-requests` | 管理员 | 两段式还书·待审核申请清单 |
| POST | `/api/circulation/return-requests/{loan_id}/approve` | 管理员 | 两段式还书·审核通过（确认收书，结算超期罚款） |
| POST | `/api/circulation/return-requests/{loan_id}/reject` | 管理员 | 两段式还书·驳回（未收到图书，记录退回在借） |
| POST | `/api/circulation/renew` | 读者本人 / 管理员 | 续借 |
| GET | `/api/circulation/records/{reader_id}` | 本人 / 管理员 | 借阅记录（可选 `?status=` 过滤） |
| POST | `/api/circulation/lost` | 管理员 | 登记丢失与赔偿 |
| GET | `/api/circulation/fines`、`/api/circulation/lost` | 管理员 | 罚款 / 赔偿清单（`?paid=false` 即待缴） |
| POST | `/api/circulation/fines/{fine_id}/pay`、`/api/circulation/lost/{lost_id}/pay` | 管理员 | 缴清罚款 / 赔偿 |
| POST | `/api/reservations` | 读者 | 预约（7 天有效期） |
| POST | `/api/reservations/{id}/cancel` | 读者 | 取消预约 |
| GET | `/api/reservations` | 本人 / 管理员 | 预约记录（管理员需显式传 `reader_id`） |
| POST | `/api/reviews` | 读者 | 评分评论（需审核） |
| GET | `/api/reviews?title_id=` | 登录 | 已通过评论 + 平均分 |
| GET | `/api/reviews/pending` | 系统管理员 | 待审核评论清单 |
| POST | `/api/reviews/{id}/moderate` | 系统管理员 | 审核 |
| `/api/admin/**` | — | 系统管理员 | 借阅证、管理员、图书、规则维护（`GET /api/admin/readers` 返回含 `card_no`） |

> Agent 注意：`user_id`（账户 ID）与 `reader_id`（读者 ID）编号独立，借书/续借/查记录用 `reader_id`，
> 登录后经 `GET /api/auth/me` 解析；借书还需 `card_no`，同一接口或 `GET /api/admin/readers` 均可取得。

统一响应信封：`{"code": 200|400|403|404|500, "message": "...", "data": {...}}`。

## 8. 业务规则速查

- **二维借阅策略** `(reader_type, item_type)`：专科 3/30、本科 5/30、研究生 10/60、博士 15/90、教师 20/90；杂志 2 本 7 天、论文 2 本 3 天；未命中回退 `(reader_type, ALL)`
- **罚款含宽限期**：`max(0, 逾期天数 - grace_days) × amount_per_day`，宽限期内不计费
- **预约有效期 7 天**，过期惰性失效，不占排队位次、不阻塞续借
- **续借**每本限 1 次，以原 `due_date` 为基数延长，存在他人有效预约时不可续借
- **评论**需审核，`average_rating` 仅统计 `APPROVED`
- **两段式还书（BR-020）**状态机：`BORROWED --读者申请--> RETURN_REQUESTED --馆员通过--> RETURNED`，
  馆员驳回则退回 `BORROWED`；申请期间该记录**仍占借阅配额**，罚款在馆员审核通过时按实际归还日结算；
  管理员仍可用 `/api/circulation/return` 现场直办

## 9. 端到端验收

对**正在运行的**服务调用真实接口，**30 个场景**覆盖实验二最终验收第 9/10/11 条与任务卡两个扩展任务：

```powershell
# 1）以重置模式启动，获得干净的种子库（脚本会改变库状态）
$env:RESET_DB_ON_START="1"
python main.py
# 2）另开一个终端执行
$env:PYTHONIOENCODING="utf-8"
python scripts/e2e_acceptance.py
```

- 通过后生成 `scripts/e2e_report.md`（含每个场景的请求、预期与实际、结论），当前结果 **30 / 30 通过**
- 失败时以非 0 退出码结束，并打印失败用例编号
- 覆盖：借还预约查询、三种读者类型借期与数量上限、出借物维度（杂志 7 天 / 论文 3 天）、
  续借与续借上限、评论 1–5 校验与审核后可见、权限收口，
  以及同样逾期 10 天下图书 5.00 元 vs 论文 20.00 元的罚款差异
- 两段式还书（BR-020）不在该脚本内，由集成测试 `tests/integration/test_circulation.py`
  与 `demo/return-flow-curl-verify.ps1`（对真实服务跑完整状态流转）覆盖

## 10. 规格文档

完整需求、用例、领域模型、架构、数据库、详细设计、API、测试计划见 `specs/`（编号 00–19）。
实验一 baseline：`experiment1-specs-baseline-v1`；实验二 baseline：`experiment2-specs-baseline-v1`。
实现阶段**不得修改 specs**，如需变更请先提交变更影响分析。

## 11. 提交产物（demo/）

| 文档 | 内容 | 复现方式 |
|---|---|---|
| `demo/curl-tests.md` | 任务一（续借）+ 任务二（评论与评分）接口 curl 测试记录 | `powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1`（需先启动后端） |
| `demo/return-flow-curl-test.md` | 扩展功能 BR-020 两段式还书 curl 记录（申请 → 驳回 → 再审 → 通过的完整状态流转） | `powershell -ExecutionPolicy Bypass -File demo/return-flow-curl-verify.ps1`（自包含：自动启停后端并重写报告） |
| `demo/chat-demo.md` | 4 段对话演示记录（借书 / 续借 / 评论 / 还书），逐条对齐任务卡验收标准 | — |
| `demo/curl-output.txt` | `curl-demo.ps1` 的原始输出（token 已脱敏为 `<TOKEN>`） | — |

- 两份 curl 记录中展示的令牌均已脱敏为 `<TOKEN>`，命令可直接在 bash / Git Bash / WSL 中执行
- 记录中的具体日期随运行日变化（借期由运行当日推算），属正常现象
- 提交物与任务卡第 5 节的逐项对照见仓库根目录 `提交产物清单.md`
