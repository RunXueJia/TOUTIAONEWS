"""用于统一 API 响应格式的应用中间件。"""

import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """将 API 命名空间中的成功 JSON 响应包装为统一结构。"""

    api_prefix = "/api"

    async def dispatch(self, request: Request, call_next) -> Response:
        """包装符合条件的 API JSON 响应，并保留原有错误码与响应头。"""
        response = await call_next(request)

        if not self._should_wrap(request, response):
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return self._restore_response(response, body)

        if self._is_standard_response(data):
            return self._restore_response(response, body)

        if response.status_code == 404:
            return self._not_found_response(request, response, data)

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
            and (200 <= response.status_code < 300 or response.status_code == 404)
            and "application/json" in content_type.lower()
        )

    @staticmethod
    def _is_standard_response(data: object) -> bool:
        """判断负载是否已经使用标准响应结构。"""
        return isinstance(data, dict) and {"code", "message", "data"}.issubset(data)

    @staticmethod
    def _not_found_response(
        request: Request, response: Response, data: object
    ) -> JSONResponse:
        """将 API 的 404 响应转换为项目统一的未找到结构。"""
        message = "Not Found"
        if isinstance(data, dict) and isinstance(data.get("detail"), str):
            message = data["detail"]

        is_data_not_found = request.scope.get("route") is not None

        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() not in {"content-length", "content-type"}
        }
        return JSONResponse(
            content={"code": 404, "message": message, "data": None},
            status_code=200 if is_data_not_found else 404,
            headers=headers,
            background=response.background,
        )

    @staticmethod
    def _restore_response(response: Response, body: bytes) -> Response:
        """在不改变原语义的前提下重建已消费的响应体。"""
        headers = {
            key: value
            for key, value in response.headers.items()
            if key.lower() != "content-length"
        }
        return Response(
            content=body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
            background=response.background,
        )
