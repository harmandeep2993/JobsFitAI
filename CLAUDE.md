# CLAUDE.md — JobsFitAI

## Project overview

JobsFitAI is a local-first resume-to-job-description analyser. Users upload a resume, paste a job description, and get an AI-generated match score with breakdown, keyword analysis, and recommendations. A second tab fetches live job listings (via Adzuna + Arbeitnow) and scores each against the loaded resume. A history tab tracks past analyses, fetcher runs, and job applications.

Stack: **FastAPI + Uvicorn** backend, **server-rendered HTML** injected via `fetch()`, vanilla JS frontend, SQLite via a custom store layer.

---

## Running the app

```bash
uv run uvicorn app:app --reload --port 8000
```

Open `http://localhost:8000`. The single-page app is served from `templates/index.html`.

---

## Key files

| Path | Role |
|------|------|
| `app.py` | FastAPI entry point — all REST routes (`/api/*`), background scheduler, startup tasks |
| `templates/index.html` | Single HTML shell; views switched by JS |
| `src/frontend/results.py` | Builds all analysis result HTML server-side |
| `src/frontend/components.py` | Shared HTML helpers (`safe_html`, `make_tags`, `prog_grad`, `score_col`) |
| `src/services/summary.py` | LLM summary — returns JSON `{profile, strengths, gaps, focus}` |
| `src/services/resume_store.py` | Disk + SQLite resume storage under `resumes/` |
| `src/services/match_store.py` | SQLite store for job match results |
| `src/services/analysis_store.py` | SQLite store for per-resume analysis history (deduplicates by resume+JD) |
| `src/services/event_store.py` | Event log: seen jobs, scored events, applied events, fetcher run events |
| `src/services/settings_store.py` | User settings: target titles, countries, location, scheduler on/off/interval |
| `src/services/job_matcher.py` | Main job-match pipeline: `fetch_combined`, `discover_and_score`, `rescore_all` |
| `src/services/relevance.py` | LLM batch relevance gate — classifies jobs as relevant/entry-level |
| `src/services/vector_store.py` | Local embedding dedup — skips near-duplicate job postings |
| `src/services/db.py` | SQLite bootstrap — `init()` creates all tables, `connect()` context manager |
| `src/matcher/matcher.py` | Scoring engine — `match()` → `{overall_score, section_scores, matched_*, missing_*}` |
| `src/extractors/resume.py` | LLM extraction of structured data from resume text |
| `src/extractors/jd.py` | LLM extraction of structured data from a job description |
| `src/utils/router.py` | `call_llm()` — single entry point for all LLM calls; returns `LLMResult`, handles retry + Groq fallback |
| `src/utils/session.py` | In-memory resume + provider state for the job-match session |
| `src/utils/config.py` | Loads `config.yaml` — `SEARCH_PER_TITLE`, `MAX_AGE_DAYS`, provider defaults |
| `assets/css/theme.css` | CSS custom properties (all design tokens) |
| `assets/css/layout.css` | Sidebar, main scroll area, view containers |
| `assets/css/components.css` | All UI components: panels, job cards, modals, buttons, workspace, resume slots, history entries |
| `assets/css/results.css` | Analysis result panels: nb-card, tabs, breakdown, summary, keywords, export row |
| `assets/js/fetch.js` | View router: `showView()`, loads per-view JS on first visit |
| `assets/js/analysis.js` | Analyzer flow, `jfTab()`, breakdown toggles, ring animations, `copyResults()` |
| `assets/js/upload.js` | Analyzer upload zone (saves to store), JD counter, preview modal |
| `assets/js/resumes.js` | My Resumes view — upload, picker, rename, delete, preview |
| `assets/js/matches.js` | Job Matches tab — fetch, score, render job cards, detail modal |
| `assets/js/history.js` | History view — 3-tab: Analyser / Fetcher / Applications |
| `assets/js/settings.js` | LLM settings panel |
| `assets/js/toast.js` | Toast notification system |
| `assets/js/theme.js` | Dark/light mode toggle |
| `config.yaml` | LLM provider, matcher weights, job search settings |

---

## SQLite schema (`data/jobsfitai.db`)

