"""读者、管理员与借阅证仓储实现。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.entities.identity import BorrowCard, Librarian, Reader
from app.domain.value_objects.enums import CardStatus, ReaderStatus, ReaderType
from app.infrastructure.models.orm import (
    BorrowCardORM,
    LibrarianORM,
    ReaderORM,
)


def _to_reader(orm: ReaderORM) -> Reader:
    return Reader(
        id=orm.id,
        account_id=orm.account_id,
        name=orm.name,
        reader_type=ReaderType(orm.reader_type),
        email=orm.email,
        phone=orm.phone,
        status=ReaderStatus(orm.status),
        grade=orm.grade,
        department=orm.department,
    )


def _to_card(orm: BorrowCardORM) -> BorrowCard:
    return BorrowCard(
        id=orm.id,
        card_no=orm.card_no,
        reader_id=orm.reader_id,
        status=CardStatus(orm.status),
    )


class SQLAlchemyReaderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, reader_id: int) -> Reader | None:
        orm = self.db.query(ReaderORM).filter(ReaderORM.id == reader_id).first()
        return _to_reader(orm) if orm else None

    def find_by_account_id(self, account_id: int) -> Reader | None:
        orm = self.db.query(ReaderORM).filter(ReaderORM.account_id == account_id).first()
        return _to_reader(orm) if orm else None

    def add(self, reader: Reader) -> Reader:
        orm = ReaderORM(
            account_id=reader.account_id,
            name=reader.name,
            reader_type=reader.reader_type.value,
            email=reader.email,
            phone=reader.phone,
            status=reader.status.value,
            grade=reader.grade,
            department=reader.department,
        )
        self.db.add(orm)
        self.db.flush()
        reader.id = orm.id
        return reader

    def save(self, reader: Reader) -> Reader:
        orm = self.db.query(ReaderORM).filter(ReaderORM.id == reader.id).first()
        if orm is None:
            raise ValueError("读者不存在")
        orm.name = reader.name
        orm.reader_type = reader.reader_type.value
        orm.email = reader.email
        orm.phone = reader.phone
        orm.status = reader.status.value
        self.db.flush()
        return reader

    def search(self, name, reader_type, page, page_size):
        query = self.db.query(ReaderORM)
        if name:
            query = query.filter(ReaderORM.name.contains(name))
        if reader_type:
            query = query.filter(ReaderORM.reader_type == str(reader_type))
        total = query.count()
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return [_to_reader(r) for r in rows], total


class SQLAlchemyLibrarianRepository:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_entity(orm: LibrarianORM) -> Librarian:
        return Librarian(
            id=orm.id,
            account_id=orm.account_id,
            name=orm.name,
            employee_no=orm.employee_no,
        )

    def get(self, librarian_id: int) -> Librarian | None:
        orm = self.db.query(LibrarianORM).filter(LibrarianORM.id == librarian_id).first()
        return self._to_entity(orm) if orm else None

    def list(self, page, page_size):
        query = self.db.query(LibrarianORM)
        total = query.count()
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return [self._to_entity(r) for r in rows], total

    def add(self, librarian: Librarian) -> Librarian:
        orm = LibrarianORM(
            account_id=librarian.account_id,
            name=librarian.name,
            employee_no=librarian.employee_no,
        )
        self.db.add(orm)
        self.db.flush()
        librarian.id = orm.id
        return librarian

    def save(self, librarian: Librarian) -> Librarian:
        orm = self.db.query(LibrarianORM).filter(LibrarianORM.id == librarian.id).first()
        if orm is None:
            raise ValueError("管理员不存在")
        orm.name = librarian.name
        orm.employee_no = librarian.employee_no
        self.db.flush()
        return librarian

    def delete(self, librarian_id: int) -> None:
        self.db.query(LibrarianORM).filter(LibrarianORM.id == librarian_id).delete()
        self.db.flush()


class SQLAlchemyBorrowCardRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_no(self, card_no: str) -> BorrowCard | None:
        orm = self.db.query(BorrowCardORM).filter(BorrowCardORM.card_no == card_no).first()
        return _to_card(orm) if orm else None

    def find_active_by_reader(self, reader_id: int) -> BorrowCard | None:
        orm = (
            self.db.query(BorrowCardORM)
            .filter(
                BorrowCardORM.reader_id == reader_id,
                BorrowCardORM.status == CardStatus.ACTIVE.value,
            )
            .first()
        )
        return _to_card(orm) if orm else None

    def get(self, card_id: int) -> BorrowCard | None:
        orm = self.db.query(BorrowCardORM).filter(BorrowCardORM.id == card_id).first()
        return _to_card(orm) if orm else None

    def add(self, card: BorrowCard) -> BorrowCard:
        orm = BorrowCardORM(
            card_no=card.card_no,
            reader_id=card.reader_id,
            status=card.status.value,
            issued_at=datetime.now(),
        )
        self.db.add(orm)
        self.db.flush()
        card.id = orm.id
        return card

    def save(self, card: BorrowCard) -> BorrowCard:
        orm = self.db.query(BorrowCardORM).filter(BorrowCardORM.id == card.id).first()
        if orm is None:
            raise ValueError("借阅证不存在")
        orm.status = card.status.value
        if card.status != CardStatus.ACTIVE:
            orm.revoked_at = datetime.now()
        self.db.flush()
        return card
