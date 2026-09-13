"""仓储实现集成测试（TASK-005）。"""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.domain.entities.circulation import Loan, LostItem, Reservation
from app.domain.entities.identity import BorrowCard, Reader
from app.domain.entities.review import BookReview
from app.domain.policies.borrow_policy import BorrowPolicy, BorrowPolicyTable
from app.domain.value_objects.enums import (
    CardStatus,
    ItemStatus,
    ItemType,
    LoanStatus,
    ReaderType,
    ReservationStatus,
    ReviewStatus,
)
from app.infrastructure.repositories.account_repository import SQLAlchemyAccountRepository
from app.infrastructure.repositories.catalog_repository import (
    SQLAlchemyItemRepository,
    SQLAlchemyTitleRepository,
)
from app.infrastructure.repositories.circulation_repository import (
    SQLAlchemyFineRepository,
    SQLAlchemyLoanRepository,
    SQLAlchemyLostRepository,
)
from app.infrastructure.repositories.policy_repository import SQLAlchemyPolicyRepository
from app.infrastructure.repositories.reader_repository import (
    SQLAlchemyBorrowCardRepository,
    SQLAlchemyReaderRepository,
)
from app.infrastructure.repositories.reservation_repository import (
    SQLAlchemyReservationRepository,
)
from app.infrastructure.repositories.review_repository import SQLAlchemyReviewRepository


class TestAccountRepository:
    def test_add_and_find(self, db):
        from app.domain.entities.identity import Account
        from app.domain.value_objects.enums import Role

        repo = SQLAlchemyAccountRepository(db)
        account = Account(username="lisi", password_hash="h", salt="s", role=Role.READER)
        repo.add(account)
        db.commit()

        found = repo.find_by_username("lisi")
        assert found is not None
        assert found.role == Role.READER

    def test_find_by_username_not_found(self, db):
        assert SQLAlchemyAccountRepository(db).find_by_username("nobody") is None


class TestReaderRepository:
    def test_get_and_search(self, db, seeded):
        repo = SQLAlchemyReaderRepository(db)
        reader = repo.get(seeded["reader_id"])
        assert reader is not None
        assert reader.name == "张三"
        assert reader.reader_type == ReaderType.UNDERGRADUATE

        rows, total = repo.search(name="张", reader_type=None, page=1, page_size=10)
        assert total == 1
        assert rows[0].id == seeded["reader_id"]

    def test_save_updates_fields(self, db, seeded):
        repo = SQLAlchemyReaderRepository(db)
        reader = repo.get(seeded["reader_id"])
        reader.name = "张三丰"
        reader.reader_type = ReaderType.GRADUATE
        repo.save(reader)
        db.commit()

        reloaded = repo.get(seeded["reader_id"])
        assert reloaded.name == "张三丰"
        assert reloaded.reader_type == ReaderType.GRADUATE


class TestBorrowCardRepository:
    def test_find_by_no_and_active(self, db, seeded):
        repo = SQLAlchemyBorrowCardRepository(db)
        card = repo.find_by_no("CARD2026000001")
        assert card is not None
        assert card.is_valid() is True

        active = repo.find_active_by_reader(seeded["reader_id"])
        assert active is not None and active.card_no == "CARD2026000001"

    def test_only_one_active_card_per_reader(self, db, seeded):
        """部分唯一索引：同一读者不能有两张 ACTIVE 借阅证。"""
        repo = SQLAlchemyBorrowCardRepository(db)
        with pytest.raises(IntegrityError):
            repo.add(BorrowCard(card_no="CARD2026000002", reader_id=seeded["reader_id"],
                                status=CardStatus.ACTIVE))
        db.rollback()


class TestCatalogRepository:
    def test_find_available_item(self, db, seeded):
        repo = SQLAlchemyItemRepository(db)
        item = repo.find_available_by_title(seeded["title_id"])
        assert item is not None
        assert item.is_available() is True

        item.mark_borrowed()
        repo.save(item)
        db.commit()

        another = repo.find_available_by_title(seeded["title_id"])
        assert another is not None
        assert another.barcode == "ITEM2026000002"

    def test_search_titles(self, db, seeded):
        repo = SQLAlchemyTitleRepository(db)
        rows, total = repo.search(keyword="三体", author=None, category=None,
                                  item_type=None, page=1, page_size=10)
        assert total == 1
        assert rows[0].title == "三体"
        assert rows[0].price == Decimal("39.80")


class TestLoanRepository:
    def test_count_active_with_item_type(self, db, seeded):
        repo = SQLAlchemyLoanRepository(db)
        today = seeded["today"]
        repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                      borrow_date=today, due_date=today + timedelta(days=30),
                      status=LoanStatus.BORROWED))
        db.commit()

        assert repo.count_active(seeded["reader_id"]) == 1
        # 按杂志维度统计（库中该读者的在借记录是图书）
        assert repo.count_active(seeded["reader_id"], ItemType.MAGAZINE) == 0

    def test_count_overdue(self, db, seeded):
        repo = SQLAlchemyLoanRepository(db)
        today = seeded["today"]
        repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                      borrow_date=today - timedelta(days=40),
                      due_date=today - timedelta(days=10),
                      status=LoanStatus.BORROWED))
        db.commit()
        assert repo.count_overdue(seeded["reader_id"], today) == 1

    def test_only_one_active_loan_per_item(self, db, seeded):
        """部分唯一索引：同一副本同时只能有一条 BORROWED 记录。"""
        repo = SQLAlchemyLoanRepository(db)
        today = seeded["today"]
        repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                      borrow_date=today, due_date=today, status=LoanStatus.BORROWED))
        db.commit()
        with pytest.raises(IntegrityError):
            repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                          borrow_date=today, due_date=today, status=LoanStatus.BORROWED))
        db.rollback()

    def test_has_active_loan_of_title(self, db, seeded):
        repo = SQLAlchemyLoanRepository(db)
        today = seeded["today"]
        repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                      borrow_date=today, due_date=today, status=LoanStatus.BORROWED))
        db.commit()
        assert repo.has_active_loan_of_title(seeded["reader_id"], seeded["title_id"]) is True


