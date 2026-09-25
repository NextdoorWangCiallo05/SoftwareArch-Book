"""认证相关 DTO（Pydantic）。

请求 DTO 不接受 role、paid 等敏感或派生字段；响应 DTO 不返回密码哈希与盐。
"""

from pydantic import BaseModel, Field

from app.domain.value_objects.enums import ReaderType


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=50)
    reader_type: ReaderType = ReaderType.UNDERGRADUATE
    email: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ReaderDTO(BaseModel):
    reader_id: int | None = None
    username: str
    name: str
    reader_type: str


class LoginDTO(BaseModel):
    token: str
    user_id: int
    role: str
    username: str


class ProfileDTO(BaseModel):
    """当前登录身份（供 Agent 解析 reader_id / card_no，避免猜测）。"""

    user_id: int
    username: str
    role: str
    reader_id: int | None = None
    name: str | None = None
    reader_type: str | None = None
    card_no: str | None = None
