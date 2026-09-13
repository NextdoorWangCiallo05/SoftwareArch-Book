"""图书标题与馆藏副本仓储实现。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.entities.catalog import BookTitle, LibraryItem, create_item
from app.domain.value_objects.enums import ItemStatus, ItemType
from app.infrastructure.models.orm import BookTitleORM, LibraryItemORM


def _to_title(orm: BookTitleORM) -> BookTitle:
    return BookTitle(
        id=orm.id,
        title=orm.title,
        author=orm.author,
        isbn=orm.isbn,
        publisher=orm.publisher,
        published_year=orm.published_year,
        category=orm.category,
        item_type=ItemType(orm.item_type),
        price=Decimal(str(orm.price)) if orm.price is not None else None,
        is_active=orm.is_active,
    )


def _to_item(orm: LibraryItemORM) -> LibraryItem:
    item = create_item(
        ItemType(orm.item_type),
        id=orm.id,
        barcode=orm.barcode,
        title_id=orm.title_id,
        status=ItemStatus(orm.status),
        location=orm.location,
        fine_category=orm.fine_category,
    )
    _apply_sub_fields(item, orm)
    return item


def _apply_sub_fields(item: LibraryItem, orm: LibraryItemORM) -> None:
    if hasattr(item, "edition"):
        item.edition = orm.edition
        item.pages = orm.pages
    if hasattr(item, "issue_no"):
        item.issue_no = orm.issue_no
        item.period = orm.period
    if hasattr(item, "degree"):
        item.degree = orm.degree
        item.school = orm.school


class SQLAlchemyTitleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, title_id: int) -> BookTitle | None:
        orm = self.db.query(BookTitleORM).filter(BookTitleORM.id == title_id).first()
        return _to_title(orm) if orm else None

    def find_by_isbn(self, isbn: str) -> BookTitle | None:
        orm = self.db.query(BookTitleORM).filter(BookTitleORM.isbn == isbn).first()
        return _to_title(orm) if orm else None

    def search(self, keyword, author, category, item_type, page, page_size):
        query = self.db.query(BookTitleORM).filter(BookTitleORM.is_active.is_(True))
        if keyword:
            query = query.filter(BookTitleORM.title.contains(keyword))
        if author:
            query = query.filter(BookTitleORM.author.contains(author))
        if category:
            query = query.filter(BookTitleORM.category == category)
        if item_type:
            query = query.filter(BookTitleORM.item_type == str(item_type))
        total = query.count()
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return [_to_title(r) for r in rows], total

    def add(self, title: BookTitle) -> BookTitle:
        orm = BookTitleORM(
            title=title.title,
            author=title.author,
            isbn=title.isbn,
            publisher=title.publisher,
            published_year=title.published_year,
            category=title.category,
            item_type=title.item_type.value,
            price=title.price,
            is_active=title.is_active,
        )
        self.db.add(orm)
        self.db.flush()
        title.id = orm.id
        return title

    def save(self, title: BookTitle) -> BookTitle:
        orm = self.db.query(BookTitleORM).filter(BookTitleORM.id == title.id).first()
        if orm is None:
            raise ValueError("图书不存在")
        orm.title = title.title
        orm.author = title.author
        orm.publisher = title.publisher
        orm.published_year = title.published_year
        orm.category = title.category
        orm.price = title.price
        orm.is_active = title.is_active
        self.db.flush()
        return title


class SQLAlchemyItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: int) -> LibraryItem | None:
        orm = self.db.query(LibraryItemORM).filter(LibraryItemORM.id == item_id).first()
        return _to_item(orm) if orm else None

    def find_by_barcode(self, barcode: str) -> LibraryItem | None:
        orm = self.db.query(LibraryItemORM).filter(LibraryItemORM.barcode == barcode).first()
        return _to_item(orm) if orm else None

    def find_available_by_title(self, title_id: int) -> LibraryItem | None:
        orm = (
            self.db.query(LibraryItemORM)
            .filter(
                LibraryItemORM.title_id == title_id,
                LibraryItemORM.status == ItemStatus.AVAILABLE.value,
            )
            .first()
        )
        return _to_item(orm) if orm else None

    def add(self, item: LibraryItem) -> LibraryItem:
        orm = LibraryItemORM(
            barcode=item.barcode,
            title_id=item.title_id,
            item_type=item.item_type.value,
            status=item.status.value,
            location=item.location,
            fine_category=item.fine_category,
        )
        self.db.add(orm)
        self.db.flush()
        item.id = orm.id
        return item

    def save(self, item: LibraryItem) -> LibraryItem:
        orm = self.db.query(LibraryItemORM).filter(LibraryItemORM.id == item.id).first()
        if orm is None:
            raise ValueError("馆藏不存在")
        orm.status = item.status.value
        orm.location = item.location
        self.db.flush()
        return item
