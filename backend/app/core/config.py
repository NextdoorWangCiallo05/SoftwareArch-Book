"""全局配置。

集中放置端口、数据库路径、令牌有效期等可配置项，禁止在业务代码中散落魔法值。
所有项均可通过环境变量覆盖，便于部署时调整（见 README 的启动说明）。
"""

import os
from pathlib import Path

# backend/ 目录（app/core/config.py -> parents[2]）
BASE_DIR = Path(__file__).resolve().parents[2]


def _env_int(name: str, default: int) -> int:
    """读取整数型环境变量；缺省或非法时回退默认值。"""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    """读取布尔型环境变量：1/true/yes/on（不区分大小写）视为真。"""
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# 数据库连接串：默认 SQLite 文件 backend/app/library.db，可用 DATABASE_URL 覆盖
DEFAULT_DB_PATH = BASE_DIR / "app" / "library.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# SQLite 库文件路径（seed 模块重建库时直接删除该文件；DATABASE_URL 覆盖为非 SQLite 时该路径仅作占位）
DB_PATH = DEFAULT_DB_PATH

# 服务端口（避开常见的 8000）
API_PORT = _env_int("API_PORT", 8001)

# 允许跨域访问的前端来源，逗号分隔（默认覆盖 Vite 开发与预览端口）
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if origin.strip()
]

# 令牌有效期（小时）
TOKEN_TTL_HOURS = _env_int("TOKEN_TTL_HOURS", 8)

# 预约有效期（天），对应 BR-008
RESERVATION_VALID_DAYS = _env_int("RESERVATION_VALID_DAYS", 7)

# 密码哈希迭代次数
PBKDF2_ITERATIONS = _env_int("PBKDF2_ITERATIONS", 120_000)

# 借阅规则与罚款规则的默认值（种子数据使用）
DEFAULT_READER_TYPE = os.getenv("DEFAULT_READER_TYPE", "UNDERGRADUATE")

# 启动时是否强制重置数据库（默认关闭，避免误删演示数据）
RESET_DB_ON_START = _env_bool("RESET_DB_ON_START", False)
