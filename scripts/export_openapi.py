#!/usr/bin/env python3
"""Export OpenAPI schema and a path summary into docs/manuals/."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.main import create_app  # noqa: E402


def main() -> int:
    out_dir = ROOT / "docs" / "manuals"
    out_dir.mkdir(parents=True, exist_ok=True)

    app = create_app()
    schema = app.openapi()
    json_path = out_dir / "openapi.json"
    json_path.write_text(json.dumps(schema, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    lines = [
        "# OpenAPI path summary",
        "",
        f"**Title:** {schema.get('info', {}).get('title')}",
        f"**Version:** {schema.get('info', {}).get('version')}",
        "",
        "| Method | Path | Summary |",
        "|---|---|---|",
    ]
    paths = schema.get("paths") or {}
    for path in sorted(paths.keys()):
        methods = paths[path]
        for method, meta in sorted(methods.items()):
            if method.startswith("x-") or not isinstance(meta, dict):
                continue
            summary = (meta.get("summary") or meta.get("operationId") or "").replace("|", "/")
            lines.append(f"| {method.upper()} | `{path}` | {summary} |")
    lines.append("")
    summary_path = out_dir / "openapi.summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {json_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Paths: {len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
