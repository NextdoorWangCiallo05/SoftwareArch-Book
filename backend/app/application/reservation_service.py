"""预约应用服务（FR-018 / FR-019）。"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

import threading

from app.core.config import RESERVATION_VALID_DAYS
from app.core.exceptions import BusinessError, NotFoundError, PermissionDeniedError
from app.domain.entities.circulation import Reservation
from app.domain.repositories.protocols import (
    LoanRepository,
    ReaderRepository,
    ReservationRepository,
    TitleRepository,
)
from app.domain.value_objects.enums import ReservationStatus

# 单进程内串行化"位次计算 + 写入"，避免并发预约产生相同位次；
# 多 worker 部署应改用数据库唯一索引（见 specs/17-risk-register.md）。
_RESERVE_LOCK = threading.Lock()


class ReservationService:
    """依赖由组合根（app.presentation.dependencies）注入，仅依赖领域协议。"""

    def __init__(
        self,
        db: Session,
        titles: TitleRepository,
        loans: LoanRepository,
        reservations: ReservationRepository,
        readers: ReaderRepository,
    ) -> None:
        self.db = db
        self.titles = titles
        self.loans = loans
        self.reservations = reservations
        self.readers = readers

    def reader_id_of_account(self, account_id: int) -> int | None:
        """当前账户对应的读者 ID（无读者档案时返回 None）。"""
        reader = self.readers.find_by_account_id(account_id)
        return reader.id if reader else None

    def create(self, reader_id: int, title_id: int, today: date | None = None) -> dict:
        """预约（UC-013）。进程内串行化，避免并发下位次重复。"""
        with _RESERVE_LOCK:
            return self._create(reader_id, title_id, today or date.today())

    def _create(self, reader_id: int, title_id: int, today: date) -> dict:
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

    # ---------- 查询预约（供前端"我的预约"使用） ----------

    def list_by_reader(self, reader_id: int) -> dict:
        rows = self.reservations.list_by_reader(reader_id)
        items = []
        for resv in rows:
            title = self.titles.get(resv.title_id)
            items.append(
                {
                    "reservation_id": resv.id,
                    "title_id": resv.title_id,
                    "title": title.title if title else "",
                    "created_at": resv.created_at.isoformat() if resv.created_at else None,
                    "expires_at": resv.expires_at.isoformat() if resv.expires_at else None,
                    "status": str(resv.status),
                    "queue_position": resv.queue_position,
                }
            )
        return {"total": len(items), "reservations": items}
