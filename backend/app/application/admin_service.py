"""系统管理应用服务（FR-004 ~ FR-007、FR-028 ~ FR-030）。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, NotFoundError
from app.domain.entities.identity import Account, BorrowCard, Librarian
from app.domain.policies.borrow_policy import BorrowPolicy
from app.domain.policies.fine_rule import FineRule
from app.domain.value_objects.enums import ReaderStatus, Role
from app.infrastructure.repositories.account_repository import SQLAlchemyAccountRepository
from app.infrastructure.repositories.circulation_repository import SQLAlchemyLoanRepository
from app.infrastructure.repositories.policy_repository import SQLAlchemyPolicyRepository
from app.infrastructure.repositories.reader_repository import (
    SQLAlchemyBorrowCardRepository,
    SQLAlchemyLibrarianRepository,
    SQLAlchemyReaderRepository,
)
from app.infrastructure.security.password_hasher import Pbkdf2PasswordHasher


class AdminService:
    def __init__(self, db: Session):
        self.db = db
        self.accounts = SQLAlchemyAccountRepository(db)
        self.readers = SQLAlchemyReaderRepository(db)
        self.librarians = SQLAlchemyLibrarianRepository(db)
        self.cards = SQLAlchemyBorrowCardRepository(db)
        self.loans = SQLAlchemyLoanRepository(db)
        self.policies = SQLAlchemyPolicyRepository(db)
        self.hasher = Pbkdf2PasswordHasher()

    # ---------- 借阅证（FR-004 / FR-005） ----------

    def issue_card(self, reader_id: int) -> BorrowCard:
        reader = self.readers.get(reader_id)
        if reader is None:
            raise NotFoundError("读者不存在")
        if self.cards.find_active_by_reader(reader_id) is not None:
            raise BusinessError("该读者已持有有效借阅证")

        card_no = self._next_card_no()
        card = self.cards.add(
            BorrowCard(card_no=card_no, reader_id=reader_id)
        )
        self.db.commit()
        return card

    def revoke_card(self, card_id: int) -> BorrowCard:
        card = self.cards.get(card_id)
        if card is None:
            raise NotFoundError("借阅证不存在")
        if self.loans.count_active(card.reader_id) > 0:
            raise BusinessError("请先归还全部图书后再注销借阅证")
        card.revoke()
        saved = self.cards.save(card)
        self.db.commit()
        return saved

    def _next_card_no(self) -> str:
        year = datetime.now().year
        # 顺序探测首个未被占用的证号（教学项目，够用且可读）
        seq = 1
        while self.cards.find_by_no(f"CARD{year}{seq:06d}") is not None:
            seq += 1
        return f"CARD{year}{seq:06d}"

    # ---------- 图书管理员（FR-006 / FR-007 / FR-029） ----------

    def add_librarian(self, req) -> Librarian:
        if self.accounts.find_by_username(req.username) is not None:
            raise BusinessError("用户名已存在")
        password_hash, salt = self.hasher.hash(req.password)
        account = self.accounts.add(
            Account(username=req.username, password_hash=password_hash,
                    salt=salt, role=Role.LIBRARIAN)
        )
        librarian = self.librarians.add(
            Librarian(account_id=account.id, name=req.name, employee_no=req.employee_no)
        )
        self.db.commit()
        return librarian

    def list_librarians(self, page: int, page_size: int):
        return self.librarians.list(page, page_size)

    def update_librarian(self, librarian_id: int, req) -> Librarian:
        librarian = self.librarians.get(librarian_id)
        if librarian is None:
            raise NotFoundError("管理员不存在")
        if req.name is not None:
            librarian.name = req.name
        if req.employee_no is not None:
            librarian.employee_no = req.employee_no
        saved = self.librarians.save(librarian)
        self.db.commit()
        return saved

    def remove_librarian(self, librarian_id: int) -> None:
        if self.librarians.get(librarian_id) is None:
            raise NotFoundError("管理员不存在")
        self.librarians.delete(librarian_id)
        self.db.commit()

    # ---------- 借阅者（FR-028） ----------

    def list_readers(self, name, reader_type, page, page_size):
        return self.readers.search(name, reader_type, page, page_size)

    def update_reader(self, reader_id: int, req):
        reader = self.readers.get(reader_id)
        if reader is None:
            raise NotFoundError("读者不存在")
        if req.name is not None:
            reader.name = req.name
        if req.reader_type is not None:
            reader.reader_type = req.reader_type
        if req.email is not None:
            reader.email = req.email
        if req.phone is not None:
            reader.phone = req.phone
        saved = self.readers.save(reader)
        self.db.commit()
        return saved

    def deactivate_reader(self, reader_id: int):
        reader = self.readers.get(reader_id)
        if reader is None:
            raise NotFoundError("读者不存在")
        if self.loans.count_active(reader_id) > 0:
            raise BusinessError("请先归还全部图书")
        reader.status = ReaderStatus.INACTIVE
        saved = self.readers.save(reader)
        self.db.commit()
        return saved

    # ---------- 规则维护（FR-025 / FR-026） ----------

    def upsert_borrow_policy(self, reader_type, item_type, max_borrow_count, borrow_days):
        if max_borrow_count <= 0 or borrow_days <= 0:
            raise BusinessError("借阅数量与期限必须大于 0")
        policy = BorrowPolicy(
            reader_type=reader_type,
            item_type=item_type,
            max_borrow_count=max_borrow_count,
            borrow_days=borrow_days,
        )
        saved = self.policies.upsert_borrow_policy(policy)
        self.db.commit()
        return saved

    def upsert_fine_rule(self, item_category, grace_days, amount_per_day):
        if grace_days < 0 or amount_per_day < 0:
            raise BusinessError("宽限期与罚款金额不能为负")
        rule = FineRule(
            item_category=item_category,
            grace_days=grace_days,
            amount_per_day=amount_per_day,
        )
        saved = self.policies.upsert_fine_rule(rule)
        self.db.commit()
        return saved

    def list_borrow_policies(self):
        """列出全部借阅规则（供管理端规则页展示当前配置）。"""
        return self.policies.borrow_policies()

    def list_fine_rules(self):
        """列出全部罚款规则。"""
        return self.policies.fine_rules()
