"""流通领域实体：借阅记录、预约、罚款与赔偿。"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.core.exceptions import BusinessError
from app.domain.value_objects.enums import LoanStatus, ReservationStatus


@dataclass
class Loan:
    """借阅记录（聚合根）：承载借出、归还、续借与超期判定。"""

    id: Optional[int] = None
    reader_id: Optional[int] = None
    item_id: Optional[int] = None
    borrow_date: Optional[date] = None
    due_date: Optional[date] = None
    return_date: Optional[date] = None
    status: LoanStatus = LoanStatus.BORROWED
    renew_count: int = 0

    def is_overdue(self, today: date) -> bool:
        """是否超期未还。"""
        return self.status == LoanStatus.BORROWED and self.due_date < today

    def renew(
        self,
        borrow_days: int,
        today: date,
        has_other_active_reservation: bool = False,
    ) -> date:
        """续借（BR-012）。

        基数为原 due_date，避免逾期前突击续借造成期限损失。
        """
        if self.status != LoanStatus.BORROWED:
            raise BusinessError("该图书已归还，无法续借")
        if self.is_overdue(today):
            raise BusinessError("该图书已逾期，请归还后重新借阅")
        if self.renew_count >= 1:
            raise BusinessError("该图书已达续借上限（1 次）")
        if has_other_active_reservation:
            raise BusinessError("该图书已被预约，暂不可续借")

        self.due_date = self.due_date + timedelta(days=borrow_days)
        self.renew_count += 1
        return self.due_date

    def return_item(self, today: date) -> int:
        """归还，返回逾期天数（未超期为 0 或负数时归一为 0）。"""
        self.return_date = today
        self.status = LoanStatus.RETURNED
        if self.due_date is None:
            return 0
        return max(0, (today - self.due_date).days)

    def close_as_lost(self) -> None:
        """因丢失而结束借阅。"""
        self.status = LoanStatus.RETURNED


@dataclass
class Reservation:
    """预约（BR-007 / BR-008：唯一性、排队与 7 天有效期）。"""

    id: Optional[int] = None
    reader_id: Optional[int] = None
    title_id: Optional[int] = None
    created_at: Optional[date] = None
    expires_at: Optional[date] = None
    status: ReservationStatus = ReservationStatus.ACTIVE
    queue_position: Optional[int] = None

    def is_expired(self, today: date) -> bool:
        return self.expires_at is not None and today > self.expires_at

    def is_effective(self, today: date) -> bool:
        """有效预约：ACTIVE 且未过期（惰性失效判定）。"""
        return self.status == ReservationStatus.ACTIVE and not self.is_expired(today)

    def cancel(self) -> None:
        self.status = ReservationStatus.CANCELLED

    def fulfill(self) -> None:
        self.status = ReservationStatus.FULFILLED

    def expire(self) -> None:
        self.status = ReservationStatus.EXPIRED


@dataclass
class FineRecord:
    """罚款记录（BR-005 / BR-006）。"""

    id: Optional[int] = None
    loan_id: Optional[int] = None
    amount: Decimal = Decimal("0.00")
    paid: bool = False

    def mark_paid(self) -> None:
        if self.paid:
            raise BusinessError("该罚款已缴清")
        self.paid = True


@dataclass
class LostItem:
    """丢失与赔偿记录（BR-018a）。"""

    id: Optional[int] = None
    loan_id: Optional[int] = None
    item_id: Optional[int] = None
    lost_date: Optional[date] = None
    amount: Decimal = Decimal("0.00")
    paid: bool = False

    def mark_paid(self) -> None:
        if self.paid:
            raise BusinessError("该赔偿已缴清")
        self.paid = True
