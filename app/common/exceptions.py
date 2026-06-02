from fastapi import FastAPI, Request
from starlette.responses import JSONResponse


class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

class NotFoundException(BusinessException):
    def __init__(self, message: str = '资源不存在'):
        super().__init__(404, message)

class UnauthorizedException(BusinessException):
    def __init__(self, message: str = '未授权,请先登录'):
        super().__init__(401, message)

class ForbiddenException(BusinessException):
    def __init__(self, message: str = '无权限访问'):
        super().__init__(403, message)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BusinessException)
    async def business_exception_handler(_request: Request, exc: BusinessException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.code,
            content={
                'code': exc.code,
                'data': None,
                'message': exc.message
            }
        )