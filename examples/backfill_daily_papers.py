#!/usr/bin/env python3
"""One-time backfill of Hugging Face's daily-papers feed, 2023-05-04 to now.

    python examples/backfill_daily_papers.py --limit 5     # pilot
    python examples/backfill_daily_papers.py               # the lot (~22 min)

**Why this exists, and why it is not a registry source.** The registry entry for
`hf.papers.daily` carries `destroys_own_history: true`, and that is half right. The
feed's *upvote trajectory* is destroyed — ask today and you get today's total, never
what it stood at last March. But the feed's *membership* is not: `?date=YYYY-MM-DD`
returns what was on the page that day, back to 2023-05-04. Believing the flag covered
both is what made this recipe look like it needed until 2029.

So this is a one-time recovery of 1,215 days that the weekly capture would otherwise
only ever see going forward. It is not a cadence, `wss capture` must not re-run it,
and it therefore gets no registry entry — the same reasoning that keeps
`enrich_paper_titles.py` out of the registry, except that arXiv archives itself and
Hugging Face does not.

**What it writes** is ordinary archive shape: one raw file per date under
`raw/hf.papers.daily.backfill/`, partitioned by FETCH time per convention, with the
target date carried in the manifest `url` column where it belongs. The manifest is
the index; the path is just storage.

**What it cannot recover** is the upvote count as it stood on the day. Every row here
carries today's total. For "was this paper over- or under-rated" that is the right
number anyway; for "how fast did it spike" it is useless, and only forward capture
will do.
"""
import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "hf.papers.daily.backfill"
API = "https://huggingface.co/api/daily_papers?date={date}"
FIRST = dt.date(2023, 5, 4)          # nothing before this returns rows
PAUSE = 1.0
FIELDS = ["source_id", "url", "fetched_at", "http_status", "content_type",
          "content_length", "content_sha256", "etag", "last_modified", "outcome",
          "raw_ref", "reason", "warnings"]


def fetch(url, ua):
    r = subprocess.run(
        ["curl", "-sS", "--max-time", "30", "-A", ua, "-w", "\\n%{http_code}", url],
        capture_output=True, timeout=45)
    out = r.stdout.decode("utf-8", "replace")
    body, _, code = out.rpartition("\n")
    return body, int(code or 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="stop after N dates (pilot)")
    ap.add_argument("--since", type=str, help="YYYY-MM-DD, default 2023-05-04")
    args = ap.parse_args()

    ua = os.environ.get("WSS_CONTACT", "wss-hugging-face backfill")
    start = dt.date.fromisoformat(args.since) if args.since else FIRST
    today = dt.date.today()
    dates = [start + dt.timedelta(days=i) for i in range((today - start).days + 1)]

    done = set()
    mdir = ROOT / "manifest" / SOURCE
    for m in sorted(mdir.glob("*.csv")) if mdir.exists() else []:
        for row in csv.DictReader(m.open()):
            if row.get("url"):
                done.add(row["url"].rsplit("=", 1)[-1])
    dates = [d for d in dates if d.isoformat() not in done]
    if args.limit:
        dates = dates[:args.limit]
    print(f"  {len(dates)} dates to fetch ({len(done)} already in the manifest)")

    rows_by_month, written, empty = {}, 0, 0
    for i, d in enumerate(dates, 1):
        url = API.format(date=d.isoformat())
        body, code = fetch(url, ua)
        now = dt.datetime.now(dt.timezone.utc)
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        raw = body.encode()
        sha = hashlib.sha256(raw).hexdigest()
        try:
            n = len(json.loads(body))
        except Exception:
            n = -1
        if code != 200 or n < 0:
            print(f"    {d} http={code} — skipped, not written")
        elif n == 0:
            empty += 1     # a real empty day: recorded, no bytes worth keeping
        else:
            rel = f"raw/{SOURCE}/{now:%Y}/{now:%m}/{ts}-{sha[:12]}.json.gz"
            p = ROOT / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            with gzip.open(p, "wb") as fh:
                fh.write(raw)
            written += 1
            rows_by_month.setdefault(f"{now:%Y-%m}", []).append({
                "source_id": SOURCE, "url": url,
                "fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "http_status": code,
                "content_type": "application/json", "content_length": len(raw),
                "content_sha256": sha, "etag": "", "last_modified": "",
                "outcome": "first_capture", "raw_ref": rel, "reason": "",
                "warnings": f"backfill of {d.isoformat()}; upvotes are as-of-fetch, not as-of-date",
            })
        if i % 50 == 0:
            print(f"    {i}/{len(dates)}  written={written} empty={empty}", flush=True)
        time.sleep(PAUSE)

    for month, rows in rows_by_month.items():
        mp = mdir / f"{month}.csv"
        mp.parent.mkdir(parents=True, exist_ok=True)
        new = not mp.exists()
        with mp.open("a", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            if new:
                w.writeheader()
            w.writerows(rows)
        print(f"  manifest/{SOURCE}/{month}.csv  +{len(rows)} rows")
    print(f"  done: {written} files written, {empty} genuinely empty days")
    return 0


if __name__ == "__main__":
    sys.exit(main())
