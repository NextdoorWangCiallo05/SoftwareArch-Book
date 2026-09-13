"""罚款规则策略（BR-005，含宽限期）。

计费公式：计费天数 = max(0, 逾期天数 - grace_days)；罚款 = 计费天数 × amount_per_day
"""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FineRule:
    """罚款规则（按出借物罚款档位）。"""

    item_category: str
    grace_days: int = 0
    amount_per_day: Decimal = Decimal("0.00")

    def chargeable_days(self, overdue_days: int) -> int:
        """计费天数：扣除宽限期后的天数。"""
        return max(0, overdue_days - self.grace_days)

    def should_charge(self, overdue_days: int) -> bool:
        """是否需要计费（宽限期内不计费，但仍判定为超期）。"""
        return self.chargeable_days(overdue_days) > 0

    def calculate_fine(self, overdue_days: int) -> Decimal:
        """计算罚款金额，保留 2 位小数。"""
        if overdue_days <= 0:
            return Decimal("0.00")
        amount = Decimal(self.chargeable_days(overdue_days)) * Decimal(self.amount_per_day)
        return amount.quantize(Decimal("0.01"))
