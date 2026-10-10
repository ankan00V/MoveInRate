"""Assemble the GitHub Pages site in _site/.

  _site/index.html         live dashboard (polls metrics.json)
  _site/metrics.json       latest metrics
  _site/report/index.html  the recommendation report
  _site/report/*.pdf       PDF of the report

Usage: python pipeline/build_site.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"

REPORT_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
</head>
<body>
"""


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "report").mkdir(parents=True)
    shutil.copy(ROOT / "dashboard" / "index.html", SITE / "index.html")
    shutil.copy(ROOT / "data" / "metrics.json", SITE / "metrics.json")
    # The report source is written as a page body (it is also published as a claude.ai artifact)
    report = (ROOT / "report" / "index.html").read_text()
    (SITE / "report" / "index.html").write_text(REPORT_HEAD + report + "\n</body>\n</html>\n")
    for pdf in (ROOT / "report").glob("*.pdf"):
        shutil.copy(pdf, SITE / "report" / pdf.name)
    (SITE / ".nojekyll").write_text("")
    print(f"site: {SITE}")


if __name__ == "__main__":
    main()
