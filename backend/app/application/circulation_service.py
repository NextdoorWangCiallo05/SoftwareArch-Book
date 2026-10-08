"""流通应用服务（FR-014 ~ FR-017、FR-020 ~ FR-022、FR-027）。

用例编排与事务边界均在本层：借书、还书、续借、查询、罚款与赔偿。
业务规则委托给领域策略与领域服务，本层不硬编码任何规则数值。
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError, InfrastructureError, NotFoundError
from app.domain.entities.circulation import FineRecord, Loan, LostItem
from app.domain.policies.borrow_policy import BorrowPolicyTable
from app.domain.services.circulation_policy_checker import (
    BorrowCheckContext,
    CirculationPolicyChecker,
)
from app.domain.services.fine_calculator import CompensationCalculator, FineCalculator
from app.domain.value_objects.enums import ItemStatus, LoanStatus
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
from app.schemas.circulation import (
    BorrowResultDTO,
    FineDTO,
    LoanDTO,
    LostResultDTO,
    RenewResultDTO,
    ReturnRequestDTO,
    ReturnResultDTO,
)


class CirculationService:
    def __init__(self, db: Session):
        self.db = db
        self.cards = SQLAlchemyBorrowCardRepository(db)
        self.readers = SQLAlchemyReaderRepository(db)
        self.items = SQLAlchemyItemRepository(db)
        self.titles = SQLAlchemyTitleRepository(db)
        self.loans = SQLAlchemyLoanRepository(db)
        self.fines = SQLAlchemyFineRepository(db)
        self.losts = SQLAlchemyLostRepository(db)
        self.policies = SQLAlchemyPolicyRepository(db)
        self.reservations = SQLAlchemyReservationRepository(db)
        self.checker = CirculationPolicyChecker()
        self.fine_calc = FineCalculator()
        self.comp_calc = CompensationCalculator()

    # ---------- 借书（UC-009） ----------

    def borrow(self, card_no: str, barcode: str, today: date | None = None) -> BorrowResultDTO:
        today = today or date.today()

        card = self.cards.find_by_no(card_no)
        if card is None:
            raise NotFoundError("借阅证不存在")
        reader = self.readers.get(card.reader_id)
        if reader is None:
            raise NotFoundError("读者不存在")

        item = self.items.find_by_barcode(barcode)
        if item is None:
            raise NotFoundError("馆藏不存在")

        table = BorrowPolicyTable(self.policies.borrow_policies())
        self.checker.check(
            BorrowCheckContext(
                card_valid=card.is_valid(),
                active_count=self.loans.count_active(reader.id, item.item_type),
                max_borrow_count=table.get_max_borrow_count(reader.reader_type, item.item_type),
                has_overdue=self.loans.count_overdue(reader.id, today) > 0,
                has_unpaid_fine=self.fines.has_unpaid(reader.id),
                has_unpaid_compensation=self.losts.has_unpaid(reader.id),
                item_status=item.status,
            )
        )

        borrow_days = table.get_borrow_days(reader.reader_type, item.item_type)
        loan = Loan(
            reader_id=reader.id,
            item_id=item.id,
            borrow_date=today,
            due_date=today + timedelta(days=borrow_days),
            status=LoanStatus.BORROWED,
        )
        item.mark_borrowed()
        # 同一事务：创建借阅记录 + 更新副本状态
        self.loans.add(loan)
        self.items.save(item)
        self.db.commit()

        title = self.titles.get(item.title_id)
        return BorrowResultDTO(
            loan_id=loan.id,
            title=title.title if title else "",
            barcode=item.barcode,
            borrow_date=today.isoformat(),
            due_date=loan.due_date.isoformat(),
        )

    # ---------- 还书（UC-010 / UC-015，BR-020 两段式流程） ----------

    def request_return(self, loan_id: int, today: date | None = None) -> ReturnRequestDTO:
        """读者发起归还申请：BORROWED → RETURN_REQUESTED（书仍在读者手上）。"""
        today = today or date.today()

        loan = self.loans.get(loan_id)
        if loan is None:
            raise NotFoundError("借阅记录不存在")

        loan.request_return()
        self.loans.save(loan)
        self.db.commit()
        return self._to_return_request_dto(loan, today)

    def list_return_requests(self, today: date | None = None) -> list[ReturnRequestDTO]:
        """待审核的归还申请清单（馆员审核台）。"""
        today = today or date.today()
        result = []
        for row in self.loans.list_return_requests():
            due = row["due_date"]
            is_overdue = bool(due) and date.fromisoformat(due) < today
            result.append(
                ReturnRequestDTO(
                    **row,
                    is_overdue=is_overdue,
                    status=LoanStatus.RETURN_REQUESTED.value,
                )
            )
        return result

    def approve_return(self, loan_id: int, today: date | None = None) -> ReturnResultDTO:
        """馆员审核通过：确认收到图书，执行归还与超期罚款结算。"""
        today = today or date.today()

        loan = self.loans.get(loan_id)
        if loan is None:
            raise NotFoundError("借阅记录不存在")
        if loan.status != LoanStatus.RETURN_REQUESTED:
            raise BusinessError("该借阅记录没有待审核的归还申请")

        item = self.items.get(loan.item_id)
        if item is None:
            raise NotFoundError("馆藏不存在")

        return self._settle_return(item, loan, today)

    def reject_return(self, loan_id: int, today: date | None = None) -> ReturnRequestDTO:
        """馆员驳回：未收到图书，借阅记录退回在借状态。"""
        today = today or date.today()

        loan = self.loans.get(loan_id)
        if loan is None:
            raise NotFoundError("借阅记录不存在")

        loan.reject_return_request()
        self.loans.save(loan)
        self.db.commit()
        return self._to_return_request_dto(loan, today)

    def return_book(self, barcode: str, today: date | None = None) -> ReturnResultDTO:
        """馆员现场办理还书（条码直办，读者无需先提交归还申请）。"""
        today = today or date.today()

        item = self.items.find_by_barcode(barcode)
        if item is None:
            raise BusinessError("非本馆藏书")

        loan = self.loans.find_active_by_item(item.id)
        if loan is None:
            raise BusinessError("未找到该馆藏的借阅记录")

        return self._settle_return(item, loan, today)

    def _settle_return(self, item, loan: Loan, today: date) -> ReturnResultDTO:
        """归还结算：更新借阅记录 + 副本回架 + 超期罚款，同一事务提交。"""
        overdue_days = loan.return_item(today)
        item.mark_available()

        fine = Decimal("0.00")
        if overdue_days > 0:
            rule = self.policies.get_fine_rule(item.fine_category)
            if rule is None:
                raise InfrastructureError("未配置罚款规则")
            if self.fine_calc.needs_record(overdue_days, rule):
                fine = self.fine_calc.calculate_amount(overdue_days, rule)
                self.fines.add(FineRecord(loan_id=loan.id, amount=fine))

        # 同一事务：更新借阅记录 + 副本状态 + 罚款记录
        self.loans.save(loan)
        self.items.save(item)
        self.db.commit()

        title = self.titles.get(item.title_id)
        return ReturnResultDTO(
            loan_id=loan.id,
            title=title.title if title else "",
            return_date=today.isoformat(),
            overdue_days=overdue_days,
            fine=fine,
        )

    def _to_return_request_dto(self, loan: Loan, today: date | None = None) -> ReturnRequestDTO:
        today = today or date.today()
        item = self.items.get(loan.item_id)
        title = self.titles.get(item.title_id) if item else None
        reader = self.readers.get(loan.reader_id)
        return ReturnRequestDTO(
            loan_id=loan.id,
            reader_id=loan.reader_id,
            reader_name=reader.name if reader else "",
            title=title.title if title else "",
            barcode=item.barcode if item else "",
            borrow_date=loan.borrow_date.isoformat() if loan.borrow_date else None,
            due_date=loan.due_date.isoformat() if loan.due_date else None,
            is_overdue=loan.is_overdue(today),
            renew_count=loan.renew_count,
            status=str(loan.status),
        )

    # ---------- 续借（UC-011） ----------

    def renew(self, loan_id: int, today: date | None = None) -> RenewResultDTO:
        today = today or date.today()

        loan = self.loans.get(loan_id)
        if loan is None:
            raise NotFoundError("借阅记录不存在")

        item = self.items.get(loan.item_id)
        if item is None:
            raise NotFoundError("馆藏不存在")

        title_id = item.title_id
        # 是否存在他人未过期的有效预约
        has_other = self.reservations.count_effective_by_others(
            title_id, loan.reader_id, today
        ) > 0

        table = BorrowPolicyTable(self.policies.borrow_policies())
        borrow_days = table.get_borrow_days(self._reader_type_of(loan), item.item_type)
        new_due = loan.renew(borrow_days, today, has_other_active_reservation=has_other)

        self.loans.save(loan)
        self.db.commit()

        title = self.titles.get(title_id)
        return RenewResultDTO(
            loan_id=loan.id,
            title=title.title if title else "",
            new_due_date=new_due.isoformat(),
            renew_count=loan.renew_count,
        )

    def _reader_type_of(self, loan: Loan):
        reader = self.readers.get(loan.reader_id)
        return reader.reader_type if reader else "UNDERGRADUATE"

    # ---------- 查询借阅记录（FR-017） ----------

    def list_loans(self, reader_id: int, status: LoanStatus | None,
                   today: date | None = None) -> list[LoanDTO]:
        today = today or date.today()
        rows = self.loans.list_by_reader(reader_id, status)
        result = []
        for loan in rows:
            item = self.items.get(loan.item_id)
            title = self.titles.get(item.title_id) if item else None
            result.append(
                LoanDTO(
                    loan_id=loan.id,
                    title=title.title if title else "",
                    barcode=item.barcode if item else "",
                    borrow_date=loan.borrow_date.isoformat() if loan.borrow_date else None,
                    due_date=loan.due_date.isoformat() if loan.due_date else None,
                    return_date=loan.return_date.isoformat() if loan.return_date else None,
                    status=str(loan.status),
                    is_overdue=loan.is_overdue(today),
                    renew_count=loan.renew_count,
                )
            )
        return result

    # ---------- 罚款缴清（UC-016） ----------

    def pay_fine(self, fine_id: int) -> FineDTO:
        fine = self.fines.get(fine_id)
        if fine is None:
            raise NotFoundError("罚款记录不存在")
        fine.mark_paid()
        self.fines.save(fine)
        self.db.commit()
        return FineDTO(fine_id=fine.id, loan_id=fine.loan_id,
                       amount=fine.amount, paid=fine.paid)

    # ---------- 丢失与赔偿（UC-022） ----------

    def report_lost(self, barcode: str, today: date | None = None) -> LostResultDTO:
        today = today or date.today()

        item = self.items.find_by_barcode(barcode)
        if item is None:
            raise NotFoundError("馆藏不存在")

        loan = self.loans.find_active_by_item(item.id)
        if loan is None:
            raise BusinessError("未找到该馆藏的借阅记录")

        title = self.titles.get(item.title_id)
        policy = self.policies.get_compensation_policy(item.item_type)
        if policy is None:
            raise InfrastructureError("未配置赔偿策略")

        amount = self.comp_calc.calculate_amount(title.price if title else None, policy)

        loan.close_as_lost()
        item.mark_removed()
        # 同一事务：结束借阅 + 副本下架 + 生成赔偿记录
        self.loans.save(loan)
        self.items.save(item)
        lost = self.losts.add(
            LostItem(loan_id=loan.id, item_id=item.id, lost_date=today, amount=amount)
        )
        self.db.commit()

        return LostResultDTO(
            lost_id=lost.id,
            loan_id=loan.id,
            title=title.title if title else "",
            amount=amount,
            lost_date=today.isoformat(),
        )

    def pay_compensation(self, lost_id: int) -> dict:
        lost = self.losts.get(lost_id)
        if lost is None:
            raise NotFoundError("赔偿记录不存在")
        lost.mark_paid()
        self.losts.save(lost)
        self.db.commit()
        return {"lost_id": lost.id, "amount": lost.amount, "paid": lost.paid}

    # ---------- 查询罚款与赔偿（UC-016 / UC-022，供馆员缴费台） ----------

    def list_fines(
        self, reader_id: int | None = None, paid: bool | None = None
    ) -> list[dict]:
        return self.fines.list_all(reader_id, paid)

    def list_losts(
        self, reader_id: int | None = None, paid: bool | None = None
    ) -> list[dict]:
        return self.losts.list_all(reader_id, paid)
