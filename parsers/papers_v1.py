"""Parser for schema papers.v1 — the Hugging Face `/api/daily_papers` feed.

Each item wraps a paper object; the entity is the arxiv id. Community
upvotes and comment counts are the interest signals; their trajectories
across daily captures are what makes over/underrated calls defensible.

**github_stars is the second signal and it measures something different.** Upvotes
are what the Hugging Face community noticed; stars are what people went and used.
The two are only loosely related -- r = 0.13 raw and 0.54 on logs across 150 papers
carrying both -- so a paper can be admired and unused, or used and unremarked.

One caution that belongs with every use of it: the star count is as-of-fetch, never
as-of-date. A backfill returns today's total for a paper from 2023, so stars can
describe a paper's standing now but cannot say what it was when a model was built on
it. Only forward capture gives that.
"""

import json

from wss import derive

PARSER_VERSION = "2"


def parse(body: bytes, ctx: derive.ParseContext):
    items = json.loads(body)
    if not isinstance(items, list):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON list from /api/daily_papers")
    seen: set[str] = set()
    for item in items:
        paper = item["paper"]
        arxiv_id = paper["id"]
        if arxiv_id in seen:  # the feed window can resurface a paper
            continue
        seen.add(arxiv_id)
        if paper.get("upvotes") is not None:
            yield derive.Observation(entity_id=arxiv_id, metric="upvotes", value=int(paper["upvotes"]), unit="count")
        if item.get("numComments") is not None:
            yield derive.Observation(entity_id=arxiv_id, metric="comments", value=int(item["numComments"]), unit="count")
        if paper.get("githubStars") is not None:
            yield derive.Observation(entity_id=arxiv_id, metric="github_stars", value=int(paper["githubStars"]), unit="count")


derive.register("papers.v1", parse, PARSER_VERSION)
