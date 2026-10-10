"""Render data/metrics.json into dashboard/index.html.

The page itself lives in pipeline/templates/dashboard.html (React + Tailwind) and shares
its hero with the report (pipeline/templates/hero.js). This script only injects the data.

Usage: python pipeline/build_dashboard.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).resolve().parent / "templates"


def safe_json(obj):
    """JSON that can sit inside a <script> tag: review text can't close the tag or break the line."""
    return (json.dumps(obj, ensure_ascii=False, default=float)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
            .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def main():
    metrics = json.loads((ROOT / "data" / "metrics.json").read_text())
    page = (TEMPLATES / "dashboard.html").read_text()
    page = page.replace("/*__HERO_JS__*/", (TEMPLATES / "hero.js").read_text())
    page = page.replace("/*__METRICS__*/null", safe_json(metrics))
    out = ROOT / "dashboard" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(f"dashboard: {out}")


if __name__ == "__main__":
    main()