class TestFineAndLostRepository:
    def test_has_unpaid_fine(self, db, seeded):
        loan_repo = SQLAlchemyLoanRepository(db)
        fine_repo = SQLAlchemyFineRepository(db)
        today = seeded["today"]
        loan = loan_repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                                  borrow_date=today, due_date=today,
                                  status=LoanStatus.BORROWED))
        db.commit()
        assert fine_repo.has_unpaid(seeded["reader_id"]) is False

        from app.domain.entities.circulation import FineRecord

        fine_repo.add(FineRecord(loan_id=loan.id, amount=Decimal("2.00")))
        db.commit()
        assert fine_repo.has_unpaid(seeded["reader_id"]) is True

    def test_has_unpaid_lost(self, db, seeded):
        loan_repo = SQLAlchemyLoanRepository(db)
        lost_repo = SQLAlchemyLostRepository(db)
        today = seeded["today"]
        loan = loan_repo.add(Loan(reader_id=seeded["reader_id"], item_id=1,
                                  borrow_date=today, due_date=today,
                                  status=LoanStatus.BORROWED))
        db.commit()
        lost_repo.add(LostItem(loan_id=loan.id, item_id=1, lost_date=today,
                               amount=Decimal("79.60")))
        db.commit()
        assert lost_repo.has_unpaid(seeded["reader_id"]) is True


class TestReservationRepository:
    def test_has_effective_and_expiry(self, db, seeded):
        repo = SQLAlchemyReservationRepository(db)
        today = seeded["today"]
        resv = Reservation(reader_id=seeded["reader_id"], title_id=seeded["title_id"],
                           created_at=datetime.now(), expires_at=today + timedelta(days=7),
                           status=ReservationStatus.ACTIVE, queue_position=1)
        repo.add(resv)
        db.commit()

        assert repo.has_effective(seeded["reader_id"], seeded["title_id"], today) is True
        # 超过有效期后视为失效（惰性判定）
        later = today + timedelta(days=8)
        assert repo.has_effective(seeded["reader_id"], seeded["title_id"], later) is False

    def test_queue_position(self, db, seeded):
        repo = SQLAlchemyReservationRepository(db)
        today = seeded["today"]
        now = datetime.now()
        repo.add(Reservation(reader_id=seeded["reader_id"], title_id=seeded["title_id"],
                             created_at=now - timedelta(hours=1),
                             expires_at=today + timedelta(days=7),
                             status=ReservationStatus.ACTIVE, queue_position=1))
        db.commit()
        count = repo.count_effective_before(seeded["title_id"], now, today)
        assert count == 1


class TestReviewRepository:
    def test_save_creates_then_updates(self, db, seeded):
        repo = SQLAlchemyReviewRepository(db)
        review = BookReview(title_id=seeded["title_id"], reader_id=seeded["reader_id"])
        review.update(5, "太好看了")
        repo.save(review)
        db.commit()

        found = repo.find_by_reader_and_title(seeded["reader_id"], seeded["title_id"])
        assert found is not None
        assert found.status == ReviewStatus.PENDING

        found.approve()
        repo.save(found)
        db.commit()

        approved = repo.list_by_status(seeded["title_id"], ReviewStatus.APPROVED)
        assert len(approved) == 1
        assert approved[0].rating == 5


class TestPolicyRepository:
    def test_load_two_dimensional_policies(self, db, seeded):
        repo = SQLAlchemyPolicyRepository(db)
        table = BorrowPolicyTable(repo.borrow_policies())

        assert table.get_borrow_days(ReaderType.UNDERGRADUATE, ItemType.BOOK) == 30
        # 杂志维度覆盖
        assert table.get_borrow_days(ReaderType.UNDERGRADUATE, ItemType.MAGAZINE) == 7
        assert table.get_max_borrow_count(ReaderType.UNDERGRADUATE, ItemType.MAGAZINE) == 2

    def test_fine_rule_with_grace_days(self, db, seeded):
        repo = SQLAlchemyPolicyRepository(db)
        rule = repo.get_fine_rule("FOREIGN_BOOK")
        assert rule is not None
        assert rule.grace_days == 3
        assert rule.amount_per_day == Decimal("1.00")

    def test_upsert_borrow_policy(self, db, seeded):
        repo = SQLAlchemyPolicyRepository(db)
        repo.upsert_borrow_policy(
            BorrowPolicy(ReaderType.UNDERGRADUATE, ItemType.THESIS, 2, 3)
        )
        db.commit()
        table = BorrowPolicyTable(repo.borrow_policies())
        assert table.get_borrow_days(ReaderType.UNDERGRADUATE, ItemType.THESIS) == 3
