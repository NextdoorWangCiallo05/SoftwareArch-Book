"""值对象与枚举（领域层）。

使用 StrEnum：枚举值即持久化字符串，避免 (str, Enum) 在
SQLAlchemy 与 f-string 场景下出现 "ReaderType.UNDERGRADUATE" 这类取值。
"""

from enum import StrEnum


class Role(StrEnum):
    """账户角色。"""

    READER = "reader"
    LIBRARIAN = "librarian"
    ADMIN = "admin"


class ReaderType(StrEnum):
    """读者类型（含指导书要求的专科生）。"""

    ASSOCIATE = "ASSOCIATE"          # 专科生
    UNDERGRADUATE = "UNDERGRADUATE"  # 本科生
    GRADUATE = "GRADUATE"            # 研究生
    DOCTOR = "DOCTOR"                # 博士生
    TEACHER = "TEACHER"              # 教师


class ReaderStatus(StrEnum):
    """读者账户状态。"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class ItemType(StrEnum):
    """出借物类型。"""

    BOOK = "BOOK"
    MAGAZINE = "MAGAZINE"
    THESIS = "THESIS"


class ItemStatus(StrEnum):
    """馆藏副本状态（BR-010 状态机）。"""

    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    RESERVED = "RESERVED"
    REMOVED = "REMOVED"


class LoanStatus(StrEnum):
    """借阅记录状态。

    BR-020：还书采用「读者发起申请 + 图书管理员审核」的两段式流程，
    故在 BORROWED 与 RETURNED 之间引入 RETURN_REQUESTED（归还申请中）。
    """

    BORROWED = "BORROWED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"

    @classmethod
    def active_statuses(cls) -> tuple["LoanStatus", ...]:
        """仍在读者手上、占用借阅配额的状态（书未真正回馆）。"""
        return (cls.BORROWED, cls.RETURN_REQUESTED)


class CardStatus(StrEnum):
    """借阅证状态。"""

    ACTIVE = "ACTIVE"
    LOST = "LOST"
    REVOKED = "REVOKED"


class ReservationStatus(StrEnum):
    """预约状态。"""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"


class ReviewStatus(StrEnum):
    """评论状态（BR-018 审核规则）。"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
