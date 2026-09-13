"""预约应用服务（FR-018 / FR-019）。"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import RESERVATION_VALID_DAYS
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.domain.entities.circulation import Reservation
from app.domain.value_objects.enums import ReservationStatus
from app.infrastructure.repositories.catalog_repository import SQLAlchemyTitleRepository
from app.infrastructure.repositories.circulation_repository import SQLAlchemyLoanRepository
from app.infrastructure.repositories.reservation_repository import (
    SQLAlchemyReservationRepository,
)


class ReservationService:
    def __init__(self, db: Session):
        self.db = db
        self.titles = SQLAlchemyTitleRepository(db)
        self.loans = SQLAlchemyLoanRepository(db)
        self.reservations = SQLAlchemyReservationRepository(db)

    def create(self, reader_id: int, title_id: int, today: date | None = None) -> dict:
        today = today or date.today()

        title = self.titles.get(title_id)
        if title is None:
            raise NotFoundError("图书不存在")

        # 惰性失效：先把已过期的旧预约落库为 EXPIRED
        self.reservations.expire_outdated(reader_id, title_id, today)

        if self.reservations.has_effective(reader_id, title_id, today):
            raise BusinessError("您已预约过该书")

        if self.loans.has_active_loan_of_title(reader_id, title_id):
            raise BusinessError("您已借有该书，无需预约")

        now = datetime.now()
        expires_at = today + timedelta(days=RESERVATION_VALID_DAYS)
        queue_position = self.reservations.count_effective_before(title_id, now, today) + 1

        resv = self.reservations.add(
            Reservation(
                reader_id=reader_id,
                title_id=title_id,
                created_at=now,
                expires_at=expires_at,
                status=ReservationStatus.ACTIVE,
                queue_position=queue_position,
            )
        )
        self.db.commit()

        return {
            "reservation_id": resv.id,
            "title_id": title_id,
            "queue_position": queue_position,
            "expires_at": expires_at.isoformat(),
        }

    def cancel(self, reservation_id: int, reader_id: int) -> dict:
        resv = self.reservations.get(reservation_id)
        if resv is None:
            raise NotFoundError("预约不存在")
        if resv.reader_id != reader_id:
            raise PermissionDeniedError("无权取消他人预约")
        if resv.status != ReservationStatus.ACTIVE:
            raise BusinessError("该预约已取消或已失效")

        resv.cancel()
        self.reservations.save(resv)
        self.db.commit()
        return {"reservation_id": resv.id, "status": str(resv.status)}
