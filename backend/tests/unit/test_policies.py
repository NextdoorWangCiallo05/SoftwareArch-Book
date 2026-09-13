"""策略对象与领域服务单元测试。"""

from decimal import Decimal

import pytest

from app.core.exceptions import BusinessError
from app.domain.policies.borrow_policy import BorrowPolicy, BorrowPolicyTable
from app.domain.policies.compensation_policy import CompensationPolicy
from app.domain.policies.fine_rule import FineRule
from app.domain.services.circulation_policy_checker import (
    BorrowCheckContext,
    CirculationPolicyChecker,
)
from app.domain.services.fine_calculator import CompensationCalculator, FineCalculator
from app.domain.value_objects.enums import ItemStatus, ItemType, ReaderType


@pytest.fixture
def policy_table() -> BorrowPolicyTable:
    policies = [
        BorrowPolicy(ReaderType.ASSOCIATE, "ALL", 3, 30),
        BorrowPolicy(ReaderType.UNDERGRADUATE, "ALL", 5, 30),
        BorrowPolicy(ReaderType.GRADUATE, "ALL", 10, 60),
        BorrowPolicy(ReaderType.DOCTOR, "ALL", 15, 90),
        BorrowPolicy(ReaderType.TEACHER, "ALL", 20, 90),
        BorrowPolicy(ReaderType.UNDERGRADUATE, ItemType.MAGAZINE, 2, 7),
        BorrowPolicy(ReaderType.TEACHER, ItemType.THESIS, 2, 3),
    ]
    return BorrowPolicyTable(policies)


class TestBorrowPolicyTable:
    def test_main_rules(self, policy_table):
        assert policy_table.get_max_borrow_count(ReaderType.ASSOCIATE, ItemType.BOOK) == 3
        assert policy_table.get_borrow_days(ReaderType.GRADUATE, ItemType.BOOK) == 60
        assert policy_table.get_borrow_days(ReaderType.DOCTOR, ItemType.BOOK) == 90

    def test_item_type_override(self, policy_table):
        # 杂志覆盖：本科生借杂志 7 天、最多 2 本
        assert policy_table.get_borrow_days(ReaderType.UNDERGRADUATE, ItemType.MAGAZINE) == 7
        assert policy_table.get_max_borrow_count(ReaderType.UNDERGRADUATE, ItemType.MAGAZINE) == 2

    def test_fallback_to_all(self, policy_table):
        # 未配置 (UNDERGRADUATE, THESIS)，回退 (UNDERGRADUATE, ALL)
        assert policy_table.get_borrow_days(ReaderType.UNDERGRADUATE, ItemType.THESIS) == 30

    def test_can_borrow(self, policy_table):
        allowed, _ = policy_table.can_borrow(ReaderType.UNDERGRADUATE, ItemType.BOOK, 4)
        assert allowed is True
        allowed, reason = policy_table.can_borrow(ReaderType.UNDERGRADUATE, ItemType.BOOK, 5)
        assert allowed is False
        assert "借阅已满" in reason


class TestFineRule:
    def test_no_overdue(self):
        rule = FineRule("CHINESE_BOOK", 0, Decimal("0.50"))
        assert rule.calculate_fine(0) == Decimal("0.00")

    def test_without_grace(self):
        rule = FineRule("CHINESE_BOOK", 0, Decimal("0.50"))
        assert rule.calculate_fine(4) == Decimal("2.00")

    def test_within_grace_period(self):
        rule = FineRule("FOREIGN_BOOK", 3, Decimal("1.00"))
        assert rule.calculate_fine(3) == Decimal("0.00")
        assert rule.should_charge(3) is False

    def test_beyond_grace_period(self):
        rule = FineRule("FOREIGN_BOOK", 3, Decimal("1.00"))
        assert rule.chargeable_days(5) == 2
        assert rule.calculate_fine(5) == Decimal("2.00")

    def test_thesis_rate(self):
        rule = FineRule("THESIS", 0, Decimal("2.00"))
        assert rule.calculate_fine(2) == Decimal("4.00")


class TestCompensationPolicy:
    def test_book_rate(self):
        policy = CompensationPolicy(ItemType.BOOK, Decimal("2.00"))
        assert policy.calculate_compensation(Decimal("39.80")) == Decimal("79.60")

    def test_missing_price(self):
        policy = CompensationPolicy(ItemType.BOOK, Decimal("2.00"))
        with pytest.raises(BusinessError) as exc:
            policy.calculate_compensation(None)
        assert exc.value.code == 400


class TestCalculators:
    def test_fine_calculator(self):
        rule = FineRule("THESIS", 0, Decimal("2.00"))
        calc = FineCalculator()
        assert calc.calculate_amount(2, rule) == Decimal("4.00")
        assert calc.needs_record(2, rule) is True

    def test_fine_calculator_within_grace(self):
        rule = FineRule("FOREIGN_BOOK", 3, Decimal("1.00"))
        calc = FineCalculator()
        assert calc.calculate_amount(2, rule) == Decimal("0.00")
        assert calc.needs_record(2, rule) is False

    def test_compensation_calculator(self):
        policy = CompensationPolicy(ItemType.MAGAZINE, Decimal("1.50"))
        calc = CompensationCalculator()
        assert calc.calculate_amount(Decimal("60.00"), policy) == Decimal("90.00")


class TestCirculationPolicyChecker:
    def _ctx(self, **kwargs) -> BorrowCheckContext:
        base = dict(
            card_valid=True,
            active_count=0,
            max_borrow_count=5,
            has_overdue=False,
            has_unpaid_fine=False,
            has_unpaid_compensation=False,
            item_status=ItemStatus.AVAILABLE,
        )
        base.update(kwargs)
        return BorrowCheckContext(**base)

    def test_pass(self):
        CirculationPolicyChecker().check(self._ctx())

    def test_invalid_card(self):
        with pytest.raises(BusinessError) as exc:
            CirculationPolicyChecker().check(self._ctx(card_valid=False))
        assert "借阅证无效" in exc.value.message

    def test_quota_exceeded(self):
        with pytest.raises(BusinessError):
            CirculationPolicyChecker().check(self._ctx(active_count=5, max_borrow_count=5))

    def test_has_overdue(self):
        with pytest.raises(BusinessError):
            CirculationPolicyChecker().check(self._ctx(has_overdue=True))

    def test_unpaid_fine(self):
        with pytest.raises(BusinessError):
            CirculationPolicyChecker().check(self._ctx(has_unpaid_fine=True))

    def test_unpaid_compensation(self):
        with pytest.raises(BusinessError):
            CirculationPolicyChecker().check(self._ctx(has_unpaid_compensation=True))

    def test_item_not_available(self):
        with pytest.raises(BusinessError):
            CirculationPolicyChecker().check(self._ctx(item_status=ItemStatus.BORROWED))
