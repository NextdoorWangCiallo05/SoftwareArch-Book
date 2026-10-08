"""预约仓储实现（含有效期惰性判定）。"""

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.domain.entities.circulation import Reservation
from app.domain.value_objects.enums import ReservationStatus
from app.infrastructure.models.orm import ReservationORM


def _to_entity(orm: ReservationORM) -> Reservation:
    return Reservation(
        id=orm.id,
        reader_id=orm.reader_id,
        title_id=orm.title_id,
        created_at=orm.created_at,
        expires_at=orm.expires_at,
        status=ReservationStatus(orm.status),
        queue_position=orm.queue_position,
    )


class SQLAlchemyReservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, reservation_id: int) -> Reservation | None:
        orm = (
            self.db.query(ReservationORM)
            .filter(ReservationORM.id == reservation_id)
            .first()
        )
        return _to_entity(orm) if orm else None

    def add(self, reservation: Reservation) -> Reservation:
        orm = ReservationORM(
            reader_id=reservation.reader_id,
            title_id=reservation.title_id,
            created_at=reservation.created_at,
            expires_at=reservation.expires_at,
            status=reservation.status.value,
            queue_position=reservation.queue_position,
        )
        self.db.add(orm)
        self.db.flush()
        reservation.id = orm.id
        return reservation

    def save(self, reservation: Reservation) -> Reservation:
        orm = (
            self.db.query(ReservationORM)
            .filter(ReservationORM.id == reservation.id)
            .first()
        )
        if orm is None:
            raise ValueError("预约不存在")
        orm.status = reservation.status.value
        orm.queue_position = reservation.queue_position
        self.db.flush()
        return reservation

    def has_effective(self, reader_id: int, title_id: int, today: date) -> bool:
        """是否存在未过期的有效预约（过期采用惰性判定，不改状态）。"""
        return (
            self.db.query(ReservationORM)
            .filter(
                ReservationORM.reader_id == reader_id,
                ReservationORM.title_id == title_id,
                ReservationORM.status == ReservationStatus.ACTIVE.value,
                ReservationORM.expires_at >= today,
            )
            .count()
            > 0
        )

    def count_effective_before(
        self, title_id: int, created_at: datetime, today: date
    ) -> int:
        """统计同一标题下更早的有效预约数量（用于计算排队位次）。"""
        return (
            self.db.query(ReservationORM)
            .filter(
                ReservationORM.title_id == title_id,
                ReservationORM.created_at < created_at,
                ReservationORM.status == ReservationStatus.ACTIVE.value,
                ReservationORM.expires_at >= today,
            )
            .count()
        )

    def count_effective_by_others(
        self, title_id: int, reader_id: int, today: date
    ) -> int:
        """统计同一标题下**其他读者**的有效预约数量（用于续借阻塞判定）。"""
        return (
            self.db.query(ReservationORM)
            .filter(
                ReservationORM.title_id == title_id,
                ReservationORM.reader_id != reader_id,
                ReservationORM.status == ReservationStatus.ACTIVE.value,
                ReservationORM.expires_at >= today,
            )
            .count()
        )

    def expire_outdated(self, reader_id: int, title_id: int, today: date) -> int:
        """惰性失效：将该读者在该标题下已过期的 ACTIVE 预约置为 EXPIRED。

        必要性：部分唯一索引 uq_reservation_active 只按 status='ACTIVE' 约束，
        无法在索引条件中表达「未过期」，因此在创建预约前需先落库失效状态。
        """
        rows = (
            self.db.query(ReservationORM)
            .filter(
                ReservationORM.reader_id == reader_id,
                ReservationORM.title_id == title_id,
                ReservationORM.status == ReservationStatus.ACTIVE.value,
                ReservationORM.expires_at < today,
            )
            .all()
        )
        for orm in rows:
            orm.status = ReservationStatus.EXPIRED.value
        self.db.flush()
        return len(rows)

    def list_by_title(self, title_id: int) -> list[Reservation]:
        rows = (
            self.db.query(ReservationORM)
            .filter(ReservationORM.title_id == title_id)
            .order_by(ReservationORM.created_at.asc())
            .all()
        )
        return [_to_entity(r) for r in rows]

    def list_by_reader(self, reader_id: int) -> list[Reservation]:
        """某读者的全部预约（供前端展示"我的预约"）。"""
        rows = (
            self.db.query(ReservationORM)
            .filter(ReservationORM.reader_id == reader_id)
            .order_by(ReservationORM.created_at.desc())
            .all()
        )
        return [_to_entity(r) for r in rows]
