"""值对象与枚举（领域层）。

所有枚举以字符串取值持久化，便于在 SQLite 中直接阅读与调试。
"""

from enum import Enum


class Role(str, Enum):
    """账户角色。"""

    READER = "reader"
    LIBRARIAN = "librarian"
    ADMIN = "admin"


class ReaderType(str, Enum):
    """读者类型（含指导书要求的专科生）。"""

    ASSOCIATE = "ASSOCIATE"          # 专科生
    UNDERGRADUATE = "UNDERGRADUATE"  # 本科生
    GRADUATE = "GRADUATE"            # 研究生
    DOCTOR = "DOCTOR"                # 博士生
    TEACHER = "TEACHER"              # 教师


class ItemType(str, Enum):
    """出借物类型。"""

    BOOK = "BOOK"
    MAGAZINE = "MAGAZINE"
    THESIS = "THESIS"


class ItemStatus(str, Enum):
    """馆藏副本状态（BR-010 状态机）。"""

    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    RESERVED = "RESERVED"
    REMOVED = "REMOVED"


class LoanStatus(str, Enum):
    """借阅记录状态。"""

    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"


class CardStatus(str, Enum):
    """借阅证状态。"""

    ACTIVE = "ACTIVE"
    LOST = "LOST"
    REVOKED = "REVOKED"


class ReservationStatus(str, Enum):
    """预约状态。"""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"


class ReviewStatus(str, Enum):
    """评论状态（BR-018 审核规则）。"""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ReaderStatus(str, Enum):
    """读者账户状态。"""

    ACTIVE = "active"
    INACTIVE = "inactive"
