#!/usr/bin/env python3
"""Copy bundled UI assets from a sibling ConX repo into this standalone client (optional maintenance)."""

from __future__ import annotations

import shutil
from pathlib import Path

CLIENT_ROOT = Path(__file__).resolve().parents[1]
CONX_ROOT = CLIENT_ROOT.parent

PAIRS = [
    (CONX_ROOT / "static" / "conx.css", CLIENT_ROOT / "static" / "conx.css"),
    (CONX_ROOT / "static" / "workspace-contextual-live.js", CLIENT_ROOT / "static" / "workspace-contextual-live.js"),
    (CONX_ROOT / "static" / "workspace-search-tabs.js", CLIENT_ROOT / "static" / "workspace-search-tabs.js"),
    (CONX_ROOT / "static" / "intelligence-print-page.css", CLIENT_ROOT / "static" / "intelligence-print-page.css"),
    (CONX_ROOT / "static" / "js" / "conx-preview-common.js", CLIENT_ROOT / "static" / "js" / "conx-preview-common.js"),
    (
        CONX_ROOT / "templates" / "partials" / "dashboard_preview_section.html",
        CLIENT_ROOT / "templates" / "partials" / "dashboard_preview_section.html",
    ),
    (
        CONX_ROOT / "templates" / "partials" / "search_type_icon.html",
        CLIENT_ROOT / "templates" / "partials" / "search_type_icon.html",
    ),
    (CONX_ROOT / "user_intel.py", CLIENT_ROOT / "user_intel.py"),
    (CONX_ROOT / "static" / "hero-dots-interaction.js", CLIENT_ROOT / "static" / "hero-dots-interaction.js"),
]


def main() -> None:
    if not (CONX_ROOT / "app.py").is_file():
        raise SystemExit(f"ConX repo not found at {CONX_ROOT}")
    (CLIENT_ROOT / "static" / "js").mkdir(parents=True, exist_ok=True)
    for src, dst in PAIRS:
        if not src.is_file():
            raise SystemExit(f"Missing source: {src}")
        shutil.copy2(src, dst)
        print(f"Copied {src.name} -> {dst.relative_to(CLIENT_ROOT)}")
    print("Done.")


if __name__ == "__main__":
    main()