| Table | Key columns | Purpose |
|-------|-------------|---------|
| `matches` | `id, score, label, status, applied, jd_json, section_scores` | Scored job results from fetcher |
| `resume` | `id=1, name, json` | Single-row in-memory resume for job matching (singleton) |
| `seen_jobs` | `id, source, decision` | Every job id ever encountered — prevents re-fetching |
| `events` | `type, job_id, detail, created_at` | Timeline: `run`, `scored`, `applied`, `rescore`, `irrelevant`, `not_entry`, `stale` |
| `settings` | `key, value` | User settings (key-value): titles, countries, location, scheduler |
| `resumes` | `id, user_id, slot, label, original_name, file_path, mime_type, extracted_json` | Persistent resume files (up to 3 slots) |
| `analyses` | `id, resume_id, jd_snippet, score, label, scored_at` | Per-resume analysis history; deduped on `(resume_id, jd_snippet)` — repeated runs update, not insert |

`events.detail` for `type='run'` is a JSON blob: `{fetched, new, recent, relevant, scored, adzuna, arbeitnow, total_seen}`.

---

## All API endpoints

### Resume storage

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/resumes/upload` | Upload to a slot (form: `file`, `slot`); extracts JSON in background |
| `GET` | `/api/resumes` | List all stored resumes with last-analysis info |
| `DELETE` | `/api/resumes/{id}` | Delete file + record |
| `GET` | `/api/resumes/{id}/file` | Serve raw file (for preview) |
| `POST` | `/api/resumes/{id}/label` | Rename display label |
| `POST` | `/api/resumes/{id}/use-for-matching` | Load extracted JSON into job-match session + rescore all stored jobs |
| `POST` | `/api/resumes/recommend` | Score all cached resumes against a JD; returns ranked list + `recommended_id` |

### Analyzer

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/upload` | Legacy temp upload — returns `{ok, tmp, name, kb, ext}` |
| `POST` | `/api/resume-preview` | Extract text from stored or temp file — no LLM |
| `GET` | `/api/resume-file` | Serve a temp-path file for preview |
| `POST` | `/api/analyze` | Full pipeline: extract → match → summarize → render HTML; saves to analysis history |

### Job Matches

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/match/resume` | Parse temp resume + load into session for matching |
| `GET` | `/api/match/run` | Trigger background fetch + score run |
| `GET` | `/api/match/state` | Full state snapshot: resume, results, filters, scheduler, run status |
| `POST` | `/api/match/applied` | Toggle applied flag on a job |
| `GET` | `/api/match/detail` | Job detail + lazy-generated summary |
| `POST` | `/api/match/filters` | Set target titles / countries / location |
| `POST` | `/api/match/score-jd` | Manually score a `jd_unavailable` job with pasted text |
| `POST` | `/api/match/scheduler` | Enable/disable scheduler or change interval |
| `POST` | `/api/match/delete` | Delete a job + block its id from re-appearing |
| `POST` | `/api/match/clear` | Wipe all matches, events, vector store |
| `GET` | `/api/match/export` | Download all scored matches as CSV |

### History + LLM

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/history` | All history: `analyses`, `fetcher_runs`, `applications` (100 each) |
| `GET` | `/api/llm-ping` | Check whether the active LLM provider is reachable |
| `GET` | `/api/llm-settings` | Get active provider + model + full catalog |
| `POST` | `/api/llm-settings` | Set active provider + model |

---

## Architecture — analyzer results flow

```
POST /api/analyze
  → extract_all_text(path)  → resume_text
  → extract_all(text, jd)   → resume_json, jd_json  (two parallel LLM calls)
  → match()                 → results  {overall_score, section_scores, matched_*, missing_*}
  → generate_summary()      → summary  (JSON string: {profile, strengths, gaps, focus})
  → build_results_html()    → HTML string
  → analysis_store.save()   → upsert analyses table (non-fatal if it fails)
  ← {ok, html, score, label}

JS injects html into #jf-results, calls animateResRing() + animateBdRings()
Results cached in localStorage keyed on (resume_id or fingerprint + JD text).
```

