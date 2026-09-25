"""系统管理路由（FR-004 ~ FR-007、FR-028 ~ FR-030）。

全部接口仅 SystemAdmin 可访问（BR-011）。
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.application.admin_service import AdminService
from app.application.catalog_service import CatalogService
from app.core.response import APIResponse, ok
from app.core.security import require_role
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import ReaderType, Role
from app.infrastructure.db.base import get_db
from app.infrastructure.repositories.reader_repository import SQLAlchemyBorrowCardRepository
from app.schemas.admin import (
    CreateLibrarianRequest,
    IssueCardRequest,
    ReaderUpdateRequest,
    UpdateLibrarianRequest,
)
from app.schemas.catalog import ItemCreateRequest, TitleCreateRequest, TitleUpdateRequest

router = APIRouter(tags=["系统管理"])

_admin_only = require_role(Role.ADMIN)


def _card_dto(card) -> dict:
    return {
        "card_id": card.id,
        "card_no": card.card_no,
        "reader_id": card.reader_id,
        "status": str(card.status),
    }


def _staff_dto(staff) -> dict:
    return {
        "librarian_id": staff.id,
        "name": staff.name,
        "employee_no": staff.employee_no,
    }


def _reader_dto(reader, card_no: str | None = None) -> dict:
    """读者 DTO。附带有效借阅证号，便于管理员代借时无需另查。"""
    return {
        "reader_id": reader.id,
        "name": reader.name,
        "reader_type": str(reader.reader_type),
        "email": reader.email,
        "phone": reader.phone,
        "status": str(reader.status),
        "card_no": card_no,
    }


# ---------- 借阅证 ----------


@router.post("/api/admin/cards", response_model=APIResponse)
def issue_card(
    req: IssueCardRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    card = AdminService(db).issue_card(req.reader_id)
    return ok(data=_card_dto(card), message="借阅证办理成功")


@router.post("/api/admin/cards/{card_id}/revoke", response_model=APIResponse)
def revoke_card(
    card_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    card = AdminService(db).revoke_card(card_id)
    return ok(data=_card_dto(card), message="借阅证已注销")


# ---------- 图书管理员 ----------


@router.post("/api/admin/librarians", response_model=APIResponse)
def add_librarian(
    req: CreateLibrarianRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    staff = AdminService(db).add_librarian(req)
    return ok(data=_staff_dto(staff), message="管理员已添加")


@router.get("/api/admin/librarians", response_model=APIResponse)
def list_librarians(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rows, total = AdminService(db).list_librarians(page, page_size)
    return ok(data={"total": total, "librarians": [_staff_dto(r) for r in rows]})


@router.put("/api/admin/librarians/{librarian_id}", response_model=APIResponse)
def update_librarian(
    librarian_id: int,
    req: UpdateLibrarianRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    staff = AdminService(db).update_librarian(librarian_id, req)
    return ok(data=_staff_dto(staff), message="管理员信息已更新")


@router.delete("/api/admin/librarians/{librarian_id}", response_model=APIResponse)
def remove_librarian(
    librarian_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    AdminService(db).remove_librarian(librarian_id)
    return ok(message="管理员已删除")


# ---------- 借阅者（FR-028） ----------


@router.get("/api/admin/readers", response_model=APIResponse)
def list_readers(
    name: str | None = Query(default=None),
    reader_type: ReaderType | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rows, total = AdminService(db).list_readers(name, reader_type, page, page_size)
    card_repo = SQLAlchemyBorrowCardRepository(db)
    readers = []
    for row in rows:
        card = card_repo.find_active_by_reader(row.id)
        readers.append(_reader_dto(row, card.card_no if card else None))
    return ok(data={"total": total, "readers": readers})


@router.put("/api/admin/readers/{reader_id}", response_model=APIResponse)
def update_reader(
    reader_id: int,
    req: ReaderUpdateRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    reader = AdminService(db).update_reader(reader_id, req)
    return ok(data=_reader_dto(reader), message="读者信息已更新")


@router.post("/api/admin/readers/{reader_id}/deactivate", response_model=APIResponse)
def deactivate_reader(
    reader_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    reader = AdminService(db).deactivate_reader(reader_id)
    return ok(data=_reader_dto(reader), message="读者已停用")


# ---------- 图书与馆藏 ----------


@router.post("/api/admin/titles", response_model=APIResponse)
def add_title(
    req: TitleCreateRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    title = CatalogService(db).add_title(req)
    return ok(data={"title_id": title.id, "title": title.title}, message="图书已添加")


@router.put("/api/admin/titles/{title_id}", response_model=APIResponse)
def update_title(
    title_id: int,
    req: TitleUpdateRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    title = CatalogService(db).update_title(title_id, req)
    return ok(data={"title_id": title.id, "title": title.title, "price": str(title.price)},
              message="图书信息已更新")


@router.post("/api/admin/titles/{title_id}/deactivate", response_model=APIResponse)
def deactivate_title(
    title_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    CatalogService(db).deactivate_title(title_id)
    return ok(message="图书已下架")


@router.post("/api/admin/items", response_model=APIResponse)
def add_items(
    req: ItemCreateRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    items = CatalogService(db).add_items(req)
    return ok(data={"items": [{"item_id": i.id, "barcode": i.barcode} for i in items]},
              message="馆藏副本已添加")


@router.post("/api/admin/items/{item_id}/remove", response_model=APIResponse)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    CatalogService(db).remove_item(item_id)
    return ok(message="馆藏副本已删除")


# ---------- 规则维护（FR-025 / FR-026） ----------


class BorrowPolicyRequest(BaseModel):
    reader_type: ReaderType
    item_type: str = "ALL"
    max_borrow_count: int
    borrow_days: int


class FineRuleRequest(BaseModel):
    item_category: str
    grace_days: int = 0
    amount_per_day: float


@router.put("/api/admin/policies/borrow", response_model=APIResponse)
def upsert_borrow_policy(
    req: BorrowPolicyRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    policy = AdminService(db).upsert_borrow_policy(
        req.reader_type, req.item_type, req.max_borrow_count, req.borrow_days
    )
    return ok(data={"reader_type": str(policy.reader_type),
                    "item_type": str(policy.item_type),
                    "max_borrow_count": policy.max_borrow_count,
                    "borrow_days": policy.borrow_days},
              message="借阅规则已更新")


@router.put("/api/admin/policies/fine", response_model=APIResponse)
def upsert_fine_rule(
    req: FineRuleRequest,
    db: Session = Depends(get_db),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rule = AdminService(db).upsert_fine_rule(
        req.item_category, req.grace_days, req.amount_per_day
    )
    return ok(data={"item_category": rule.item_category,
                    "grace_days": rule.grace_days,
                    "amount_per_day": float(rule.amount_per_day)},
              message="罚款规则已更新")
