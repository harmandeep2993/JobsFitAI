# src/frontend/handlers.py

import os
import asyncio
from pathlib import Path

# Per-step timeout budgets (seconds). Keeps the spinner from hanging forever
# if the LLM stalls, OCR loops, or the embedding model hangs on first load.
_T_PARSE    = 60   # PDF/DOCX text extraction
_T_EXTRACT  = 90   # LLM extraction (resume + JD, two calls)
_T_MATCH    = 60   # semantic scoring + embedding model load
_T_SUMMARY  = 60   # LLM summary generation

from nicegui import ui

from src.parsers import extract_all_text
from src.extractors import extract_all
from src.utils.router import check_llm
from src.matcher.matcher import match
from src.frontend.components import make_steps
from src.frontend.results import build_results_html


def _asset_ver(rel_path: str) -> int:
    """
    Cache-busting token derived from a file's modified time.

    Appended as ?v=... to asset URLs so the browser refetches CSS/JS as
    soon as the file changes — no manual hard-refresh needed.
    """
    try:
        return int(os.path.getmtime(rel_path))
    except OSError:
        return 0


def safe_js(code: str):
    try:
        ui.run_javascript(code)
    except Exception:
        pass


def safe_notify(msg: str, type="info"):
    try:
        ui.notify(msg, type=type)
    except Exception:
        pass


