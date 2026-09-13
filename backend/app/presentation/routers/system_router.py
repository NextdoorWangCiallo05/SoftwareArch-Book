"""系统与健康检查路由（不属于业务用例，直接返回非信封结构）。"""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["系统管理"])


@router.get("/api/health")
def health_check() -> dict:
    """健康检查。"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
