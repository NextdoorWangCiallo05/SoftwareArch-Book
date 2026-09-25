---
name: book-search
description: 图书检索技能。由 orchestrator-agent / circulation-agent 按需调用，提供图书检索与详情的接口参考（检索仅为读取，执行类操作走 circulation-agent）。
metadata:
  version: "2.1"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发，而是由 `orchestrator-agent`（找书类意图）或 `circulation-agent`（需解析 `title_id` / `barcode` 时）按需调用。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。
**需要令牌**：`Authorization: Bearer <token>`（由 `user-manage` 登录获得）。

| 能力 | 方法 | 路径 | 请求体 / 参数 | 返回关键字段 |
|------|------|------|--------------|-------------|
| 检索图书 | GET | `/api/books/search` | `keyword`/`author`/`category`/`item_type`/`page`/`page_size`（query） | `data.total`、`data.books[]` |
| 图书详情 | GET | `/api/books/{title_id}` | 路径参数 | `data.items[]`、`data.average_rating` |

`data.books[]` 每项包含：`title_id`、`title`、`author`、`isbn`、`category`、`item_type`、`available_count`、`status`。
`data.items[]` 每项包含：`item_id`、`barcode`、`status`、`location`。
详情还返回 `data.average_rating`（平均评分，仅统计已审核通过的评论）与 `data.review_count`（评论条数）。

> 借书需要的是 **`barcode`**（馆藏副本），不是 `title_id`；借书前用详情接口取一个 `status=AVAILABLE` 的 `barcode`。

> 注意两处 `status` 语义不同：检索结果 `data.books[].status` 是中文（`"在馆"` / `"已借出"`），
> 详情接口 `data.items[].status` 是英文枚举（`AVAILABLE` / `BORROWED` / `RESERVED` / `REMOVED`）。
> 判断"能否借"一律以详情接口的英文枚举为准。

## Input

- keyword: string（可选）- 书名关键词
- author: string（可选）- 作者
- category: string（可选）- 分类
- item_type: string（可选）- `BOOK` / `MAGAZINE` / `THESIS`
- page / page_size: integer（可选，默认 1 / 20）
- token: string（必需）

## Output

- 图书列表（含可借副本数）或图书详情（含副本列表与平均评分）

## Procedure

### 第1步：解析用户查询意图

从用户输入中提取关键词、作者、分类等信息。

### 第2步：调用检索 API

```python
import httpx

headers = {"Authorization": f"Bearer {token}"}
params = {}
if keyword: params["keyword"] = keyword
if author: params["author"] = author
if category: params["category"] = category

resp = httpx.get(
    "http://localhost:8001/api/books/search",
    params=params,
    headers=headers,
).json()
```

### 第3步：解析并返回结果

```
共 {total} 本
《书名》- 作者（可借 {available_count} 本，状态：在馆/已借出，title_id：{title_id}）
```

### 第4步：处理特殊情况

- 无结果：返回 `200` 且 `total = 0`（**不是 404**），建议更换关键词
- 需要借阅时：调用 `GET /api/books/{title_id}` 取 `barcode`
- 接口 `403`：令牌缺失或失效，先登录
- 接口异常：`500` → "检索服务暂时不可用，请稍后重试"

## Acceptance Criteria

- 必须支持多条件组合查询
- 结果必须包含可借副本数与 `title_id`
- 必须携带令牌，不得匿名调用
- 若用户要借某本书，必须进一步取到 `barcode` 再交给 `circulation-agent`
