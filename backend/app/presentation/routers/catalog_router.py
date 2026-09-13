"""图书检索路由（FR-012 / FR-013）。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.application.catalog_service import CatalogService
from app.core.response import APIResponse, ok
from app.core.security import get_current_account
from app.domain.entities.identity import Account
from app.domain.value_objects.enums import ItemType
from app.infrastructure.db.base import get_db

router = APIRouter(tags=["图书检索"])


@router.get("/api/books/search", response_model=APIResponse)
def search_books(
    keyword: str | None = Query(default=None),
    author: str | None = Query(default=None),
    category: str | None = Query(default=None),
    item_type: ItemType | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    books, total = CatalogService(db).search(
        keyword, author, category, item_type, page, page_size
    )
    return ok(
        data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "books": [b.model_dump() for b in books],
        }
    )


@router.get("/api/books/{title_id}", response_model=APIResponse)
def get_book_detail(
    title_id: int,
    db: Session = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> APIResponse:
    detail = CatalogService(db).get_detail(title_id)
    return ok(data=detail.model_dump())
