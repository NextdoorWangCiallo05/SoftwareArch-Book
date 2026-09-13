"""借书前置校验领域服务（Facade）。

集中执行 BR-001 ~ BR-006 的校验，供应用服务调用；
只抛出领域异常，不感知 HTTP 状态码。
"""

from dataclasses import dataclass

from app.core.exceptions import BusinessError
from app.domain.value_objects.enums import ItemStatus


@dataclass
class BorrowCheckContext:
    """借书前置校验所需的全部上下文（由应用服务组装，领域服务不依赖仓储）。"""

    card_valid: bool
    active_count: int
    max_borrow_count: int
    has_overdue: bool
    has_unpaid_fine: bool
    has_unpaid_compensation: bool
    item_status: ItemStatus


class CirculationPolicyChecker:
    """借书前置校验。"""

    def check(self, ctx: BorrowCheckContext) -> None:
        # BR-001 借阅证有效
        if not ctx.card_valid:
            raise BusinessError("借阅证无效")

        # BR-002 数量上限
        if ctx.active_count >= ctx.max_borrow_count:
            raise BusinessError(
                f"借阅已满（{ctx.active_count}/{ctx.max_borrow_count}），请先归还图书"
            )

        # BR-003 超期未还
        if ctx.has_overdue:
            raise BusinessError("有超期未还图书，请先归还")

        # BR-006 未缴罚款 / 未缴赔偿
        if ctx.has_unpaid_fine or ctx.has_unpaid_compensation:
            raise BusinessError("存在未缴罚款或赔偿，请先缴清")

        # BR-010 副本状态
        if ctx.item_status != ItemStatus.AVAILABLE:
            raise BusinessError("该馆藏不可借")
