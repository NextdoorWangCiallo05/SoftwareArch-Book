"""认证与授权依赖（表现层基础设施）。

令牌来源：请求头 Authorization: Bearer <token>
角色只从令牌解析，不信任请求体中的角色字段。
"""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.exceptions import PermissionDeniedError
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.account_repository import (
    SQLAlchemyAccountRepository,
    SQLAlchemyTokenRepository,
)


def get_current_account(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Account:
    """解析并校验令牌，返回当前账户。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise PermissionDeniedError("未登录或令牌无效")

    token = authorization[len("Bearer ") :].strip()
    token_repo = SQLAlchemyTokenRepository(db)
    account_id = token_repo.find_account_id(token)
    if account_id is None:
        raise PermissionDeniedError("未登录或令牌无效")

    account = SQLAlchemyAccountRepository(db).find_by_id(account_id)
    if account is None or not account.is_active:
        raise PermissionDeniedError("账户不存在或已停用")
    return account


def require_role(*roles: Role):
    """角色校验依赖工厂。"""

    def dependency(account: Account = Depends(get_current_account)) -> Account:
        if roles and account.role not in roles:
            raise PermissionDeniedError("权限不足")
        return account

    return dependency
