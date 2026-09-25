# 接口 curl 测试记录（学生任务卡 第 5 节 第 2 条）

> 验证对象：两个任务挂接的新接口
> - **任务一 续借** `POST /api/circulation/renew`
> - **任务二 评论与评分** `POST /api/reviews`、`GET /api/reviews`、`POST /api/reviews/{review_id}/moderate`
>
> 运行环境：Windows + PowerShell 5.1，后端 `python main.py`（启动时重建库，种子数据干净）
> 复现方式：`powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1`
> 原始输出：`demo/curl-output.txt`
>
> 说明：下文命令为**标准写法，可直接在 bash / Git Bash / WSL 执行**。PowerShell 下 JSON 体内的双引号需写成 `\"`，脚本已处理。

---

## 1. 任务一：续借 `POST /api/circulation/renew`

### 1.1 前置——读者登录并解析身份

```bash
$ curl.exe -s -X POST http://localhost:8001/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"zhangsan","password":"123456"}'
{"code":200,"message":"登录成功","data":{"token":"ToK7FS...","user_id":4,"role":"reader","username":"zhangsan"}}
```

### 1.2 取在借记录，定位 `loan_id`

```bash
$ curl.exe -s "http://localhost:8001/api/circulation/records/1?status=BORROWED" \
    -H "Authorization: Bearer <reader-token>"
```

```json
{"code":200,"message":"操作成功","data":{"total":2,"records":[
  {"loan_id":1,"title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-09-25","due_date":"2026-10-25","return_date":null,"status":"BORROWED","is_overdue":false,"renew_count":0},
  {"loan_id":2,"title":"三体","barcode":"ITEM2026000002","borrow_date":"2026-09-25","due_date":"2026-10-25","return_date":null,"status":"BORROWED","is_overdue":false,"renew_count":0}
]}}
```

### 1.3 续借（核心）

```bash
$ curl.exe -s -X POST http://localhost:8001/api/circulation/renew \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <reader-token>" \
    -d '{"loan_id":2}'
```

```json
{"code":200,"message":"续借成功","data":{"loan_id":2,"title":"三体","new_due_date":"2026-11-24","renew_count":1}}
```

**结论（任务一）**：

| 校验点 | 结果 |
|---|---|
| HTTP / 业务码 | `200` / `code=200` |
| 应还日期顺延一个借期 | `2026-10-25` → **`2026-11-24`**（本科生 30 天）✅ |
| 续借次数 | `renew_count` `0` → **`1`** ✅ |
| 参与者 | 读者本人令牌即可（`renew-book` 契约：Reader 本人或 Librarian）✅ |

---

## 2. 任务二：评论与评分

### 2.1 提交评分与评论

```bash
$ curl.exe -s -X POST http://localhost:8001/api/reviews \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <reader-token>" \
    -d '{"title_id":1,"rating":5,"comment":"太好看了"}'
```

```json
{"code":200,"message":"评论已提交，待审核","data":{"review_id":1,"title_id":1,"rating":5,"comment":"太好看了","status":"PENDING"}}
```

### 2.2 审核前查看——PENDING 不可见

```bash
$ curl.exe -s "http://localhost:8001/api/reviews?title_id=1" \
    -H "Authorization: Bearer <reader-token>"
```

```json
{"code":200,"message":"操作成功","data":{"title_id":1,"average_rating":0.0,"total":0,"reviews":[]}}
```

### 2.3 系统管理员审核通过

```bash
$ curl.exe -s -X POST http://localhost:8001/api/reviews/1/moderate \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer <admin-token>" \
    -d '{"decision":"APPROVED"}'
```

```json
{"code":200,"message":"审核完成","data":{"review_id":1,"status":"APPROVED"}}
```

### 2.4 审核后查看——计入平均分

```bash
$ curl.exe -s "http://localhost:8001/api/reviews?title_id=1" \
    -H "Authorization: Bearer <reader-token>"
```

```json
{"code":200,"message":"操作成功","data":{"title_id":1,"average_rating":5.0,"total":1,
  "reviews":[{"review_id":1,"reader_id":1,"rating":5,"comment":"太好看了","created_at":"2026-09-25T18:29:20.252624"}]}}
```

**结论（任务二）**：

| 校验点 | 结果 |
|---|---|
| 提交返回状态 | `status = PENDING` ✅ |
| 未审核是否可见 | 不可见，`total=0`、`average_rating=0.0` ✅ |
| 审核权限 | 读者调该接口 → `403 权限不足`；仅系统管理员可审核 ✅ |
| 审核通过后 | 出现在列表，`average_rating` `0.0` → **`5.0`** ✅ |
| 评分边界 | `rating=6` → `400 评分必须为 1-5 的整数` ✅ |

---

## 3. 附：链路中使用的其它接口

| 接口 | 请求 | 响应关键字段 |
|---|---|---|
| 健康检查 | `GET /api/health` | `{"status":"ok",...}` |
| 管理员登录 | `POST /api/auth/login` `{lib01}` | `user_id=2`、`role=librarian` |
| 系统管理员登录 | `POST /api/auth/login` `{admin}` | `user_id=1`、`role=admin` |
| 解析身份 | `GET /api/auth/me` | `reader_id=1`、`card_no=CARD2026000001` |
| 办理借书 | `POST /api/circulation/borrow` `{card_no,barcode}` | `loan_id=2`、`due_date=2026-10-25` |

## 4. 复现步骤

```powershell
# 1）启动后端（启动时重建库）
cd backend
python main.py

# 2）另开终端执行 curl 验证
cd ..
powershell -ExecutionPolicy Bypass -File demo/curl-demo.ps1
```

> 脚本会改变库状态（借书、续借、提交评论），重复运行前请重启一次后端。
