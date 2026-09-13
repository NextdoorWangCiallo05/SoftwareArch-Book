# API 接口规范

> 输入：`specs/02-requirements.md`、`specs/03-use-cases.md`、`specs/09-design-model.md`、`specs/13-database-design.md`
> 状态：草稿（Agent 生成，待人工审查）

## 0. 通用约定

- 基址：`http://localhost:8001`
- 所有响应统一信封：`{"code": 200|400|403|404|500, "message": "...", "data": {...}}`
- 日期格式：`YYYY-MM-DD`；时间格式：`YYYY-MM-DD HH:MM:SS`
- 认证：受保护接口需携带请求头 `Authorization: Bearer <token>`
- 角色：`reader` / `librarian` / `admin`
- 分页参数：`page`（默认 1）、`page_size`（默认 20）

| 权限标记 | 含义 |
|---|---|
| `公开` | 无需令牌 |
| `登录` | 任意已登录用户 |
| `读者` | `role = reader`，且仅可访问本人资源 |
| `管理员` | `role = librarian` |
| `系统管理员` | `role = admin` |

---

## 1. 认证接口

### 1.1 注册读者

```text
POST /api/auth/register
权限：公开
请求：{ "username": "zhangsan", "password": "123456", "name": "张三",
       "reader_type": "UNDERGRADUATE", "email": "z@example.com" }
     reader_type ∈ ASSOCIATE | UNDERGRADUATE | GRADUATE | DOCTOR | TEACHER
响应：200 data: { "reader_id": 1, "username": "zhangsan", "name": "张三", "reader_type": "..." }
失败：400 用户名已存在 / 参数缺失
```

### 1.2 登录

```text
POST /api/auth/login
权限：公开
请求：{ "username": "zhangsan", "password": "123456" }
响应：200 data: { "token": "abc...", "user_id": 1, "role": "reader", "username": "zhangsan" }
失败：403 用户名或密码错误
```

### 1.3 注销

```text
POST /api/auth/logout
权限：登录
请求：无（令牌来自 Header）
响应：200 data: null
失败：403 令牌无效
```

---

## 2. 图书检索

### 2.1 检索图书

```text
GET /api/books/search?keyword=&author=&category=&item_type=&page=&page_size=
权限：登录
响应：200 data: {
  "total": 7, "page": 1, "page_size": 20,
  "books": [ { "title_id": 1, "title": "三体", "author": "刘慈欣", "isbn": "...",
               "category": "科幻", "item_type": "BOOK",
               "available_count": 3, "status": "在馆" } ]
}
说明：无结果返回 200 且 total = 0
```

### 2.2 图书详情

```text
GET /api/books/{title_id}
权限：登录
响应：200 data: { "title_id": 1, "title": ..., "author": ..., "isbn": ..., "publisher": ...,
                 "published_year": 2008, "category": ..., "price": "39.80",
                 "items": [ { "item_id": 1, "barcode": "ITEM2026000001",
                              "status": "AVAILABLE", "location": "A区" } ],
                 "average_rating": 4.5, "review_count": 2 }
失败：404 图书不存在
```

---

## 3. 流通

### 3.1 借书

```text
POST /api/circulation/borrow
权限：管理员
请求：{ "card_no": "CARD2026000001", "barcode": "ITEM2026000001" }
响应：200 data: { "loan_id": 1, "title": "三体", "barcode": "ITEM2026000001",
                 "borrow_date": "2026-09-13", "due_date": "2026-10-13" }
失败：403 非管理员 / 401 令牌无效
      404 借阅证不存在、馆藏不存在
      400 借阅证无效、借阅已满、有超期未还、存在未缴罚款、该馆藏不可借
```

### 3.2 还书

```text
POST /api/circulation/return
权限：管理员
请求：{ "barcode": "ITEM2026000001" }
响应：200 data: { "loan_id": 1, "title": "三体", "return_date": "2026-10-20",
                 "overdue_days": 7, "fine": 3.50 }
失败：403 非管理员；400 非本馆藏书、未找到该馆藏的借阅记录
```

### 3.3 续借

```text
POST /api/circulation/renew
权限：管理员 或 读者本人
请求：{ "loan_id": 1 }
响应：200 data: { "loan_id": 1, "title": "三体", "new_due_date": "2026-11-13", "renew_count": 1 }
失败：404 借阅记录不存在
      400 该图书已归还，无法续借 / 该图书已逾期，请归还后重新借阅 /
          该图书已达续借上限（1 次） / 该图书已被预约，暂不可续借
```

### 3.4 查询借阅记录

```text
GET /api/circulation/records/{reader_id}?status=BORROWED|RETURNED|OVERDUE
权限：读者（仅本人）或 管理员（任意）
响应：200 data: { "total": 2, "records": [
  { "loan_id": 1, "title": "三体", "barcode": "ITEM2026000001",
    "borrow_date": "2026-09-13", "due_date": "2026-10-13",
    "return_date": null, "status": "BORROWED", "is_overdue": false, "renew_count": 0 } ] }
失败：403 读者查询他人；404 读者不存在
```

### 3.5 标记罚款缴清

```text
POST /api/circulation/fines/{fine_id}/pay
权限：管理员
响应：200 data: { "fine_id": 1, "loan_id": 1, "amount": 3.50, "paid": true, "paid_at": "..." }
失败：403 非管理员；404 罚款记录不存在；400 该罚款已缴清
```

