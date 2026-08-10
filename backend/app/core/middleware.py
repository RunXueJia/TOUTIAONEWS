"""Application middleware for normalizing API responses."""

import json

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class ApiResponseMiddleware(BaseHTTPMiddleware):
    """Wrap successful JSON responses from the API namespace in one schema."""

    api_prefix = "/api"

    async def dispatch(self, request: Request, call_next) -> Response:
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
        content_type = response.headers.get("content-type", "")
        return (
            request.url.path.startswith(f"{self.api_prefix}/")
            and (200 <= response.status_code < 300 or response.status_code == 404)
            and "application/json" in content_type.lower()
        )

    @staticmethod
    def _is_standard_response(data: object) -> bool:
        return isinstance(data, dict) and {"code", "message", "data"}.issubset(data)

    @staticmethod
    def _not_found_response(
        request: Request, response: Response, data: object
    ) -> JSONResponse:
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
