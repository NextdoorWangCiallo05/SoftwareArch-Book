"""身份与借阅证领域实体。

认证（Account）与业务身份（Reader / Librarian / SystemAdmin）分离：
密码等凭证只存在于 Account，领域实体保持业务语义纯净。
"""

from dataclasses import dataclass, field
from typing import Optional, Protocol

from app.domain.value_objects.enums import CardStatus, ReaderStatus, ReaderType, Role


class PasswordHasher(Protocol):
    """密码校验器协议（由基础设施层实现，领域层只依赖抽象）。"""

    def verify(self, raw_password: str, salt: str, password_hash: str) -> bool:
        ...


@dataclass
class Account:
    """登录账户（聚合根）。"""

    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    salt: str = ""
    role: Role = Role.READER
    is_active: bool = True

    def has_role(self, role: Role) -> bool:
        return self.role == role

    def verify_password(self, raw_password: str, hasher: PasswordHasher) -> bool:
        return hasher.verify(raw_password, self.salt, self.password_hash)


@dataclass
class Reader:
    """读者（聚合根）。"""

    id: Optional[int] = None
    account_id: Optional[int] = None
    name: str = ""
    reader_type: ReaderType = ReaderType.UNDERGRADUATE
    email: Optional[str] = None
    phone: Optional[str] = None
    status: ReaderStatus = ReaderStatus.ACTIVE

    # 子类扩展属性（单表继承）
    grade: Optional[str] = None
    department: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status == ReaderStatus.ACTIVE


@dataclass
class StudentReader(Reader):
    """学生读者（本科 / 专科 / 研究生 / 博士生）。"""


@dataclass
class TeacherReader(Reader):
    """教师读者。"""


@dataclass
class Librarian:
    """图书管理员：代理读者办理借还、查询任意读者借阅信息。"""

    id: Optional[int] = None
    account_id: Optional[int] = None
    name: str = ""
    employee_no: Optional[str] = None


@dataclass
class SystemAdmin:
    """系统管理员：维护借阅证、管理员、馆藏与规则。"""

    id: Optional[int] = None
    account_id: Optional[int] = None
    name: str = ""


@dataclass
class BorrowCard:
    """借阅证（BR-001 / BR-017）。"""

    id: Optional[int] = None
    card_no: str = ""
    reader_id: Optional[int] = None
    status: CardStatus = CardStatus.ACTIVE

    def is_valid(self) -> bool:
        return self.status == CardStatus.ACTIVE

    def revoke(self) -> None:
        self.status = CardStatus.REVOKED
