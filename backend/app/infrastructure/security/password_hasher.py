"""密码哈希与校验（PBKDF2-HMAC-SHA256 + 随机盐）。

对应 09-design-model.md 4.1：
  - salt = os.urandom(16).hex()
  - hash = pbkdf2_hmac("sha256", raw, salt, 120000).hex()
  - 校验使用 hmac.compare_digest 做常量时间比较
"""

import hashlib
import hmac
import os

from app.core.config import PBKDF2_ITERATIONS


def generate_salt() -> str:
    """生成 16 字节随机盐的十六进制表示。"""
    return os.urandom(16).hex()


def hash_password(raw_password: str, salt: str) -> str:
    """根据明文与盐计算密码哈希。"""
    return hashlib.pbkdf2_hmac(
        "sha256",
        raw_password.encode("utf-8"),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS,
    ).hex()


def hash_with_new_salt(raw_password: str) -> tuple[str, str]:
    """生成新盐并返回 (password_hash, salt)。"""
    salt = generate_salt()
    return hash_password(raw_password, salt), salt


def verify_password(raw_password: str, salt: str, password_hash: str) -> bool:
    """常量时间比较，防止时序攻击。"""
    calc = hash_password(raw_password, salt)
    return hmac.compare_digest(calc, password_hash)
