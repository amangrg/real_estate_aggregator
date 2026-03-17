from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ingest import load_sources
from src.normalize import normalize_sources
from src.resolve import resolve_property
from src.server import create_frontend_server
from src.summarize import generate_markdown_brief


def build_outputs(data_dir: str | Path, output_dir: str | Path) -> tuple[dict, str, Path, Path]:
    raw_sources = load_sources(data_dir)
    normalized_sources = normalize_sources(raw_sources)
    resolved = resolve_property(normalized_sources)
    brief = generate_markdown_brief(resolved)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "resolved_property.json"
    markdown_path = output_path / "property_brief.md"

    json_path.write_text(json.dumps(resolved, indent=2), encoding="utf-8")
    markdown_path.write_text(brief, encoding="utf-8")

    return resolved, brief, json_path, markdown_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate resolved property outputs from local fixture data.",
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing source JSON files. Default: data",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where resolved JSON and markdown files will be written. Default: output",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a local web frontend after generating outputs.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for the local frontend server. Default: 127.0.0.1",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the local frontend server. Default: 8000",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    resolved, brief, json_path, markdown_path = build_outputs(args.data_dir, args.output_dir)

    print(f"Property ID: {resolved['property_id']}")
    print(f"Canonical address: {resolved['canonical_address']}")
    print(f"Resolved JSON: {json_path}")
    print(f"Markdown brief: {markdown_path}")

    if args.serve:
        server = create_frontend_server(args.host, args.port, resolved, brief)
        host, port = server.server_address
        print(f"Frontend URL: http://{host}:{port}")
        print("Press Ctrl+C to stop the server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
