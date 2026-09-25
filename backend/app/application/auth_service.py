"""认证应用服务（FR-001 ~ FR-003）。

负责用例编排与事务边界：注册（账户 + 读者）、登录（颁发令牌）、注销（令牌失效）。
"""

import secrets
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import TOKEN_TTL_HOURS
from app.core.exceptions import BusinessError, PermissionDeniedError
from app.domain.entities.identity import Account, Reader
from app.domain.value_objects.enums import ReaderStatus, Role
from app.infrastructure.repositories.account_repository import (
    SQLAlchemyAccountRepository,
    SQLAlchemyTokenRepository,
)
from app.infrastructure.repositories.reader_repository import (
    SQLAlchemyBorrowCardRepository,
    SQLAlchemyReaderRepository,
)
from app.infrastructure.security.password_hasher import Pbkdf2PasswordHasher
from app.schemas.auth import LoginDTO, ProfileDTO, ReaderDTO


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.accounts = SQLAlchemyAccountRepository(db)
        self.readers = SQLAlchemyReaderRepository(db)
        self.cards = SQLAlchemyBorrowCardRepository(db)
        self.tokens = SQLAlchemyTokenRepository(db)
        self.hasher = Pbkdf2PasswordHasher()

    def register(self, username: str, password: str, name: str,
                 reader_type, email: str | None = None) -> ReaderDTO:
        """注册读者（UC-001）。同一事务创建账户与读者。"""
        if self.accounts.find_by_username(username) is not None:
            raise BusinessError("用户名已存在")

        password_hash, salt = self.hasher.hash(password)
        account = self.accounts.add(
            Account(username=username, password_hash=password_hash,
                    salt=salt, role=Role.READER)
        )
        reader = self.readers.add(
            Reader(account_id=account.id, name=name, reader_type=reader_type,
                   email=email, status=ReaderStatus.ACTIVE)
        )
        self.db.commit()
        return ReaderDTO(reader_id=reader.id, username=username, name=name,
                         reader_type=str(reader_type))

    def login(self, username: str, password: str) -> LoginDTO:
        """登录（UC-002）：校验凭证并颁发令牌。"""
        account = self.accounts.find_by_username(username)
        if account is None or not account.verify_password(password, self.hasher):
            # 统一文案，不泄露用户是否存在
            raise PermissionDeniedError("用户名或密码错误")

        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=TOKEN_TTL_HOURS)
        self.tokens.save(token, account.id, expires_at)
        self.db.commit()

        return LoginDTO(token=token, user_id=account.id, role=account.role.value,
                        username=account.username)

    def profile(self, account: Account) -> ProfileDTO:
        """查询当前身份（UC-002 补充）：返回 reader_id 与有效借阅证号。

        Agent 侧的 `user_id`（账户 ID）与 `reader_id`（读者 ID）不是同一个值，
        借书、续借、查记录用的是 `reader_id`，故提供本接口显式解析。
        """
        dto = ProfileDTO(user_id=account.id, username=account.username,
                         role=account.role.value)
        reader = self.readers.find_by_account_id(account.id)
        if reader is not None:
            card = self.cards.find_active_by_reader(reader.id)
            dto.reader_id = reader.id
            dto.name = reader.name
            dto.reader_type = str(reader.reader_type)
            dto.card_no = card.card_no if card else None
        return dto

    def logout(self, token: str) -> None:
        """注销（UC-003）：令牌失效。"""
        self.tokens.delete(token)
        self.db.commit()
