"""借阅规则策略（BR-002 / BR-004）。

策略键为二维 (reader_type, item_type)，对应指导书参考类图中的
「本科生借书策略 / 研究生借杂志策略」与「书到期策略 / 杂志到期策略」。
本实现以可配置策略表 + 策略对象替代继承体系，规则可运行时调整。
"""

from dataclasses import dataclass
from typing import Iterable, Optional, Union

from app.domain.value_objects.enums import ItemType, ReaderType

ALL = "ALL"


@dataclass(frozen=True)
class BorrowPolicy:
    """单条借阅规则。"""

    reader_type: Union[ReaderType, str]
    item_type: Union[ItemType, str]
    max_borrow_count: int
    borrow_days: int


class BorrowPolicyTable:
    """借阅规则表：解析二维策略键，未命中时回退 (reader_type, ALL)。"""

    def __init__(self, policies: Iterable[BorrowPolicy]):
        self._by_key = {
            (str(p.reader_type), str(p.item_type)): p for p in policies
        }

    def resolve(
        self,
        reader_type: Union[ReaderType, str],
        item_type: Union[ItemType, str],
    ) -> BorrowPolicy:
        key = (str(reader_type), str(item_type))
        if key in self._by_key:
            return self._by_key[key]
        fallback = (str(reader_type), ALL)
        if fallback in self._by_key:
            return self._by_key[fallback]
        raise KeyError(f"未配置借阅规则：{key}")

    def get_max_borrow_count(
        self,
        reader_type: Union[ReaderType, str],
        item_type: Union[ItemType, str],
    ) -> int:
        return self.resolve(reader_type, item_type).max_borrow_count

    def get_borrow_days(
        self,
        reader_type: Union[ReaderType, str],
        item_type: Union[ItemType, str],
    ) -> int:
        return self.resolve(reader_type, item_type).borrow_days

    def can_borrow(
        self,
        reader_type: Union[ReaderType, str],
        item_type: Union[ItemType, str],
        active_count: int,
    ) -> tuple[bool, Optional[str]]:
        """数量是否允许再借，返回 (是否允许, 不允许时的原因)。"""
        policy = self.resolve(reader_type, item_type)
        if active_count >= policy.max_borrow_count:
            return False, f"借阅已满（{active_count}/{policy.max_borrow_count}），请先归还图书"
        return True, None
