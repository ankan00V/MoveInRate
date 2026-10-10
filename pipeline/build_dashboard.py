"""Render data/metrics.json into a self-contained dashboard/index.html.

Usage: python pipeline/build_dashboard.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CSS = """
:root{--bg:#f6f7f5;--surface:#fff;--ink:#17201f;--muted:#5a6764;--rule:#d9dfdc;--accent:#0d6b5f;--signal:#d98a0b;--bad:#c2412d;--ops:#6b5bd6;--chip:#e9eeec;
--fd:"Bricolage Grotesque","Avenir Next","Segoe UI",sans-serif;--fb:"Public Sans","Helvetica Neue",Arial,sans-serif;--fm:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111816;--surface:#18211f;--ink:#e6ecea;--muted:#9aa8a4;--rule:#2b3734;--accent:#4fc2ad;--signal:#f0ac3a;--bad:#f07a63;--ops:#a79bff;--chip:#22302d;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#111816;--surface:#18211f;--ink:#e6ecea;--muted:#9aa8a4;--rule:#2b3734;--accent:#4fc2ad;--signal:#f0ac3a;--bad:#f07a63;--ops:#a79bff;--chip:#22302d;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--fb);font-size:15px;line-height:1.5}
.wrap{max-width:72rem;margin:0 auto;padding-inline:1.25rem;padding-block:2rem 3rem;display:flex;flex-direction:column;gap:1.5rem}
h1,h2{font-family:var(--fd);margin:0;line-height:1.15}h1{font-size:2rem}h2{font-size:1.25rem}
.eb{font-family:var(--fm);font-size:.75rem;text-transform:uppercase;letter-spacing:.08em;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(11rem,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:6px;overflow:hidden}
.kpi{background:var(--surface);padding:1rem;display:flex;flex-direction:column;gap:.3rem}.kpi .v{font-family:var(--fd);font-size:1.9rem;font-weight:700;line-height:1}
.kpi .d{font-size:.8rem;color:var(--muted)}.bad{color:var(--bad)}.good{color:var(--accent)}
.panel{background:var(--surface);border:1px solid var(--rule);border-radius:6px;padding:1.1rem;display:flex;flex-direction:column;gap:.75rem;min-width:0}
.grid2{display:grid;grid-template-columns:repeat(auto-fit,minmax(22rem,1fr));gap:1rem}
.alert{border-left:3px solid var(--bad);padding:.2rem 0 .2rem .8rem}.alert.warn{border-color:var(--signal)}.alert.ok{border-color:var(--accent)}
.tbl{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.875rem}th,td{text-align:left;padding:.45rem .6rem;border-bottom:1px solid var(--rule);vertical-align:top}
th{font-family:var(--fm);font-size:.7rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}td.r,th.r{text-align:right;font-family:var(--fm);font-variant-numeric:tabular-nums;white-space:nowrap}
.pill{font-family:var(--fm);font-size:.7rem;padding:.1rem .4rem;border-radius:3px;background:var(--chip);white-space:nowrap}.pill.app{color:var(--accent)}.pill.ops{color:var(--ops)}.pill.flag{background:var(--bad);color:var(--surface)}.pill.up{background:var(--signal);color:#1b1404}
blockquote{margin:0;font-style:italic;color:var(--muted);font-size:.85rem}
.chart{overflow-x:auto}.chart svg{display:block;width:100%;height:auto;min-width:30rem}.chart text{fill:var(--muted);font-family:var(--fm);font-size:11px}
.g{stroke:var(--rule)}.lb{fill:none;stroke:var(--bad);stroke-width:2}.la{fill:none;stroke:var(--accent);stroke-width:2}
.fine{font-size:.8rem;color:var(--muted)}
"""


def esc(s):
    return html.escape(str(s))


def pct(x):
    return "–" if x is None else f"{x:.0%}"


def main():
    m = json.loads((ROOT / "data" / "metrics.json").read_text())
    s, y, rel, a, b = m["store"], m["last_12m"], m["most_relevant"], m["alerts"], m["benchmark"]

    alerts = []
    for r in a["release_regressions"]:
        alerts.append(f'<div class="alert"><strong>Release {esc(r["version"])}</strong>: 1★ {pct(r["one_star"])} vs {pct(r["baseline_one_star"])} baseline '
                      f'({r["reviews"]} reviews, since {esc(r["first_seen"])}). Top issues: {esc(", ".join(r["top_negative_themes"]))}</div>')
    if a["spiking_themes"]:
        alerts.append('<div class="alert warn"><strong>Rising in the last 30 days:</strong> ' + esc("; ".join(a["spiking_themes"])) + "</div>")
    for r in a["safety_last_30d"]:
        alerts.append(f'<div class="alert"><strong>Safety · {esc(r["date"])} · {r["stars"]}★</strong> <blockquote>{esc(r["text"])}</blockquote></div>')
    if not alerts:
        alerts.append('<div class="alert ok">No release regressions, rising themes or safety reviews this week.</div>')

    theme_rows = "".join(
        f'<tr><td>{esc(t["label"])}</td><td><span class="pill {t["owner"] if t["owner"] in ("app","ops") else ""}">{esc(t["owner"])}</span></td>'
        f'<td class="r">{t["reviews"]}</td><td class="r">{pct(t["share_of_negative"])}</td><td class="r">{pct(t["share_trailing_180d"])}</td>'
        f'<td class="r">{pct(t["share_last_30d"])} {"<span class=\'pill up\'>rising</span>" if t["spiking"] else ""}</td>'
        f'<td>{"".join(f"<blockquote>{esc(q["text"][:180])}</blockquote>" for q in t["quotes"][:1])}</td></tr>'
        for t in m["themes"])

    rel_rows = "".join(
        f'<tr><td>{esc(r["version"])}</td><td>{esc(r["first_seen"])}</td><td class="r">{r["reviews"]}</td><td class="r">{r["avg"]:.2f}</td>'
        f'<td class="r">{pct(r["one_star"])}</td><td class="r">{pct(r["baseline_one_star"])}</td>'
        f'<td>{"<span class=\'pill flag\'>regression</span>" if r["regression"] else ""}</td><td>{esc(", ".join(r["top_negative_themes"]))}</td></tr>'
        for r in [r for r in m["releases"] if r["reviews"] >= 10][-12:][::-1])

    apps_rows = "".join(f'<tr><td>{esc(o["title"])}</td><td class="r">{o["score"] or 0:.2f}</td><td class="r">{o["ratings"] or 0:,}</td><td class="r">{esc(o["installs"])}</td></tr>'
                        for o in m["other_apps"])

    monthly = json.dumps([[r["month"], round(r["avg"], 3), round(r["one_star"], 3), round(r["reply_rate"], 3)] for r in m["monthly"]])

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MoveInSync Ratings Monitor</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,700&family=Public+Sans:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap">
<style>{CSS}</style></head><body><div class="wrap">
<header><p class="eb">Weekly Play Store monitor · data through {esc(m["data_through"])} · generated {esc(m["generated_at"])}</p><h1>MoveInSync Ratings Monitor</h1></header>
<div class="kpis">
 <div class="kpi"><span class="eb">Store rating</span><span class="v">{s["score"]:.2f}</span><span class="d">{s["ratings"]:,} ratings · v{esc(s["version"])}</span></div>
 <div class="kpi"><span class="eb">Written reviews, 12 mo</span><span class="v bad">{y["avg"]:.2f}★</span><span class="d">{y["reviews"]:,} reviews · {pct(y["one_star"])} 1★</span></div>
 <div class="kpi"><span class="eb">"Most relevant" top {rel["n"]}</span><span class="v {'bad' if rel['avg'] < 3 else 'good'}">{rel["avg"]:.1f}★</span><span class="d">{pct(rel["one_or_two_star"])} are 1–2★ · {pct(rel["reply_rate"])} replied</span></div>
 <div class="kpi"><span class="eb">Reply rate, 12 mo</span><span class="v {'bad' if y['reply_rate'] < .5 else 'good'}">{pct(y["reply_rate"])}</span><span class="d">target ≥ 90% of 1–3★</span></div>
 <div class="kpi"><span class="eb">Benchmark</span><span class="v">{b["score"]:.2f}</span><span class="d">{esc(b["title"])} · {pct(b["last_12m_reply_rate"])} replied</span></div>
</div>
<section class="panel"><h2>Needs attention</h2>{"".join(alerts)}</section>
<section class="panel"><h2>Monthly trend, written reviews</h2>
<p class="fine"><span style="color:var(--bad)">■</span> 1★ share &nbsp; <span style="color:var(--accent)">■</span> reply rate</p><div class="chart" id="trend"></div></section>
<section class="panel"><h2>What negative reviews are about (1–2★, last 12 months, n = {y["negative"]})</h2>
<div class="tbl"><table><thead><tr><th>Theme</th><th>Owner</th><th class="r">Reviews</th><th class="r">Share 12 mo</th><th class="r">Prior 180d</th><th class="r">Last 30d</th><th>Most upvoted example</th></tr></thead><tbody>{theme_rows}</tbody></table></div></section>
<section class="panel"><h2>Releases</h2><p class="fine">A release is flagged when its 1★ share is at least 8 points above the 90 days before it shipped, with 20 or more reviews.</p>
<div class="tbl"><table><thead><tr><th>Version</th><th>First seen</th><th class="r">Reviews</th><th class="r">Avg</th><th class="r">1★</th><th class="r">Baseline 1★</th><th></th><th>Top negative themes</th></tr></thead><tbody>{rel_rows}</tbody></table></div></section>
<section class="panel"><h2>Other MoveInSync apps</h2><div class="tbl"><table><thead><tr><th>App</th><th class="r">Rating</th><th class="r">Ratings</th><th class="r">Installs</th></tr></thead><tbody>{apps_rows}</tbody></table></div></section>
<p class="fine">Source: public Google Play reviews and listings (India, English). Themes come from the rule-based classifier in pipeline/taxonomy.py. Reply triage queue: data/triage_queue.csv.</p>
</div>
<script>
const M={monthly};const NS="http://www.w3.org/2000/svg";function e(t,a,p,x){{const n=document.createElementNS(NS,t);for(const k in a)n.setAttribute(k,a[k]);if(x!=null)n.textContent=x;p&&p.appendChild(n);return n}}
(function(){{const W=900,H=240,L=40,R=10,T=10,B=28,iw=W-L-R,ih=H-T-B,s=e("svg",{{viewBox:`0 0 ${{W}} ${{H}}`}});const x=i=>L+i/(M.length-1)*iw,y=v=>T+ih-v*ih;
[0,.25,.5,.75,1].forEach(v=>{{e("line",{{x1:L,x2:W-R,y1:y(v),y2:y(v),class:"g"}},s);e("text",{{x:L-6,y:y(v)+4,"text-anchor":"end"}},s,Math.round(v*100)+"%")}});
M.forEach((m,i)=>{{if(m[0].endsWith("-01"))e("text",{{x:x(i),y:H-8,"text-anchor":"middle"}},s,m[0].slice(0,4))}});
e("path",{{d:M.map((m,i)=>(i?"L":"M")+x(i)+","+y(m[3])).join(" "),class:"la"}},s);e("path",{{d:M.map((m,i)=>(i?"L":"M")+x(i)+","+y(m[2])).join(" "),class:"lb"}},s);
document.getElementById("trend").appendChild(s)}})();
</script></body></html>"""
    out = ROOT / "dashboard" / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(page)
    print(f"dashboard: {out}")


if __name__ == "__main__":
    main()
