# src/frontend/handlers.py

import os
import asyncio
from pathlib import Path

from nicegui import ui

from src.parsers import extract_all_text
from src.extractors import extract_all
from src.utils.router import check_llm
from src.matcher import get_match_score
from src.frontend.components import make_steps
from src.frontend.results import render_results


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
    assets = Path("assets")

    # CSS
    for css in ["theme", "layout", "components", "results"]:
        ui.add_head_html(
            f'<link rel="stylesheet" href="/assets/css/{css}.css">'
        )

    # Fonts
    ui.add_head_html("""
    <link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
    """, shared=True)

    # Shell
    ui.add_body_html(render_shell(llm_ok))

    # Inject ALL main content directly into body — bypasses NiceGUI sanitizer
    steps_html = make_steps(1)
    ui.add_body_html(f"""
    <div id="ng-main-content">
      <div class="pg-title">AI Resume <em>Matcher</em></div>
      <div class="pg-sub">Upload a resume and paste a job description to get a semantic match score</div>

      {steps_html}

      <div class="divider"></div>

      <div class="content-card">
        <input type="file" id="file-input" accept=".pdf,.docx,.doc" style="display:none;"/>
        <div class="two-col">

          <!-- Resume upload — left, narrow (1fr) -->
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

          <!-- JD textarea — right, wide (2fr) -->
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
    </div>
    """)

    # JS assets
    for js in ["theme", "upload", "analysis"]:
        ui.add_body_html(
            f'<script src="/assets/js/{js}.js"></script>'
        )

    # Teleport last
    ui.add_body_html(TELEPORT_JS)

    # Results rendered via JS injection — no NiceGUI element needed
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
            results = get_match_score(resume_json, jd_json)

            safe_js('document.getElementById("spin-text").innerText="Generating summary...";')
            from src.extractors.summary import generate_summary
            summary = await asyncio.get_event_loop().run_in_executor(
                None, lambda: generate_summary(resume_json, jd_json, results)
            )

            safe_js(f"""
            var s = document.querySelector('.steps');
            if(s) s.outerHTML = `{make_steps(4)}`;
            """)

            # Build results HTML and inject via JS
            from src.frontend.results import build_results_html
            html = build_results_html(results, resume_json, jd_json, summary)

            # Escape for JS template literal
            html_escaped = html.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')
            safe_js(f"""
            var r = document.getElementById('jf-results');
            if(r) {{
                r.innerHTML = `{html_escaped}`;
                r.style.display = 'block';
            }}
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