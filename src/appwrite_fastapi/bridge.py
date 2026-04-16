import asyncio
import json
from typing import Any, Callable, Dict


class AppwriteBridge:
    def __init__(self, app: Callable):
        self.app = app

    async def handle(self, context: Any) -> Any:
        # Appwrite now runs an event loop, so we can await directly.
        return await self._async_handle(context)

    async def _async_handle(self, context: Any) -> Any:
        # 1. Prepare the ASGI Scope
        headers = []
        for key, value in context.req.headers.items():
            headers.append((key.lower().encode("utf-8"), value.encode("utf-8")))

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": "1.1",
            "method": context.req.method.upper(),
            "scheme": "http",
            "path": context.req.path,
            "raw_path": context.req.path.encode("utf-8"),
            "query_string": context.req.query_string.encode("utf-8") if hasattr(context.req, "query_string") else b"",
            "headers": headers,
            "client": (context.req.ip, 0) if hasattr(context.req, "ip") else None,
            "server": ("appwrite", 0),
        }

        # 2. Prepare the Request Body (Receive)
        body = context.req.body
        if isinstance(body, dict):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode("utf-8")
        
        async def receive() -> Dict[str, Any]:
            return {
                "type": "http.request",
                "body": body or b"",
                "more_body": False,
            }

        # 3. Prepare the Response Collector (Send)
        response_data = {
            "status": 200,
            "headers": [],
            "body": b"",
        }

        async def send(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                response_data["headers"] = message.get("headers", [])
            elif message["type"] == "http.response.body":
                response_data["body"] += message.get("body", b"")

        # 4. Execute the FastAPI App
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            context.error(f"FastAPI Execution Error: {str(e)}")
            return context.res.text("Internal Server Error", 500)

        # 5. Translate the response back to Appwrite
        resp_headers = {k.decode("utf-8"): v.decode("utf-8") for k, v in response_data["headers"]}
        content_type = resp_headers.get("content-type", "text/plain")
        
        if "application/json" in content_type:
            try:
                body_json = json.loads(response_data["body"].decode("utf-8"))
                return context.res.json(body_json, response_data["status"], resp_headers)
            except:
                pass

        return context.res.text(response_data["body"].decode("utf-8", errors="replace"), response_data["status"], resp_headers)
