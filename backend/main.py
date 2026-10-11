"""图书管理系统 - 后端服务入口。

负责装配 FastAPI 应用：注册路由、注册全局异常处理器。
业务实现分布在 app 的四层结构中（presentation / application / domain / infrastructure）。
"""

import sys

# Windows 控制台默认 GBK，重设为 UTF-8 避免中文打印崩溃
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import API_PORT, CORS_ALLOW_ORIGINS, RESET_DB_ON_START
from app.core.exceptions import AppError
from app.core.response import envelope
from app.infrastructure.db.seed import ensure_database, init_database
from app.presentation.routers.admin_router import router as admin_router
from app.presentation.routers.auth_router import router as auth_router
from app.presentation.routers.catalog_router import router as catalog_router
from app.presentation.routers.circulation_router import router as circulation_router
from app.presentation.routers.reservation_router import router as reservation_router
from app.presentation.routers.review_router import router as review_router
from app.presentation.routers.system_router import router as system_router

app = FastAPI(title="图书管理系统 - 原子能力API", version="2.0.0")

# 允许前端开发服务器跨域调用（来源清单见 app/core/config.py，可用 CORS_ALLOW_ORIGINS 覆盖）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(catalog_router)
app.include_router(circulation_router)
app.include_router(reservation_router)
app.include_router(review_router)
app.include_router(admin_router)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """将领域/应用层异常统一转换为响应信封。"""
    return JSONResponse(
        status_code=exc.code,
        content=envelope(exc.code, exc.message),
    )


def start_server(port: int = API_PORT) -> None:
    """启动服务。"""
    import uvicorn

    print("正在启动图书管理系统API服务...")
    print(f"API文档地址：http://localhost:{port}/docs")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    print("=" * 50)
    print("  图书管理系统 - 原子能力API服务")
    print("=" * 50)
    if RESET_DB_ON_START:
        print("\n[init] RESET_DB_ON_START=1：正在删除并重建数据库...")
        init_database(drop_existing=True)
    else:
        print("\n[init] 正在检查数据库（幂等初始化，不删除已有数据）...")
        ensure_database()
    start_server()
