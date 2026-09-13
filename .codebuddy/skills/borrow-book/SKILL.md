---
name: borrow-book
description: 借阅图书技能。由 circulation-agent 在 orchestrator-agent 委派下调用，提供借书接口契约。
metadata:
  version: "2.0"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发；借书意图由 `orchestrator-agent` 委派 `circulation-agent` 执行，circulation-agent 参考本 skill 调用接口。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。
**需要令牌且 `role = librarian`**（借书由图书管理员代理办理）。

| 能力 | 方法 | 路径 | 请求体 / 参数 | 返回关键字段 |
|------|------|------|--------------|-------------|
| 检索图书 | GET | `/api/books/search` | `keyword`（query） | `data.books[].title_id` |
| 图书详情 | GET | `/api/books/{title_id}` | 路径参数 | `data.items[].barcode`、`status` |
| 借阅 | POST | `/api/circulation/borrow` | `{card_no, barcode}` | `data.loan_id`、`data.due_date` |

## Input

- card_no: string（必需）- 借阅证号
- barcode: string（必需）- 馆藏副本条码（**不是** title_id）
- token: string（必需）- 图书管理员令牌

## Output

- `loan_id`、`title`、`barcode`、`borrow_date`、`due_date`

## Procedure

### 第1步：确认令牌与角色（role = librarian）

```python
headers = {"Authorization": f"Bearer {token}"}
```

### 第2步：解析馆藏条码

用 `book-search` 检索 `title_id`，再调 `GET /api/books/{title_id}` 取一个 `status = AVAILABLE` 的 `barcode`。

### 第3步：执行借阅

```python
import httpx

resp = httpx.post(
    "http://localhost:8001/api/circulation/borrow",
    json={"card_no": card_no, "barcode": barcode},
    headers=headers,
).json()
# 成功：code=200，data = {loan_id, title, barcode, borrow_date, due_date}
```

### 第4步：返回结果

"借阅成功！《{title}》已借出，请于 {due_date} 前归还。"

## 业务规则（由后端保证，Agent 只需透传 message）

- 借阅证必须有效（BR-001）
- 未超过该读者类型 + 出借物类型的数量上限（BR-002）
- 无超期未还（BR-003）
- 无未缴罚款或赔偿（BR-006）
- 副本状态必须为 AVAILABLE（BR-010）

## 错误处理

| code | message 示例 | 处理 |
|---|---|---|
| 403 | 权限不足 | 提示需由图书管理员办理 |
| 404 | 借阅证不存在 / 馆藏不存在 | 核对输入 |
| 400 | 借阅证无效 | 提示办证或换证 |
| 400 | 借阅已满（5/5），请先归还图书 | 提示先还书 |
| 400 | 有超期未还图书，请先归还 | 提示先还超期书 |
| 400 | 存在未缴罚款或赔偿，请先缴清 | 提示缴费 |
| 400 | 该馆藏不可借 | 建议预约 |

## Acceptance Criteria

- 必须使用真实 `card_no` 与 `barcode`，不得编造
- 每一步必须调用对应 API，不可直接操作数据库
- 借书成功后必须向用户确认书名与应还日期
- 如果用户只说了书名没说具体哪本，必须先用搜索让用户选择
