"""Build the reply triage queue: every unanswered 1-3 star review, tagged and routed.

Output: data/triage_queue.csv, sorted so the reviews store visitors see most
(most upvoted, newest) come first. Customer Success works top-down each day.
"""
from pathlib import Path
import pandas as pd
from taxonomy import classify, LABELS, OWNER
from csv_safe import escape_formulas

DATA = Path(__file__).resolve().parent.parent / "data"
ROUTE = {"app": "Product/Eng: answer with fix status", "ops": "Ops: forward to client transport desk",
         "both": "Ops + Product", "generic": "CS: ask for details"}


def main(days=30):
    df = pd.read_csv(DATA / "reviews_com.moveinsync.ets.csv", parse_dates=["at"])
    q = df[(df.score <= 3) & df.replyContent.isna() & (df["at"] > df["at"].max() - pd.Timedelta(days=days))].copy()
    q["tags"] = q.content.map(classify)
    owners = q.tags.map(lambda t: {OWNER[x] for x in t} - {"-"})
    q["owner"] = owners.map(lambda o: "both" if o == {"app", "ops"} else (next(iter(o)) if o else "generic"))
    q["route_to"] = q.owner.map(ROUTE)
    q["themes"] = q.tags.map(lambda t: "; ".join(LABELS[x] for x in t))
    q["safety_flag"] = q.content.str.contains(r"safety|unsafe|harass|misbehav|molest|drunk|abusive|threat", case=False, na=False)
    q = q.sort_values(["safety_flag", "thumbsUpCount", "at"], ascending=False)
    cols = ["at", "score", "safety_flag", "owner", "route_to", "themes", "thumbsUpCount", "reviewCreatedVersion", "content", "reviewId"]
    escape_formulas(q[cols], ["content", "themes"]).to_csv(DATA / "triage_queue.csv", index=False)
    print(f"triage queue: {len(q)} unanswered 1-3★ reviews from the last {days} days "
          f"({int(q.safety_flag.sum())} safety-flagged)")


if __name__ == "__main__":
    main()
