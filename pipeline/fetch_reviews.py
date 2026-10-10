"""Fetch Play Store reviews for MoveInSync apps (and a benchmark competitor).

Incremental: if data/reviews_<app>.csv exists, only pulls reviews newer than the
latest one stored, so this can run on a schedule (daily/weekly) cheaply.

Usage: python pipeline/fetch_reviews.py [--full]
"""
import sys, time
from pathlib import Path
import pandas as pd
from google_play_scraper import reviews, Sort, app

from csv_safe import escape_formulas

APPS = {
    "com.moveinsync.ets": "MoveInSync (Employee)",
    "com.moveinsync.driver.lite": "Partner - Lite (Driver)",
    "com.moveinsync.driver.dco": "Driver Partner",
    "field.moveinsync.ets": "Field app",
    "in.mtap.iincube.safetrax.commuter": "Safetrax Commuter (benchmark)",
}
DATA = Path(__file__).resolve().parent.parent / "data"
# Reviewer names are deliberately not stored: the analysis never needs them.
COLS = ["reviewId", "content", "score", "thumbsUpCount",
        "reviewCreatedVersion", "at", "replyContent", "repliedAt", "appVersion"]


def fetch(app_id, since=None, max_pages=400):
    out, token = [], None
    for _ in range(max_pages):
        batch, token = reviews(app_id, lang="en", country="in", sort=Sort.NEWEST,
                               count=200, continuation_token=token)
        if not batch:
            break
        out.extend(batch)
        if since is not None and batch[-1]["at"] <= since:
            break
        if token is None or token.token is None:
            break
        time.sleep(0.3)
    return out


def main(full=False):
    DATA.mkdir(exist_ok=True)
    meta = []
    for app_id, label in APPS.items():
        path = DATA / f"reviews_{app_id}.csv"
        old = pd.read_csv(path, parse_dates=["at", "repliedAt"]) if path.exists() and not full else None
        since = old["at"].max() if old is not None and len(old) else None
        new = pd.DataFrame(fetch(app_id, since))
        new = new[[c for c in COLS if c in new.columns]] if len(new) else new
        df = pd.concat([new, old]) if old is not None else new
        df = df.drop_duplicates("reviewId").sort_values("at", ascending=False)
        df = df.drop(columns=["app", "userName"], errors="ignore")
        df.insert(0, "app", label)
        escape_formulas(df, ["content", "replyContent"]).to_csv(path, index=False)
        a = app(app_id, lang="en", country="in")
        meta.append({"app_id": app_id, "label": label, "score": a["score"],
                     "ratings": a["ratings"], "reviews": a["reviews"],
                     "installs": a["installs"], "histogram": a["histogram"],
                     "version": a.get("version"), "updated": a.get("lastUpdatedOn"),
                     "snapshot_at": pd.Timestamp.now().isoformat()})
        print(f"{label}: {len(df)} reviews stored (+{len(new)} fetched)")
    # Append a snapshot so the store-rating trend is tracked over time
    snap = DATA / "store_snapshots.csv"
    pd.DataFrame(meta).to_csv(snap, mode="a", header=not snap.exists(), index=False)


if __name__ == "__main__":
    main(full="--full" in sys.argv)
