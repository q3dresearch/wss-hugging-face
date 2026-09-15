# Data shape

*Generated 2026-09-15T13:15:02Z by `wss schema` from the derived rows. Do not hand-edit — regenerate after any derive.*

**You should not need to download anything to read this.**

- **342,414 observations** across 2 partition(s), in **11 series**
  - `hf.datasets.newest` — 22,011 rows, **7691 entities**
  - `hf.datasets.top-downloads` — 33,011 rows, **1100 entities**
  - `hf.datasets.top-likes` — 33,011 rows, **1007 entities**
  - `hf.datasets.trending` — 33,011 rows, **1961 entities**
  - `hf.models.newest` — 22,302 rows, **8193 entities**
  - `hf.models.text-generation` — 39,013 rows, **1065 entities**
  - `hf.models.top-downloads` — 43,470 rows, **1633 entities**
  - `hf.models.top-likes` — 33,484 rows, **1062 entities**
  - `hf.models.trending` — 34,222 rows, **1762 entities**
  - `hf.papers.daily` — 2,755 rows, **273 entities**
  - `hf.papers.daily.backfill` — 46,124 rows, **17532 entities**
- Raw: 979 file(s), 45,176,976 bytes on disk, 8 capture date(s), 2026-08-31 → 2026-09-13

## Sources

| source | cadence | endpoints | storage | personal data | licence |
| --- | --- | ---: | --- | --- | --- |
| `hf.datasets.newest` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.datasets.top-downloads` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.datasets.top-likes` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.datasets.trending` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.models.newest` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.models.text-generation` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.models.top-downloads` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.models.top-likes` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.models.trending` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.papers.daily.backfill` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |
| `hf.papers.daily` | weekly | 1 | git | none | Hub metadata via public API; see https://huggingface.co/term |

## Columns

```
series_id, entity_id, observed_at, captured_at, metric, value, unit, source_id, raw_ref, parser_version
```

`entity_id` looks like: **hf.datasets.newest** `00000N0/1`, `00000N0/2`, `00000N0/3`; **hf.datasets.top-downloads** `3dlg-hcvc/omages_ABO`, `86Cao/MegaPairs-Standard`, `ACCC1380/private-model`; **hf.datasets.top-likes** `0xDing/wikipedia-cn-20230720-filtered`, `5CD-AI/LLaVA-CoT-o1-Instruct`, `5CD-AI/Viet-Handwriting-OCR-v2`; **hf.datasets.trending** `0jl/SPair-71k`, `0xDing/wikipedia-cn-20230720-filtered`, `0xSero/local-ai-registry`; **hf.models.newest** `0-ASWIN-0/CyberGPT-Qwen3-4B`, `0001hmnt/Wan2.2_I2V_SockJob`, `0Corvid0/pi05-b1k-eval-checkpoints`; **hf.models.text-generation** `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF`, `0xSero/deepseek-v4-flash-0731-spark`, `AEON-7/Ornith-1.0-35B-AEON-Ultimate-Uncensored-BF16`; **hf.models.top-downloads** `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF`, `AEON-7/Ornith-1.0-35B-AEON-Ultimate-Uncensored-BF16`, `AEON-7/Qwen3.6-35B-A3B-heretic-NVFP4`; **hf.models.top-likes** `01-ai/Yi-34B`, `2Noise/ChatTTS`, `2vXpSwA7/iroiro-lora`; **hf.models.trending** `0bserverx/Qwen3.8-27B-Heretic-Abliterated-Uncensored-GGUF`, `0bserverx/RVN-Qwen3.8-Flash-Next-Abliterated-Uncensored`, `0bserverx/RVN-Qwen3.8-Flash-Next-Abliterated-Uncensored-GGUF`; **hf.papers.daily** `2504.15476`, `2608.05879`, `2608.09408`; **hf.papers.daily.backfill** `2211.16780`, `2302.06555`, `2304.09355`

## Metrics

| metric | series | rows | entities | type | unit | distinct | range / samples |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| `comments` | hf.papers.daily, hf.papers.daily.backfill | 18,633 | 17534 | number | count | 39 | `0` … `143` |
| `downloads_30d` | hf.datasets.newest, hf.datasets.top-downloads, hf.datasets.top-likes, hf.datasets.trending, hf.models.newest, hf.models.text-generation, hf.models.top-downloads, hf.models.top-likes, hf.models.trending | 101,000 | 22785 | number | count/30d | 28252 | `0` … `255143740` |
| `downloads_all_time` | hf.datasets.top-downloads, hf.datasets.top-likes, hf.models.text-generation, hf.models.top-downloads, hf.models.top-likes | 57,000 | 4432 | number | count | 28347 | `0` … `3804110121` |
| `entities_listed` | hf.datasets.newest, hf.datasets.top-downloads, hf.datasets.top-likes, hf.datasets.trending, hf.models.newest, hf.models.text-generation, hf.models.top-downloads, hf.models.top-likes, hf.models.trending | 101 | 1 | number | count | 1 | `1000` … `1000` |
| `github_stars` | hf.papers.daily, hf.papers.daily.backfill | 11,613 | 11059 | number | count | 1581 | `0` … `91991` |
| `likes` | hf.datasets.newest, hf.datasets.top-downloads, hf.datasets.top-likes, hf.datasets.trending, hf.models.newest, hf.models.text-generation, hf.models.top-downloads, hf.models.top-likes, hf.models.trending | 101,000 | 22785 | number | count | 2199 | `0` … `14516` |
| `models_implementing` | hf.models.top-downloads | 4,718 | 449 | number | count | 29 | `1` … `42` |
| `models_serving` | hf.models.newest, hf.models.top-downloads, hf.models.top-likes, hf.models.trending | 1,654 | 54 | number | count | 111 | `1` … `324` |
| `models_using` | hf.models.top-downloads, hf.models.trending | 1,344 | 114 | number | count | 61 | `1` … `637` |
| `orgs_implementing` | hf.models.top-downloads | 4,718 | 449 | number | count | 5 | `1` … `12` |
| `trending_score` | hf.datasets.trending, hf.models.trending | 22,000 | 3584 | number | score | 322 | `1` … `4293` |
| `upvotes` | hf.papers.daily, hf.papers.daily.backfill | 18,633 | 17534 | number | count | 318 | `0` … `779` |

## Partitions

- `derived/observations/2026-08.csv.gz`
- `derived/observations/2026-09.csv.gz`
