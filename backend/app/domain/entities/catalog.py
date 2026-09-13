"""馆藏与出借物领域实体。

采用继承体系（Q-D1 已确认）：LibraryItem 为抽象父类，Book / Magazine / Thesis 为子类。
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.domain.value_objects.enums import ItemStatus, ItemType


@dataclass
class BookTitle:
    """图书标题（聚合根）：描述一类出版物的书目信息。"""

    id: Optional[int] = None
    title: str = ""
    author: str = ""
    isbn: str = ""
    publisher: Optional[str] = None
    published_year: Optional[int] = None
    category: Optional[str] = None
    item_type: ItemType = ItemType.BOOK
    price: Optional[Decimal] = None
    is_active: bool = True


@dataclass
class LibraryItem:
    """馆藏副本（抽象父类）：可被借阅的实体，承载条码与状态机。"""

    id: Optional[int] = None
    barcode: str = ""
    title_id: Optional[int] = None
    item_type: ItemType = ItemType.BOOK
    status: ItemStatus = ItemStatus.AVAILABLE
    location: Optional[str] = None
    fine_category: str = "CHINESE_BOOK"

    def is_available(self) -> bool:
        return self.status == ItemStatus.AVAILABLE

    def mark_borrowed(self) -> None:
        self.status = ItemStatus.BORROWED

    def mark_available(self) -> None:
        self.status = ItemStatus.AVAILABLE

    def mark_reserved(self) -> None:
        self.status = ItemStatus.RESERVED

    def mark_removed(self) -> None:
        self.status = ItemStatus.REMOVED


@dataclass
class Book(LibraryItem):
    """图书副本。"""

    edition: Optional[str] = None
    pages: Optional[int] = None


@dataclass
class Magazine(LibraryItem):
    """杂志副本。"""

    issue_no: Optional[str] = None
    period: Optional[str] = None


@dataclass
class Thesis(LibraryItem):
    """论文副本。"""

    degree: Optional[str] = None
    school: Optional[str] = None


def create_item(item_type: ItemType, **kwargs) -> LibraryItem:
    """Factory：按出借物类型创建子类实例。"""
    factories = {
        ItemType.BOOK: Book,
        ItemType.MAGAZINE: Magazine,
        ItemType.THESIS: Thesis,
    }
    cls = factories.get(item_type, LibraryItem)
    return cls(item_type=item_type, **kwargs)
