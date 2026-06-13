# JobFitAI - Agent Execution Plan

This is the plan the JobFitAI agent works through, one step at a time. It is
designed to be picked up across many sessions. Read this whole file at the
start of every session before doing anything.

Local-first throughout. No cloud accounts. Every change maps to the existing
FastAPI + SQLite + call_llm() architecture and the file layout in CLAUDE.md.

---

## How to work through this plan (read first, every session)

### Token-budget rule (most important)

You have a finite context window per session. Before starting EACH step:

1. Estimate the remaining context budget. A rough proxy: how much of the
   window is already consumed by files read, diffs, and conversation so far.
2. Decide using this rule:
   - If there is clearly enough budget to OPEN, IMPLEMENT, and VERIFY the next
     step in full, start it.
   - If budget is tight - meaning you could not finish the next step cleanly -
     DO NOT start a new step. Instead, finish and stabilize the step currently
     in progress, commit it, update the Progress Log below, and stop.
3. NEVER leave a step half-implemented across a session boundary. A partial
   route, a broken import, or an untested change is worse than stopping early.
   "Finish the ongoing step, do not begin a new one" always wins over
   "make more progress".

A step is "finished" only when: the code runs, it is committed with a proper
message, and the Progress Log is updated. If you cannot reach all three for a
NEW step within the remaining budget, do not begin it.

### Per-step loop

For every step:
1. Read the relevant existing file(s) first - match their patterns.
2. Implement the smallest change that completes the step.
3. Verify (run it, or run the test if one exists).
4. Commit with a Conventional Commit message (the WHY, no em-dashes, no
   Co-Authored-By trailer).
5. Update the Progress Log at the bottom of this file: mark the step done,
   note anything the next session needs to know.

### Commit discipline (do not batch unrelated work)

- Commit EVERY feature or service the moment it is done and verified. One
  logical unit = one commit. Do not let multiple finished features pile up in
  a single commit.
- A feature/service is "done" only when it runs and is verified. Then commit
  it immediately, before starting anything else.
- If a step produces both a backend service and a separate frontend panel,
  that is two commits (e.g. feat(resume): improve-resume endpoint, then
  feat(ui): diff-style rewrite panel) - they are different units.
- Never leave finished, verified work uncommitted at a session boundary. The
  Progress Log update and the commit happen together.

### Branching workflow (avoid conflicts)

- main is always working and deployable. Never commit features directly to
  main.
- One feature branch per step, named by type and scope, e.g.
  feat/router-hardening, feat/vector-store, feat/match-batch,
  feat/resume-rewrite, feat/ats-optimizer.
- Before starting a step: git checkout main, git pull, then branch off main so
  every branch starts from the latest code. This is the main defense against
  conflicts.
- Keep branches small and short-lived - one step, merged quickly. Long-lived
  branches drift and cause conflicts.
- When a step is done and verified: merge the branch back into main (or open a
  PR if you prefer review), then delete the branch.
- Do not run two overlapping branches that touch the same files (e.g. two
  branches both editing results.py) at the same time. Finish and merge one
  before branching the next. Steps that share files must be sequential.
- If a merge conflict appears, resolve it on the feature branch by pulling main
  in first - never force-push over main.

### Code quality (every file you write or touch)

- Write clear comments explaining the WHY, not the obvious WHAT. The author is
  still learning the codebase and reads comments to understand intent. Comment
  any non-obvious logic: scoring math, token-budget trimming, retry/backoff
  conditions, vector payload structure.
- Keep code modular. Small, single-responsibility functions. New logic goes in
  the right layer (services in src/services/, scoring in matcher.py, HTML in
  results.py) - never a giant function or logic dumped into a route.
- Each route in app.py stays thin: validate input, call a service, return the
  result. Real work lives in services/matcher/extractors.
- Follow the patterns of the file you are editing. Do not introduce a second
  style for the same kind of thing.
- Remember the comment/style rules still apply: no em-dashes anywhere,
  including inside comments and docstrings.

### LLM provider and token-budget handling (Groq fallback)

Provider setup, configured in config.yaml and enforced in call_llm():
- Primary provider: the configured primary (NOT Groq).
- Fallback provider: Groq, model llama-3.1-8b-instant (128k context, very
  cheap). Used when the primary fails its retries, or when explicitly chosen
  for a cheap/bulk call.

