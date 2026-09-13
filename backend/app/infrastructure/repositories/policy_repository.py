"""借阅规则、罚款规则与赔偿策略仓储实现。"""

from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.policies.borrow_policy import BorrowPolicy
from app.domain.policies.compensation_policy import CompensationPolicy
from app.domain.policies.fine_rule import FineRule
from app.domain.value_objects.enums import ItemType, ReaderType
from app.infrastructure.models.orm import (
    BorrowPolicyORM,
    CompensationPolicyORM,
    FineRuleORM,
)


class SQLAlchemyPolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    # ---------- 借阅规则 ----------

    def borrow_policies(self) -> list[BorrowPolicy]:
        rows = self.db.query(BorrowPolicyORM).all()
        return [
            BorrowPolicy(
                reader_type=ReaderType(r.reader_type),
                item_type=r.item_type,
                max_borrow_count=r.max_borrow_count,
                borrow_days=r.borrow_days,
            )
            for r in rows
        ]

    def upsert_borrow_policy(self, policy: BorrowPolicy) -> BorrowPolicy:
        orm = (
            self.db.query(BorrowPolicyORM)
            .filter(
                BorrowPolicyORM.reader_type == str(policy.reader_type),
                BorrowPolicyORM.item_type == str(policy.item_type),
            )
            .first()
        )
        if orm is None:
            orm = BorrowPolicyORM(
                reader_type=str(policy.reader_type),
                item_type=str(policy.item_type),
            )
            self.db.add(orm)
        orm.max_borrow_count = policy.max_borrow_count
        orm.borrow_days = policy.borrow_days
        self.db.flush()
        return policy

    # ---------- 罚款规则 ----------

    def get_fine_rule(self, item_category: str) -> FineRule | None:
        orm = (
            self.db.query(FineRuleORM)
            .filter(FineRuleORM.item_category == item_category)
            .first()
        )
        if orm is None:
            return None
        return FineRule(
            item_category=orm.item_category,
            grace_days=orm.grace_days,
            amount_per_day=Decimal(str(orm.amount_per_day)),
        )

    def upsert_fine_rule(self, rule: FineRule) -> FineRule:
        orm = (
            self.db.query(FineRuleORM)
            .filter(FineRuleORM.item_category == rule.item_category)
            .first()
        )
        if orm is None:
            orm = FineRuleORM(item_category=rule.item_category)
            self.db.add(orm)
        orm.grace_days = rule.grace_days
        orm.amount_per_day = rule.amount_per_day
        self.db.flush()
        return rule

    # ---------- 赔偿策略 ----------

    def get_compensation_policy(self, item_type: ItemType) -> CompensationPolicy | None:
        orm = (
            self.db.query(CompensationPolicyORM)
            .filter(CompensationPolicyORM.item_type == str(item_type))
            .first()
        )
        if orm is None:
            return None
        return CompensationPolicy(item_type=orm.item_type, rate=Decimal(str(orm.rate)))
