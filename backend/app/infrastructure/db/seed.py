"""数据库初始化与种子数据。

说明：本项目领域模型与旧版差异较大，初始化时**删除旧 library.db 后重建**（Q-I2 已确认）。
"""

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import DB_PATH, RESERVATION_VALID_DAYS
from app.infrastructure.db.base import SessionLocal, create_tables, engine
from app.infrastructure.models.orm import (
    AccountORM,
    BookTitleORM,
    BorrowCardORM,
    BorrowPolicyORM,
    CompensationPolicyORM,
    FineRuleORM,
    LibrarianORM,
    LibraryItemORM,
    LoanORM,
    ReaderORM,
    SystemAdminORM,
)
from app.infrastructure.security.password_hasher import hash_with_new_salt

# ---------- 借阅规则（BR-002 / BR-004，二维策略） ----------

_MAIN_POLICIES = [
    ("ASSOCIATE", 3, 30),
    ("UNDERGRADUATE", 5, 30),
    ("GRADUATE", 10, 60),
    ("DOCTOR", 15, 90),
    ("TEACHER", 20, 90),
]

_ITEM_OVERRIDES = {
    "MAGAZINE": (2, 7),
    "THESIS": (2, 3),
}

# ---------- 罚款规则（BR-005，含宽限期） ----------

_FINE_RULES = [
    ("CHINESE_BOOK", 0, "0.50"),
    ("FOREIGN_BOOK", 3, "1.00"),
    ("CHINESE_MAGAZINE", 0, "0.20"),
    ("FOREIGN_MAGAZINE", 2, "0.50"),
    ("THESIS", 0, "2.00"),
]

# ---------- 赔偿策略（BR-018a） ----------

_COMPENSATION_POLICIES = [
    ("BOOK", "2.00"),
    ("MAGAZINE", "1.50"),
    ("THESIS", "3.00"),
]

# ---------- 账户 ----------

_ACCOUNTS = [
    # (username, password, role, name, 备注)
    ("admin", "admin123", "admin", "系统管理员"),
    ("lib01", "123456", "librarian", "图书管理员甲"),
    ("lib02", "123456", "librarian", "图书管理员乙"),
    ("zhangsan", "123456", "reader", "张三"),
    ("lisi", "123456", "reader", "李四"),
    ("wangwu", "123456", "reader", "王五"),
    ("zhaoliu", "123456", "reader", "赵六"),
]

_READER_PROFILES = {
    "zhangsan": ("UNDERGRADUATE", "计算机科学与技术学院", None, "zhangsan@example.com"),
    "lisi": ("GRADUATE", "计算机科学与技术学院", None, "lisi@example.com"),
    "wangwu": ("TEACHER", None, "人工智能学院", "wangwu@example.com"),
    "zhaoliu": ("ASSOCIATE", "机械工程学院", None, "zhaoliu@example.com"),
}

# ---------- 图书标题 ----------

_BOOK_TITLES = [
    ("三体", "刘慈欣", "9787536692930", "重庆出版社", 2008, "科幻", "BOOK", "39.80", 5),
    ("三体II：黑暗森林", "刘慈欣", "9787536692947", "重庆出版社", 2008, "科幻", "BOOK", "42.00", 3),
    ("三体III：死神永生", "刘慈欣", "9787536692954", "重庆出版社", 2010, "科幻", "BOOK", "48.00", 3),
    ("深入理解计算机系统", "Randal E. Bryant", "9787111544937", "机械工业出版社", 2016,
     "计算机科学", "BOOK", "139.00", 2),
    ("Java核心技术", "凯·S·霍斯特曼", "9787111561033", "机械工业出版社", 2019,
     "计算机科学", "BOOK", "119.00", 3),
    ("三国演义", "罗贯中", "9787020008728", "人民文学出版社", 1953, "古典文学", "BOOK", "49.00", 4),
    ("活着", "余华", "9787506365437", "作家出版社", 1993, "当代文学", "BOOK", "28.00", 3),
    ("计算机学报", "中国计算机学会", "ISSN0254-4164", "科学出版社", 2026, "期刊",
     "MAGAZINE", "60.00", 4),
    ("软件架构设计博士论文", "陈明俊", "TH-2026-0001", "武汉理工大学", 2026, "学位论文",
     "THESIS", "0.00", 2),
]

_FINE_CATEGORY_BY_TYPE = {
    "BOOK": "CHINESE_BOOK",
    "MAGAZINE": "CHINESE_MAGAZINE",
    "THESIS": "THESIS",
}


