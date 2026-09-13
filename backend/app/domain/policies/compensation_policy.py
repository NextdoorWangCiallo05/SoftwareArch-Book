"""赔偿规则策略（BR-018a）。

赔偿金额 = 图书定价 × 倍率（BOOK=2.0 / MAGAZINE=1.5 / THESIS=3.0）
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Union

from app.core.exceptions import BusinessError
from app.domain.value_objects.enums import ItemType


@dataclass(frozen=True)
class CompensationPolicy:
    """赔偿策略（按出借物类型）。"""

    item_type: Union[ItemType, str]
    rate: Decimal = Decimal("1.00")

    def calculate_compensation(self, price: Optional[Decimal]) -> Decimal:
        """计算赔偿金额。"""
        if price is None:
            raise BusinessError("请先维护该图书定价")
        amount = Decimal(str(price)) * Decimal(self.rate)
        return amount.quantize(Decimal("0.01"))
