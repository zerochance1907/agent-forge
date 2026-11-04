#!/usr/bin/env python3
"""Deterministic GitHub scout: collects trending AI / robotics repos into JSON
for the researcher agent. Uses the `gh` CLI, so it runs with the owner's token."""
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))["scout"]


def search(query, per_page=50, attempts=3):
    for attempt in range(attempts):
        r = subprocess.run(
            ["gh", "api", "-X", "GET", "search/repositories",
             "-f", f"q={query}", "-f", "sort=stars", "-f", "order=desc",
             "-f", f"per_page={per_page}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        if not r.returncode:
            return json.loads(r.stdout).get("items", [])
        time.sleep(5 * (attempt + 1))
    print(f"search failed for {query!r}: {r.stderr.strip()}", file=sys.stderr)
    return []


def summarize(item, now):
    created = dt.datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
    age_days = max((now - created).total_seconds() / 86400, 0.5)
    return {
        "full_name": item["full_name"],
        "url": item["html_url"],
        "description": (item.get("description") or "")[:300],
        "stars": item["stargazers_count"],
        "forks": item["forks_count"],
        "stars_per_day": round(item["stargazers_count"] / age_days, 1),
        "language": item.get("language"),
        "topics": item.get("topics", [])[:12],
        "license": (item.get("license") or {}).get("spdx_id"),
        "created_at": item["created_at"],
        "pushed_at": item["pushed_at"],
        "archived": item.get("archived", False),
    }


def collect(queries, now, keep):
    seen = {}
    for q in queries:
        for item in search(q):
            if item.get("fork") or item.get("archived"):
                continue
            seen.setdefault(item["full_name"], summarize(item, now))
    ranked = sorted(seen.values(), key=lambda r: r["stars_per_day"], reverse=True)
    return ranked[:keep]


def main(out_path):
    now = dt.datetime.now(dt.timezone.utc)
    d7 = (now - dt.timedelta(days=7)).date().isoformat()
    d30 = (now - dt.timedelta(days=30)).date().isoformat()
    d365 = (now - dt.timedelta(days=365)).date().isoformat()
    topics = CFG["topics"]

    week = collect(
        [f"topic:{t} created:>={d7} stars:>={CFG['week_min_stars']}" for t in topics]
        + [f"ai agent in:name,description created:>={d7} stars:>={CFG['week_min_stars']}",
           f"robot in:name,description created:>={d7} stars:>={CFG['week_min_stars']}"],
        now, CFG["keep_per_window"])
    year = collect(
        [f"topic:{t} created:>={d365} pushed:>={d30} stars:>={CFG['year_min_stars']}" for t in topics],
        now, CFG["keep_per_window"])

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"generated_at": now.isoformat(), "week": week, "year": year},
                              indent=2), encoding="utf-8")
    print(f"scout: {len(week)} week / {len(year)} year candidates -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "research/candidates.json")
