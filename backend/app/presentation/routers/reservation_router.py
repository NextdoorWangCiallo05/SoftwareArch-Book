"""预约路由（UC-013 / UC-014）。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.reservation_service import ReservationService
from app.core.exceptions import PermissionDeniedError
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
