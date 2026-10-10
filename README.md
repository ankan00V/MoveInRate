# MoveInSync Play Store ratings: diagnosis, plan and live monitor

Submission for the MoveInSync Forward Deployed Engineer assignment.

- **Recommendation:** [`report/index.html`](report/index.html). Where the rating stands, why, ten ranked tickets, expected impact, and method.
- **Live dashboard:** https://ankan00v.github.io/MoveInRate/. Refreshed from the Play Store every hour, and updates itself in the browser without a reload.
- **Report on the web:** https://ankan00v.github.io/MoveInRate/report/
- **Reply triage queue:** [`data/triage_queue.csv`](data/triage_queue.csv). Unanswered 1–3★ reviews from the last 30 days, tagged and routed.

## Findings

| | |
|---|---|
| Store rating | **4.64** (114,849 ratings) |
| Written reviews, last 12 months | **3.83★**, 24% are 1★, roughly flat since 2022 |
| "Most relevant" reviews a store visitor sees | **1.4★** average; 37 of the top 40 are 1–2★ |
| Developer reply rate | **3%**, down from about 95% before July 2024 |
| Negative reviews that name a cause and involve the app | **84%** |
| Rising in the last 30 days | "Not installed from Play Store" lockouts (2% → 9%), forced rating prompts (3% → 8%), notification spam |

What to do first:
1. Make trip feedback skippable and move Play review requests to the In-App Review API after good trips.
2. Fix the false install-source lockout.
3. Restart replying, with real, closed-loop answers.

Then: session persistence, a cached "today's trip" launch card, and staged rollouts gated on review signals.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python pipeline/run_weekly.py            # incremental fetch → metrics → triage → dashboard → weekly Slack summary
.venv/bin/python pipeline/run_weekly.py --hourly   # same, but Slack only for alerts that are new since the last live run
.venv/bin/python pipeline/build_site.py            # assemble _site/ (dashboard, metrics.json, report) for GitHub Pages
.venv/bin/python pipeline/fetch_reviews.py --full  # full re-fetch from scratch
```

`.github/workflows/weekly-ratings.yml` runs **every hour**: it fetches new reviews, redeploys the live dashboard to GitHub Pages, and posts any new release regression, rising theme or safety review to Slack. **Every Monday at 07:00 IST** it also posts the full weekly summary and commits a data snapshot. Hourly runs do not commit, so the history stays clean. Add a `SLACK_WEBHOOK_URL` repo secret to post the alert summary to a channel. For local runs, copy `.env.example` to `.env` (git-ignored) and fill it in.

## Pipeline

| File | What it does |
|---|---|
| `pipeline/fetch_reviews.py` | Incremental Play Store fetch for all MoveInSync apps plus the Safetrax benchmark. Appends a store snapshot to `data/store_snapshots.csv` on every run, so the store-rating history builds up over time. |
| `pipeline/taxonomy.py` | 17-theme complaint classifier (English and Hinglish regex). Each theme has an owner: `app` or `ops`. |
| `pipeline/analyze.py` | Monthly trends, theme shares (12 months, prior 180 days, last 30 days), per-release regression check, safety list, benchmark. Writes `data/metrics.json`. |
| `pipeline/triage.py` | Builds the daily reply queue, safety-flagged reviews first, then by upvotes. |
| `pipeline/templates/` | `hero.js` (shared React hero) and `dashboard.html` (React + Tailwind dashboard that polls `metrics.json` every 5 minutes). |
| `pipeline/build_dashboard.py` | Injects `metrics.json` into the dashboard template, escaped for safe embedding. |
| `pipeline/build_site.py` | Assembles the GitHub Pages site. |
| `pipeline/run_weekly.py` | Runs the pipeline. Weekly mode posts the summary to Slack. Hourly mode compares against the live site and posts only new alerts. |

**Alert rules**, set in `analyze.py`:
- **Release regression:** a release's 1★ share is at least 8 points above the 90 days before it shipped, with 20 or more reviews.
- **Rising theme:** a theme's share in the last 30 days is at least 1.5 times its prior-180-day share.
- **Safety:** every safety-related review is listed individually.

## Method and tools

- **Data:** all 24,314 public reviews of `com.moveinsync.ets`, the store histogram, and the "most relevant" ordering. The open-source `google-play-scraper` library was used for collection.
- **Taxonomy:** built by reading about 400 recent 1–2★ reviews by hand. It was then checked on a separate 80-review holdout (`data/validation_sample.csv`). About 91% of assigned tags were correct and about 88% of themes present were caught. The misses were fixed afterwards.
- **Star-only vs written ratings:** estimated by subtracting the written-review counts from the store histogram.
- **Tools:** Python (pandas, google-play-scraper). Claude Code was used as an AI pair for code, regex drafting and page building. Every number comes from the pipeline output. Google's Android documentation was used for the In-App Review API rules and Android Vitals thresholds.
- **Limits:** public data only. Play Console, Android Vitals, Play Integrity verdicts, iOS and internal tickets were not visible. The root causes for tickets 2 and 4 are hypotheses to confirm against those sources.
