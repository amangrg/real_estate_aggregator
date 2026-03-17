from __future__ import annotations

import json
import threading
import unittest
from urllib.request import urlopen

from src.ingest import load_sources
from src.normalize import normalize_sources
from src.resolve import resolve_property
from src.server import create_frontend_server
from src.summarize import generate_markdown_brief


class TestServer(unittest.TestCase):
    def test_frontend_server_serves_api_and_static_assets(self) -> None:
        resolved = resolve_property(normalize_sources(load_sources("data")))
        brief = generate_markdown_brief(resolved)
        server = create_frontend_server("127.0.0.1", 0, resolved, brief)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"

            with urlopen(f"{base_url}/api/property") as response:
                payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(payload["property_id"], resolved["property_id"])

            with urlopen(f"{base_url}/api/brief") as response:
                body = response.read().decode("utf-8")
                self.assertIn("# Property Brief: 1428 Maple Creek Dr, Austin, TX 78748", body)

            with urlopen(base_url) as response:
                html = response.read().decode("utf-8")
                self.assertIn("Property Intelligence Prototype", html)
                self.assertIn("Buyer Brief", html)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
