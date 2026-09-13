"""系统管理 DTO。"""

from pydantic import BaseModel, Field

from app.domain.value_objects.enums import ReaderType


class IssueCardRequest(BaseModel):
    reader_id: int


class CardDTO(BaseModel):
    card_id: int | None = None
    card_no: str
    reader_id: int | None = None
    status: str


class CreateLibrarianRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=50)
    employee_no: str | None = None


class UpdateLibrarianRequest(BaseModel):
    name: str | None = None
    employee_no: str | None = None


class StaffDTO(BaseModel):
    librarian_id: int | None = None
    name: str
    employee_no: str | None = None


class ReaderUpdateRequest(BaseModel):
    name: str | None = None
    reader_type: ReaderType | None = None
    email: str | None = None
    phone: str | None = None


class ReaderManageDTO(BaseModel):
    reader_id: int | None = None
    name: str
    reader_type: str
    email: str | None = None
    phone: str | None = None
    status: str
