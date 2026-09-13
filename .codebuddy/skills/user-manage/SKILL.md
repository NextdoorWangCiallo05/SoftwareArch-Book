---
name: user-manage
description: 用户管理技能。提供注册与登录接口契约，是所有受保护接口的前置步骤。
metadata:
  version: "2.0"
  api-base: "http://localhost:8001"
---

> 说明：本 skill 不在用户输入时自动触发，而是由 `orchestrator-agent`（登录类意图）或 `circulation-agent`（需解析 reader_id / 取令牌时）按需调用。

## 后端真实 API 映射

基址 `http://localhost:8001`，统一返回 `{code, message, data}`。

| 能力 | 方法 | 路径 | 请求体 | 返回关键字段 |
|------|------|------|--------|-------------|
| 注册读者 | POST | `/api/auth/register` | `{username, password, name, reader_type, email?}` | `data.reader_id`、`data.username` |
| 登录 | POST | `/api/auth/login` | `{username, password}` | `data.token`、`data.user_id`、`data.role`、`data.username` |
| 注销 | POST | `/api/auth/logout` | 无（Header 携带令牌） | — |

`reader_type` 取值：`ASSOCIATE`（专科生）/ `UNDERGRADUATE` / `GRADUATE` / `DOCTOR` / `TEACHER`。

## Input

- action: string（必需）- `register` / `login` / `logout`
- username: string（注册、登录必需）
- password: string（注册、登录必需）
- name / reader_type / email（注册时）

## Output

- 登录结果：`token`、`user_id`、`role`、`username`

## Procedure

### 第1步：登录

```python
import httpx

resp = httpx.post(
    "http://localhost:8001/api/auth/login",
    json={"username": username, "password": password},
).json()
# resp = {"code": 200, "message": "登录成功",
#         "data": {"token": "...", "user_id": 1, "role": "reader", "username": "zhangsan"}}
token = resp["data"]["token"]
```

### 第2步：保存上下文

将 `token`、`user_id`、`role` 保存到对话上下文；后续所有受保护接口加请求头：

```python
headers = {"Authorization": f"Bearer {token}"}
```

### 第3步：测试账号

| 用户名 | 密码 | 角色 |
|---|---|---|
| admin | admin123 | 系统管理员 |
| lib01 | 123456 | 图书管理员 |
| zhangsan | 123456 | 读者（本科生） |

## 错误处理

- `code = 403`，message = "用户名或密码错误" → 提示用户核对凭据（后端统一文案，不区分用户是否存在）
- `code = 400`，message = "用户名已存在" → 注册时换一个用户名

## Acceptance Criteria

- 登录成功后必须保存 `token` 与 `role`，供后续接口使用
- 未登录状态下，当用户尝试借书、评论等操作时，先引导登录
- 令牌失效（403）时重新登录，不得重试原请求
