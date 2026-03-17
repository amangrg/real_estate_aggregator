from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
STATIC_ASSETS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
}


class PropertyFrontendServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        resolved: dict[str, Any],
        brief: str,
    ) -> None:
        self.resolved = resolved
        self.brief = brief
        super().__init__(server_address, FrontendRequestHandler)


class FrontendRequestHandler(BaseHTTPRequestHandler):
    server: PropertyFrontendServer

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/property":
            self._send_json(self.server.resolved)
            return
        if path == "/api/brief":
            self._send_text(self.server.brief, "text/plain; charset=utf-8")
            return
        if path == "/resolved_property.json":
            self._send_json(self.server.resolved)
            return
        if path == "/property_brief.md":
            self._send_text(self.server.brief, "text/markdown; charset=utf-8")
            return
        if path in STATIC_ASSETS:
            asset_name, content_type = STATIC_ASSETS[path]
            self._send_file(FRONTEND_DIR / asset_name, content_type)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, payload: str, content_type: str) -> None:
        body = payload.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_frontend_server(
    host: str,
    port: int,
    resolved: dict[str, Any],
    brief: str,
) -> PropertyFrontendServer:
    return PropertyFrontendServer((host, port), resolved, brief)
