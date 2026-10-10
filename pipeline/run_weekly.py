"""Refresh everything: fetch -> analyze -> triage -> dashboard -> alerts.

Usage:
  python pipeline/run_weekly.py            # weekly: full Slack summary
  python pipeline/run_weekly.py --hourly   # hourly: Slack only for what is new since the last live run

Set SLACK_WEBHOOK_URL (env or .env) to post to Slack. In hourly mode the previous run's
metrics are read from the live dashboard (PAGES_URL) so only new alerts are posted.
"""
import json, os, sys, urllib.request
from pathlib import Path

import fetch_reviews, analyze, triage, build_dashboard

ROOT = Path(__file__).resolve().parent.parent
PAGES_URL = "https://ankan00v.github.io/MoveInRate/"


def load_env(path=ROOT / ".env"):
    """Read KEY=VALUE lines from a local .env (git-ignored). Real env vars win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def esc(text):
    """Escape Slack mrkdwn control characters so review text can't add links or @-mentions."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def weekly_text(m):
    a, s, y = m["alerts"], m["store"], m["last_12m"]
    lines = [f"*MoveInSync Play Store, week of {m['data_through']}*",
             f"Store rating {s['score']:.2f} ({s['ratings']:,} ratings) · written reviews last 12 mo {y['avg']:.2f}★, "
             f"{y['one_star']:.0%} 1★ · reply rate {y['reply_rate']:.0%}"]
    for r in a["release_regressions"]:
        lines.append(f":rotating_light: Release {esc(r['version'])}: 1★ {r['one_star']:.0%} vs baseline {r['baseline_one_star']:.0%} "
                     f"({r['reviews']} reviews). Top issues: {esc(', '.join(r['top_negative_themes']))}")
    if a["spiking_themes"]:
        lines.append(":chart_with_upwards_trend: Rising in last 30 days: " + esc("; ".join(a["spiking_themes"])))
    if a["safety_last_30d"]:
        lines.append(f":warning: {len(a['safety_last_30d'])} safety-related review(s) in last 30 days. Route to Ops today.")
    lines.append(f"Live dashboard: {PAGES_URL}")
    return "\n".join(lines)


def previous_live_metrics():
    try:
        with urllib.request.urlopen(PAGES_URL + "metrics.json", timeout=20) as r:
            return json.loads(r.read())
    except Exception:
        return None


def new_alerts_text(m, prev):
    """Only what appeared since the last live run. Without a previous run, say nothing."""
    if prev is None:
        return None
    a, pa = m["alerts"], prev["alerts"]
    lines = []
    old_versions = {r["version"] for r in pa["release_regressions"]}
    for r in a["release_regressions"]:
        if r["version"] not in old_versions:
            lines.append(f":rotating_light: New release regression: {esc(r['version'])} at {r['one_star']:.0%} 1★ vs "
                         f"{r['baseline_one_star']:.0%} baseline. Top issues: {esc(', '.join(r['top_negative_themes']))}")
    for t in set(a["spiking_themes"]) - set(pa["spiking_themes"]):
        lines.append(f":chart_with_upwards_trend: Now rising: {esc(t)}")
    old_safety = {(x["date"], x["text"]) for x in pa["safety_last_30d"]}
    for x in a["safety_last_30d"]:
        if (x["date"], x["text"]) not in old_safety:
            lines.append(f":warning: New safety review ({x['date']}, {x['stars']}★): \"{esc(x['text'][:200])}\". Route to Ops now.")
    if not lines:
        return None
    return "\n".join([f"*MoveInSync Play Store, new since last hour*"] + lines + [f"Live dashboard: {PAGES_URL}"])


def post(text):
    hook = os.environ.get("SLACK_WEBHOOK_URL")
    if hook and text:
        req = urllib.request.Request(hook, data=json.dumps({"text": text, "link_names": False, "unfurl_links": False, "unfurl_media": False}).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=20)


def main():
    load_env()
    hourly = "--hourly" in sys.argv
    prev = previous_live_metrics() if hourly else None
    fetch_reviews.main()
    analyze.main()
    triage.main()
    build_dashboard.main()
    m = json.loads((ROOT / "data" / "metrics.json").read_text())
    text = new_alerts_text(m, prev) if hourly else weekly_text(m)
    print("\n" + (text or "No new alerts since the last run."))
    post(text)


if __name__ == "__main__":
    main()
