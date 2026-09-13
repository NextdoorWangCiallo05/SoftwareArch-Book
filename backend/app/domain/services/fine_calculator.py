"""罚款计算领域服务（UC-015）。

本身不持有单价与倍率，只做编排：接收逾期天数与规则，返回金额与是否需要生成记录。
"""

from decimal import Decimal

from app.domain.policies.compensation_policy import CompensationPolicy
from app.domain.policies.fine_rule import FineRule


class FineCalculator:
    """超期罚款计算。"""

    def calculate_amount(self, overdue_days: int, rule: FineRule) -> Decimal:
        return rule.calculate_fine(overdue_days)

    def needs_record(self, overdue_days: int, rule: FineRule) -> bool:
        """是否需要生成罚款记录（宽限期内不生成）。"""
        return rule.should_charge(overdue_days)


class CompensationCalculator:
    """丢失赔偿计算。"""

    def calculate_amount(self, price, policy: CompensationPolicy) -> Decimal:
        return policy.calculate_compensation(price)
