"""ORM 模型定义（对应 specs/13-database-design.md 的 16 张表）。

继承映射说明：
`readers` 与 `library_items` 采用**单表 + 鉴别列**方式（`reader_type` / `item_type`），
子类专有列允许为空；领域层的继承语义（StudentReader/TeacherReader、Book/Magazine/Thesis）
由领域实体与 Factory 承载，ORM 层保持扁平，避免 SQLAlchemy 多态配置的复杂度。
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    text,
)

from app.infrastructure.db.base import Base


class AccountORM(Base):
    """登录账户（认证）。"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(String(20), nullable=False, default="reader")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class AuthTokenORM(Base):
    """访问令牌。"""

    __tablename__ = "auth_tokens"

    token = Column(String(64), primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class ReaderORM(Base):
    """读者（单表，含子类专有列）。"""

    __tablename__ = "readers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    reader_type = Column(String(20), nullable=False, index=True)
    grade = Column(String(50), nullable=True)        # 学生读者扩展
    department = Column(String(100), nullable=True)  # 教师读者扩展
    email = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    status = Column(String(20), nullable=False, default="active")


class LibrarianORM(Base):
    """图书管理员。"""

    __tablename__ = "librarians"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    employee_no = Column(String(30), unique=True, nullable=True)


class SystemAdminORM(Base):
    """系统管理员。"""

    __tablename__ = "system_admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), unique=True, nullable=False)
    name = Column(String(50), nullable=False)


class BorrowCardORM(Base):
    """借阅证。同一读者最多一张 ACTIVE 证（部分唯一索引）。"""

    __tablename__ = "borrow_cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_no = Column(String(30), unique=True, index=True, nullable=False)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    issued_at = Column(DateTime, nullable=False, default=datetime.now)
    revoked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index(
            "uq_borrow_card_active",
            "reader_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
    )


class BookTitleORM(Base):
    """图书标题。"""

    __tablename__ = "book_titles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False)
    publisher = Column(String(100), nullable=True)
    published_year = Column(Integer, nullable=True)
    category = Column(String(50), nullable=True, index=True)
    item_type = Column(String(20), nullable=False, default="BOOK")
    price = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


class LibraryItemORM(Base):
    """馆藏副本（单表，含各子类专有列）。"""

    __tablename__ = "library_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    barcode = Column(String(30), unique=True, index=True, nullable=False)
    title_id = Column(Integer, ForeignKey("book_titles.id"), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True, default="AVAILABLE")
    location = Column(String(50), nullable=True)
    fine_category = Column(String(30), nullable=False, default="CHINESE_BOOK")
    edition = Column(String(30), nullable=True)      # Book
    pages = Column(Integer, nullable=True)           # Book
    issue_no = Column(String(30), nullable=True)     # Magazine
    period = Column(String(30), nullable=True)       # Magazine
    degree = Column(String(30), nullable=True)       # Thesis
    school = Column(String(100), nullable=True)      # Thesis
    acquired_at = Column(DateTime, nullable=False, default=datetime.now)


class LoanORM(Base):
    """借阅记录。同一副本同时最多一条 BORROWED 记录（部分唯一索引）。"""

    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("library_items.id"), nullable=False, index=True)
    borrow_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    return_date = Column(Date, nullable=True)
    status = Column(String(20), nullable=False, index=True, default="BORROWED")
    renew_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index(
            "uq_item_active_loan",
            "item_id",
            unique=True,
            sqlite_where=text("status IN ('BORROWED', 'RETURN_REQUESTED')"),
        ),
    )


class ReservationORM(Base):
    """预约。同一读者对同一标题最多一条 ACTIVE 预约（部分唯一索引）。"""

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False, index=True)
    title_id = Column(Integer, ForeignKey("book_titles.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    expires_at = Column(Date, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    queue_position = Column(Integer, nullable=True)

    __table_args__ = (
        Index(
            "uq_reservation_active",
            "reader_id",
            "title_id",
            unique=True,
            sqlite_where=text("status = 'ACTIVE'"),
        ),
        Index("ix_reservations_title_created", "title_id", "created_at"),
    )


class FineRecordORM(Base):
    """罚款记录。"""

    __tablename__ = "fine_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    paid = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    paid_at = Column(DateTime, nullable=True)


class LostItemORM(Base):
    """丢失与赔偿记录。"""

    __tablename__ = "lost_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("library_items.id"), nullable=False)
    lost_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid = Column(Boolean, nullable=False, default=False)
    paid_at = Column(DateTime, nullable=True)


class BorrowPolicyORM(Base):
    """借阅规则（(reader_type, item_type) 二维策略）。"""

    __tablename__ = "borrow_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    reader_type = Column(String(20), nullable=False)
    item_type = Column(String(20), nullable=False, default="ALL")
    max_borrow_count = Column(Integer, nullable=False)
    borrow_days = Column(Integer, nullable=False)

    __table_args__ = (
        Index("uq_borrow_policy", "reader_type", "item_type", unique=True),
    )


class FineRuleORM(Base):
    """罚款规则（含宽限期）。"""

    __tablename__ = "fine_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_category = Column(String(30), unique=True, nullable=False)
    grace_days = Column(Integer, nullable=False, default=0)
    amount_per_day = Column(Numeric(10, 2), nullable=False)


class CompensationPolicyORM(Base):
    """赔偿策略（倍率）。"""

    __tablename__ = "compensation_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_type = Column(String(20), unique=True, nullable=False)
    rate = Column(Numeric(4, 2), nullable=False)


class BookReviewORM(Base):
    """图书评论与评分（同一读者对同一标题唯一）。"""

    __tablename__ = "book_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title_id = Column(Integer, ForeignKey("book_titles.id"), nullable=False, index=True)
    reader_id = Column(Integer, ForeignKey("readers.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String(1000), nullable=True)
    status = Column(String(20), nullable=False, index=True, default="PENDING")
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    updated_at = Column(DateTime, nullable=False, default=datetime.now)

    __table_args__ = (
        Index("uq_review_reader_title", "title_id", "reader_id", unique=True),
        Index("ix_reviews_title_status", "title_id", "status"),
    )
