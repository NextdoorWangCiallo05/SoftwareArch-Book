"""借阅、罚款与赔偿仓储实现。"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.entities.circulation import FineRecord, Loan, LostItem
from app.domain.value_objects.enums import ItemType, LoanStatus
from app.infrastructure.models.orm import (
    FineRecordORM,
    LibraryItemORM,
    LoanORM,
    LostItemORM,
)


def _to_loan(orm: LoanORM) -> Loan:
    return Loan(
        id=orm.id,
        reader_id=orm.reader_id,
        item_id=orm.item_id,
        borrow_date=orm.borrow_date,
        due_date=orm.due_date,
        return_date=orm.return_date,
        status=LoanStatus(orm.status),
        renew_count=orm.renew_count,
    )


def _to_fine(orm: FineRecordORM) -> FineRecord:
    return FineRecord(
        id=orm.id,
        loan_id=orm.loan_id,
        amount=Decimal(str(orm.amount)),
        paid=orm.paid,
    )


def _to_lost(orm: LostItemORM) -> LostItem:
    return LostItem(
        id=orm.id,
        loan_id=orm.loan_id,
        item_id=orm.item_id,
        lost_date=orm.lost_date,
        amount=Decimal(str(orm.amount)),
        paid=orm.paid,
    )


class SQLAlchemyLoanRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, loan_id: int) -> Loan | None:
        orm = self.db.query(LoanORM).filter(LoanORM.id == loan_id).first()
        return _to_loan(orm) if orm else None

    def add(self, loan: Loan) -> Loan:
        orm = LoanORM(
            reader_id=loan.reader_id,
            item_id=loan.item_id,
            borrow_date=loan.borrow_date,
            due_date=loan.due_date,
            return_date=loan.return_date,
            status=loan.status.value,
            renew_count=loan.renew_count,
        )
        self.db.add(orm)
        self.db.flush()
        loan.id = orm.id
        return loan

    def save(self, loan: Loan) -> Loan:
        orm = self.db.query(LoanORM).filter(LoanORM.id == loan.id).first()
        if orm is None:
            raise ValueError("借阅记录不存在")
        orm.due_date = loan.due_date
        orm.return_date = loan.return_date
        orm.status = loan.status.value
        orm.renew_count = loan.renew_count
        self.db.flush()
        return loan

    def find_active_by_item(self, item_id: int) -> Loan | None:
        orm = (
            self.db.query(LoanORM)
            .filter(LoanORM.item_id == item_id, LoanORM.status == LoanStatus.BORROWED.value)
            .first()
        )
        return _to_loan(orm) if orm else None

    def count_active(self, reader_id: int, item_type: ItemType | None = None) -> int:
        query = (
            self.db.query(LoanORM)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .filter(LoanORM.reader_id == reader_id, LoanORM.status == LoanStatus.BORROWED.value)
        )
        if item_type is not None:
            query = query.filter(LibraryItemORM.item_type == str(item_type))
        return query.count()

    def count_overdue(self, reader_id: int, today: date) -> int:
        return (
            self.db.query(LoanORM)
            .filter(
                LoanORM.reader_id == reader_id,
                LoanORM.status == LoanStatus.BORROWED.value,
                LoanORM.due_date < today,
            )
            .count()
        )

    def has_active_loan_of_title(self, reader_id: int, title_id: int) -> bool:
        return (
            self.db.query(LoanORM)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .filter(
                LoanORM.reader_id == reader_id,
                LoanORM.status == LoanStatus.BORROWED.value,
                LibraryItemORM.title_id == title_id,
            )
            .count()
            > 0
        )

    def list_by_reader(self, reader_id: int, status: LoanStatus | None = None):
        query = self.db.query(LoanORM).filter(LoanORM.reader_id == reader_id)
        if status is not None:
            query = query.filter(LoanORM.status == status.value)
        rows = query.order_by(LoanORM.borrow_date.desc()).all()
        return [_to_loan(r) for r in rows]


class SQLAlchemyFineRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, fine: FineRecord) -> FineRecord:
        orm = FineRecordORM(loan_id=fine.loan_id, amount=fine.amount, paid=fine.paid)
        self.db.add(orm)
        self.db.flush()
        fine.id = orm.id
        return fine

    def get(self, fine_id: int) -> FineRecord | None:
        orm = self.db.query(FineRecordORM).filter(FineRecordORM.id == fine_id).first()
        return _to_fine(orm) if orm else None

    def has_unpaid(self, reader_id: int) -> bool:
        return (
            self.db.query(FineRecordORM)
            .join(LoanORM, FineRecordORM.loan_id == LoanORM.id)
            .filter(LoanORM.reader_id == reader_id, FineRecordORM.paid.is_(False))
            .count()
            > 0
        )

    def save(self, fine: FineRecord) -> FineRecord:
        orm = self.db.query(FineRecordORM).filter(FineRecordORM.id == fine.id).first()
        if orm is None:
            raise ValueError("罚款记录不存在")
        orm.paid = fine.paid
        self.db.flush()
        return fine


class SQLAlchemyLostRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, lost: LostItem) -> LostItem:
        orm = LostItemORM(
            loan_id=lost.loan_id,
            item_id=lost.item_id,
            lost_date=lost.lost_date,
            amount=lost.amount,
            paid=lost.paid,
        )
        self.db.add(orm)
        self.db.flush()
        lost.id = orm.id
        return lost

    def get(self, lost_id: int) -> LostItem | None:
        orm = self.db.query(LostItemORM).filter(LostItemORM.id == lost_id).first()
        return _to_lost(orm) if orm else None

    def has_unpaid(self, reader_id: int) -> bool:
        return (
            self.db.query(LostItemORM)
            .join(LoanORM, LostItemORM.loan_id == LoanORM.id)
            .filter(LoanORM.reader_id == reader_id, LostItemORM.paid.is_(False))
            .count()
            > 0
        )

    def save(self, lost: LostItem) -> LostItem:
        orm = self.db.query(LostItemORM).filter(LostItemORM.id == lost.id).first()
        if orm is None:
            raise ValueError("赔偿记录不存在")
        orm.paid = lost.paid
        self.db.flush()
        return lost
