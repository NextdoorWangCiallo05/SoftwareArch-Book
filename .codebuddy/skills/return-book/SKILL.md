---
name: return-book
description: 归还图书技能。由 circulation-agent 在 orchestrator-agent 委派下调用，提供两段式还书（读者申请 + 馆员审核）、现场办理与超期罚款的接口契约。
metadata:
  version: "2.1"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发；还书意图由 `orchestrator-agent` 委派 `circulation-agent` 执行，circulation-agent 参考本 skill 调用接口。
>
> 还书采用**两段式流程（BR-020）**：
> ① **申请阶段**：读者对本人 `BORROWED` 的借阅记录提交归还申请 → `BORROWED → RETURN_REQUESTED`；此阶段图书仍在读者手上，**不改副本状态**，仍占用借阅配额、参与超期检查（BR-003），且不可续借（BR-012）。
> ② **审核阶段**：图书管理员确认收到图书 → `RETURN_REQUESTED → RETURNED`，结算逾期罚款；若未收到图书则驳回 → 退回 `BORROWED`。
>
> 另保留**现场办理通道**：读者到馆台还书时，馆员可凭条码直接归还，无需读者先提交申请。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。

| 能力 | 方法 | 路径 | 请求体 / 参数 | 权限 | 返回关键字段 |
|------|------|------|--------------|------|-------------|
| **读者发起归还申请** | POST | `/api/circulation/return-request` | `{loan_id}` | reader（本人）/ librarian | `data.status = RETURN_REQUESTED` |
| **待审核归还申请清单** | GET | `/api/circulation/return-requests` | 无 | librarian | `data.total`、`data.records[]` |
| **审核通过（确认收书）** | POST | `/api/circulation/return-requests/{loan_id}/approve` | 路径参数 | librarian | `data.overdue_days`、`data.fine` |
| **审核驳回（未收到书）** | POST | `/api/circulation/return-requests/{loan_id}/reject` | 路径参数 | librarian | `data.status = BORROWED` |
| **现场办理归还** | POST | `/api/circulation/return` | `{barcode}` | librarian | `data.overdue_days`、`data.fine` |
| 缴清罚款 | POST | `/api/circulation/fines/{fine_id}/pay` | 路径参数 | librarian | `data.paid` |
| 登记丢失 | POST | `/api/circulation/lost` | `{barcode}` | librarian | `data.amount` |
| 缴清赔偿 | POST | `/api/circulation/lost/{lost_id}/pay` | 路径参数 | librarian | `data.paid` |

## Input

- 读者申请归还：`loan_id: int`（必需）+ 读者令牌
- 馆员审核：`loan_id: int`（必需）+ 图书管理员令牌
- 现场办理：`barcode: string`（必需）+ 图书管理员令牌

## Output

- 申请 / 驳回：`loan_id`、`reader_id`、`reader_name`、`title`、`barcode`、`due_date`、`is_overdue`、`status`
- 审核通过 / 现场办理：`loan_id`、`title`、`return_date`、`overdue_days`、`fine`

## Procedure

### A. 读者发起归还申请（默认路径）

第1步：读者登录（参考 `user-manage` skill），`GET /api/auth/me` 取 `reader_id`；
第2步：`GET /api/circulation/records/{reader_id}?status=BORROWED` 取 `loan_id`（同名多本按 `barcode`/`borrow_date` 消歧，不确定则让用户确认）；
第3步：`POST /api/circulation/return-request {"loan_id": ..}`；
第4步：告知用户"归还申请已提交，请将图书交至馆台等待审核；审核通过前图书仍计入在借且不可续借"。

```python
import httpx

headers = {"Authorization": f"Bearer {reader_token}"}
resp = httpx.post(
    "http://localhost:8001/api/circulation/return-request",
    json={"loan_id": loan_id},
    headers=headers,
).json()
# 成功：code=200，data.status = "RETURN_REQUESTED"
```

### B. 图书管理员审核

第1步：`GET /api/circulation/return-requests` 查看待审核清单（含 `reader_name`、`title`、`barcode`、`due_date`、`is_overdue`）；
第2步：确认收到图书 → `POST /api/circulation/return-requests/{loan_id}/approve`；
　　　　未收到图书 → `POST /api/circulation/return-requests/{loan_id}/reject`；
第3步：审核通过后读取 `data.fine` / `data.overdue_days` 告知用户罚款情况。

```python
headers = {"Authorization": f"Bearer {librarian_token}"}
resp = httpx.post(
    f"http://localhost:8001/api/circulation/return-requests/{loan_id}/approve",
    headers=headers,
).json()
# 成功：code=200，data = {loan_id, title, return_date, overdue_days, fine}
```

### C. 现场办理（保留通道）

读者到馆台还书、由馆员凭条码直接办理：`POST /api/circulation/return {"barcode": ..}`。

### D. 处理超期罚款

- `fine > 0`：告知用户"超期 {overdue_days} 天，产生罚款 {fine} 元"，并提示需缴清后才能再借；
- `fine == 0` 但 `overdue_days > 0`：处于宽限期内，不产生罚金。

### E. 若图书遗失

调用 `POST /api/circulation/lost {"barcode":..}`，赔偿金额 = 定价 × 倍率（图书 2.0、杂志 1.5、论文 3.0）。

## 错误处理

| code | message 示例 | 处理 |
|---|---|---|
| 403 | 权限不足 | 提示需由图书管理员办理 |
| 403 | 只能申请归还本人的图书 | 读者只能对自己的借阅记录发起申请 |
| 400 | 该图书已提交归还申请，请等待馆员审核 | 重复申请，无需再次提交 |
| 400 | 该借阅记录当前状态不可申请归还 | 记录非 BORROWED（已归还/丢失等） |
| 400 | 该借阅记录没有待审核的归还申请 | 审核时无待审申请，刷新清单 |
| 400 | 非本馆藏书 | 核对条码 |
| 400 | 未找到该馆藏的借阅记录 | 该书未在借 |
| 400 | 请先维护该图书定价 | 登记丢失前需管理员维护定价 |
| 500 | 未配置罚款规则 | 系统配置问题，提示管理员 |

## Acceptance Criteria

- 必须使用真实 `loan_id` / `barcode`，不得编造
- 每一步必须调用对应 API，不可直接操作数据库
- 归还成功后必须告知用户是否产生罚款及金额
- 字段 `overdue_days`、`fine`、`status` 与后端返回逐字一致
- 区分三条通道：读者申请（默认）、馆员审核、现场办理，不得混用
