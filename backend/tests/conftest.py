"""测试公共 fixture：使用独立的临时 SQLite 库，不污染运行库。"""

from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.base import Base
from app.infrastructure.models import orm  # noqa: F401  确保模型被注册
from app.infrastructure.models.orm import (
    AccountORM,
    BookTitleORM,
    BorrowCardORM,
    BorrowPolicyORM,
    CompensationPolicyORM,
    FineRuleORM,
    LibraryItemORM,
    ReaderORM,
)


@pytest.fixture()
def db():
    """每个用例一套全新内存数据库。

    注意：使用 StaticPool 保证同一连接，避免内存库跨连接丢表。
    """
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture()
def seeded(db):
    """写入最小可用种子：策略、读者、借阅证、图书与副本。"""
    # 借阅规则（主规则 + 杂志覆盖）
    db.add(BorrowPolicyORM(reader_type="UNDERGRADUATE", item_type="ALL",
                           max_borrow_count=5, borrow_days=30))
    db.add(BorrowPolicyORM(reader_type="UNDERGRADUATE", item_type="MAGAZINE",
                           max_borrow_count=2, borrow_days=7))
    # 罚款规则（含宽限期）
    db.add(FineRuleORM(item_category="CHINESE_BOOK", grace_days=0, amount_per_day="0.50"))
    db.add(FineRuleORM(item_category="FOREIGN_BOOK", grace_days=3, amount_per_day="1.00"))
    db.add(CompensationPolicyORM(item_type="BOOK", rate="2.00"))

    account = AccountORM(username="zhangsan", password_hash="h", salt="s", role="reader")
    db.add(account)
    db.flush()
    reader = ReaderORM(account_id=account.id, name="张三", reader_type="UNDERGRADUATE")
    db.add(reader)
    db.flush()
    db.add(BorrowCardORM(card_no="CARD2026000001", reader_id=reader.id, status="ACTIVE"))

    title = BookTitleORM(title="三体", author="刘慈欣", isbn="ISBN-001",
                         item_type="BOOK", price="39.80")
    db.add(title)
    db.flush()
    db.add(LibraryItemORM(barcode="ITEM2026000001", title_id=title.id, item_type="BOOK",
                          status="AVAILABLE", fine_category="CHINESE_BOOK"))
    db.add(LibraryItemORM(barcode="ITEM2026000002", title_id=title.id, item_type="BOOK",
                          status="AVAILABLE", fine_category="CHINESE_BOOK"))
    db.commit()

    return {
        "account_id": account.id,
        "reader_id": reader.id,
        "title_id": title.id,
        "today": date.today(),
        "future": date.today() + timedelta(days=30),
    }
