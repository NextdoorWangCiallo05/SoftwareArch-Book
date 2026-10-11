"""系统管理路由（FR-004 ~ FR-007、FR-028 ~ FR-030）。

全部接口仅 SystemAdmin 可访问（BR-011）。
服务实例由组合根 `app.presentation.dependencies` 注入，本层不直接依赖基础设施。
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.application.admin_service import AdminService
from app.application.catalog_service import CatalogService
from app.core.response import APIResponse, ok
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import ReaderType, Role
from app.presentation.dependencies import (
    get_admin_service,
    get_catalog_service,
    require_role,
)
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
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    card = service.issue_card(req.reader_id)
    return ok(data=_card_dto(card), message="借阅证办理成功")


@router.post("/api/admin/cards/{card_id}/revoke", response_model=APIResponse)
def revoke_card(
    card_id: int,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    card = service.revoke_card(card_id)
    return ok(data=_card_dto(card), message="借阅证已注销")


# ---------- 图书管理员 ----------


@router.post("/api/admin/librarians", response_model=APIResponse)
def add_librarian(
    req: CreateLibrarianRequest,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    staff = service.add_librarian(req)
    return ok(data=_staff_dto(staff), message="管理员已添加")


@router.get("/api/admin/librarians", response_model=APIResponse)
def list_librarians(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rows, total = service.list_librarians(page, page_size)
    return ok(data={"total": total, "librarians": [_staff_dto(r) for r in rows]})


@router.put("/api/admin/librarians/{librarian_id}", response_model=APIResponse)
def update_librarian(
    librarian_id: int,
    req: UpdateLibrarianRequest,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    staff = service.update_librarian(librarian_id, req)
    return ok(data=_staff_dto(staff), message="管理员信息已更新")


@router.delete("/api/admin/librarians/{librarian_id}", response_model=APIResponse)
def remove_librarian(
    librarian_id: int,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    service.remove_librarian(librarian_id)
    return ok(message="管理员已删除")


# ---------- 借阅者（FR-028） ----------


@router.get("/api/admin/readers", response_model=APIResponse)
def list_readers(
    name: str | None = Query(default=None),
    reader_type: ReaderType | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rows, total = service.list_readers(name, reader_type, page, page_size)
    readers = [_reader_dto(row, service.active_card_no(row.id)) for row in rows]
    return ok(data={"total": total, "readers": readers})


@router.put("/api/admin/readers/{reader_id}", response_model=APIResponse)
def update_reader(
    reader_id: int,
    req: ReaderUpdateRequest,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    reader = service.update_reader(reader_id, req)
    return ok(data=_reader_dto(reader), message="读者信息已更新")


@router.post("/api/admin/readers/{reader_id}/deactivate", response_model=APIResponse)
def deactivate_reader(
    reader_id: int,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    reader = service.deactivate_reader(reader_id)
    return ok(data=_reader_dto(reader), message="读者已停用")


# ---------- 图书与馆藏（FR-030） ----------


@router.post("/api/admin/titles", response_model=APIResponse)
def add_title(
    req: TitleCreateRequest,
    service: CatalogService = Depends(get_catalog_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    title = service.add_title(req)
    return ok(data={"title_id": title.id, "title": title.title}, message="图书已添加")


@router.put("/api/admin/titles/{title_id}", response_model=APIResponse)
def update_title(
    title_id: int,
    req: TitleUpdateRequest,
    service: CatalogService = Depends(get_catalog_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    title = service.update_title(title_id, req)
    return ok(data={"title_id": title.id, "title": title.title, "price": str(title.price)},
              message="图书信息已更新")


@router.post("/api/admin/titles/{title_id}/deactivate", response_model=APIResponse)
def deactivate_title(
    title_id: int,
    service: CatalogService = Depends(get_catalog_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    service.deactivate_title(title_id)
    return ok(message="图书已下架")


@router.post("/api/admin/items", response_model=APIResponse)
def add_items(
    req: ItemCreateRequest,
    service: CatalogService = Depends(get_catalog_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    items = service.add_items(req)
    return ok(data={"items": [{"item_id": i.id, "barcode": i.barcode} for i in items]},
              message="馆藏副本已添加")


@router.post("/api/admin/items/{item_id}/remove", response_model=APIResponse)
def remove_item(
    item_id: int,
    service: CatalogService = Depends(get_catalog_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    service.remove_item(item_id)
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


@router.get("/api/admin/policies/borrow", response_model=APIResponse)
def list_borrow_policies(
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    """列出借阅规则当前配置。"""
    rows = service.list_borrow_policies()
    return ok(
        data={
            "total": len(rows),
            "policies": [
                {
                    "reader_type": str(p.reader_type),
                    "item_type": str(p.item_type),
                    "max_borrow_count": p.max_borrow_count,
                    "borrow_days": p.borrow_days,
                }
                for p in rows
            ],
        }
    )


@router.get("/api/admin/policies/fine", response_model=APIResponse)
def list_fine_rules(
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    """列出罚款规则当前配置。"""
    rows = service.list_fine_rules()
    return ok(
        data={
            "total": len(rows),
            "rules": [
                {
                    "item_category": r.item_category,
                    "grace_days": r.grace_days,
                    "amount_per_day": float(r.amount_per_day),
                }
                for r in rows
            ],
        }
    )


@router.put("/api/admin/policies/borrow", response_model=APIResponse)
def upsert_borrow_policy(
    req: BorrowPolicyRequest,
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    policy = service.upsert_borrow_policy(
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
    service: AdminService = Depends(get_admin_service),
    account: Account = Depends(_admin_only),
) -> APIResponse:
    rule = service.upsert_fine_rule(
        req.item_category, req.grace_days, req.amount_per_day
    )
    return ok(data={"item_category": rule.item_category,
                    "grace_days": rule.grace_days,
                    "amount_per_day": float(rule.amount_per_day)},
              message="罚款规则已更新")
