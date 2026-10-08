"""借阅、罚款与赔偿仓储实现。"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.entities.circulation import FineRecord, Loan, LostItem
from app.domain.value_objects.enums import ItemType, LoanStatus
from app.infrastructure.models.orm import (
    BookTitleORM,
    FineRecordORM,
    LibraryItemORM,
    LoanORM,
    LostItemORM,
    ReaderORM,
)


_ACTIVE_STATUSES = tuple(s.value for s in LoanStatus.active_statuses())
"""在借状态（BORROWED / RETURN_REQUESTED）：书仍在读者手上，占用配额、计入超期。"""


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
            .filter(LoanORM.item_id == item_id, LoanORM.status.in_(_ACTIVE_STATUSES))
            .first()
        )
        return _to_loan(orm) if orm else None

    def count_active(self, reader_id: int, item_type: ItemType | None = None) -> int:
        query = (
            self.db.query(LoanORM)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .filter(LoanORM.reader_id == reader_id, LoanORM.status.in_(_ACTIVE_STATUSES))
        )
        if item_type is not None:
            query = query.filter(LibraryItemORM.item_type == str(item_type))
        return query.count()

    def count_overdue(self, reader_id: int, today: date) -> int:
        return (
            self.db.query(LoanORM)
            .filter(
                LoanORM.reader_id == reader_id,
                LoanORM.status.in_(_ACTIVE_STATUSES),
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
                LoanORM.status.in_(_ACTIVE_STATUSES),
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

    def list_return_requests(self) -> list[dict]:
        """待审核的归还申请（BR-020），连带读者与书名供馆员审核台展示。"""
        rows = (
            self.db.query(LoanORM, ReaderORM, LibraryItemORM, BookTitleORM)
            .join(ReaderORM, LoanORM.reader_id == ReaderORM.id)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .join(BookTitleORM, LibraryItemORM.title_id == BookTitleORM.id)
            .filter(LoanORM.status == LoanStatus.RETURN_REQUESTED.value)
            .order_by(LoanORM.due_date.asc())
            .all()
        )
        return [
            {
                "loan_id": loan.id,
                "reader_id": reader.id,
                "reader_name": reader.name,
                "title": title.title,
                "barcode": item.barcode,
                "borrow_date": loan.borrow_date.isoformat() if loan.borrow_date else None,
                "due_date": loan.due_date.isoformat() if loan.due_date else None,
                "renew_count": loan.renew_count,
            }
            for loan, reader, item, title in rows
        ]


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

    def list_all(
        self, reader_id: int | None = None, paid: bool | None = None
    ) -> list[dict]:
        """列出罚款记录（连带读者与书名，供前端缴费台展示）。"""
        query = (
            self.db.query(FineRecordORM, LoanORM, ReaderORM, BookTitleORM)
            .join(LoanORM, FineRecordORM.loan_id == LoanORM.id)
            .join(ReaderORM, LoanORM.reader_id == ReaderORM.id)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .join(BookTitleORM, LibraryItemORM.title_id == BookTitleORM.id)
        )
        if reader_id is not None:
            query = query.filter(LoanORM.reader_id == reader_id)
        if paid is not None:
            query = query.filter(FineRecordORM.paid.is_(paid))

        rows = query.order_by(FineRecordORM.id.desc()).all()
        return [
            {
                "fine_id": fine.id,
                "loan_id": loan.id,
                "reader_id": reader.id,
                "reader_name": reader.name,
                "title": title.title,
                "amount": float(fine.amount),
                "paid": bool(fine.paid),
            }
            for fine, loan, reader, title in rows
        ]


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

    def list_all(
        self, reader_id: int | None = None, paid: bool | None = None
    ) -> list[dict]:
        """列出赔偿记录（连带读者与书名，供前端赔偿台展示）。"""
        query = (
            self.db.query(LostItemORM, LoanORM, ReaderORM, BookTitleORM)
            .join(LoanORM, LostItemORM.loan_id == LoanORM.id)
            .join(ReaderORM, LoanORM.reader_id == ReaderORM.id)
            .join(LibraryItemORM, LoanORM.item_id == LibraryItemORM.id)
            .join(BookTitleORM, LibraryItemORM.title_id == BookTitleORM.id)
        )
        if reader_id is not None:
            query = query.filter(LoanORM.reader_id == reader_id)
        if paid is not None:
            query = query.filter(LostItemORM.paid.is_(paid))

        rows = query.order_by(LostItemORM.id.desc()).all()
        return [
            {
                "lost_id": lost.id,
                "loan_id": loan.id,
                "item_id": lost.item_id,
                "reader_id": reader.id,
                "reader_name": reader.name,
                "title": title.title,
                "amount": float(lost.amount),
                "lost_date": lost.lost_date.isoformat() if lost.lost_date else None,
                "paid": bool(lost.paid),
            }
            for lost, loan, reader, title in rows
        ]
