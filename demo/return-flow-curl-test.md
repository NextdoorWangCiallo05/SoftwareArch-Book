# 两段式还书接口 curl 测试记录

> 生成时间：2026-10-08 22:47:00
> 后端地址：http://127.0.0.1:8001（端口 8001）
> 测试覆盖：BR-020 两段式还书 —— 读者发起归还申请 + 图书管理员审核
> 标记为 新接口 的为本次新增接口

## 1. 认证
读者令牌 READER_TOKEN、馆员令牌 LIBRARIAN_TOKEN 均通过 POST /api/auth/login 取得（用户名 zhangsan / lib01，密码 123456）。
- 读者登录响应：{"code":200,"message":"登录成功","data":{"token":"<READER_TOKEN>","user_id":4,"role":"reader","username":"zhangsan"}}
- 馆员登录响应：{"code":200,"message":"登录成功","data":{"token":"<LIBRARIAN_TOKEN>","user_id":2,"role":"librarian","username":"lib01"}}

### 查询读者在借记录（定位 loan_id）
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/records/1?status=BORROWED" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":1,"records":[{"loan_id":1,"title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","return_date":null,"status":"BORROWED","is_overdue":false,"renew_count":0}]}}
```
> 结构正确：code=200, message=操作成功

## 2. 两段式还书核心接口验证

### 读者发起归还申请（BORROWED -> RETURN_REQUESTED） [新接口]
```bash
curl.exe -s -X POST "http://127.0.0.1:8001/api/circulation/return-request" -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"loan_id":1}'
```
**响应：**
```json
{"code":200,"message":"归还申请已提交，等待馆员审核","data":{"loan_id":1,"reader_id":1,"reader_name":"张三","title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","is_overdue":false,"renew_count":0,"status":"RETURN_REQUESTED"}}
```
> 结构正确：code=200, message=归还申请已提交，等待馆员审核

### 馆员查询待审核归还申请清单 [新接口]
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/return-requests" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":1,"records":[{"loan_id":1,"reader_id":1,"reader_name":"张三","title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","is_overdue":false,"renew_count":0,"status":"RETURN_REQUESTED"}]}}
```
> 结构正确：code=200, message=操作成功

### 申请期间复核记录（状态应为 RETURN_REQUESTED，仍占借阅配额）
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/records/1?status=RETURN_REQUESTED" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":1,"records":[{"loan_id":1,"title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","return_date":null,"status":"RETURN_REQUESTED","is_overdue":false,"renew_count":0}]}}
```
> 结构正确：code=200, message=操作成功

### 馆员审核驳回（RETURN_REQUESTED -> BORROWED） [新接口]
```bash
curl.exe -s -X POST "http://127.0.0.1:8001/api/circulation/return-requests/1/reject" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"归还申请已驳回","data":{"loan_id":1,"reader_id":1,"reader_name":"张三","title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","is_overdue":false,"renew_count":0,"status":"BORROWED"}}
```
> 结构正确：code=200, message=归还申请已驳回

### 驳回后复核在借记录（恢复在借）
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/records/1?status=BORROWED" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":1,"records":[{"loan_id":1,"title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","return_date":null,"status":"BORROWED","is_overdue":false,"renew_count":0}]}}
```
> 结构正确：code=200, message=操作成功

### 读者再次发起归还申请 [新接口]
```bash
curl.exe -s -X POST "http://127.0.0.1:8001/api/circulation/return-request" -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"loan_id":1}'
```
**响应：**
```json
{"code":200,"message":"归还申请已提交，等待馆员审核","data":{"loan_id":1,"reader_id":1,"reader_name":"张三","title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","is_overdue":false,"renew_count":0,"status":"RETURN_REQUESTED"}}
```
> 结构正确：code=200, message=归还申请已提交，等待馆员审核

### 馆员再次查询待审清单 [新接口]
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/return-requests" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":1,"records":[{"loan_id":1,"reader_id":1,"reader_name":"张三","title":"三体","barcode":"ITEM2026000001","borrow_date":"2026-10-08","due_date":"2026-11-07","is_overdue":false,"renew_count":0,"status":"RETURN_REQUESTED"}]}}
```
> 结构正确：code=200, message=操作成功

### 馆员审核通过（确认收书，RETURN_REQUESTED -> RETURNED） [新接口]
```bash
curl.exe -s -X POST "http://127.0.0.1:8001/api/circulation/return-requests/1/approve" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"归还审核通过","data":{"loan_id":1,"title":"三体","return_date":"2026-10-08","overdue_days":0,"fine":"0.00"}}
```
> 结构正确：code=200, message=归还审核通过

### 复核读者在借记录（应无在借）
```bash
curl.exe -s -X GET "http://127.0.0.1:8001/api/circulation/records/1?status=BORROWED" -H "Authorization: Bearer <TOKEN>"
```
**响应：**
```json
{"code":200,"message":"操作成功","data":{"total":0,"records":[]}}
```
> 结构正确：code=200, message=操作成功

## 3. 结构校验结论
- 读者发起归还申请 POST /api/circulation/return-request：返回 code/message/data，data.status = RETURN_REQUESTED 通过
- 馆员待审核清单 GET /api/circulation/return-requests：返回 code/message/data，data.total 与 data.records 通过
- 馆员审核驳回 POST /api/circulation/return-requests/{loan_id}/reject：返回 code/message/data，记录回到 BORROWED 通过
- 馆员审核通过 POST /api/circulation/return-requests/{loan_id}/approve：返回 code/message/data，含 return_date / overdue_days / fine 通过
- 四个接口统一遵循 {code, message, data} 信封结构，与 specs/14-api-spec.md 契约一致 通过