Accepts either `{resume_id, jd}` (persistent store) or `{tmp, jd}` (legacy temp path).

`build_results_html` is wrapped in its own `try/except` — if it raises, the server returns `{"ok": false, "error": "results_render_failed"}` and logs the full traceback. `analysis_store.save()` is also wrapped and non-fatal.

---

## Architecture — job fetch + score flow

```
GET /api/match/run  (fires background task)
  → fetch_combined(titles, location, countries)
      → fetch_adzuna_multi()  (per country)
      → fetch_arbeitnow_jobs() + role_filter.is_target_role()  (DE only)
      → merge + dedup by id + content key
  → discover_and_score(jobs)
      → skip seen_jobs  (free, DB lookup)
      → role_filter.is_recent()  (free, date check)
      → relevance.classify_batch()  (1-2 LLM calls for the whole batch)
      → vector_store.is_duplicate()  (free, local embeddings)
      → enrich thin Adzuna snippets via scrape
      → extract_jd() + match()  (1 LLM call per job)
      → match_store.upsert(), event_store.mark_seen()
  → event_store.log_event("run", detail=JSON)
```

---

## LLM router (`src/utils/router.py`)

All LLM calls go through `call_llm(prompt)` — never import provider SDKs elsewhere.

### Return type

`call_llm()` returns `LLMResult | None`:

```python
@dataclass
class LLMResult:
    text:          str | None   # response text; None when all providers failed
    provider_used: str          # "openai" | "groq" | "ollama" | "none"
    attempts:      int          # total provider.call() invocations across all retries
    degraded:      bool         # True when fell back to Groq OR text is None
```

Callers extract text with: `_res = call_llm(prompt); response = _res.text if (_res and _res.text) else None`

### Retry and fallback

1. Trim prompt so `prompt_tokens + LLM_MAX_OUTPUT_TOKENS <= 5800` (4 chars/token, truncates from the END)
2. Try primary provider up to 4 attempts - backoff 1s / 2s / 4s / 8s + random jitter
3. If primary exhausts retries: Groq (`llama-3.1-8b-instant`) fallback with the same retry logic
4. If Groq also fails: return `LLMResult(text=None, degraded=True)`, never raise an exception

Groq fallback is skipped when the primary IS Groq. `degraded=True` signals the answer came from the fallback or failed entirely.

### 6000-token ceiling

Hard limit: prompt + response combined must not exceed 6000 tokens. The router enforces `_MAX_TOTAL = 5800` (200-token safety margin). Oversized prompts are truncated before any provider call - the instruction at the top is always preserved since truncation happens from the END.

---

## Background scheduler

`_auto_fetch_loop()` runs every 30 seconds and checks whether the configured interval has elapsed. On startup it seeds `_sched_last` from the last `events.type='run'` timestamp so server restarts don't immediately re-trigger a run.

`_backfill_extractions()` runs once on startup — extracts resume JSON for any stored resumes that were uploaded before the extraction cache was added.

---

## Resume storage

Files live at `resumes/<user_id>/<uuid>.<ext>` (gitignored). Records in SQLite `resumes` table.

Up to 3 slots per user:
- Slot 0 — Base Resume (complete, all experience)
- Slot 1 — Tailored Resume 1
- Slot 2 — Tailored Resume 2

`user_id` defaults to `'local'` — schema is multi-user ready; swap in auth and the rest is unchanged.

When a resume is uploaded, JSON extraction runs in a background task and is cached in `resumes.extracted_json`. This cache powers:
- `/api/resumes/recommend` — score all resumes against a JD with 1 LLM call
- `/api/resumes/{id}/use-for-matching` — load a resume into the job-match session
- `list_all()` returns `last_score, last_label, last_jd, last_analysed_at` via LEFT JOIN on `analyses`

---

## Frontend views and JS

### Views (sidebar nav)

| View | JS file | Load trigger |
|------|---------|-------------|
| Analyzer | `analysis.js`, `upload.js` | default on load |
| My Resumes | `resumes.js` | `showView('resumes')` |
| Job Matches | `matches.js` | `showView('matches')` |
| History | `history.js` | `showView('history')` → calls `loadHistory()` |
| Settings | `settings.js` | `showView('settings')` |

