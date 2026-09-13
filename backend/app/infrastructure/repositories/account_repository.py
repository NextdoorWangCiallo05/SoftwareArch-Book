"""账户与令牌仓储实现。"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.entities.identity import Account
from app.domain.value_objects.enums import Role
from app.infrastructure.models.orm import AccountORM, AuthTokenORM


def _to_account(orm: AccountORM) -> Account:
    return Account(
        id=orm.id,
        username=orm.username,
        password_hash=orm.password_hash,
        salt=orm.salt,
        role=Role(orm.role),
        is_active=orm.is_active,
    )


class SQLAlchemyAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_username(self, username: str) -> Account | None:
        orm = self.db.query(AccountORM).filter(AccountORM.username == username).first()
        return _to_account(orm) if orm else None

    def find_by_id(self, account_id: int) -> Account | None:
        orm = self.db.query(AccountORM).filter(AccountORM.id == account_id).first()
        return _to_account(orm) if orm else None

    def add(self, account: Account) -> Account:
        orm = AccountORM(
            username=account.username,
            password_hash=account.password_hash,
            salt=account.salt,
            role=account.role.value,
            is_active=account.is_active,
        )
        self.db.add(orm)
        self.db.flush()
        account.id = orm.id
        return account


class SQLAlchemyTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, token: str, account_id: int, expires_at: datetime) -> None:
        self.db.add(
            AuthTokenORM(token=token, account_id=account_id, expires_at=expires_at)
        )
        self.db.flush()

    def find_account_id(self, token: str) -> int | None:
        orm = self.db.query(AuthTokenORM).filter(AuthTokenORM.token == token).first()
        if orm is None:
            return None
        if orm.expires_at < datetime.now():
            self.db.delete(orm)
            self.db.flush()
            return None
        return orm.account_id

    def delete(self, token: str) -> None:
        self.db.query(AuthTokenORM).filter(AuthTokenORM.token == token).delete()
        self.db.flush()