HARD per-call limit: 6000 tokens total = prompt + response COMBINED, on any
single LLM call. This is a hard ceiling, not a target. Enforce it:
- Before any call, estimate prompt tokens. Reserve headroom for the response
  and cap max_tokens so that prompt_tokens + max_tokens stays under 6000
  (leave a small safety margin, e.g. target <= 5800).
- If a prompt plus its needed response would exceed 6000, do NOT send it whole.
  Trim or chunk the input (e.g. truncate JD/resume to the relevant sections,
  or split a batch into per-item calls) so each call fits.
- Prefer fewer, well-scoped calls over many tiny ones, but never exceed the
  6000 ceiling on a single call.
- Use Groq deliberately for cheap/bulk work (e.g. batch pre-scoring summaries),
  and reserve the primary for higher-quality single calls. Route both through
  call_llm() - never call Groq's SDK directly outside the router.

Implement this cap inside call_llm() in src/utils/router.py so every caller is
protected automatically. Round any token estimate up to be safe.

### Hard rules (apply to every step)

- All LLM calls go through call_llm() in src/utils/router.py - never a
  provider SDK directly elsewhere.
- Routes in app.py under /api/*. Result HTML in src/frontend/results.py.
  SQLite access through the store layer only.
- No hardcoded colors or sizes - use theme.css tokens. Score tiers:
  sc-exc >=80, sc-good >=60, sc-partial >=40, sc-poor <40.
- NEVER use em-dashes or en-dashes anywhere - plain hyphens only.
- Conventional Commits; no Co-Authored-By: Claude trailer; git status before
  committing.
- Output language matches the JD language (EN JD = EN, DE JD = DE).
- Job sources: Adzuna now, Arbeitnow later, Bundesagentur fur Arbeit last,
  all behind one fetch_jobs(source, query, n) interface.
- Do not skip ahead in the build order. Later steps depend on earlier ones.

---

## PART 1 - Production hardening (do first)

The advanced features lean on this foundation. Build it before any feature.

### Step 1.1 - Harden the LLM router (src/utils/router.py)

call_llm() is the single choke point, so hardening here protects everything.

- Wrap the provider call in retry-with-exponential-backoff. Retry on HTTP 429,
  500-503, and timeouts. Max 4 attempts; backoff 1s, 2s, 4s, 8s with jitter.
- Add a hard per-request timeout (e.g. 30s).
- Read a provider fallback chain from config.yaml: primary provider first,
  then Groq (llama-3.1-8b-instant) as the cheap fallback. On exhausting
  retries for the primary, fall through to Groq. If all fail, return a
  structured degraded response, never a raw exception.
- Enforce the 6000-token total ceiling (prompt + response) on every call here:
  estimate prompt tokens, cap max_tokens so the sum stays under ~5800, and
  trim/chunk oversized inputs before sending. This protects every caller.
- Return a typed result {text, provider_used, attempts, degraded} so callers
  can tell a real answer from a fallback.

Verify: simulate a 429/timeout and confirm it falls back to Groq, then to a
graceful degraded result if Groq also fails - not a 500. Confirm an
oversized prompt is trimmed/capped under 6000, not sent whole. Done when
committed and logged.

### Step 1.2 - Validate config.yaml on startup (Pydantic)

- Define a Settings Pydantic model mirroring config.yaml (LLM provider block,
  matcher weights, job search settings).
- Validate matcher weights are present and sum to the expected total.
- Load and validate once at startup in app.py; on failure log the exact field
  and exit non-zero.

Verify: introduce a bad weight, confirm a clear boot-time failure.

### Step 1.3 - Input validation and limits

- /api/resumes/upload: enforce allowed extensions (pdf, docx), max file size,
  reject empty files. Return structured error JSON.
- /api/analyze: cap JD length, reject empty JD, handle unparseable PDF/DOCX
  with a clear error rather than a throw.
- Add an error-panel render path in src/frontend/results.py in the existing
  card style.

Verify: upload a bad file and an oversized file, confirm clean error panels.

### Step 1.4 - Structured logging and a real /health

- Add logging (stdlib or structlog) with a per-request ID middleware in
  app.py. Log route, duration, provider used, degraded flag.
- Expand /health to actually check: SQLite opens, config loaded, LLM provider
  reachable. Return per-component status, not just {ok: true}.

Verify: hit /health with the DB path broken, confirm it reports the failure.

### Step 1.5 - Server-side result cache

- New table analysis_cache (hash TEXT PRIMARY KEY, result_json TEXT,
  created_at).
- Cache key = content hash of (resume_id or fingerprint + normalized JD text).
- /api/analyze checks cache first, stores on miss. Keep localStorage as a fast
  client layer but treat SQLite as source of truth.

Verify: analyze the same resume+JD twice, confirm the second is a cache hit.

---

## PART 2A - Vector store (Qdrant, local)

Build first among the features. Everything else gets cheaper once vectors
exist.

### Step 2A.1 - Run Qdrant locally

- Add Qdrant via Docker (qdrant/qdrant), port 6333, local mode only.
- Add connection settings to config.yaml (host, port, collection names).
- Document the docker run/compose command in CLAUDE.md.

Verify: container up, client connects.

### Step 2A.2 - Embedding layer

- New module src/services/embeddings.py wrapping
  paraphrase-multilingual-MiniLM-L12-v2, exposing embed(text) and
  embed_batch(texts).
- Two collections: resumes and jobs, vector size 384 (MiniLM-L12).
- SQLite stays source of truth; Qdrant points carry the SQLite id in payload.

Verify: embed a sample, confirm vector length and an upsert/read round-trip.

### Step 2A.3 - Index on write

- On resume save (resume_store.py): embed and upsert into resumes.
- On job fetch/score: embed the JD and upsert into jobs.
- Backfill script to embed existing stored resumes and matches once.

Verify: run backfill, confirm Qdrant point counts match SQLite row counts.

### Step 2A.4 - Semantic search endpoints

- GET /api/jobs/similar?job_id=... - stored jobs nearest a given job's vector.
- POST /api/jobs/search with free text - embed query, return nearest jobs.

Verify: search returns ranked, sensible neighbors.

---

## PART 2B - Ranked batch scoring (Adzuna only at first)

Sits on the vector layer.

### Step 2B.1 - Batch fetch and score

- New route POST /api/match-batch - accepts {resume_id, query, n}.
- Fetch N jobs from Adzuna, embed each JD, score by vector similarity against
  the resume vector (cheap, no LLM).
- Sort by similarity. Run the full LLM breakdown only on the top K (e.g. 5).
- Use Groq (the cheap fallback) for any bulk/per-item LLM summaries here, since
  batch work is exactly the cheap-and-many case. Keep each call under the 6000
  token ceiling - score one job per call, trimming the JD to relevant sections
  rather than sending all N at once.
- Persist all batch results in match_store.py.

Verify: batch of N returns a sorted list; only top K have full breakdowns.

### Step 2B.2 - Leaderboard view (frontend)

- New view reusing the .job-thumb card pattern with animated score rings.
- Sort controls (by score, by date) in JS, no server round-trip.
- Each card links to the full analysis for that job.

Verify: cards render, sort works client-side, rings animate.

---

## PART 2C - Resume rewrite / improve engine (NEW TAB)

Reuses generate_summary() gap data. The missing "act" half of the loop.
This is a NEW, separate feature with its own tab in the results notebook -
not folded into the existing Summary/Breakdown/Keywords panels.

Linking into existing features (build these connections, do not leave it
standalone):
- Reads the gaps and matched skills produced by the existing analyze flow
  (matcher.py + generate_summary()), so it only runs after an analysis exists.
- The existing Recommendations panel gets a "Rewrite to fix" action that opens
  this tab pre-loaded with the relevant gaps.
- The ATS tab (Part 2D) hands flagged items here via the same endpoint.

### Step 2C.1 - Improve endpoint (branch: feat/resume-rewrite)

- POST /api/improve-resume - accepts {resume_id, jd, gaps}.
- Prompt: rewrite content bullet by bullet, grounded in matched skills, so the
  LLM tightens real experience rather than inventing it. Output in the JD's
  language. Keep each call under the 6000 token ceiling (rewrite in small
  batches of bullets if needed, via call_llm()).
- Return structured before/after pairs.
- Commit when done and verified (feat(resume): improve-resume endpoint).

Verify: a real resume+JD returns grounded before/after bullets in the right
language.

### Step 2C.2 - Rewrite tab (frontend, same branch or feat/resume-rewrite-ui)

- New dedicated tab in the notebook .nb-card (alongside Summary, Breakdown,
  Keywords, Recommendations), switched via jfTab.
- Shows before/after bullets diff-style. Reuse tier colors: green for
  strengthened, amber for changed. "Copy improved bullet" per row.
- Wire the link from the Recommendations panel "Rewrite to fix" action.
- Commit separately (feat(ui): resume rewrite tab).

Verify: tab renders inside the notebook card, copy works, the link from
Recommendations opens it.

---

## PART 2D - ATS keyword optimizer (NEW TAB, build last)

Consumes the keyword and rewrite layers. This is a NEW, separate feature with
its own tab in the results notebook - not merged into the existing Keywords
panel.

Linking into existing features:
- Builds on the matched/missing keywords already computed in matcher.py.
- Its "Fix with rewrite" action hands flagged items to the Part 2C rewrite
  endpoint (/api/improve-resume), opening the Rewrite tab.
- Runs off the same analysis result as the other tabs (resume + JD already
  loaded).

### Step 2D.1 - ATS scoring pass (branch: feat/ats-optimizer)

- Extend matcher.py (already computes matched/missing keywords) to produce:
  exact-match coverage, keyword density, required-section presence, formatting
  flags that commonly break ATS parsers. Keep this modular - a separate
  ats_check() function, well commented, not piled into the existing match().
- New route POST /api/ats-check returning a structured report.
- Commit when done (feat(ats): ats coverage, density, and formatting checks).

Verify: report flags a deliberately ATS-hostile resume.

### Step 2D.2 - ATS tab (frontend, separate commit)

- New dedicated tab in the notebook .nb-card, switched via jfTab.
- Coverage bar (reuse the kw-card pattern), density warnings, missing-section
  flags. "Fix with rewrite" button calls /api/improve-resume and opens the
  Rewrite tab.
- Commit separately (feat(ui): ats tab with handoff to rewrite).

Verify: flags render, handoff button opens the rewrite tab with flagged items.

---

## LATER - Additional job sources

Do not block batch scoring on these. Each is a new adapter behind
fetch_jobs(source, query, n).

1. Arbeitnow - second fetcher behind the same interface.
2. Bundesagentur fur Arbeit - last. Public API
   (X-API-Key: jobboerse-jobsuche).

---

## Commit sequence reference

Each line is its own commit on its own feature branch (branch off latest main,
merge when done, delete the branch). Backend and UI are separate commits.

```
feat(router): add retry-backoff, groq fallback, 6k token cap
feat(config): validate config.yaml on startup with pydantic
feat(api): validate uploads and JD input, structured error panel
feat(obs): request-id logging and component health checks
feat(cache): move analysis cache server-side to sqlite
feat(vectors): add qdrant client and embeddings service
feat(vectors): index resumes and jobs on write, add backfill
feat(search): semantic similar-jobs and free-text search endpoints
feat(match): batch fetch, vector rank, top-k llm breakdown via groq
feat(ui): batch leaderboard view with sortable job cards
feat(resume): improve-resume endpoint with before/after rewrites
feat(ui): resume rewrite tab, linked from recommendations
feat(ats): ats coverage, density, and formatting checks
feat(ui): ats tab with handoff to rewrite
feat(sources): add arbeitnow fetcher behind job-fetch interface
```

---

## Progress Log

Update this at the end of every session. The next session reads it first.

| Step | Status | Notes for next session |
|------|--------|------------------------|
| 1.1  | done | LLMResult dataclass; primary + Groq fallback; 6k token cap; 6 call sites updated |
| 1.2  | not started | |
| 1.3  | not started | |
| 1.4  | not started | |
| 1.5  | not started | |
| 2A.1 | not started | |
| 2A.2 | not started | |
| 2A.3 | not started | |
| 2A.4 | not started | |
| 2B.1 | not started | |
| 2B.2 | not started | |
| 2C.1 | not started | |
| 2C.2 | not started | |
| 2D.1 | not started | |
| 2D.2 | not started | |

Legend: not started / in progress / done. If a step is "in progress" at
session end, the next session FINISHES it before reading ahead.
