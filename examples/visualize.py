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
    """House technique or standard: the two rankings of the same 430 papers disagree.

    `models_implementing` counts models, so a lab shipping thirty size variants of one
    family votes thirty times while a lab shipping one votes once. Ranked by it, YaRN
    reads 34 models -- of which 32 are Qwen. `orgs_implementing` counts distinct
    namespaces, which is the number of independent parties who chose the idea.

    Plotting one against the other separates two things a single ranking conflates.
    **Bottom right is a house technique**: many models, one publisher, an idea its
    author ships a lot of. **Top left is a standard**: several publishers, few models
    each, an idea other people picked up. The diagonal is empty, which is the finding.

    An earlier version of this chart was a ranked bar of models_implementing alone. It
    was one axis, it was the misleading axis, and it put SigLIP -- nine models, all of
    them google/siglip* -- above ViT, which three independent orgs implement.
    """
    import json

    rows = []
    for partition in sorted((root / "derived" / "observations").glob("*.csv*")):
        with _open_partition(partition) as fh:
            rows.extend(
                r for r in csv.DictReader(fh)
                if r["metric"] in ("models_implementing", "orgs_implementing")
                and r["series_id"] == "hf.models.top-downloads"
            )
    if not rows:
        return "papers-in-production.svg skipped: no models_implementing observations yet"

    latest = max(r["observed_at"] for r in rows)
    models, orgs = {}, {}
    for r in rows:
        if r["observed_at"] != latest:
            continue
        pid = r["entity_id"].removeprefix("paper:arxiv:")
        (models if r["metric"] == "models_implementing" else orgs)[pid] = int(r["value"])
    if not orgs:
        return "papers-in-production.svg skipped: re-run derive, orgs_implementing is missing"

    titles = {}
    cache = root / "examples" / "paper-titles.json"
    if cache.exists():
        titles = json.loads(cache.read_text(encoding="utf-8"))

    # 1910.09700 is the carbon-emissions field of Hugging Face's model-card template,
    # not an implementation of anything. It reaches 12 publishers on boilerplate alone
    # and, left in, it sets the y-scale and empties the plot. Named and excluded rather
    # than quietly clipped.
    BOILERPLATE = {"1910.09700", "2205.05198"}
    excluded = [(models[p], orgs.get(p, 1), p) for p in BOILERPLATE if p in models]
    pts = [(m, orgs.get(pid, 1), pid) for pid, m in models.items()
           if m > 0 and pid not in BOILERPLATE]
    width, height = 980.0, 512.0
    left, right, top_pad, bottom = 70.0, 268.0, 96.0, 128.0
    plot_w, plot_h = width - left - right, height - top_pad - bottom
    max_m = max(m for m, _, _ in pts)
    max_o = max(o for _, o, _ in pts)
    sx = lambda m: left + math.log10(m) / math.log10(max_m) * plot_w
    sy = lambda o: top_pad + plot_h - (o - 1) / max(1, max_o - 1) * plot_h

    body = [chart_header(width, "House technique, or standard?",
                         "Each of %d papers by how many models cite it and how many distinct "
                         "publishers do. Log x." % len(pts))]
    for o in range(1, max_o + 1):
        y = sy(o)
        body.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w:.1f}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        body.append(svg_text(left - 10, y + 4, str(o), size=11, fill=MUTED, anchor="end", tabular=True))
    for m in (1, 3, 10, 30, 100, 300):
        if m > max_m:
            continue
        x = sx(m)
        body.append(f'<line x1="{x:.1f}" y1="{top_pad}" x2="{x:.1f}" y2="{top_pad + plot_h:.1f}" stroke="{GRID}" stroke-width="1"/>')
        body.append(svg_text(x, top_pad + plot_h + 20, str(m), size=11, fill=MUTED, anchor="middle", tabular=True))
    body.append(svg_text(left + plot_w / 2, top_pad + plot_h + 44, "models citing the paper", size=12, fill=INK2, anchor="middle"))
    body.append(svg_text(left - 10, top_pad - 14, "distinct publishers", size=12, fill=INK2, anchor="start"))

    # Label the extremes of each story, never the middle: the corners are the claim.
    house = sorted((p for p in pts if p[1] == 1), key=lambda p: -p[0])[:4]
    standard = sorted(pts, key=lambda p: (-p[1], p[0]))[:5]
    named = {p[2] for p in house + standard}
    for m, o, pid in sorted(pts, key=lambda p: p[2]):
        x, y = sx(m), sy(o)
        hot = pid in named
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5.0 if hot else 3.2}" '
            f'fill="{SERIES[1] if o == 1 else SERIES[0]}" fill-opacity="{0.9 if hot else 0.32}" '
            f'{"stroke=\"" + SURFACE + "\" stroke-width=\"1.5\"" if hot else ""}/>')
    placed = []
    for m, o, pid in sorted(house + standard, key=lambda p: (-p[1], -p[0])):
        x, y = sx(m), sy(o)
        # Dodge away from the nearer edge: a stack starting at the plot floor would
        # otherwise walk straight down through the footnote rule.
        step = -15 if y > top_pad + plot_h * 0.6 else 15
        ly = y
        while any(abs(ly - q) < 15 for q in placed):
            ly += step
        placed.append(ly)
        label = truncate(titles.get(pid, pid).split(":")[0], right - 86, 11)
        body.append(f'<line x1="{x + 6:.1f}" y1="{y:.1f}" x2="{left + plot_w + 12:.1f}" y2="{ly:.1f}" stroke="{BASELINE}" stroke-width="0.8"/>')
        body.append(svg_text(left + plot_w + 16, ly + 3.5, f"{label}  {m}m/{o}o", size=11, fill=INK2))

    n_house = sum(1 for _, o, _ in pts if o == 1)
    body.append(f'<line x1="24" y1="{height - 46:.1f}" x2="{width - 24:.1f}" y2="{height - 46:.1f}" stroke="{GRID}" stroke-width="1"/>')
    body.append(svg_text(24, height - 28,
                         "%d of %d papers (%.0f%%) are cited by exactly one publisher — their own author. "
                         "A ranking by model count alone hides that entirely." % (n_house, len(pts), 100 * n_house / len(pts)),
                         size=11, fill=INK2))
    if excluded:
        m0, o0, p0 = excluded[0]
        body.append(svg_text(24, height - 12,
                             "Excluded: %s on %d publishers — the carbon-emissions field of the model-card "
                             "template, and it would set the y-scale on its own." % (p0, o0),
                             size=11, fill=MUTED))
    out.write_text(wrap_svg(width, height, "House technique or standard",
                            "Models citing each paper against distinct publishers citing it.",
                            "\n".join(body)), encoding="utf-8")
    return f"wrote {out.relative_to(REPO)}"


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
