"""异常体系。

领域层与应用层只抛出本模块定义的异常，由表现层的全局异常处理器统一转换为
统一响应信封 {code, message, data}。
"""


class AppError(Exception):
    """所有业务/系统异常的基类。"""

    code: int = 500
    default_message = "系统繁忙，请稍后重试"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class BusinessError(AppError):
    """业务规则不满足，对应 code=400，message 可直接呈现给用户。"""

    code = 400
    default_message = "操作失败"


class PermissionDeniedError(AppError):
    """未认证或权限不足，对应 code=403。"""

    code = 403
    default_message = "未登录或权限不足"


class NotFoundError(AppError):
    """资源不存在，对应 code=404。"""

    code = 404
    default_message = "资源不存在"


class InfrastructureError(AppError):
    """底层故障（数据库等），对应 code=500。"""

    code = 500
    default_message = "系统繁忙，请稍后重试"
