"""One command for the weekly refresh: fetch -> analyze -> triage -> dashboard -> alerts.

Usage: python pipeline/run_weekly.py
Set SLACK_WEBHOOK_URL to also post the alert summary to Slack.
"""
import json, os, urllib.request
from pathlib import Path

import fetch_reviews, analyze, triage, build_dashboard

ROOT = Path(__file__).resolve().parent.parent


def load_env(path=ROOT / ".env"):
    """Read KEY=VALUE lines from a local .env (git-ignored). Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def alert_text(m):
    a, s, y = m["alerts"], m["store"], m["last_12m"]
    lines = [f"*MoveInSync Play Store, week of {m['data_through']}*",
             f"Store rating {s['score']:.2f} ({s['ratings']:,} ratings) · written reviews last 12 mo {y['avg']:.2f}★, "
             f"{y['one_star']:.0%} 1★ · reply rate {y['reply_rate']:.0%}"]
    for r in a["release_regressions"]:
        lines.append(f":rotating_light: Release {r['version']}: 1★ {r['one_star']:.0%} vs baseline {r['baseline_one_star']:.0%} "
                     f"({r['reviews']} reviews). Top issues: {', '.join(r['top_negative_themes'])}")
    if a["spiking_themes"]:
        lines.append(":chart_with_upwards_trend: Rising in last 30 days: " + "; ".join(a["spiking_themes"]))
    if a["safety_last_30d"]:
        lines.append(f":warning: {len(a['safety_last_30d'])} safety-related review(s) in last 30 days. See dashboard, route to Ops today.")
    return "\n".join(lines)


def main():
    load_env()
    fetch_reviews.main()
    analyze.main()
    triage.main()
    build_dashboard.main()
    m = json.loads((ROOT / "data" / "metrics.json").read_text())
    text = alert_text(m)
    print("\n" + text)
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    if hook:
        req = urllib.request.Request(hook, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)


if __name__ == "__main__":
    main()
