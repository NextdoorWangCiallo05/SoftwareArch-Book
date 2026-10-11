"""表现层依赖装配（Composition Root）。

分层约束（对应 specs/08-package-diagram.puml）：
    presentation --> application --> domain <-- infrastructure

本模块是表现层中唯一允许接触 infrastructure 的位置：Session、仓储实现、密码哈希器
都在此装配；router 只通过本模块获取应用服务，application 层只通过 domain 协议使用仓储。

注意：FastAPI 在一次请求内缓存依赖结果，因此同一请求中的服务共享同一个 Session。
"""

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.application.admin_service import AdminService
from app.application.auth_service import AuthService
from app.application.catalog_service import CatalogService
from app.application.circulation_service import CirculationService
from app.application.reservation_service import ReservationService
from app.application.review_service import ReviewService
from app.core.exceptions import PermissionDeniedError
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.account_repository import (
    SQLAlchemyAccountRepository,
    SQLAlchemyTokenRepository,
)
from app.infrastructure.repositories.catalog_repository import (
    SQLAlchemyItemRepository,
    SQLAlchemyTitleRepository,
)
from app.infrastructure.repositories.circulation_repository import (
    SQLAlchemyFineRepository,
    SQLAlchemyLoanRepository,
    SQLAlchemyLostRepository,
)
from app.infrastructure.repositories.policy_repository import SQLAlchemyPolicyRepository
from app.infrastructure.repositories.reader_repository import (
    SQLAlchemyBorrowCardRepository,
    SQLAlchemyLibrarianRepository,
    SQLAlchemyReaderRepository,
)
from app.infrastructure.repositories.reservation_repository import (
    SQLAlchemyReservationRepository,
)
from app.infrastructure.repositories.review_repository import SQLAlchemyReviewRepository
from app.infrastructure.security.password_hasher import Pbkdf2PasswordHasher

__all__ = [
    "get_db",
    "get_auth_service",
    "get_catalog_service",
    "get_circulation_service",
    "get_reservation_service",
    "get_review_service",
    "get_admin_service",
    "get_current_account",
    "require_role",
]


# ---------- 应用服务装配 ----------


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """装配认证服务（UC-001 ~ UC-003）。"""
    return AuthService(
        db=db,
        accounts=SQLAlchemyAccountRepository(db),
        readers=SQLAlchemyReaderRepository(db),
        cards=SQLAlchemyBorrowCardRepository(db),
        tokens=SQLAlchemyTokenRepository(db),
        hasher=Pbkdf2PasswordHasher(),
    )


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    """装配馆藏与检索服务（FR-006 ~ FR-013）。"""
    return CatalogService(
        db=db,
        titles=SQLAlchemyTitleRepository(db),
        items=SQLAlchemyItemRepository(db),
        reviews=SQLAlchemyReviewRepository(db),
    )


def get_circulation_service(db: Session = Depends(get_db)) -> CirculationService:
    """装配流通服务（借书 / 还书 / 续借 / 罚款 / 赔偿）。"""
    return CirculationService(
        db=db,
        cards=SQLAlchemyBorrowCardRepository(db),
        readers=SQLAlchemyReaderRepository(db),
        items=SQLAlchemyItemRepository(db),
        titles=SQLAlchemyTitleRepository(db),
        loans=SQLAlchemyLoanRepository(db),
        fines=SQLAlchemyFineRepository(db),
        losts=SQLAlchemyLostRepository(db),
        policies=SQLAlchemyPolicyRepository(db),
        reservations=SQLAlchemyReservationRepository(db),
    )


def get_reservation_service(db: Session = Depends(get_db)) -> ReservationService:
    """装配预约服务（UC-013 / UC-014）。"""
    return ReservationService(
        db=db,
        titles=SQLAlchemyTitleRepository(db),
        loans=SQLAlchemyLoanRepository(db),
        reservations=SQLAlchemyReservationRepository(db),
        readers=SQLAlchemyReaderRepository(db),
    )


def get_review_service(db: Session = Depends(get_db)) -> ReviewService:
    """装配评论与评分服务（UC-016 ~ UC-018）。"""
    return ReviewService(
        db=db,
        titles=SQLAlchemyTitleRepository(db),
        readers=SQLAlchemyReaderRepository(db),
        reviews=SQLAlchemyReviewRepository(db),
    )


def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    """装配系统管理服务（FR-004 ~ FR-007、FR-028 ~ FR-030）。"""
    return AdminService(
        db=db,
        accounts=SQLAlchemyAccountRepository(db),
        readers=SQLAlchemyReaderRepository(db),
        librarians=SQLAlchemyLibrarianRepository(db),
        cards=SQLAlchemyBorrowCardRepository(db),
        loans=SQLAlchemyLoanRepository(db),
        policies=SQLAlchemyPolicyRepository(db),
        hasher=Pbkdf2PasswordHasher(),
    )


# ---------- 认证与授权依赖 ----------
# 令牌来源：请求头 Authorization: Bearer <token>
# 角色只从令牌解析，不信任请求体中的角色字段。


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
