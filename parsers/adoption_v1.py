"""Parser for schema adoption.v1 — Hugging Face `/api/models` listings.

Pure function of the archived bytes. A bug here is fixed by bumping
PARSER_VERSION and re-running `wss derive` over the raw archive —
never by re-fetching.

Emits two layers from the same response:

  per-entity   downloads / likes / trending score for each model or dataset
  aggregate    how many models in the listing use each library, serve each
               task, and implement each arXiv paper

The aggregate layer is the substitution measure. Citation counts track
academic attention; `paper:<id>` tracks how many models people actually
download were built on that idea — production adoption, and the thing that
says an idea won rather than merely trended.

**Two counts, because one of them is a trap.** `models_implementing` counts
models, and a lab that ships thirty size variants of one family votes thirty
times while a lab that ships one votes once. In the 2026-09-08 capture YaRN
reads 34 models, of which 32 are Qwen: one adoption decision, counted 32
times. `orgs_implementing` counts distinct namespaces instead, which is the
number of independent parties who chose the idea. Rank by the first and you
measure release cadence; rank by the second and you measure adoption. Both
are emitted because their ratio is informative on its own — a paper with many
models and one org is a house technique, many orgs and few models each is a
standard.

Run: wss derive
"""

import json
from collections import Counter

from wss import derive

PARSER_VERSION = "3"

# (response key, metric name, unit) — keys verified against the live API 2026-08-31.
# Only keys present in the payload are emitted, so one parser serves every
# listing source (models and datasets, whatever mix of expand[] it requests).
METRICS = (
    ("downloads", "downloads_30d", "count/30d"),
    ("downloadsAllTime", "downloads_all_time", "count"),
    ("likes", "likes", "count"),
    ("trendingScore", "trending_score", "score"),
)

# entity_id is namespaced because several kinds of entity share one table:
# a model id, a library, a task and a paper must not collide.
ARXIV_PREFIX = "arxiv:"


def _org(entity_id: str) -> str:
    """The namespace that published this entity.

    Legacy canonical models carry no namespace at all (`gpt2`,
    `bert-base-uncased`). None appear in the current top-1000 listings, but the
    parser runs over whatever the archive holds, so a bare id counts as its own
    publisher rather than collapsing every such model into one empty-string org.
    """
    return entity_id.split("/", 1)[0] if "/" in entity_id else entity_id


def parse(body: bytes, ctx: derive.ParseContext):
    items = json.loads(body)
    if not isinstance(items, list):
        raise ValueError(f"{ctx.raw_ref}: expected a JSON list from the listing endpoint")

    libraries: Counter = Counter()
    tasks: Counter = Counter()
    papers: Counter = Counter()
    paper_orgs: dict[str, set[str]] = {}

    for item in items:
        entity_id = item["id"]
        for key, metric, unit in METRICS:
            if key in item and item[key] is not None:
                yield derive.Observation(
                    entity_id=entity_id, metric=metric, value=int(item[key]), unit=unit
                )

        if item.get("library_name"):
            libraries[item["library_name"]] += 1
        if item.get("pipeline_tag"):
            tasks[item["pipeline_tag"]] += 1
        # One model can cite several papers; count each at most once per model.
        for paper in {t for t in item.get("tags", []) if t.startswith(ARXIV_PREFIX)}:
            arxiv_id = paper[len(ARXIV_PREFIX) :]
            papers[arxiv_id] += 1
            paper_orgs.setdefault(arxiv_id, set()).add(_org(entity_id))

    listing_size = len(items)
    if listing_size:
        yield derive.Observation(
            entity_id="listing", metric="entities_listed", value=listing_size, unit="count"
        )
    for library, count in sorted(libraries.items()):
        yield derive.Observation(
            entity_id=f"library:{library}", metric="models_using", value=count, unit="count"
        )
    for task, count in sorted(tasks.items()):
        yield derive.Observation(
            entity_id=f"task:{task}", metric="models_serving", value=count, unit="count"
        )
    for paper, count in sorted(papers.items()):
        yield derive.Observation(
            entity_id=f"paper:arxiv:{paper}",
            metric="models_implementing",
            value=count,
            unit="count",
        )
        yield derive.Observation(
            entity_id=f"paper:arxiv:{paper}",
            metric="orgs_implementing",
            value=len(paper_orgs[paper]),
            unit="count",
        )


derive.register("adoption.v1", parse, PARSER_VERSION)
