"""认证路由（UC-001 / UC-002 / UC-003）。"""

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.application.auth_service import AuthService
from app.core.response import APIResponse, ok
from app.core.security import get_current_account
from app.domain.entities.identity import Account
from app.infrastructure.db.base import get_db
from app.schemas.auth import LoginRequest, RegisterRequest

router = APIRouter(tags=["认证"])


@router.post("/api/auth/register", response_model=APIResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> APIResponse:
    service = AuthService(db)
    reader = service.register(
        username=req.username,
        password=req.password,
        name=req.name,
        reader_type=req.reader_type,
        email=req.email,
    )
    return ok(data=reader.model_dump(), message="注册成功")


@router.post("/api/auth/login", response_model=APIResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> APIResponse:
    service = AuthService(db)
    result = service.login(req.username, req.password)
    return ok(data=result.model_dump(), message="登录成功")


@router.get("/api/auth/me", response_model=APIResponse)
def me(
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> APIResponse:
    """当前登录身份：解析 reader_id 与有效借阅证号（供借书/续借/查记录使用）。"""
    return ok(data=AuthService(db).profile(account).model_dump(), message="查询成功")


@router.post("/api/auth/logout", response_model=APIResponse)
def logout(
    authorization: str | None = Header(default=None),
    account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
) -> APIResponse:
    token = authorization[len("Bearer ") :].strip() if authorization else ""
    AuthService(db).logout(token)
    return ok(message="已退出登录")
