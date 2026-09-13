---
name: book-review
description: 图书评论与评分技能。由 orchestrator-agent 在"评论/评分/书评"类意图下调用，提供评分评论、查看评论与审核的接口契约。
metadata:
  version: "1.0"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发；评论类意图由 `orchestrator-agent` 直接 `use_skill("book-review")` 后自行按契约调用接口（与 `book-search` 同层，不交给 circulation-agent）。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。

| 能力 | 方法 | 路径 | 请求体 / 参数 | 返回关键字段 |
|------|------|------|--------------|-------------|
| 提交评分与评论 | POST | `/api/reviews` | `{title_id, rating, comment?}` | `data.review_id`、`data.rating`、`data.status` |
| 查看评论与平均分 | GET | `/api/reviews` | `title_id`（query） | `data.average_rating`、`data.total`、`data.reviews[]` |
| 审核评论 | POST | `/api/reviews/{review_id}/moderate` | `{decision}` | `data.review_id`、`data.status` |

`decision` 取值：`APPROVED` / `REJECTED`。

## Input

- action: string（必需）- `submit` / `list` / `moderate`
- title_id: integer（必需）- 图书标题 ID（可先经 `book-search` 解析）
- rating: integer（提交时必需）- **1–5 的整数**
- comment: string（可选）
- review_id: integer（审核时必需）
- decision: string（审核时必需）
- token: string（必需）- 来自 `user-manage` 登录（提交需 reader，审核需 admin）

## Output

- 提交结果：`review_id`、`rating`、`status`（提交后为 `PENDING`）
- 列表结果：`average_rating`（保留 1 位小数）、`total`、`reviews[]`（含 `review_id`、`reader_id`、`rating`、`comment`、`created_at`）

## Procedure

### 第1步：解析图书

若用户只给了书名，先用 `book-search` 检索得到 `title_id`。

### 第2步：提交评分与评论

```python
import httpx

headers = {"Authorization": f"Bearer {token}"}
resp = httpx.post(
    "http://localhost:8001/api/reviews",
    json={"title_id": title_id, "rating": 5, "comment": "太好看了"},
    headers=headers,
).json()
# 成功：code=200，data.status == "PENDING"
```

### 第3步：查看评论与平均分

```python
resp = httpx.get(
    "http://localhost:8001/api/reviews",
    params={"title_id": title_id},
    headers=headers,
).json()
# data.average_rating 仅统计已审核通过（APPROVED）的评论
```

### 第4步：审核（仅系统管理员）

```python
resp = httpx.post(
    f"http://localhost:8001/api/reviews/{review_id}/moderate",
    json={"decision": "APPROVED"},
    headers=headers,
).json()
```

## 错误处理

- 评分不是 1–5 的整数 → `400`，message 含"评分必须为 1-5 的整数"，应提示用户重新给出分值
- 图书不存在 → `404`
- 非系统管理员审核 → `403`
- 重复审核 → `400`，"该评论已审核"
- 更新评论后状态重置为 `PENDING`，需重新审核才公开

## Acceptance Criteria

- 必须先解析出 `title_id` 再提交，不得编造
- 提交成功后必须明确告知用户"已提交，待管理员审核后公开"
- 展示评论时必须同时给出 `average_rating` 与评论条数
- 字段 `average_rating`、`review_id`、`status`、`decision` 与后端返回逐字一致
