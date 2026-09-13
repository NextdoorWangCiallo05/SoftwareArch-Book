"""流通相关 DTO。"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class BorrowRequest(BaseModel):
    card_no: str
    barcode: str


class ReturnRequest(BaseModel):
    barcode: str


class RenewRequest(BaseModel):
    loan_id: int


class BorrowResultDTO(BaseModel):
    loan_id: int | None = None
    title: str
    barcode: str
    borrow_date: str
    due_date: str


class ReturnResultDTO(BaseModel):
    loan_id: int | None = None
    title: str
    return_date: str
    overdue_days: int = 0
    fine: Decimal = Decimal("0.00")


class RenewResultDTO(BaseModel):
    loan_id: int | None = None
    title: str
    new_due_date: str
    renew_count: int


class LostResultDTO(BaseModel):
    lost_id: int | None = None
    loan_id: int | None = None
    title: str
    amount: Decimal
    lost_date: str


class LoanDTO(BaseModel):
    loan_id: int | None = None
    title: str
    barcode: str
    borrow_date: str | None = None
    due_date: str | None = None
    return_date: str | None = None
    status: str
    is_overdue: bool = False
    renew_count: int = 0


class FineDTO(BaseModel):
    fine_id: int | None = None
    loan_id: int | None = None
    amount: Decimal
    paid: bool
