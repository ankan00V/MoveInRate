"""Turn stored reviews into metrics.json: trends, themes, release regressions, alerts.

Usage: python pipeline/analyze.py
Reads data/reviews_*.csv (from fetch_reviews.py), writes data/metrics.json.
"""
import json
from pathlib import Path

import pandas as pd
from google_play_scraper import app as play_app, reviews, Sort

from taxonomy import classify, LABELS, OWNER

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MAIN = "com.moveinsync.ets"
BENCH = "in.mtap.iincube.safetrax.commuter"

# Alert thresholds (tune with the team)
RELEASE_MIN_REVIEWS = 20          # don't judge a release on fewer reviews than this
RELEASE_ONE_STAR_DELTA = 0.08     # flag if 1-star share is 8pp above trailing baseline
RELEASE_WATCH_DELTA = 0.05       # mark "watch" from 5pp up to the flag line
THEME_SPIKE_RATIO = 1.5           # flag theme if last-30d share >= 1.5x trailing 180d share
SAFETY_PATTERN = r"safety|unsafe|not safe|harass|misbehav|molest|drunk|rash driv|abusive|threat|sos"


def load(app_id):
    df = pd.read_csv(DATA / f"reviews_{app_id}.csv", parse_dates=["at", "repliedAt"])
    df["content"] = df["content"].fillna("")
    df["tags"] = df["content"].map(classify)
    return df


def owner_of(tags):
    owners = {OWNER[t] for t in tags} - {"-"}
    if owners == {"app", "ops"}:
        return "both"
    return owners.pop() if owners else "generic"


def quotes(frame, n=3):
    f = frame[frame.content.str.len().between(60, 260)]
    f = f.sort_values(["thumbsUpCount", "at"], ascending=False).head(n)
    return [{"text": r.content.replace("\n", " "), "stars": int(r.score), "date": str(r.at.date()),
             "version": None if pd.isna(r.reviewCreatedVersion) else str(r.reviewCreatedVersion)}
            for r in f.itertuples()]


