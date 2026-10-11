# 前端（Vue 3 + Vite）

对话式图书管理系统的可视化界面层，覆盖读者 / 图书管理员 / 系统管理员三类工作台。
所有数据来自 `backend` 的 REST 接口（统一响应信封 `{code, message, data}`），前端不直连数据库。

## 环境要求

| 组件 | 最低要求 | 实测版本 |
|---|---|---|
| Node.js | 18+ | 24.21.0 |
| npm | 9+ | 11.19.0 |

运行前请先启动后端（`backend/main.py`，默认 `http://localhost:8001`）。

## 运行

```bash
npm install
npm run dev       # http://localhost:5173，/api 请求经 Vite 代理转发到 http://localhost:8001
npm run build     # 构建产物在 dist/，部署时由同源反向代理转发 /api
npm run preview   # 预览构建产物（默认 http://localhost:4173，已加入后端 CORS 白名单）
```

开发代理配置见 `vite.config.js`；后端端口 / CORS 来源可用环境变量覆盖，见 `backend/app/core/config.py`。

## 工作台与路由

| 角色 | 路由 |
|---|---|
| 读者 | `/search` 检索、`/book/:titleId` 详情（借阅 / 预约 / 评论）、`/my/loans` 我的借阅、`/my/reservations` 我的预约 |
| 图书管理员 | `/circ/borrow` 借书办理、`/circ/return` 现场还书、`/circ/return-audit` 还书申请审核、`/circ/charges` 罚款与赔偿、`/circ/reader-records` 读者借阅查询 |
| 系统管理员 | `/admin/readers` 读者与借阅证、`/admin/catalog` 馆藏维护、`/admin/policies` 借阅与罚款规则、`/admin/reviews` 评论审核、`/admin/librarians` 管理员账号 |

路由守卫按 `meta.roles` 控制访问，登录后自动跳转到对应角色首页（`composables/useAuth.js`）。

## 目录结构

```text
src/
├── api/            # 统一请求封装：token 注入、响应信封解包、错误提示
├── components/     # 通用组件：AppModal、StateBlock、PaginationBar
├── composables/    # useAuth（登录态与角色路由）、useToast（轻提示）
├── router/         # 路由表与角色守卫
├── views/          # 页面：reader/ 读者端、staff/ 馆员端、admin/ 管理端
├── constants.js    # 枚举值与中文标签映射（与后端枚举保持一致）
└── styles.css      # 全局样式
```

## 接口约定

- 所有请求经 `src/api/index.js` 封装：自动附带 `Authorization: Bearer <token>`，按信封 `code` 判定成败并统一弹错。
- 列表接口统一分页参数 `page` / `page_size`（页面默认 20 条），响应含 `total`，管理端表格底部提供分页条。
- 枚举（借阅状态、读者类型、评论状态等）以后端 `14-api-spec.md` 为准，前端仅做展示映射。

## 演示账号（仅本地演示）

登录页提供演示账号快捷填充，与后端种子数据（`backend/app/infrastructure/db/seed.py`）一一对应：

| 角色 | 用户名 | 密码 |
|---|---|---|
| 读者 | `zhangsan` | `123456` |
| 图书管理员 | `lib01` | `123456` |
| 系统管理员 | `admin` | `admin123` |

该区块仅用于本地演示与课程验收；正式部署请删除登录页的演示账号区块，或构建时设置
`VITE_SHOW_DEMO_ACCOUNTS=false` 将其隐藏。
