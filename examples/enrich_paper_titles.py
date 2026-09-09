#!/usr/bin/env python3
"""Resolve arXiv IDs seen in derived/ to titles, cached in examples/.

    python examples/enrich_paper_titles.py

This is *enrichment*, not capture. arXiv archives its own metadata
permanently, so titles are not ours to preserve — the registry would rightly
reject a source with `destroys_own_history: false`. The cache is committed so
charts render identically offline, and it is keyed by arXiv ID, so it only
ever grows.
"""

from __future__ import annotations

import csv
import glob
import json
import re
import time
import urllib.request
from pathlib import Path


def _open_partition(path):
    """Open a derived partition, gzipped or not.

    Engine v0.6.34 made `derived/observations/*.csv.gz` the written form. Every
    reader in this repo went on globbing `*.csv`, found nothing, and said "no
    observations yet -- run capture + derive first" over a full archive. Stdlib
    only, so `head`/`zcat` remain the only tools a reader needs.
    """
    import gzip
    import io
    if str(path).endswith(".gz"):
        return io.TextIOWrapper(gzip.open(path, "rb"), encoding="utf-8", newline="")
    return open(path, encoding="utf-8", newline="")

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "examples" / "paper-titles.json"
API = "https://export.arxiv.org/api/query?id_list={ids}&max_results={n}"
BATCH = 40
ENTRY_RE = re.compile(r"<entry>.*?<id>http://arxiv\.org/abs/(\S+?)</id>.*?<title>(.*?)</title>", re.S)


def ids_in_derived() -> set[str]:
    found: set[str] = set()
    for partition in sorted(glob.glob(str(REPO / "derived" / "observations" / "*.csv*"))):
        with _open_partition(partition) as fh:
            for row in csv.DictReader(fh):
                if row["metric"] == "models_implementing":
                    found.add(row["entity_id"].removeprefix("paper:arxiv:"))
    return found


def fetch(ids: list[str], contact: str) -> dict[str, str]:
    url = API.format(ids=",".join(ids), n=len(ids))
    req = urllib.request.Request(url, headers={"User-Agent": f"wss-hugging-face (contact: {contact})"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    out: dict[str, str] = {}
    for match in ENTRY_RE.finditer(body):
        versioned, title = match.group(1), " ".join(match.group(2).split())
        out[versioned.split("v")[0]] = title
    return out


def main() -> int:
    import os

    contact = os.environ.get("WSS_CONTACT", "unset")
    cache: dict[str, str] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    missing = sorted(ids_in_derived() - set(cache))
    print(f"{len(cache)} cached, {len(missing)} to resolve")

    for i in range(0, len(missing), BATCH):
        batch = missing[i : i + BATCH]
        try:
            cache.update(fetch(batch, contact))
        except Exception as exc:  # arXiv hiccups should not lose earlier work
            print(f"  batch {i // BATCH + 1} failed: {exc}")
        print(f"  resolved {len(cache)} total")
        if i + BATCH < len(missing):
            time.sleep(3)  # arXiv asks for 3s between requests

    CACHE.write_text(json.dumps(dict(sorted(cache.items())), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {CACHE.relative_to(REPO)} ({len(cache)} titles)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
