---
name: return-book
description: 归还图书技能。由 circulation-agent 在 orchestrator-agent 委派下调用，提供还书与超期罚款的接口契约。
metadata:
  version: "2.0"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发；还书意图由 `orchestrator-agent` 委派 `circulation-agent` 执行，circulation-agent 参考本 skill 调用接口。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。
**需要令牌且 `role = librarian`**。

| 能力 | 方法 | 路径 | 请求体 / 参数 | 返回关键字段 |
|------|------|------|--------------|-------------|
| 归还 | POST | `/api/circulation/return` | `{barcode}` | `data.overdue_days`、`data.fine` |
| 缴清罚款 | POST | `/api/circulation/fines/{fine_id}/pay` | 路径参数 | `data.paid` |
| 登记丢失 | POST | `/api/circulation/lost` | `{barcode}` | `data.amount` |
| 缴清赔偿 | POST | `/api/circulation/lost/{lost_id}/pay` | 路径参数 | `data.paid` |

## Input

- barcode: string（必需）- 馆藏副本条码
- token: string（必需）- 图书管理员令牌

## Output

- `loan_id`、`title`、`return_date`、`overdue_days`、`fine`

## Procedure

### 第1步：确认令牌与角色（role = librarian）

### 第2步：执行归还

```python
import httpx

headers = {"Authorization": f"Bearer {token}"}
resp = httpx.post(
    "http://localhost:8001/api/circulation/return",
    json={"barcode": barcode},
    headers=headers,
).json()
# 成功：code=200，data = {loan_id, title, return_date, overdue_days, fine}
```

### 第3步：处理超期罚款

- `fine > 0`：告知用户"超期 {overdue_days} 天，产生罚款 {fine} 元"，并提示需缴清后才能再借
- `fine == 0` 但 `overdue_days > 0`：处于宽限期内，不产生罚金

### 第4步：若图书遗失

调用 `POST /api/circulation/lost {"barcode":..}`，赔偿金额 = 定价 × 倍率（图书 2.0、杂志 1.5、论文 3.0）。

## 错误处理

| code | message 示例 | 处理 |
|---|---|---|
| 403 | 权限不足 | 提示需由图书管理员办理 |
| 400 | 非本馆藏书 | 核对条码 |
| 400 | 未找到该馆藏的借阅记录 | 该书未在借 |
| 400 | 请先维护该图书定价 | 登记丢失前需管理员维护定价 |
| 500 | 未配置罚款规则 | 系统配置问题，提示管理员 |

## Acceptance Criteria

- 必须使用真实 `barcode`，不得编造
- 每一步必须调用对应 API，不可直接操作数据库
- 还书成功后必须告知用户是否产生罚款及金额
- 字段 `overdue_days`、`fine` 与后端返回逐字一致
