"""统一响应信封与辅助构造器。

所有业务接口统一返回 {code, message, data}：
  200 成功 / 400 业务错误 / 403 未认证或权限不足 / 404 资源不存在 / 500 系统错误
"""

from typing import Any, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    """统一响应模型。"""

    code: int
    message: str
    data: Optional[Any] = None


def ok(data: Any = None, message: str = "操作成功") -> APIResponse:
    return APIResponse(code=200, message=message, data=data)


def fail(code: int, message: str) -> APIResponse:
    return APIResponse(code=code, message=message, data=None)


def envelope(code: int, message: str, data: Any = None) -> dict:
    """返回可直接序列化的字典，供异常处理器使用。"""
    return {"code": code, "message": message, "data": data}