### 3.6 登记丢失与赔偿

```text
POST /api/circulation/lost
权限：管理员
请求：{ "barcode": "ITEM2026000001" }
响应：200 data: { "lost_id": 1, "loan_id": 1, "title": "三体",
                 "amount": 79.60, "lost_date": "2026-09-13" }
失败：403 非管理员；404 馆藏不存在
      400 未找到该馆藏的借阅记录 / 请先维护该图书定价
```

### 3.7 缴清赔偿

```text
POST /api/circulation/lost/{lost_id}/pay
权限：管理员
响应：200 data: { "lost_id": 1, "amount": 79.60, "paid": true, "paid_at": "..." }
失败：403 非管理员；404 赔偿记录不存在；400 该赔偿已缴清
```

---

## 4. 预约

### 4.1 创建预约

```text
POST /api/reservations
权限：读者
请求：{ "title_id": 1 }
响应：200 data: { "reservation_id": 1, "title_id": 1, "queue_position": 2,
                 "expires_at": "2026-09-20", "created_at": "2026-09-13 10:00:00" }
失败：404 图书不存在；400 您已预约过该书 / 您已借有该书，无需预约
```

### 4.2 取消预约

```text
POST /api/reservations/{reservation_id}/cancel
权限：读者（仅本人）
响应：200 data: { "reservation_id": 1, "status": "CANCELLED" }
失败：403 非本人；404 预约不存在；400 该预约已取消或已失效
```

---

## 5. 评论与评分

### 5.1 提交评分与评论

```text
POST /api/reviews
权限：读者
请求：{ "title_id": 1, "rating": 5, "comment": "太好看了" }
响应：200 data: { "review_id": 1, "title_id": 1, "rating": 5, "comment": "太好看了",
                 "status": "PENDING", "created_at": "..." }
失败：404 图书不存在；400 评分必须为 1-5 的整数
```

### 5.2 查看评论与平均分

```text
GET /api/reviews?title_id=1
权限：登录
响应：200 data: { "title_id": 1, "average_rating": 4.5, "total": 2,
                 "reviews": [ { "review_id": 1, "username": "zhangsan", "rating": 5,
                                "comment": "太好看了", "created_at": "2026-09-13" } ] }
说明：仅返回 APPROVED 评论；无评论时 average_rating = 0.0、total = 0
失败：404 图书不存在
```

### 5.3 审核评论

```text
POST /api/reviews/{review_id}/moderate
权限：系统管理员
请求：{ "decision": "APPROVED" | "REJECTED" }
响应：200 data: { "review_id": 1, "status": "APPROVED" }
失败：403 非系统管理员；404 评论不存在；400 该评论已审核
```

---

## 6. 系统管理

| 编号 | 方法与路径 | 权限 | 请求 | 响应 `data` 关键字段 | 主要失败 |
|---|---|---|---|---|---|
| 6.1 | `POST /api/admin/cards` | 系统管理员 | `{reader_id}` | `card_no`, `issued_at` | 404 读者不存在；400 已持有有效借阅证 |
| 6.2 | `POST /api/admin/cards/{id}/revoke` | 系统管理员 | — | `card_no`, `status=REVOKED` | 404；400 存在未归还图书 |
| 6.3 | `POST /api/admin/librarians` | 系统管理员 | `{username,password,name,employee_no}` | `librarian_id` | 400 用户名已存在 |
| 6.4 | `DELETE /api/admin/librarians/{id}` | 系统管理员 | — | `librarian_id` | 404 管理员不存在 |
| 6.5 | `POST /api/admin/titles` | 系统管理员 | `{title,author,isbn,publisher,published_year,category,item_type,price}` | `title_id` | 400 ISBN 重复 |
| 6.6 | `POST /api/admin/titles/{id}/deactivate` | 系统管理员 | — | `title_id`, `is_active=false` | 404；400 存在未归还副本 |
| 6.7 | `POST /api/admin/items` | 系统管理员 | `{title_id, count, location, fine_category}` | `items:[{barcode}]` | 404 标题不存在 |
| 6.8 | `POST /api/admin/items/{id}/remove` | 系统管理员 | — | `item_id`, `status=REMOVED` | 404；400 副本在借中 |
| 6.9 | `PUT /api/admin/policies/borrow` | 系统管理员 | `{reader_type, item_type, max_borrow_count, borrow_days}` | `reader_type`,`item_type`,`max_borrow_count`,`borrow_days` | 400 数值非法 |
| 6.10 | `PUT /api/admin/policies/fine` | 系统管理员 | `{item_category, grace_days, amount_per_day}` | `item_category`,`grace_days`,`amount_per_day` | 400 数值非法 |

---

## 7. 健康检查

```text
GET /api/health
权限：公开
响应：{ "status": "ok", "timestamp": "2026-09-13T10:00:00" }
```

---

## 8. 接口与 SKILL.md 的一致性约定

`.codebuddy/skills/*/SKILL.md` 与 `.codebuddy/agents/*/SKILL.md` 中出现的**路径、请求字段名、响应字段名**必须与本文档逐字一致；接口变更后必须同步更新，否则视为破坏性变更（宪法第 10 条）。
