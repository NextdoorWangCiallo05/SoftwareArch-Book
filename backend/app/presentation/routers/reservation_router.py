"""预约路由（UC-013 / UC-014）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.reservation_service import ReservationService
from app.core.exceptions import BusinessError, PermissionDeniedError
from app.core.response import APIResponse, ok
from app.core.security import get_current_account, require_role
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.infrastructure.db.base import get_db
from pydantic import BaseModel


class ReserveRequest(BaseModel):
    title_id: int


router = APIRouter(tags=["预约管理"])


@router.post("/api/reservations", response_model=APIResponse)
def create_reservation(
    req: ReserveRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(require_role(Role.READER)),
) -> APIResponse:
    service = ReservationService(db)
    from app.infrastructure.repositories.reader_repository import (
        SQLAlchemyReaderRepository,
    )

    reader = SQLAlchemyReaderRepository(db).find_by_account_id(account.id)
    if reader is None:
        raise PermissionDeniedError("读者信息不存在")

    result = service.create(reader.id, req.title_id)
    return ok(data=result, message="预约成功")


@router.post("/api/reservations/{reservation_id}/cancel", response_model=APIResponse)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(require_role(Role.READER)),
) -> APIResponse:
    from app.infrastructure.repositories.reader_repository import (
        SQLAlchemyReaderRepository,
    )

    reader = SQLAlchemyReaderRepository(db).find_by_account_id(account.id)
    if reader is None:
        raise PermissionDeniedError("读者信息不存在")

    result = ReservationService(db).cancel(reservation_id, reader.id)
    return ok(data=result, message="预约已取消")


@router.get("/api/reservations", response_model=APIResponse)
def list_reservations(
    reader_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    """查询预约记录：读者仅本人；馆员/管理员需显式传 `reader_id`。"""
    from app.infrastructure.repositories.reader_repository import (
        SQLAlchemyReaderRepository,
    )

    if account.role == Role.READER:
        reader = SQLAlchemyReaderRepository(db).find_by_account_id(account.id)
        if reader is None:
            raise PermissionDeniedError("读者信息不存在")
        target_id = reader.id
    elif account.role in (Role.LIBRARIAN, Role.ADMIN):
        if reader_id is None:
            raise BusinessError("请指定 reader_id")
        target_id = reader_id
    else:
        raise PermissionDeniedError("权限不足")

    return ok(data=ReservationService(db).list_by_reader(target_id))
