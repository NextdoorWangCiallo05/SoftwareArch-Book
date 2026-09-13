"""馆藏与检索应用服务（FR-006 ~ FR-013、FR-030）。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError
from app.domain.entities.catalog import BookTitle, LibraryItem
from app.domain.value_objects.enums import ItemStatus, ItemType, ReviewStatus
from app.infrastructure.repositories.catalog_repository import (
    SQLAlchemyItemRepository,
    SQLAlchemyTitleRepository,
)
from app.infrastructure.repositories.review_repository import SQLAlchemyReviewRepository
from app.schemas.catalog import BookDTO, BookDetailDTO, ItemDTO


class CatalogService:
    def __init__(self, db: Session):
        self.db = db
        self.titles = SQLAlchemyTitleRepository(db)
        self.items = SQLAlchemyItemRepository(db)
        self.reviews = SQLAlchemyReviewRepository(db)

    # ---------- 检索 ----------

    def search(self, keyword, author, category, item_type, page, page_size):
        rows, total = self.titles.search(keyword, author, category, item_type, page, page_size)
        books = [
            BookDTO(
                title_id=t.id,
                title=t.title,
                author=t.author,
                isbn=t.isbn,
                category=t.category,
                item_type=str(t.item_type),
                available_count=self.items.count_available(t.id),
                status="在馆" if self.items.count_available(t.id) > 0 else "已借出",
            )
            for t in rows
        ]
        return books, total

    def get_detail(self, title_id: int) -> BookDetailDTO:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")

        item_rows = self.items.list_by_title(title_id)
        approved = self.reviews.list_by_status(title_id, ReviewStatus.APPROVED)
        average = (
            round(sum(r.rating for r in approved) / len(approved), 1) if approved else 0.0
        )

        return BookDetailDTO(
            title_id=title.id,
            title=title.title,
            author=title.author,
            isbn=title.isbn,
            publisher=title.publisher,
            published_year=title.published_year,
            category=title.category,
            item_type=str(title.item_type),
            price=title.price,
            items=[ItemDTO(item_id=i.id, barcode=i.barcode,
                           status=str(i.status), location=i.location) for i in item_rows],
            average_rating=average,
            review_count=len(approved),
        )

    # ---------- 管理：图书标题 ----------

    def add_title(self, req) -> BookTitle:
        if self.titles.find_by_isbn(req.isbn) is not None:
            raise BusinessError("ISBN 已存在")
        title = BookTitle(
            title=req.title,
            author=req.author,
            isbn=req.isbn,
            publisher=req.publisher,
            published_year=req.published_year,
            category=req.category,
            item_type=req.item_type,
            price=req.price,
        )
        created = self.titles.add(title)
        self.db.commit()
        return created

    def update_title(self, title_id: int, req) -> BookTitle:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")
        if req.title is not None:
            title.title = req.title
        if req.author is not None:
            title.author = req.author
        if req.publisher is not None:
            title.publisher = req.publisher
        if req.published_year is not None:
            title.published_year = req.published_year
        if req.category is not None:
            title.category = req.category
        if req.price is not None:
            title.price = req.price
        # ISBN 不可修改
        saved = self.titles.save(title)
        self.db.commit()
        return saved

    def deactivate_title(self, title_id: int) -> BookTitle:
        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")
        borrowed = [i for i in self.items.list_by_title(title_id)
                    if i.status == ItemStatus.BORROWED]
        if borrowed:
            raise BusinessError("存在未归还副本，无法下架")
        title.is_active = False
        saved = self.titles.save(title)
        self.db.commit()
        return saved

    # ---------- 管理：馆藏副本 ----------

    def add_items(self, req) -> list[LibraryItem]:
        title = self.titles.get(req.title_id)
        if title is None:
            raise NotFoundError("图书不存在")

        year = datetime.now().year
        start = len(self.items.list_by_title(req.title_id)) + 1
        created = []
        for offset in range(req.count):
            seq = start + offset
            item = LibraryItem(
                barcode=f"ITEM{year}{seq:06d}",
                title_id=req.title_id,
                item_type=title.item_type,
                status=ItemStatus.AVAILABLE,
                location=req.location,
                fine_category=req.fine_category or self._default_fine_category(title.item_type),
            )
            created.append(self.items.add(item))
        self.db.commit()
        return created

    def remove_item(self, item_id: int) -> LibraryItem:
        item = self.items.get(item_id)
        if item is None:
            raise NotFoundError("馆藏不存在")
        if item.status == ItemStatus.BORROWED:
            raise BusinessError("副本在借中，无法删除")
        item.mark_removed()
        saved = self.items.save(item)
        self.db.commit()
        return saved

    @staticmethod
    def _default_fine_category(item_type: ItemType) -> str:
        return {
            ItemType.BOOK: "CHINESE_BOOK",
            ItemType.MAGAZINE: "CHINESE_MAGAZINE",
            ItemType.THESIS: "THESIS",
        }.get(item_type, "CHINESE_BOOK")