def main():
    df = load(MAIN)
    now = df["at"].max()
    y1 = df[df["at"] > now - pd.Timedelta(days=365)]
    neg = y1[y1.score <= 2]

    meta = play_app(MAIN, lang="en", country="in")
    hist = meta["histogram"]
    written_hist = [int((df.score == s).sum()) for s in range(1, 6)]
    star_only = [max(h - w, 0) for h, w in zip(hist, written_hist)]

    # What a store visitor sees first
    rel, _ = reviews(MAIN, lang="en", country="in", sort=Sort.MOST_RELEVANT, count=40)
    rel_df = pd.DataFrame(rel)

    # Monthly trend (last 36 months)
    m = df[df["at"] > now - pd.DateOffset(months=36)].copy()
    m["month"] = m["at"].dt.to_period("M").astype(str)
    monthly = m.groupby("month").agg(
        n=("score", "size"), avg=("score", "mean"),
        one_star=("score", lambda s: (s == 1).mean()),
        reply_rate=("replyContent", lambda s: s.notna().mean()),
    ).reset_index()

    # Themes on last-12-month negative reviews
    ex = neg.explode("tags")
    recent = neg[neg["at"] > now - pd.Timedelta(days=30)]
    trailing = neg[(neg["at"] <= now - pd.Timedelta(days=30)) & (neg["at"] > now - pd.Timedelta(days=210))]
    themes = []
    for tag, g in ex.groupby("tags"):
        share_recent = recent.tags.map(lambda t: tag in t).mean() if len(recent) else 0
        share_trail = trailing.tags.map(lambda t: tag in t).mean() if len(trailing) else 0
        themes.append({
            "key": tag, "label": LABELS[tag], "owner": OWNER[tag],
            "reviews": int(g.reviewId.nunique()), "share_of_negative": g.reviewId.nunique() / len(neg),
            "upvotes": int(g.thumbsUpCount.sum()),
            "share_last_30d": share_recent, "share_trailing_180d": share_trail,
            "spiking": bool(share_trail and share_recent >= THEME_SPIKE_RATIO * share_trail and len(recent) >= 30),
            "quotes": quotes(neg[neg.tags.map(lambda t: tag in t)]),
        })
    themes.sort(key=lambda t: -t["reviews"])

    # Release regressions: each version's 1-star share vs trailing 90-day baseline before it shipped
    releases = []
    for ver, g in y1.dropna(subset=["reviewCreatedVersion"]).groupby("reviewCreatedVersion"):
        first = g["at"].min()
        base = df[(df["at"] < first) & (df["at"] >= first - pd.Timedelta(days=90))]
        one, base_one = (g.score == 1).mean(), (base.score == 1).mean() if len(base) else None
        top = g[g.score <= 2].explode("tags").tags.value_counts().drop("unspecified", errors="ignore").head(3).index.tolist()
        releases.append({
            "version": str(ver), "first_seen": str(first.date()), "reviews": len(g), "avg": g.score.mean(),
            "one_star": one, "baseline_one_star": base_one,
            "regression": bool(len(g) >= RELEASE_MIN_REVIEWS and base_one is not None and one - base_one >= RELEASE_ONE_STAR_DELTA),
            "watch": bool(len(g) >= RELEASE_MIN_REVIEWS and base_one is not None and RELEASE_WATCH_DELTA <= one - base_one < RELEASE_ONE_STAR_DELTA),
            "top_negative_themes": [LABELS[t] for t in top],
        })
    releases.sort(key=lambda r: r["first_seen"])

    # Safety: never left in an aggregate — surfaced individually for same-day ops follow-up
    safety = y1[(y1.score <= 3) & y1.content.str.contains(SAFETY_PATTERN, case=False, regex=True)]
    safety = safety[safety["at"] > now - pd.Timedelta(days=30)]

    # Benchmark
    b = load(BENCH)
    b1 = b[b["at"] > now - pd.Timedelta(days=365)]
    bmeta = play_app(BENCH, lang="en", country="in")

    other_apps = []
    for aid in ["com.moveinsync.driver.lite", "com.moveinsync.driver.dco", "field.moveinsync.ets"]:
        a = play_app(aid, lang="en", country="in")
        other_apps.append({"app_id": aid, "title": a["title"], "score": a["score"], "ratings": a["ratings"],
                           "installs": a["installs"]})

    out = {
        "generated_at": pd.Timestamp.now(tz="UTC").isoformat(timespec="minutes"),
        "data_through": str(now.date()),
        "store": {"title": meta["title"], "score": meta["score"], "ratings": meta["ratings"],
                  "reviews": meta["reviews"], "installs": meta["installs"], "version": meta.get("version"),
                  "histogram": hist, "written_histogram": written_hist, "star_only_histogram": star_only},
        "corpus": {"reviews_total": len(df), "first": str(df["at"].min().date())},
        "last_12m": {
            "reviews": len(y1), "avg": y1.score.mean(), "one_star": (y1.score == 1).mean(),
            "negative": len(neg), "negative_share": len(neg) / len(y1),
            "reply_rate": y1.replyContent.notna().mean(),
            "negative_by_owner": neg.tags.map(owner_of).value_counts(normalize=True).to_dict(),
        },
        "most_relevant": {"avg": rel_df.score.mean(), "n": len(rel_df),
                          "reply_rate": rel_df.replyContent.notna().mean(),
                          "one_or_two_star": (rel_df.score <= 2).mean()},
        "monthly": monthly.to_dict("records"),
        "themes": themes,
        "releases": releases,
        "alerts": {
            "release_regressions": [r for r in releases if r["regression"]
                                    and pd.Timestamp(r["first_seen"]) > now - pd.Timedelta(days=90)],
            "spiking_themes": [t["label"] for t in themes if t["spiking"]],
            "safety_last_30d": [{"date": str(r.at.date()), "stars": int(r.score), "text": r.content[:280]}
                                for r in safety.itertuples()],
        },
        "benchmark": {"title": bmeta["title"], "score": bmeta["score"], "ratings": bmeta["ratings"],
                      "last_12m_reviews": len(b1), "last_12m_avg": b1.score.mean(),
                      "last_12m_one_star": (b1.score == 1).mean(),
                      "last_12m_reply_rate": b1.replyContent.notna().mean()},
        "other_apps": other_apps,
    }
    (DATA / "metrics.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: out[k] for k in ["store", "last_12m", "most_relevant", "alerts", "benchmark"]},
                     indent=1, default=float)[:6000])


if __name__ == "__main__":
    main()
