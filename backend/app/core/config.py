"""全局配置。

集中放置端口、数据库路径、令牌有效期等可配置项，禁止在业务代码中散落魔法值。
"""

from pathlib import Path

# backend/ 目录（app/core/config.py -> parents[2]）
BASE_DIR = Path(__file__).resolve().parents[2]

# 数据库文件：backend/app/library.db
DB_PATH = BASE_DIR / "app" / "library.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

# 服务端口（避开常见的 8000）
API_PORT = 8001

# 令牌有效期（小时）
TOKEN_TTL_HOURS = 8

# 预约有效期（天），对应 BR-008
RESERVATION_VALID_DAYS = 7

# 密码哈希迭代次数
PBKDF2_ITERATIONS = 120_000

# 借阅规则与罚款规则的默认值（种子数据使用）
DEFAULT_READER_TYPE = "UNDERGRADUATE"
