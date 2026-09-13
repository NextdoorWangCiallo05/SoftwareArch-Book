---
name: renew-book
description: 续借图书技能。由 circulation-agent 在 orchestrator-agent 委派下调用，提供续借接口契约。
metadata:
  version: "1.0"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发；续借意图由 `orchestrator-agent` 委派 `circulation-agent` 执行，circulation-agent 参考本 skill 调用接口。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。
**需要令牌**：读者本人（`role=reader`）或图书管理员（`role=librarian`）。

| 能力 | 方法 | 路径 | 请求体 | 返回关键字段 |
|------|------|------|--------|-------------|
| 查在借记录 | GET | `/api/circulation/records/{reader_id}` | `status=BORROWED`（query） | `data.records[].loan_id` |
| 续借 | POST | `/api/circulation/renew` | `{loan_id}` | `data.new_due_date`、`data.renew_count` |

## Input

- loan_id: integer（必需）- 借阅记录 ID（先经查记录获得）
- token: string（必需）
- reader_id: integer（查记录时需要；读者本人只能查自己）

## Output

- `new_due_date`：新的应还日期（`YYYY-MM-DD`）
- `renew_count`：已续借次数（上限 1）

## Procedure

### 第1步：定位借阅记录

```python
import httpx

headers = {"Authorization": f"Bearer {token}"}
resp = httpx.get(
    f"http://localhost:8001/api/circulation/records/{reader_id}",
    params={"status": "BORROWED"},
    headers=headers,
).json()
# 从 data.records 中按书名匹配，取出 loan_id
```

### 第2步：调用续借接口

```python
resp = httpx.post(
    "http://localhost:8001/api/circulation/renew",
    json={"loan_id": loan_id},
    headers=headers,
).json()
# 成功：code=200，data.new_due_date、data.renew_count
```

### 第3步：返回结果

告知用户："续借成功！新的应还日期为 {new_due_date}。"

## 业务规则（BR-012）

- 仅 `BORROWED` 且**未逾期**的记录可续借；已归还或已逾期会被拒绝
- 每本最多续借 1 次
- 存在他人**未过期**的有效预约时不可续借
- 延长天数 = 该读者类型的借阅期限（本科生/专科生 30 天、研究生 60 天、博士/教师 90 天；杂志 7 天、论文 3 天）

## 错误处理

| code | message 示例 | 处理 |
|---|---|---|
| 400 | 该图书已归还，无法续借 | 提示该书已还 |
| 400 | 该图书已逾期，请归还后重新借阅 | 提示先归还 |
| 400 | 该图书已达续借上限（1 次） | 告知不能再续 |
| 400 | 该图书已被预约，暂不可续借 | 说明有人排队 |
| 403 | 只能续借本人的图书 / 未登录 | 引导登录或说明权限 |
| 404 | 借阅记录不存在 | 核对记录 |

## Acceptance Criteria

- 必须先查在借记录拿到真实 `loan_id`，不得猜测
- 每一步必须调用对应 API，不可直接操作数据库
- 返回的"新应还日期"字段必须与后端一致：`new_due_date`
