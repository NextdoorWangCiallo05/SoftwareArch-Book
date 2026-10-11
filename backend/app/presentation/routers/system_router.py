"""系统与健康检查路由（不属于业务用例）。"""

from datetime import datetime

from fastapi import APIRouter

from app.core.response import APIResponse, ok

router = APIRouter(tags=["系统管理"])


@router.get("/api/health", response_model=APIResponse)
def health_check() -> APIResponse:
    """健康检查：与其它接口一样返回统一响应信封（code/message/data）。"""
    return ok(data={"status": "ok", "timestamp": datetime.now().isoformat()})
