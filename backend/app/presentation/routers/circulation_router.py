"""流通路由（UC-009 ~ UC-012、UC-015、UC-016、UC-022）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.circulation_service import CirculationService
from app.core.response import APIResponse, ok
from app.core.security import get_current_account, require_role
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import LoanStatus, Role
from app.infrastructure.db.base import get_db
from app.schemas.circulation import BorrowRequest, RenewRequest, ReturnRequest

router = APIRouter(tags=["流通管理"])

_librarian_only = require_role(Role.LIBRARIAN)


@router.post("/api/circulation/borrow", response_model=APIResponse)
def borrow(
    req: BorrowRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    result = CirculationService(db).borrow(req.card_no, req.barcode)
    return ok(data=result.model_dump(), message="借阅成功")


@router.post("/api/circulation/return", response_model=APIResponse)
def return_book(
    req: ReturnRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    result = CirculationService(db).return_book(req.barcode)
    return ok(data=result.model_dump(), message="归还成功")


@router.post("/api/circulation/renew", response_model=APIResponse)
def renew(
    req: RenewRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    """续借：读者本人或图书管理员可发起（权限归属校验在服务层）。"""
    service = CirculationService(db)
    # 角色校验：读者需本人，管理员可代理
    if account.role == Role.READER:
        loan = service.loans.get(req.loan_id)
        if loan is None:
            from app.core.exceptions import NotFoundError

            raise NotFoundError("借阅记录不存在")
        reader = service.readers.find_by_account_id(account.id)
        if reader is None or loan.reader_id != reader.id:
            from app.core.exceptions import PermissionDeniedError

            raise PermissionDeniedError("只能续借本人的图书")
    elif account.role != Role.LIBRARIAN:
        from app.core.exceptions import PermissionDeniedError

        raise PermissionDeniedError("权限不足")

    result = service.renew(req.loan_id)
    return ok(data=result.model_dump(), message="续借成功")


@router.get("/api/circulation/records/{reader_id}", response_model=APIResponse)
def list_records(
    reader_id: int,
    status: LoanStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    """查询借阅信息：读者仅本人，图书管理员可查任意读者。"""
    service = CirculationService(db)
    if account.role == Role.READER:
        reader = service.readers.find_by_account_id(account.id)
        if reader is None or reader.id != reader_id:
            from app.core.exceptions import PermissionDeniedError

            raise PermissionDeniedError("只能查询本人的借阅信息")
    elif account.role != Role.LIBRARIAN:
        from app.core.exceptions import PermissionDeniedError

        raise PermissionDeniedError("权限不足")

    rows = service.list_loans(reader_id, status)
    return ok(data={"total": len(rows), "records": [r.model_dump() for r in rows]})


@router.post("/api/circulation/lost", response_model=APIResponse)
def report_lost(
    req: ReturnRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    result = CirculationService(db).report_lost(req.barcode)
    return ok(data=result.model_dump(), message="丢失登记成功")


@router.post("/api/circulation/lost/{lost_id}/pay", response_model=APIResponse)
def pay_compensation(
    lost_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    result = CirculationService(db).pay_compensation(lost_id)
    return ok(data=result, message="赔偿已缴清")


@router.post("/api/circulation/fines/{fine_id}/pay", response_model=APIResponse)
def pay_fine(
    fine_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    result = CirculationService(db).pay_fine(fine_id)
    return ok(data=result.model_dump(), message="罚款已缴清")
