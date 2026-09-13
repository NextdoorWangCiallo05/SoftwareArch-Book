"""馆藏与检索 DTO。"""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.value_objects.enums import ItemStatus, ItemType


class ItemDTO(BaseModel):
    item_id: int | None = None
    barcode: str
    status: str
    location: str | None = None


class BookDTO(BaseModel):
    title_id: int | None = None
    title: str
    author: str
    isbn: str
    category: str | None = None
    item_type: str
    available_count: int = 0
    status: str = "在馆"


class BookDetailDTO(BaseModel):
    title_id: int | None = None
    title: str
    author: str
    isbn: str
    publisher: str | None = None
    published_year: int | None = None
    category: str | None = None
    item_type: str
    price: Decimal | None = None
    items: list[ItemDTO] = []
    average_rating: float = 0.0
    review_count: int = 0


class TitleCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=1, max_length=20)
    publisher: str | None = None
    published_year: int | None = None
    category: str | None = None
    item_type: ItemType = ItemType.BOOK
    price: Decimal | None = None


class TitleUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    published_year: int | None = None
    category: str | None = None
    price: Decimal | None = None


class ItemCreateRequest(BaseModel):
    title_id: int
    count: int = Field(1, ge=1, le=100)
    location: str | None = None
    fine_category: str | None = None