### analysis.js

- `startAnalysis()` — sends `{resume_id, jd}` or `{tmp, jd}`, injects `d.html` into `#jf-results`
- `jfTab(el, panelId)` — switches Summary / Breakdown / Keywords / Recommendations tabs
- `bdToggle(item)` — open/close a breakdown accordion row
- `bdToggleAll(btn)` — expand or collapse all breakdown rows
- `animateBdRings()` — animates all `.jt-gauge-arc[data-offset]` inside `#jf-summary` and `#jf-breakdown`
- `animateResRing()` — animates the overall score ring
- `copyResults()` — extracts text from DOM and writes to clipboard

### upload.js

- `handleFileSelect(file)` — POSTs to `/api/resumes/upload` (slot 0) and calls `rvSelect(id, name)`; if no resumes exist shows drag-drop zone, otherwise shows picker
- `checkJD(val)` — validates JD length, enables Analyse button
- `previewResume()` — shows PDF in iframe or DOCX as extracted text via `/api/resume-preview`

### resumes.js

- `rvLoad()` — fetches list, renders slot cards + analyzer picker; shows `az-rv-card-hist` with last score + JD snippet when `last_score != null`
- `rvSelect(id, name)` — sets `window._resumeId`, highlights card, auto-advances step, fires `/api/resumes/{id}/use-for-matching` fire-and-forget
- `rvUpload(file, slot)` — POSTs to `/api/resumes/upload`, refreshes, auto-selects
- `rvEditLabel(id)` — inline rename: Enter saves, Escape cancels
- `rvPreview(id, filename)` — PDF in iframe (`/api/resumes/{id}/file`), DOCX as text
- `rvDelete(id)` — deletes, clears `window._resumeId` if it was selected

### matches.js

- `matchCardHTML(job)` — renders `.job-thumb` card with score ring, tags, apply button
- `animateScores()` — animates all gauge arcs in job cards
- `showDetail(id)` — fetches `/api/match/detail` and renders slide-in panel
- Polls `/api/match/state` while a run is active

### history.js

`window.loadHistory = window.hvLoad = function()` — dual alias; `fetch.js` calls `loadHistory()` when switching to the history view.

Three panels rendered from `/api/history`:

- `_hvRenderAnalyser(entries)` — blue search icon, JD snippet title, slot badge + resume label, score tier badge
- `_hvRenderFetcher(entries)` — stats bar (total runs / fetched / scored / last run), scored runs visible by default, zero-result runs behind toggle via `hvToggleZeroRuns(btn)`
- `_hvRenderApplications(entries)` — green checkbox icon, title/company, applied time, link, score

`_hvParseFetchDetail(raw)` — JSON.parse first, fallback regex for old plain-text format.

---

## Input workspace layout

```
.az-workspace  (grid: 2fr 3fr, gap 14px)
  .az-panel.az-panel-resume
    .az-panel-hd              ← "01" badge + "Resume" title + "Manage" link
    #az-resume-picker         ← .az-rv-picker cards (shown when resumes exist)
    #up-zone                  ← drag-drop zone (shown when no resumes stored)
  .az-panel.az-panel-jd
    .az-panel-hd              ← "02" badge + "Job Description" title + char counter
    .jd-box                   ← textarea; placeholder centered via padding-top
```

When stored resumes exist the upload zone is hidden and replaced by `.az-rv-picker`. Selecting a card sets `window._resumeId`. "Upload another" button at the bottom triggers `rvPickFile()`. If no resumes exist the standard drag-drop zone is shown; dropping saves to slot 0 via `/api/resumes/upload`.

---

## CSS design tokens (theme.css)

Always use these — never hardcode colours or sizes.

