"""用于统一 API 响应格式的应用中间件。"""

import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """将 API 命名空间中的成功和错误 JSON 响应包装为统一结构。"""

    api_prefix = "/api"

    async def dispatch(self, request: Request, call_next) -> Response:
        """包装 API JSON 响应；错误业务码写入响应体，HTTP 状态统一为 200。"""
        response = await call_next(request)

        if not self._should_wrap(request, response):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._restore_response(response, body)

        if self._is_standard_response(data):
            if response.status_code >= 400:
                return self._restore_response(response, body, status_code=200)
            return self._restore_response(response, body)

        if response.status_code >= 400:
            return self._error_response(response, data)

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {"content-length", "content-type"}
        }
        return JSONResponse(
            content={"code": 200, "message": "success", "data": data},
            status_code=response.status_code,
            headers=headers,
            background=response.background,
        )

    def _should_wrap(self, request: Request, response: Response) -> bool:
        """判断响应是否需要套用统一返回结构。"""
        content_type = response.headers.get("content-type", "")
        return (
            request.url.path.startswith(f"{self.api_prefix}/")
            and (200 <= response.status_code < 300 or response.status_code >= 400)
            and "application/json" in content_type.lower()
        )

    @staticmethod
    def _is_standard_response(data: object) -> bool:
        """判断负载是否已经使用标准响应结构。"""
        return isinstance(data, dict) and {"code", "message", "data"}.issubset(data)

    @staticmethod
    def _error_response(response: Response, data: object) -> JSONResponse:
        """将 API 错误转换为 HTTP 200，并保留业务状态码和错误消息。"""
        message = data.get("detail") if isinstance(data, dict) else None
        if not isinstance(message, str):
            message = "Request failed"
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {"content-length", "content-type"}
        }
        return JSONResponse(
            content={"code": response.status_code, "message": message, "data": None},
            status_code=200,
            headers=headers,
            background=response.background,
        )

    @staticmethod
    def _restore_response(
        response: Response,
        body: bytes,
        *,
        status_code: int | None = None,
    ) -> Response:
        """在不改变原语义的前提下重建已消费的响应体。"""
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() != "content-length"
        }
        return Response(
            content=body,
            status_code=response.status_code if status_code is None else status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
