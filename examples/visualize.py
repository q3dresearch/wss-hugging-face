#!/usr/bin/env python3
"""Render example visualizations from derived/observations/*.csv as SVG.

    python examples/visualize.py                       # leaderboard from this repo
    python examples/visualize.py --timeseries-root ../wss-engine/sandbox/out

Two charts, written to examples/charts/:

  leaderboard.svg      top models by downloads_30d at the latest capture
  adoption-curves.svg  downloads over time. Uses this repo's history once
                       >= 8 distinct capture dates exist; until then pass
                       --timeseries-root pointing at the engine sandbox's
                       synthetic archive (clearly captioned as synthetic).

Stdlib only, deterministic output. Colors are the validated reference palette
from the dataviz method (categorical slots in fixed order, assigned to
entities alphabetically so a re-render never repaints a surviving series).
"""

from __future__ import annotations

import argparse
import csv
import math
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape


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
OUT_DIR = REPO / "examples" / "charts"

# Reference palette (validated: adjacent CVD dE >= 8, normal-vision >= 15).
# Aqua and yellow sit below 3:1 on this surface -> relief rule: every series
# carries a visible direct label in ink, never color alone.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SERIES = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")  # fixed slot order, never cycled
SEQ_HUE = "#2a78d6"
FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

METRIC = "downloads_30d"


def load_observations(root: Path) -> list[dict]:
    rows: list[dict] = []
    for partition in sorted((root / "derived" / "observations").glob("*.csv*")):
        with _open_partition(partition) as fh:
            rows.extend(r for r in csv.DictReader(fh) if r["metric"] == METRIC)
    return rows


def compact(value: float) -> str:
    for cut, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if value >= cut:
            text = f"{value / cut:.1f}".rstrip("0").rstrip(".")
            return f"{text}{suffix}"
    return f"{value:.0f}"


def text_width(text: str, size: float) -> float:
    return len(text) * size * 0.58  # sans-serif estimate, generous


def truncate(name: str, max_px: float, size: float) -> str:
    if text_width(name, size) <= max_px:
        return name
    keep = max(8, int(max_px / (size * 0.58)) - 1)
    return name[: keep - 6] + "…" + name[-5:]


def svg_text(x: float, y: float, text: str, *, size: float, fill: str, anchor: str = "start", weight: str = "normal", tabular: bool = False) -> str:
    style = "font-variant-numeric: tabular-nums;" if tabular else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family=\'{FONT}\' font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" style="{style}">{escape(text)}</text>'
    )


def chart_header(width: float, title: str, subtitle: str) -> str:
    return svg_text(24, 30, title, size=16, fill=INK, weight="600") + svg_text(24, 50, subtitle, size=12, fill=INK2)


def wrap_svg(width: float, height: float, title: str, desc: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">\n'
        f"<title>{escape(title)}</title>\n<desc>{escape(desc)}</desc>\n"
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>\n{body}\n</svg>\n'
    )


def rounded_end_bar(x: float, y: float, w: float, h: float, r: float = 4) -> str:
    """Horizontal bar: square at the baseline (left), 4px rounded data-end (right)."""
    r = min(r, w / 2, h / 2)
    return (
        f'<path d="M{x:.1f},{y:.1f} h{w - r:.1f} q{r},0 {r},{r} v{h - 2 * r:.1f} '
        f'q0,{r} -{r},{r} h-{w - r:.1f} z" fill="{SEQ_HUE}"/>'
    )


def leaderboard(rows: list[dict], out: Path, top_n: int = 15) -> str:
    latest = max(r["observed_at"] for r in rows)
    day = {r["entity_id"]: float(r["value"]) for r in rows if r["observed_at"] == latest}
    ranked = sorted(day.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]

    width, left, right, top = 920.0, 292.0, 84.0, 72.0
    bar_h, gap = 20.0, 10.0
    height = top + len(ranked) * (bar_h + gap) + 26
    vmax = ranked[0][1]
    span = width - left - right

    body = [chart_header(width, "Most downloaded text-generation models", f"top {top_n} of {len(day):,} tracked models · downloads in the trailing 30 days · snapshot {latest[:10]}")]
    body.append(f'<line x1="{left}" y1="{top - 6}" x2="{left}" y2="{height - 24}" stroke="{BASELINE}" stroke-width="1"/>')
    for i, (entity, value) in enumerate(ranked):
        y = top + i * (bar_h + gap)
        w = max(2.0, value / vmax * span)
        body.append(rounded_end_bar(left, y, w, bar_h))
        body.append(svg_text(left - 10, y + bar_h - 5.5, truncate(entity, left - 40, 12), size=12, fill=INK2, anchor="end"))
        body.append(svg_text(left + w + 8, y + bar_h - 5.5, compact(value), size=12, fill=INK, weight="600"))
    body.append(svg_text(24, height - 8, "source: wss-hugging-face · hf.models.text-generation · CC-BY-4.0", size=10, fill=MUTED))

    desc = "Horizontal bar chart of the most downloaded text-generation models on the Hugging Face Hub, trailing 30-day downloads."
    out.write_text(wrap_svg(width, height, "Most downloaded text-generation models", desc, "\n".join(body)), encoding="utf-8")
    return f"{out.relative_to(REPO)} — {len(ranked)} bars, snapshot {latest[:10]}"


