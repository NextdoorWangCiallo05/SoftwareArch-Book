"""领域实体单元测试（不依赖数据库与框架）。"""

from datetime import date

import pytest

from app.core.exceptions import BusinessError
from app.domain.entities import (
    Book,
    BookReview,
    Loan,
    LostItem,
    Reservation,
    create_item,
)
from app.domain.value_objects.enums import (
    ItemStatus,
    ItemType,
    LoanStatus,
    ReservationStatus,
    ReviewStatus,
)


class TestLoan:
    def test_renew_extends_due_date_based_on_original(self):
        loan = Loan(due_date=date(2026, 10, 1), status=LoanStatus.BORROWED)
        new_due = loan.renew(borrow_days=30, today=date(2026, 9, 13))
        assert new_due == date(2026, 10, 31)
        assert loan.renew_count == 1

    def test_renew_rejected_when_limit_reached(self):
        loan = Loan(due_date=date(2026, 10, 1), status=LoanStatus.BORROWED)
        loan.renew(30, date(2026, 9, 13))
        with pytest.raises(BusinessError) as exc:
            loan.renew(30, date(2026, 9, 13))
        assert exc.value.code == 400

    def test_renew_rejected_when_overdue(self):
        loan = Loan(due_date=date(2026, 9, 1), status=LoanStatus.BORROWED)
        with pytest.raises(BusinessError):
            loan.renew(30, date(2026, 9, 13))

    def test_renew_rejected_when_returned(self):
        loan = Loan(due_date=date(2026, 10, 1), status=LoanStatus.RETURNED)
        with pytest.raises(BusinessError):
            loan.renew(30, date(2026, 9, 13))

    def test_renew_rejected_when_reserved_by_others(self):
        loan = Loan(due_date=date(2026, 10, 1), status=LoanStatus.BORROWED)
        with pytest.raises(BusinessError):
            loan.renew(30, date(2026, 9, 13), has_other_active_reservation=True)

    def test_return_item_returns_overdue_days(self):
        loan = Loan(due_date=date(2026, 9, 10), status=LoanStatus.BORROWED)
        overdue = loan.return_item(date(2026, 9, 13))
        assert overdue == 3
        assert loan.status == LoanStatus.RETURNED

    def test_is_overdue(self):
        loan = Loan(due_date=date(2026, 9, 1), status=LoanStatus.BORROWED)
        assert loan.is_overdue(date(2026, 9, 13)) is True
        loan.status = LoanStatus.RETURNED
        assert loan.is_overdue(date(2026, 9, 13)) is False


class TestReservation:
    def test_effective_before_expiry(self):
        resv = Reservation(expires_at=date(2026, 9, 20), status=ReservationStatus.ACTIVE)
        assert resv.is_effective(date(2026, 9, 13)) is True

    def test_expired_after_expiry(self):
        resv = Reservation(expires_at=date(2026, 9, 20), status=ReservationStatus.ACTIVE)
        assert resv.is_expired(date(2026, 9, 21)) is True
        assert resv.is_effective(date(2026, 9, 21)) is False

    def test_cancel_and_fulfill(self):
        resv = Reservation(status=ReservationStatus.ACTIVE)
        resv.cancel()
        assert resv.status == ReservationStatus.CANCELLED
        resv2 = Reservation(status=ReservationStatus.ACTIVE)
        resv2.fulfill()
        assert resv2.status == ReservationStatus.FULFILLED


class TestBookReview:
    def test_rating_out_of_range_rejected(self):
        review = BookReview()
        with pytest.raises(BusinessError) as exc:
            review.update(6, "太好看了")
        assert exc.value.code == 400

    def test_update_resets_status_to_pending(self):
        review = BookReview()
        review.update(5, "good")
        review.approve()
        assert review.status == ReviewStatus.APPROVED
        review.update(4, "changed")
        assert review.status == ReviewStatus.PENDING
        assert review.is_visible() is False

    def test_approve_then_visible(self):
        review = BookReview()
        review.update(5, "good")
        review.approve()
        assert review.is_visible() is True

    def test_double_moderate_rejected(self):
        review = BookReview()
        review.update(5, "good")
        review.approve()
        with pytest.raises(BusinessError):
            review.approve()


class TestLibraryItem:
    def test_factory_creates_subclass(self):
        item = create_item(ItemType.BOOK, barcode="ITEM2026000001", title_id=1)
        assert isinstance(item, Book)

    def test_status_transition(self):
        item = Book(barcode="ITEM2026000001")
        assert item.is_available() is True
        item.mark_borrowed()
        assert item.status == ItemStatus.BORROWED
        assert item.is_available() is False
        item.mark_available()
        assert item.is_available() is True
        item.mark_removed()
        assert item.status == ItemStatus.REMOVED


class TestLostItem:
    def test_mark_paid_only_once(self):
        lost = LostItem(amount=79.60)
        lost.mark_paid()
        assert lost.paid is True
        with pytest.raises(BusinessError):
            lost.mark_paid()