| Token | Use |
|-------|-----|
| `--bg`, `--bg-r`, `--bg-c` | Page / raised / card backgrounds |
| `--bd`, `--bd-s` | Border / subtle border |
| `--t1`, `--t2`, `--t3` | Text: primary / secondary / muted |
| `--accent`, `--accent-s`, `--accent-xl` | Brand orange, focus ring, pale tint |
| `--green`, `--green-bg`, `--green-bd` | Success / matched |
| `--blue`, `--blue-bg`, `--blue-bd` | Info / good match |
| `--amber`, `--amber-bg`, `--amber-bd` | Warning / partial |
| `--red`, `--red-bg`, `--red-bd` | Error / missing / gap |
| `--radius`, `--radius-s` | Card / small border-radius |
| `--sha-s`, `--sha-lg` | Card shadow / modal shadow |

Tier CSS classes: `sc-exc` (>=80) · `sc-good` (>=60) · `sc-partial` (>=40) · `sc-poor` (<40)

---

## Results HTML structure

```
#jf-results
  .res-section
    .nb-card                          ← unified card: border + shadow + overflow:hidden
      .tab-row#jf-tab-row             ← gray (--bg-r) strip; active tab is white, no bottom border
      #jf-summary.jf-panel            ← 3-col grid: .sum-hero | .sum-sec--profile | .sum-sec--strengths
      #jf-breakdown.jf-panel          ← .bd-panel-hd + .bd-list accordion
      #jf-keywords.jf-panel           ← .kw-card coverage bar + tag sections
      #jf-reco.jf-panel               ← recommendation action cards
    .callout
    .res-export-row                   ← foot-note (score · label · model) + Copy + Print buttons
```

### Notebook tab design

Active tab and panel are one unified white surface — no dividing line:
- `.nb-card .tab-row` — gray background (`--bg-r`), `border-bottom: none`
- `.nb-card .tab-item.active` — white (`--bg`), no border, flows into panel below
- `.nb-card .jf-panel` — white (`--bg`), `padding: 20px`
- Tab switching via `jfTab(el, panelId)` in `analysis.js`

### Summary panel (3-column grid)

`_render_summary_panel()` in `results.py`:
- Column 1 — `.sum-hero`: 72px gauge ring + tier-coloured pill + pct text
- Column 2 — `.sum-sec.sum-sec--profile`: "Your Profile" bullets, blue header bar
- Column 3 — `.sum-sec.sum-sec--strengths`: "Strengths" bullets, green header bar

`generate_summary()` returns JSON `{"profile":[...],"strengths":[...],"gaps":[...],"focus":[...]}`. Falls back to `_fallback_summary()` if parse fails.

### Breakdown accordion

Each `.bd-item` has `data-open="false"`. Click `.bd-item-hd` calls `bdToggle(item)` — CSS shows `.bd-item-detail` and rotates `.bd-chevron` via attribute selector. `bdToggleAll(btn)` expands/collapses all.

### Gauge rings

- **Job cards**: animated by `animateScores()` in `matches.js`
- **Summary hero + breakdown**: animated by `animateBdRings()` in `analysis.js`
- Selector: `#jf-summary .jt-gauge-arc[data-offset], #jf-breakdown .jt-gauge-arc[data-offset]`
- Circumference = 106.81 (r=17); summary hero overrides ring to 72px

---

## History view HTML structure

```
#view-history
  .hv-card
    .hv-tab-row#hv-tab-row      ← Analyser | Fetcher | Applications tabs
    #hv-analyser.hv-panel       ← list of .hv-entry rows
    #hv-fetcher.hv-panel        ← .hv-stats-bar + scored runs + zero-run toggle
    #hv-applications.hv-panel   ← list of .hv-entry rows
```

`.hv-stats-bar` shows: total runs · fetched · scored · total seen · last run timestamp.
Fetcher entries with `scored=0` are hidden behind a "Show N zero-result runs" toggle.

---

## Job card thumbnail pattern

The `.job-thumb` card in Job Matches is the canonical design unit. Mirror its structure for new list-style UI:

```
.job-thumb / .bd-item
  |- .jt-body / .bd-item-hd  ← title left, gauge ring right
  |- [progress bar]
  |- [tags / detail content]
  `- .jt-foot / .bd-foot     ← bg-c strip, border-top
```

---

## Commit rules

- **Never** add `Co-Authored-By: Claude` trailers to commits
- **Never** use em-dashes or en-dashes in commit messages - plain hyphens only
- Keep commit messages concise; focus on the "why" not the "what"