def register_page():
    from src.frontend.layout import render_shell, TELEPORT_JS

    llm_ok = check_llm()

    # CSS
    for css in ["theme", "layout", "components", "results"]:
        ui.add_head_html(
            f'<link rel="stylesheet" href="/assets/css/{css}.css?v={_asset_ver(f"assets/css/{css}.css")}">'
        )

    # Fonts
    ui.add_head_html("""
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
    """, shared=True)

    # Shell
    ui.add_body_html(render_shell(llm_ok))

    # Main content
    steps_html = make_steps(1)
    ui.add_body_html(f"""
    <div id="ng-main-content">

      <div id="view-analyzer" class="view">
      <div class="pg-title">AI Resume <em>Matcher</em></div>
      <div class="pg-sub">Upload a resume and paste a job description to get a semantic match score</div>

      {steps_html}

      <div class="divider"></div>

      <div class="content-card">
        <input type="file" id="file-input" accept=".pdf,.docx" style="display:none;"/>
        <div class="two-col">

          <div>
            <div class="sec-lbl-row">
              <div class="sec-lbl">Resume File</div>
              <button class="clear-btn" onclick="clearResume()" title="Clear resume">✕</button>
            </div>
            <div class="up-zone" id="up-zone"
                ondragover="event.preventDefault();this.classList.add('drag')"
                ondragleave="this.classList.remove('drag')"
                ondrop="event.preventDefault();this.classList.remove('drag');handleFileSelect(event.dataTransfer.files[0])">
              <svg width="30" height="36" viewBox="0 0 36 44" fill="none" style="opacity:0.3;">
                <rect x="1" y="1" width="26" height="34" rx="3" stroke="currentColor" stroke-width="2" fill="none"/>
                <path d="M27 1l8 8h-8V1z" stroke="currentColor" stroke-width="2" fill="none"/>
                <line x1="6" y1="13" x2="22" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="6" y1="19" x2="22" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <line x1="6" y1="25" x2="15" y2="25" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
              <div class="up-text">Drop file or <strong>browse</strong></div>
              <div class="up-hint">PDF &nbsp;&middot;&nbsp; DOCX</div>
            </div>
          </div>

          <div>
            <div class="sec-lbl-row">
              <div class="sec-lbl">Job Description</div>
              <button class="clear-btn" onclick="clearJD()" title="Clear job description">✕</button>
            </div>
            <div class="jd-wrap">
              <textarea id="jd-input" class="jd-box"
                placeholder="Paste the full job description here..."></textarea>
              <div class="jd-counter" id="jd-counter">0 / 5000</div>
            </div>
          </div>

        </div>
        <div style="margin-top:24px;">
          <button class="btn-primary" id="analyse-btn">&rarr; Analyse Match</button>
        </div>
      </div>

      <div class="spinner-bar" id="spinner" style="display:none;">
        <div class="spin-dots">
          <div class="spin-dot"></div>
          <div class="spin-dot"></div>
          <div class="spin-dot"></div>
        </div>
        <span class="spin-text" id="spin-text">Analysing&hellip;</span>
      </div>

      <div class="divider"></div>
      <div id="jf-results" style="display:none;"></div>
      </div><!-- /view-analyzer -->

      <div id="view-matches" class="view" style="display:none;">
        <div class="pg-title">Job <em>Matches</em></div>
        <div class="pg-sub">Load your resume once, then fetch German AI/ML jobs (full descriptions) and score each against it</div>

        <div class="divider"></div>

        <div class="mt-stats" id="mt-stats"></div>

        <div class="content-card">
          <input type="file" id="mt-file" accept=".pdf,.docx" style="display:none;"/>
          <div class="mt-row">
            <button class="btn-ghost" id="mt-upload-btn"
              onclick="document.getElementById('mt-file').click()">📄 Load Resume</button>
            <span class="mt-status" id="mt-resume-status">No resume loaded</span>
          </div>

          <div class="jd-fetch" style="margin-top:16px;">
            <input id="mt-query" class="fetch-inp" placeholder="Optional: search one role now (default = your saved titles)"/>
            <button class="btn-primary" id="mt-run-btn" onclick="runMatch()">&rarr; Fetch &amp; Score</button>
          </div>

          <div class="mt-row" style="margin-top:12px;">
            <label class="mt-auto"><input type="checkbox" id="mt-entry" checked/> Entry-level only</label>
          </div>

          <div class="mt-row" style="margin-top:12px;">
            <label class="mt-auto"><input type="checkbox" id="mt-sched" onchange="toggleScheduler()"/> Auto-fetch in background</label>
            <select id="mt-sched-interval" class="mt-select" onchange="toggleScheduler()">
              <option value="30">every 30 min</option>
              <option value="60" selected>every 1 hr</option>
              <option value="180">every 3 hr</option>
              <option value="360">every 6 hr</option>
            </select>
            <span class="mt-status" id="mt-sched-status"></span>
          </div>

          <div class="mt-row" style="margin-top:14px;">
            <span class="mt-status" id="mt-poll-status"></span>
            <button class="mt-clear" onclick="clearAllMatches()">🗑 Clear all</button>
          </div>

          <button class="mt-toggle" id="mt-filters-toggle" aria-expanded="false" aria-controls="mt-filters" onclick="toggleFilters()">&#9881; Filters &amp; keywords &#9656;</button>
          <div class="mt-filters" id="mt-filters" style="display:none;"></div>
        </div>

        <div class="mt-resume-row">
          <button class="btn-ghost" id="mt-resume-btn" style="display:none;" onclick="openResume()">&#128196; View Resume Details</button>
        </div>

        <div class="fetch-results" id="mt-results"></div>
      </div><!-- /view-matches -->

      <div id="view-history" class="view" style="display:none;">
        <div class="pg-title">Match <em>History</em></div>
        <div class="pg-sub">Every job you've scored — track which ones you've applied to</div>

        <div class="divider"></div>

        <div id="hist-filters" class="hist-filters">
          <button class="hist-fbtn active" data-f="all" onclick="setHistFilter('all')">All <span class="hist-count">0</span></button>
          <button class="hist-fbtn" data-f="open" onclick="setHistFilter('open')">Not applied <span class="hist-count">0</span></button>
          <button class="hist-fbtn" data-f="applied" onclick="setHistFilter('applied')">Applied <span class="hist-count">0</span></button>
        </div>

        <div class="fetch-results" id="hist-results"></div>
      </div><!-- /view-history -->

      <div id="view-settings" class="view" style="display:none;">
        <div class="pg-title">LLM <em>Settings</em></div>
        <div class="pg-sub">Choose the provider and model used for extraction, matching, and summaries</div>

        <div class="divider"></div>

        <div class="content-card">
          <div class="set-row">
            <label class="set-lbl">Provider</label>
            <div class="dd" id="dd-provider">
              <button class="dd-btn" type="button" onclick="ddToggle(event,'provider')">
                <span class="dd-val" id="dd-provider-val">—</span>
                <span class="dd-arrow">▾</span>
              </button>
              <div class="dd-menu" id="dd-provider-menu"></div>
            </div>
          </div>
          <div class="set-row">
            <label class="set-lbl">Model</label>
            <div class="dd" id="dd-model">
              <button class="dd-btn" type="button" onclick="ddToggle(event,'model')">
                <span class="dd-val" id="dd-model-val">—</span>
                <span class="dd-arrow">▾</span>
              </button>
              <div class="dd-menu" id="dd-model-menu"></div>
            </div>
          </div>
          <div class="set-row">
            <label class="set-lbl">Custom model</label>
            <input id="set-model-custom" class="fetch-inp"
              placeholder="Optional — type a model id to override the dropdown"/>
          </div>
          <div class="set-actions">
            <button class="btn-primary" id="set-apply" onclick="applySettings()">Apply</button>
            <span class="set-status" id="set-status"></span>
          </div>
        </div>
      </div><!-- /view-settings -->

      <div id="detail-modal" class="modal-overlay" style="display:none;" onclick="closeDetail(event)">
        <div class="modal-box" id="detail-box"></div>
      </div>

    </div>
    """)

    # JS assets
    for js in ["theme", "upload", "analysis", "fetch", "settings", "matches", "history"]:
        ui.add_body_html(
            f'<script src="/assets/js/{js}.js?v={_asset_ver(f"assets/js/{js}.js")}"></script>'
        )

    ui.add_body_html(TELEPORT_JS)

    def on_file_uploaded():
        safe_js(f"""
        var s = document.querySelector('.steps');
        if(s) s.outerHTML = `{make_steps(2)}`;
        """)

    def on_jd_added():
        safe_js(f"""
        var s = document.querySelector('.steps');
        if(s) s.outerHTML = `{make_steps(2)}`;
        """)

    async def run_analysis():
        jd_text  = await ui.run_javascript("window._jdText || ''")
        tmp_path = await ui.run_javascript("window._resumeTmp || ''")

        if not jd_text or len(jd_text.strip()) < 50:
            safe_notify("Paste a job description", type="warning")
            return

        if not tmp_path or not os.path.exists(tmp_path):
            safe_notify("Upload a resume file first", type="warning")
            return

        if not check_llm():
            safe_notify("LLM provider not available", type="negative")
            return

        safe_js(f"""
        var s = document.querySelector('.steps');
        if(s) s.outerHTML = `{make_steps(3)}`;
        """)
        safe_js(
            'document.getElementById("spinner").style.display="flex";'
            'document.getElementById("analyse-btn").disabled=true;'
            'document.getElementById("analyse-btn").style.opacity=".45";'
        )

        try:
            loop = asyncio.get_event_loop()

            safe_js('document.getElementById("spin-text").innerText="Parsing resume...";')
            try:
                resume_text = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: extract_all_text(tmp_path)),
                    timeout=_T_PARSE,
                )
            except asyncio.TimeoutError:
                safe_notify(f"Resume parsing timed out ({_T_PARSE}s) -- try a smaller or simpler file", type="negative")
                return

            if not resume_text or len(resume_text) < 50:
                safe_notify("Could not parse resume", type="negative")
                return

            safe_js('document.getElementById("spin-text").innerText="Extracting information...";')
            try:
                resume_json, jd_json = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: extract_all(resume_text, jd_text)),
                    timeout=_T_EXTRACT,
                )
            except asyncio.TimeoutError:
                safe_notify(f"LLM extraction timed out ({_T_EXTRACT}s) -- the provider may be slow, try again", type="negative")
                return

            if not resume_json and not jd_json:
                safe_notify("Extraction failed for both resume and job description", type="negative")
                return
            if not resume_json:
                safe_notify("Could not extract resume -- check the file format or try a different file", type="negative")
                return
            if not jd_json:
                safe_notify("Could not extract job description -- make sure it contains enough text (50+ chars)", type="negative")
                return

            safe_js('document.getElementById("spin-text").innerText="Calculating match score...";')
            try:
                results = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: match(resume_json, jd_json)),
                    timeout=_T_MATCH,
                )
            except asyncio.TimeoutError:
                safe_notify(f"Scoring timed out ({_T_MATCH}s) -- embedding model may still be loading, try again", type="negative")
                return

            safe_js('document.getElementById("spin-text").innerText="Generating summary...";')
            from src.services.summary import generate_summary
            try:
                summary = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: generate_summary(resume_json, jd_json, results)),
                    timeout=_T_SUMMARY,
                )
            except asyncio.TimeoutError:
                summary = ""  # summary is optional -- show results without it

        except Exception as exc:
            print(f"[ERROR] {exc}")
            import traceback
            traceback.print_exc()
            safe_notify(f"Error: {exc}", type="negative")

        finally:
            safe_js(
                'document.getElementById("spinner").style.display="none";'
                'document.getElementById("analyse-btn").disabled=false;'
                'document.getElementById("analyse-btn").style.opacity="1";'
            )
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    safe_js("window._resumeTmp=null;window._resumeName=null;")
            except Exception as e:
                print(f"[ERROR] cleanup: {e}")

    ui.on("file_uploaded", on_file_uploaded)
    ui.on("jd_added",      on_jd_added)
    ui.on("run_analysis",  run_analysis)