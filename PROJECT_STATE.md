# JobFitAI — Project State

A working reference for the current pipeline and the **reuse points** the
job-fetcher work builds on. Kept short and accurate; update it when the
public surface of a stage changes.

## Pipeline overview

```
file ──parsers──▶ raw text ──extractors──▶ structured JSON ──matcher──▶ score ──frontend──▶ UI
                                                  ▲
                                  fetchers ───────┘  (new: supply JD text without manual paste)
```

1. **parsers** — read PDF/DOCX/TXT into clean text (3-tier PDF fallback).
2. **extractors** — LLM turns text into schema-shaped dicts.
3. **matcher** — semantic scoring across 7 weighted sections.
4. **frontend** — NiceGUI app renders the result tabs.

## Reuse points

These are the stable entry points downstream code (including the fetcher
feature) should call rather than re-implementing.

### Extractors — `src/extractors`

| Symbol | Signature | Notes |
|---|---|---|
| `extract_all` | `(resume_text: str, jd_text: str) -> tuple[dict, dict]` | Runs both extractors; checks LLM availability first. Returns `({}, {})` if the provider is down or inputs are missing; partial failure yields one populated dict. |
| `extract_jd` | `(jd_text: str) -> dict` | JD-only path. Truncates to `JD_MAX_CHARS`, lowercases all string values. **A fetched `Job.description` plugs straight in here.** |
| `extract_resume` | `(resume_text: str) -> dict` | Resume-only path (in `extractors.resume`). |

### Matcher — `src/matcher`

| Symbol | Signature | Notes |
|---|---|---|
| `match` / `get_match_score` | `(resume: dict, jd: dict) -> dict` | Runs all 7 scorers, applies `WEIGHTS` from config, clamps 0–100. Returns `{}` on empty input. |
| `load_model` | `() -> SentenceTransformer` | Module-level singleton (in `matcher.embedding_model`). Multilingual model, loaded once and reused. |

`match` output shape:

```python
{
  "overall_score": 74.5,
  "label": "Good Match 🟡",
  "section_scores": { "required_skills": ..., "preferred_skills": ...,
                      "responsibilities": ..., "experience": ...,
                      "education": ..., "languages": ..., "certifications": ... },
  "matched_required": [...], "missing_required": [...],
  "matched_preferred": [...], "missing_preferred": [...],
}
```

### Infrastructure — `src/utils`

| Symbol | Notes |
|---|---|
| `get_logger(__name__)` | Loguru-backed logger. Every module uses this — fetchers included. |
| `load_config` / config constants | `WEIGHTS`, `JD_MAX_CHARS`, etc. sourced from `config.yaml`. |
| `router` (`call_llm`, `check_llm`, `parse_json_response`) | Provider-agnostic LLM access. Active provider set in `src/utils/router.py`. |

## Fetchers — current state

`src/fetchers/job_fetcher.py` (feature branch `feat/job-fetcher`):

- `fetch_adzuna_jobs(query, location, results, country="de") -> list[Job]`
- `Job` dataclass: `title, company, location, url, description, language`
- Descriptions are HTML-stripped; `language` is detected via `langdetect`.
- Returns `[]` on missing credentials or request failure (no raises).

**Not yet wired into the UI.** Next step: feed `Job.description` into
`extract_jd` so a fetched posting flows through the existing match pipeline
without manual paste.

## Provider state

Active provider is selected in `src/utils/router.py`; OpenAI, Groq, and
Ollama are functional. Gemini and HuggingFace are in progress (see README).
Keys load from `.env` (gitignored).