def adoption_curves(rows: list[dict], out: Path, synthetic: bool) -> str:
    # series per entity: sorted (date, value); slots assigned alphabetically so
    # a re-render with the same entities never repaints anyone
    by_entity: dict[str, dict[str, float]] = {}
    for r in rows:
        by_entity.setdefault(r["entity_id"], {})[r["observed_at"][:10]] = float(r["value"])
    latest_value = {e: series[max(series)] for e, series in by_entity.items()}
    keep = sorted(sorted(by_entity, key=lambda e: -latest_value[e])[:4])
    series = {e: sorted(by_entity[e].items()) for e in keep}

    all_dates = sorted({d for s in series.values() for d, _ in s})
    d0, d1 = date.fromisoformat(all_dates[0]).toordinal(), date.fromisoformat(all_dates[-1]).toordinal()
    values = [v for s in series.values() for _, v in s if v > 0]
    lo = 10 ** math.floor(math.log10(min(values)))
    hi = max(values) * 1.25  # headroom, not a whole empty decade

    width, height = 920.0, 500.0
    left, right, top, bottom = 64.0, 168.0, 92.0, 48.0

    def x_of(day_iso: str) -> float:
        o = date.fromisoformat(day_iso).toordinal()
        return left + (o - d0) / max(1, d1 - d0) * (width - left - right)

    def y_of(v: float) -> float:
        f = (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
        return (height - bottom) - f * (height - bottom - top)

    sub = "trailing 30-day downloads per model · log scale"
    sub += " · SYNTHETIC sandbox data (planted trajectories)" if synthetic else f" · captured daily since {all_dates[0]}"
    body = [chart_header(width, "Adoption curves", sub)]

    # legend (always present for >= 2 series), one row under the header
    lx = 24.0
    for i, e in enumerate(keep):
        body.append(f'<circle cx="{lx + 4}" cy="66" r="4" fill="{SERIES[i]}"/>')
        label = e.split("/")[-1]
        body.append(svg_text(lx + 12, 70, label, size=11, fill=INK2))
        lx += 12 + text_width(label, 11) + 18

    # horizontal decade gridlines, hairline, recessive
    v = lo
    while v <= hi * 1.001:
        y = y_of(v)
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        body.append(svg_text(left - 8, y + 3.5, compact(v), size=11, fill=MUTED, anchor="end", tabular=True))
        v *= 10
    # month ticks
    seen_months = sorted({d[:7] for d in all_dates})
    for month in seen_months:
        first = next(d for d in all_dates if d.startswith(month))
        body.append(svg_text(x_of(first), height - bottom + 18, month, size=11, fill=MUTED, tabular=True))
    body.append(f'<line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="{BASELINE}" stroke-width="1"/>')

    # lines (2px, round), broken on gaps > 3 days; end marker with surface ring
    ends: list[tuple[float, str, str, bool, float]] = []  # (y, label, color, died, x)
    for i, e in enumerate(keep):
        pts = series[e]
        segments: list[list[tuple[float, float]]] = [[]]
        prev_o = None
        for d, v in pts:
            o = date.fromisoformat(d).toordinal()
            if prev_o is not None and o - prev_o > 3:
                segments.append([])
            segments[-1].append((x_of(d), y_of(v)))
            prev_o = o
        for seg in segments:
            if len(seg) > 1:
                path = " ".join(f"{x:.1f},{y:.1f}" for x, y in seg)
                body.append(f'<polyline points="{path}" fill="none" stroke="{SERIES[i]}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>')
        ex, ey = segments[-1][-1]
        body.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="{SERIES[i]}" stroke="{SURFACE}" stroke-width="2"/>')
        died = pts[-1][0] < all_dates[-1]
        name = e.split("/")[-1] + (" (gone)" if died else f"  {compact(pts[-1][1])}")
        ends.append((ey, name, SERIES[i], died, ex))

    # direct end labels; resolve collisions by nudging, leader line if moved far
    ends.sort(key=lambda t: t[0])
    placed: list[float] = []
    for ey, name, color, died, ex in ends:
        y = ey
        for p in placed:
            if abs(y - p) < 14:
                y = p + 14
        placed.append(y)
        anchor_x = ex + 12 if not died else ex + 10
        if abs(y - ey) > 7:
            body.append(f'<line x1="{ex + 7}" y1="{ey:.1f}" x2="{anchor_x - 2}" y2="{y - 3.5:.1f}" stroke="{BASELINE}" stroke-width="1"/>')
        body.append(svg_text(anchor_x, y + 3.5, name, size=11, fill=MUTED if died else INK, weight="normal" if died else "600"))

    caption = "source: wss sandbox — ground truth planted, recovered by this chart" if synthetic else "source: wss-hugging-face · hf.models.text-generation · CC-BY-4.0"
    body.append(svg_text(24, height - 10, caption, size=10, fill=MUTED))

    desc = "Line chart of trailing 30-day downloads per model over time on a log scale, one line per model."
    out.write_text(wrap_svg(width, height, "Adoption curves", desc, "\n".join(body)), encoding="utf-8")
    return f"{out.relative_to(REPO)} — {len(keep)} series over {len(all_dates)} capture dates" + (" (synthetic)" if synthetic else "")


def papers_in_production(root: Path, out: Path, top_n: int = 18) -> str:
    """Which papers' ideas are actually built into models people download.

    Citation counts measure academic attention. This measures production
    adoption: how many of the top-1,000 most-downloaded models carry an
    `arxiv:` tag for the paper. It is the difference between an idea being
    discussed and an idea having won.
    """
    import json

    rows = []
    for partition in sorted((root / "derived" / "observations").glob("*.csv*")):
        with _open_partition(partition) as fh:
            rows.extend(
                r for r in csv.DictReader(fh)
                if r["metric"] == "models_implementing" and r["series_id"] == "hf.models.top-downloads"
            )
    if not rows:
        return "papers-in-production.svg skipped: no models_implementing observations yet"

    latest = max(r["observed_at"] for r in rows)
    ranked = sorted(
        ((r["entity_id"].removeprefix("paper:arxiv:"), int(r["value"])) for r in rows if r["observed_at"] == latest),
        key=lambda kv: (-kv[1], kv[0]),
    )
    titles = {}
    cache = root / "examples" / "paper-titles.json"
    if cache.exists():
        titles = json.loads(cache.read_text(encoding="utf-8"))

    top = ranked[:top_n]
    width, left, right, top_pad = 940.0, 430.0, 90.0, 74.0
    bar_h, gap = 16.0, 8.0
    height = top_pad + len(top) * (bar_h + gap) + 34
    vmax = top[0][1]
    span = width - left - right

    body = [
        chart_header(
            width,
            "Papers that actually shipped",
            f"models among the top 1,000 by downloads that implement each paper · "
            f"{len(ranked)} papers represented · snapshot {latest[:10]}",
        )
    ]
    body.append(f'<line x1="{left}" y1="{top_pad - 8}" x2="{left}" y2="{height - 30}" stroke="{BASELINE}" stroke-width="1"/>')
    for i, (arxiv_id, count) in enumerate(top):
        y = top_pad + i * (bar_h + gap)
        w = max(2.0, count / vmax * span)
        body.append(rounded_end_bar(left, y, w, bar_h))
        label = titles.get(arxiv_id, arxiv_id)
        body.append(svg_text(left - 10, y + bar_h - 4, truncate(label, left - 40, 11), size=11, fill=INK2, anchor="end"))
        body.append(svg_text(left + w + 7, y + bar_h - 4, str(count), size=11, fill=INK, weight="600", tabular=True))
    body.append(
        svg_text(24, height - 6, "source: wss-hugging-face · hf.models.top-downloads · titles via arXiv · CC-BY-4.0", size=10, fill=MUTED)
    )
    out.write_text(wrap_svg(width, height, "Papers that actually shipped", "Ranked bar chart of research papers by how many of the top 1,000 Hugging Face models implement them.", "\n".join(body)), encoding="utf-8")
    return f"{out.relative_to(REPO)} — {len(top)} of {len(ranked)} papers"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(REPO), help="data root for the leaderboard (default: this repo)")
    ap.add_argument("--timeseries-root", help="fallback archive for adoption curves (e.g. ../wss-engine/sandbox/out)")
    ap.add_argument("--min-real-dates", type=int, default=8, help="real capture dates needed before curves switch to real data")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_observations(Path(args.root))
    if not rows:
        print(f"no {METRIC} observations under {args.root} — run capture + derive first")
        return 1
    print(leaderboard(rows, OUT_DIR / "leaderboard.svg"))

    real_dates = {r["observed_at"][:10] for r in rows}
    if len(real_dates) >= args.min_real_dates:
        print(adoption_curves(rows, OUT_DIR / "adoption-curves.svg", synthetic=False))
    elif args.timeseries_root:
        ts_rows = load_observations(Path(args.timeseries_root))
        print(adoption_curves(ts_rows, OUT_DIR / "adoption-curves.svg", synthetic=True))
    else:
        print(f"adoption-curves.svg skipped: only {len(real_dates)} real capture date(s) (< {args.min_real_dates}) and no --timeseries-root given")

    print(papers_in_production(Path(args.root), OUT_DIR / "papers-in-production.svg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
