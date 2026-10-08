"""流通路由（UC-009 ~ UC-012、UC-015、UC-016、UC-022）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.circulation_service import CirculationService
from app.core.response import APIResponse, ok
from app.core.security import get_current_account, require_role
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import LoanStatus, Role
from app.infrastructure.db.base import get_db
from app.schemas.circulation import (
    BorrowRequest,
    RenewRequest,
    ReturnApplyRequest,
    ReturnRequest,
)

router = APIRouter(tags=["流通管理"])

_librarian_only = require_role(Role.LIBRARIAN)


def _assert_loan_owner_or_librarian(service, account: Account, loan_id: int) -> None:
    """归还申请发起人校验：读者仅限本人，图书管理员可代理（BR-020）。"""
    from app.core.exceptions import NotFoundError, PermissionDeniedError

    if account.role == Role.LIBRARIAN:
        return
    if account.role != Role.READER:
        raise PermissionDeniedError("权限不足")

    loan = service.loans.get(loan_id)
    if loan is None:
        raise NotFoundError("借阅记录不存在")
    reader = service.readers.find_by_account_id(account.id)
    if reader is None or loan.reader_id != reader.id:
        raise PermissionDeniedError("只能申请归还本人的图书")


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
    """馆员现场办理还书（条码直办，读者无需先提交申请）。"""
    result = CirculationService(db).return_book(req.barcode)
    return ok(data=result.model_dump(), message="归还成功")


# ---------- 还书申请与审核（BR-020：读者发起 + 馆员审核） ----------


@router.post("/api/circulation/return-request", response_model=APIResponse)
def request_return(
    req: ReturnApplyRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    """读者发起归还申请；图书管理员可代读者发起。"""
    service = CirculationService(db)
    _assert_loan_owner_or_librarian(service, account, req.loan_id)
    result = service.request_return(req.loan_id)
    return ok(data=result.model_dump(), message="归还申请已提交，等待馆员审核")


@router.get("/api/circulation/return-requests", response_model=APIResponse)
def list_return_requests(
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    """待审核的归还申请清单（馆员审核台）。"""
    rows = CirculationService(db).list_return_requests()
    return ok(data={"total": len(rows), "records": [r.model_dump() for r in rows]})


@router.post(
    "/api/circulation/return-requests/{loan_id}/approve", response_model=APIResponse
)
def approve_return(
    loan_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    """馆员审核通过：确认收到图书，执行归还与超期罚款结算。"""
    result = CirculationService(db).approve_return(loan_id)
    return ok(data=result.model_dump(), message="归还审核通过")


@router.post(
    "/api/circulation/return-requests/{loan_id}/reject", response_model=APIResponse
)
def reject_return(
    loan_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    """馆员驳回归还申请：未收到图书，借阅记录退回在借状态。"""
    result = CirculationService(db).reject_return(loan_id)
    return ok(data=result.model_dump(), message="归还申请已驳回")


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


# ---------- 查询（供馆员缴费台列出待缴记录，缴费需要 fine_id / lost_id） ----------


@router.get("/api/circulation/fines", response_model=APIResponse)
def list_fines(
    reader_id: int | None = Query(default=None),
    paid: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    """罚款记录列表；`paid=false` 即待缴清单。"""
    rows = CirculationService(db).list_fines(reader_id, paid)
    return ok(data={"total": len(rows), "records": rows})


@router.get("/api/circulation/lost", response_model=APIResponse)
def list_losts(
    reader_id: int | None = Query(default=None),
    paid: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    account: Account = Depends(_librarian_only),
) -> APIResponse:
    """赔偿记录列表；`paid=false` 即待缴清单。"""
    rows = CirculationService(db).list_losts(reader_id, paid)
    return ok(data={"total": len(rows), "records": rows})
