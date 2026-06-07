# src/frontend/handlers.py

import os
import asyncio
from pathlib import Path

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
        <input type="file" id="file-input" accept=".pdf,.docx,.doc" style="display:none;"/>
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
              <div class="up-hint">PDF &nbsp;&middot;&nbsp; DOCX &nbsp;&middot;&nbsp; DOC</div>
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

      <div id="view-jobsearch" class="view" style="display:none;">
        <div class="pg-title">Job <em>Search</em></div>
        <div class="pg-sub">Search live job postings from Adzuna</div>

        <div class="divider"></div>

        <div class="content-card">
          <div class="jd-fetch">
            <input id="fetch-query" class="fetch-inp"
              placeholder="Role e.g. machine learning engineer"/>
            <input id="fetch-loc" class="fetch-inp fetch-inp-sm"
              placeholder="Location"/>
            <button class="btn-primary fetch-btn" id="fetch-btn" onclick="fetchJobs()">&rarr; Fetch Jobs</button>
          </div>
        </div>

        <div class="fetch-results" id="fetch-results" style="display:none;"></div>
      </div><!-- /view-jobsearch -->

      <div id="view-matches" class="view" style="display:none;">
        <div class="pg-title">Job <em>Matches</em></div>
        <div class="pg-sub">Load your resume once, then fetch German jobs (full descriptions via Arbeitnow) and score each against it</div>

        <div class="divider"></div>

        <div class="content-card">
          <input type="file" id="mt-file" accept=".pdf,.docx,.doc" style="display:none;"/>
          <div class="mt-row">
            <button class="btn-ghost" id="mt-upload-btn"
              onclick="document.getElementById('mt-file').click()">📄 Load Resume</button>
            <span class="mt-status" id="mt-resume-status">No resume loaded</span>
          </div>

          <div class="jd-fetch" style="margin-top:16px;">
            <input id="mt-query" class="fetch-inp" placeholder="Optional: override role (default = your target AI/ML titles)"/>
            <input id="mt-loc" class="fetch-inp fetch-inp-sm" placeholder="Location e.g. berlin"/>
            <button class="btn-primary" id="mt-run-btn" onclick="runMatch()">&rarr; Fetch &amp; Score</button>
          </div>

          <div class="mt-row" style="margin-top:12px;">
            <label class="mt-auto"><input type="checkbox" id="mt-entry" checked/> Entry-level only</label>
          </div>

          <div class="mt-row" style="margin-top:14px;">
            <label class="mt-auto">
              <input type="checkbox" id="mt-auto" onchange="toggleAutoMatch()"/> Auto-refresh every
            </label>
            <select id="mt-interval" class="mt-select">
              <option value="60">1 min</option>
              <option value="300" selected>5 min</option>
              <option value="900">15 min</option>
            </select>
            <span class="mt-status" id="mt-poll-status"></span>
          </div>

          <div class="mt-filters" id="mt-filters"></div>
        </div>

        <div class="fetch-results" id="mt-results"></div>
      </div><!-- /view-matches -->

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

    </div>
    """)

    # JS assets
    for js in ["theme", "upload", "analysis", "fetch", "settings", "matches"]:
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
            safe_js('document.getElementById("spin-text").innerText="Parsing resume...";')
            resume_text = await asyncio.get_event_loop().run_in_executor(
                None, lambda: extract_all_text(tmp_path)
            )

            if not resume_text or len(resume_text) < 50:
                safe_notify("Could not parse resume", type="negative")
                return

            safe_js('document.getElementById("spin-text").innerText="Extracting information...";')
            resume_json, jd_json = await asyncio.get_event_loop().run_in_executor(
                None, lambda: extract_all(resume_text, jd_text)
            )

            if not resume_json or not jd_json:
                safe_notify("Extraction failed", type="negative")
                return

            safe_js('document.getElementById("spin-text").innerText="Calculating match score...";')
            results = match(resume_json, jd_json)

            safe_js('document.getElementById("spin-text").innerText="Generating summary...";')
            from src.services.summary import generate_summary
            summary = await asyncio.get_event_loop().run_in_executor(
                None, lambda: generate_summary(resume_json, jd_json, results)
            )

            safe_js(f"""
            var s = document.querySelector('.steps');
            if(s) s.outerHTML = `{make_steps(4)}`;
            """)

            html = build_results_html(results, resume_json, jd_json, summary)
            html_escaped = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

            safe_js(f"""
            var r = document.getElementById('jf-results');
            if(r) {{
                r.innerHTML = `{html_escaped}`;
                r.style.display = 'block';
            }}
            """)

            safe_js("""
            window.jfTab = function(el, panelId) {
                document.querySelectorAll('#jf-tab-row .tab-item').forEach(function(t) {
                    t.classList.remove('active');
                });
                document.querySelectorAll('.jf-panel').forEach(function(p) {
                    p.style.display = 'none';
                });
                el.classList.add('active');
                var panel = document.getElementById(panelId);
                if (panel) panel.style.display = 'block';
            };
            """)

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