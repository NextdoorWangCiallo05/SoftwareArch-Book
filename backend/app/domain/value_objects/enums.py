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
    """借阅记录状态。"""

    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


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