def _seed_policies(db: Session) -> None:
    for reader_type, max_count, days in _MAIN_POLICIES:
        db.add(BorrowPolicyORM(reader_type=reader_type, item_type="ALL",
                               max_borrow_count=max_count, borrow_days=days))
    for item_type, (max_count, days) in _ITEM_OVERRIDES.items():
        for reader_type, _, _ in _MAIN_POLICIES:
            db.add(BorrowPolicyORM(reader_type=reader_type, item_type=item_type,
                                   max_borrow_count=max_count, borrow_days=days))
    for category, grace, amount in _FINE_RULES:
        db.add(FineRuleORM(item_category=category, grace_days=grace, amount_per_day=amount))
    for item_type, rate in _COMPENSATION_POLICIES:
        db.add(CompensationPolicyORM(item_type=item_type, rate=rate))


def _seed_accounts(db: Session) -> dict:
    """创建账户与业务身份，返回 username -> (account_id, reader_id|None)。"""
    result = {}
    year = datetime.now().year

    for username, password, role, name in _ACCOUNTS:
        password_hash, salt = hash_with_new_salt(password)
        account = AccountORM(username=username, password_hash=password_hash,
                             salt=salt, role=role)
        db.add(account)
        db.flush()

        if role == "reader":
            reader_type, grade, department, email = _READER_PROFILES[username]
            reader = ReaderORM(account_id=account.id, name=name, reader_type=reader_type,
                               grade=grade, department=department, email=email)
            db.add(reader)
            db.flush()
            result[username] = (account.id, reader.id)
        elif role == "librarian":
            index = len([k for k in result if k.startswith("lib")]) + 1
            db.add(LibrarianORM(account_id=account.id, name=name,
                                employee_no=f"EMP{year}{index:04d}"))
            result[username] = (account.id, None)
        else:
            db.add(SystemAdminORM(account_id=account.id, name=name))
            result[username] = (account.id, None)

    return result


def _seed_cards(db: Session, accounts: dict) -> None:
    year = datetime.now().year
    for index, username in enumerate(["zhangsan", "lisi", "wangwu", "zhaoliu"], start=1):
        _, reader_id = accounts[username]
        db.add(BorrowCardORM(card_no=f"CARD{year}{index:06d}", reader_id=reader_id,
                             status="ACTIVE", issued_at=datetime.now()))


def _seed_catalog(db: Session) -> dict:
    """创建图书标题与馆藏副本，返回 title_name -> (title_id, [item_ids])。"""
    year = datetime.now().year
    barcode_seq = 0
    catalog = {}

    for (title, author, isbn, publisher, year_pub, category, item_type,
         price, copies) in _BOOK_TITLES:
        title_orm = BookTitleORM(title=title, author=author, isbn=isbn, publisher=publisher,
                                 published_year=year_pub, category=category,
                                 item_type=item_type, price=price)
        db.add(title_orm)
        db.flush()

        item_ids = []
        for _ in range(copies):
            barcode_seq += 1
            item = LibraryItemORM(
                barcode=f"ITEM{year}{barcode_seq:06d}",
                title_id=title_orm.id,
                item_type=item_type,
                status="AVAILABLE",
                location="普通阅览室A区" if item_type == "BOOK" else "期刊/论文阅览室",
                fine_category=_FINE_CATEGORY_BY_TYPE[item_type],
            )
            db.add(item)
            db.flush()
            item_ids.append(item.id)

        catalog[title] = (title_orm.id, item_ids)

    return catalog


def _seed_loans(db: Session, accounts: dict, catalog: dict) -> None:
    """给张三预置一条在借记录（便于演示续借与还书）。"""
    _, reader_id = accounts["zhangsan"]
    title_id, item_ids = catalog["三体"]
    item_id = item_ids[0]

    today = date.today()
    loan = LoanORM(reader_id=reader_id, item_id=item_id, borrow_date=today,
                   due_date=today + timedelta(days=30), status="BORROWED", renew_count=0)
    db.add(loan)

    # 副本状态同步为 BORROWED
    db.query(LibraryItemORM).filter(LibraryItemORM.id == item_id).update(
        {"status": "BORROWED"}
    )


def init_database(drop_existing: bool = True, verbose: bool = True) -> None:
    """初始化数据库。默认删除旧库后重建。"""
    if drop_existing:
        engine.dispose()
        if DB_PATH.exists():
            DB_PATH.unlink()
        create_tables()

    db: Session = SessionLocal()
    try:
        _seed_policies(db)
        accounts = _seed_accounts(db)
        _seed_cards(db, accounts)
        catalog = _seed_catalog(db)
        _seed_loans(db, accounts, catalog)
        db.commit()
        if verbose:
            print("[init] 数据库初始化完成，已插入种子数据")
            print(f"[init] 预约有效期：{RESERVATION_VALID_DAYS} 天")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
