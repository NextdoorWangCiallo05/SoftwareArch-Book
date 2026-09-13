"""数据库引擎、会话与 ORM 基类。"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖注入：获取数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def recreate_database() -> None:
    """删除所有表后重建（教学项目：领域模型变更后使用）。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_tables() -> None:
    """建表（幂等）。"""
    Base.metadata.create_all(bind=engine)


def check_connection() -> bool:
    """检查数据库连接可用。"""
    with engine.connect() as conn:
        return conn.execute(text("SELECT 1")).scalar() == 1
