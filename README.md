<div align="center">

![Status](https://img.shields.io/badge/Status-Active_Development-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=flat-square&logo=openai&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-llama--3.1-F55036?style=flat-square)
![Ollama](https://img.shields.io/badge/Ollama-Local-black?style=flat-square)
![Adzuna](https://img.shields.io/badge/Adzuna-Germany-0055A4?style=flat-square)
![Arbeitnow](https://img.shields.io/badge/Arbeitnow-Germany-E63946?style=flat-square)
![Bundesagentur](https://img.shields.io/badge/Bundesagentur-Germany-003082?style=flat-square)

# JobsFitAI

### Stop applying blind. Know your fit before you apply.

*Built for job seekers in Germany.*
*Upload your resume, paste a job description, and get a precise AI-powered match score*
*with keyword gaps, section breakdown, and live job listings from three German job boards.*

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/harmandeep/)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/harmandeep2993)

</div>

---

## Why I Built This

The job search process is opaque for candidates. Companies run resumes through automated filters
and candidates have no visibility into what those filters are looking for. You apply, you wait,
you hear nothing, and you have no idea why.

I needed a tool that would look at any job description and tell me exactly how well my profile
matches it, which keywords I am missing, and whether it is even worth tailoring my resume for
that role. Not a generic score. A specific analysis against a specific job every time.

So I built it. The core works and I use it for every role I consider applying to.

---

## What It Does

**Resume Analyser** - Upload a PDF or DOCX resume and paste any job description. The AI
pipeline extracts structured data from both, runs a weighted scoring engine across six dimensions,
and returns a 0-100 match score with a full breakdown, keyword gap list, and actionable
recommendations.

**Live Job Fetcher** - Pulls fresh listings from Adzuna Germany, Arbeitnow, and the
Bundesagentur fur Arbeit (up to 200 per search title with pagination), scores each against
your loaded resume, and presents them ranked by match score. Supports scheduled auto-runs.

**ATS Check** - Scans your resume for structural issues that confuse Applicant Tracking Systems:
missing sections, formatting problems, and keyword coverage against a job description.

**Resume Vault** - Store up to 3 resume versions (base + tailored). Switch between them
instantly when scoring a new job. The system remembers which version you used for each analysis.

**Multi-provider LLM** - Works with OpenAI GPT-4o, Groq (fast, free tier), or a local Ollama
model. Switch providers from the Settings tab. Falls back automatically if the primary provider
fails.

---

## Score Labels

| Score | Label |
|-------|-------|
| 80 and above | Excellent Match |
| 60 to 79 | Good Match |
| 40 to 59 | Partial Match |
| Below 40 | Poor Match |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI + Uvicorn |
| Database | SQLite (local) or Turso (cloud) |
| Frontend | React 18 + Vite + Tailwind CSS |
| Animations | Framer Motion |
| PDF / DOCX parsing | pdfplumber, PyMuPDF, python-docx |
| LLM extraction | OpenAI GPT-4o / Groq / Ollama |
| Semantic dedup | sentence-transformers + ChromaDB |
| Job sources | Adzuna Germany, Arbeitnow, Bundesagentur fur Arbeit |
| Auth | JWT (HS256) via python-jose + bcrypt |

---

## Project Structure

```
JobsFitAI/
  backend/
    main.py                    FastAPI entry point, routers, scheduler
    config.yaml                LLM providers, matcher weights, job search settings
    api/routes/                One file per feature group (auth, resumes, analyzer, matches, ats)
    core/                      Config, database, security, logger, state
    models/                    User model (DB queries for the users table)
    repositories/              Data access layer for all other tables
    schemas/                   Pydantic request/response shapes
    services/
      ats.py                   ATS check and optimise logic
      job_matcher.py           Fetch + score pipeline orchestration
      job_relevance.py         LLM batch relevance gate
      fetchers/                Adzuna, Arbeitnow, Bundesagentur fetchers
      extractors/              LLM-based resume and JD extraction
      llm/                     call_llm() router + provider implementations
      matcher/                 Scoring engine (engine.py + per-section scorers)
      parsers/                 PDF / DOCX text extraction
      prompts/                 LLM prompt builders + JSON schemas

  frontend/
    src/
      pages/                   Landing, Login, About, Pricing, Privacy
      components/tabs/         Analyzer, ATS, JobMatches, Resumes, History, Settings
      components/              ResumePicker, TopBar, Sidebar, Toast, ui
      layouts/AppShell.jsx     Main app shell (sidebar + content)
      lib/auth.js              apiFetch() - attaches Bearer token to every API call
      App.jsx                  React Router config
      index.css                Design tokens + global styles
```

---

## Running Locally

**Backend**

```bash
cd backend
uv run uvicorn main:app --reload --port 8080
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` for the React app, or `http://localhost:8080` to hit the API directly.

**Environment variables** - copy `.env.example` to `backend/.env` and fill in your keys:

```
JWT_SECRET=your-long-random-secret
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk-...
ADZUNA_APP_ID=your-app-id
ADZUNA_APP_KEY=your-app-key
```

For fully local usage with no cloud API keys, install [Ollama](https://ollama.com) and set
the provider to `ollama` in the Settings tab.

---

## API Endpoints (summary)

| Group | Endpoints |
|-------|-----------|
| Auth | POST /api/auth/register, /login, GET /me |
| Resumes | GET/POST/DELETE /api/resumes, /api/resumes/{id}/file, /label, /use-for-matching |
| Analyzer | POST /api/upload, /resume-preview, /analyze |
| Job Matches | GET /api/match/run, /state, /export; POST /applied, /filters, /scheduler, /clear |
| ATS | POST /api/ats/check, /optimise |
| History | GET /api/history |
| LLM Settings | GET/POST /api/llm-settings, GET /api/llm-ping |

---

## Current Status

Core pipeline works end to end: resume parsing, LLM extraction, semantic scoring, keyword
gap analysis, ATS check, and live job fetching from three German job boards.

The React frontend is live with full auth, resume vault, analyzer, ATS check, job matches,
history, and settings tabs.

**In progress:** Pro plan billing, AI-powered ATS optimise, resume improvement suggestions.

---

## Connect

Built by Harman. Open to feedback, ideas, and conversations about making the job search
less of a black box.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat&logo=linkedin)](https://linkedin.com/in/harmandeep)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=flat&logo=github)](https://github.com/harmandeep2993)

---

## License

MIT License. See LICENSE file.
