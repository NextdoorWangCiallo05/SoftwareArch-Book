"""预约路由（UC-013 / UC-014）。"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.application.reservation_service import ReservationService
from app.core.exceptions import BusinessError, PermissionDeniedError
from app.core.response import APIResponse, ok
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.presentation.dependencies import (
    get_current_account,
    get_reservation_service,
    require_role,
)


class ReserveRequest(BaseModel):
    title_id: int


router = APIRouter(tags=["预约管理"])


@router.post("/api/reservations", response_model=APIResponse)
def create_reservation(
    req: ReserveRequest,
    service: ReservationService = Depends(get_reservation_service),
    account: Account = Depends(require_role(Role.READER)),
) -> APIResponse:
    reader_id = service.reader_id_of_account(account.id)
    if reader_id is None:
        raise PermissionDeniedError("读者信息不存在")

    result = service.create(reader_id, req.title_id)
    return ok(data=result, message="预约成功")


@router.post("/api/reservations/{reservation_id}/cancel", response_model=APIResponse)
def cancel_reservation(
    reservation_id: int,
    service: ReservationService = Depends(get_reservation_service),
    account: Account = Depends(require_role(Role.READER)),
) -> APIResponse:
    reader_id = service.reader_id_of_account(account.id)
    if reader_id is None:
        raise PermissionDeniedError("读者信息不存在")

    result = service.cancel(reservation_id, reader_id)
    return ok(data=result, message="预约已取消")


@router.get("/api/reservations", response_model=APIResponse)
def list_reservations(
    reader_id: int | None = Query(default=None),
    service: ReservationService = Depends(get_reservation_service),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    """查询预约记录：读者仅本人；馆员/管理员需显式传 `reader_id`。"""
    if account.role == Role.READER:
        target_id = service.reader_id_of_account(account.id)
        if target_id is None:
            raise PermissionDeniedError("读者信息不存在")
    elif account.role in (Role.LIBRARIAN, Role.ADMIN):
        if reader_id is None:
            raise BusinessError("请指定 reader_id")
        target_id = reader_id
    else:
        raise PermissionDeniedError("权限不足")

    return ok(data=service.list_by_reader(target_id))
