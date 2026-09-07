# How this repo works

This repo is a **capture fleet**, driven entirely by its registry. No
workflow names a source; a handful of scheduled workflows shard whatever
`registry/` marks active. The engine is
[wss](https://github.com/q3dresearch/wss-engine), pinned to one version in
`requirements.txt` and in every workflow's `ENGINE_SPEC`.

## The daily cycle

```
22:10 UTC  capture-daily   plan → matrix of shards → capture → commit deltas
23:40 UTC  health          rebuild health.csv, auto-disable, open issues
00:20 UTC  derive          rebuild derived/ observation tables, commit
```

Each capture job, per source in its shard:

1. honours `robots.txt`, waits the per-host delay, sends an identifiable
   user-agent carrying the `WSS_CONTACT` secret
2. fetches with 3 retries + exponential backoff
3. runs the entry's **gates** (status, size, content-type, must/must-not
   contain, shrink guard) — a failed gate quarantines the bytes, which never
   enter the archive and never reach git (CI artifacts only, 90 days)
4. hashes the body; identical content skips the file write but **still
   appends a manifest row** — "we looked and it was identical" is what makes
   a revision date defensible
5. archives the raw bytes verbatim under `raw/…`, appends to `manifest/…`

Nothing is parsed at capture time. Parsing happens once a day in `derive`,
from the archive — so a parser bug is fixed by re-parsing history, never by
re-fetching a page that has since changed.

## Adding a source

Create `registry/<source_id>.yml` (see the engine's
`examples/registry/example.web.stats.yml`). That is the whole change — no
workflow edits, ever. Start it `paused`, run
`wss doctor <source_id>`, read the raw response, then flip to
`active`.

The workflows here cover `cadence: daily` only, because that's all the
registry currently holds. The first `weekly` or `monthly` source also needs
its capture workflow: copy `capture-daily.yml`, change three lines (`name`,
the cron, `CADENCE`) — or take the template from the engine's
`examples/workflows/`. That's a one-time cost per cadence, not per source.

## Removing / pausing a source

Change its `status`. The raw archive and manifest history stay.

## When something breaks

Sources that fail 5 consecutive times are auto-disabled by the health run,
which opens a GitHub issue. `health/health.csv` is sorted worst-first —
triage is a weekly read of that file. To re-enable: fix the cause, set
`status: active`, commit.

## Local development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt      # or, against a sibling checkout: pip install -e ../wss-engine
export WSS_CONTACT="neldivad +https://github.com/q3dresearch/wss-hugging-face"

wss validate
wss doctor hf.models.text-generation
wss capture --cadence daily          # --shard 1/1 by default
wss derive --parsers parsers.adoption_v1
wss health --dry-run
```

## Standing up your own fork

This repo runs live at `q3dresearch/wss-hugging-face` against the engine at
[q3dresearch/wss-engine](https://github.com/q3dresearch/wss-engine). To run your
own copy:

1. Fork (or push) **both repos under one GitHub owner** — the workflows
   install the engine from `github.com/<your-owner>/wss-engine` at the tag
   pinned in `ENGINE_SPEC`.
2. Set the repo secret `WSS_CONTACT` to identify whoever runs the capture —
   `<your-username> +https://github.com/<owner>/<repo>` needs no personal
   data. Capture refuses to run without it.
3. Run the `capture-daily` workflow once by hand (Actions → capture-daily →
   Run workflow), confirm the bot's data commit lands, then let the cron
   take over.
