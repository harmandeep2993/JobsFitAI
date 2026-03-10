# app.py

import asyncio
import tempfile
import os
from pathlib import Path

from nicegui import ui, app as ngapp
from starlette.requests  import Request
from starlette.responses import JSONResponse

from src.parser import extract_resume_text
from src.extractor import extract_all
from src.matcher import get_match_score

from src.utils.ollama import check_ollama


# UPLOAD ENDPOINT
@ngapp.post("/api/upload")
async def api_upload(request: Request):
    form    = await request.form()
    upload  = form.get("file")
    if upload is None:
        return JSONResponse({"ok": False, "error": "no file"}, status_code=400)
    data   = await upload.read()
    name   = upload.filename or "resume"
    suffix = Path(name).suffix.lower()
    if suffix not in {".pdf", ".docx", ".doc"}:
        return JSONResponse({"ok": False, "error": "unsupported type"}, status_code=400)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data); tmp.close()
    return JSONResponse({"ok": True, "name": name, "tmp": tmp.name,
                         "kb": round(len(data)/1024, 1), "ext": suffix.upper()[1:]})


# FONTS + CSS

ui.add_head_html("""
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Sans:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
:root {
  --accent:#e8471a; --accent-s:rgba(232,71,26,0.08); --accent-h:#d13c14;
  --bg:#eeede9; --bg-r:#ffffff; --bg-c:#ffffff;
  --bd:#e0ded8; --bd-s:#eae9e4;
  --t1:#18181f; --t2:#68667a; --t3:#aeacbe;
  --green:#18994e; --green-bg:#edf8f2; --green-bd:#b4e4cc;
  --red:#d42c1c;   --red-bg:#fdf0ee;   --red-bd:#f4bab4;
  --amber:#b87010; --amber-bg:#fdf4e6; --amber-bd:#eecca0;
  --blue:#1868c8;  --blue-bg:#ecf3fd;  --blue-bd:#a4c4ee;
  --sha-s:0 1px 2px rgba(0,0,0,0.05);
}
:root.dark {
  --bg:#0c0c0e; --bg-r:#131316; --bg-c:#1a1a1f;
  --bd:#252530; --bd-s:#1e1e28;
  --t1:#f0f0f5; --t2:#7070a0; --t3:#38385a;
  --green:#32d474; --green-bg:#0a2018; --green-bd:#183c28;
  --red:#f5564a;   --red-bg:#200c0a;   --red-bd:#4a1812;
  --amber:#f0a832; --amber-bg:#201408; --amber-bd:#503810;
  --blue:#58b4f5;  --blue-bg:#081428;  --blue-bd:#183858;
  --sha-s:0 1px 3px rgba(0,0,0,.3);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{background:var(--bg)!important;color:var(--t1)!important;font-family:'Instrument Sans',sans-serif!important;transition:background .25s,color .25s;}
.nicegui-content,.q-page{padding:0!important;margin:0!important;background:var(--bg)!important;min-height:100vh!important;}
.q-header{display:none!important}

/* ─────────────────────────────────────────────────────
   SHELL — the one centered card that holds everything
   We render ALL structural divs as raw HTML so NiceGUI
   wrapper divs cannot interfere with the flex layout.
   Only the main-wrap inner content uses NiceGUI elements.
───────────────────────────────────────────────────── */

.jfai-page {min-height: 200vh;background: var(--bg);display: block;padding: 16px;transition: background .25s;}

.jfai-shell {width: 150%;max-width: 200%; margin: 0 auto;background: var(--bg-r);border: 1px solid var(--bd);border-radius: 16px;overflow: hidden;
            box-shadow: 0 4px 32px rgba(0,0,0,0.09), 0 1px 4px rgba(0,0,0,0.06);display: flex;flex-direction: column;transition: background .25s, border-color .25s;}

/* Topbar */
.jfai-topbar {height: 52px;background: var(--bg-r);border-bottom: 1px solid var(--bd);display: flex;align-items: center;
  padding: 0 20px;gap: 12px;flex-shrink: 0;transition: background .25s, border-color .25s;}
.logo-mark {width:30px;height:30px;background:var(--accent);border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:13px;font-weight:800;color:#fff;flex-shrink:0;}
.logo-name{font-size:15px;font-weight:700;color:var(--t1);letter-spacing:-.3px}
.logo-name em{color:var(--accent);font-style:normal}
.topbar-r{margin-left:auto;display:flex;align-items:center;gap:8px}
.t-chip{padding:4px 11px;border-radius:99px;font-size:11px;font-weight:500;font-family:'DM Mono',monospace;background:var(--bg-c);border:1px solid var(--bd);
  color:var(--t2);display:flex;align-items:center;gap:5px;transition:background .25s,border-color .25s;}
.t-bead{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.bon{background:var(--green);box-shadow:0 0 5px var(--green)}
.boff{background:var(--red);box-shadow:0 0 5px var(--red)}
.theme-btn{width:34px;height:34px;border-radius:8px;border:1px solid var(--bd);background:var(--bg-c);display:flex;align-items:center;
  justify-content:center;font-size:15px;cursor:pointer;transition:all .2s;}
.theme-btn:hover{border-color:var(--accent);background:var(--accent-s)}

/* Body row: sidebar + main */
.jfai-body {display: flex;flex: 1;min-height: 680px;}

/* Sidebar */
.jfai-sidebar {width: 200px;min-width: 200px;flex-shrink: 0;background: var(--bg-r);border-right: 1px solid var(--bd);
  padding: 20px 10px;display: flex;flex-direction: column;transition: background .25s, border-color .25s;}
.sb-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:1.2px;padding:4px 10px 8px;color:var(--t3);font-family:'DM Mono',monospace;}
.sb-item{padding:8px 10px;border-radius:7px;font-size:13px;font-weight:500;color:var(--t2);cursor:pointer;display:flex;align-items:center;gap:8px;
  transition:all .15s;margin-bottom:2px;}
.sb-item:hover{background:var(--bd-s);color:var(--t1)}
.sb-item.active{background:var(--accent-s);color:var(--accent);font-weight:600}
.sb-rule{height:1px;background:var(--bd);margin:10px 0}
.sb-meta{font-size:11px;color:var(--t3);padding:6px 10px;
  font-family:'DM Mono',monospace;line-height:1.7;}
.sb-foot{margin-top:auto;padding:10px;border-top:1px solid var(--bd);
  font-size:10px;color:var(--t3);font-family:'DM Mono',monospace;}

/* Main content */
.jfai-main {flex: 1;min-width: 0;background: var(--bg);overflow-y: auto;transition: background .25s;}

/* The NiceGUI element we inject into jfai-main fills it */
#main-content {padding: 36px 44px;width: 100%;}

.pg-title{font-size:28px;font-weight:700;color:var(--t1);letter-spacing:-.5px;margin-bottom:6px;}
.pg-title em{color:var(--accent);font-style:normal}
.pg-sub{font-size:14px;color:var(--t2);margin-bottom:32px}
.divider{height:1px;background:var(--bd);margin:24px 0}
.sec-lbl{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:1.2px;color:var(--t3);margin-bottom:12px;font-family:'DM Mono',monospace;}

/* Steps */
.steps{display:flex;align-items:center;margin-bottom:32px;gap:0;}
.step-pill{display:flex;align-items:center;gap:8px}
.step-num{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;
          font-size:11px;font-weight:700;font-family:'DM Mono',monospace;flex-shrink:0;}
.s-done{background:var(--green);color:#fff}
.s-act{background:var(--accent);color:#fff}
.s-todo{background:transparent;color:var(--t3);border:1.5px solid var(--bd)}
.step-lbl{font-size:13px;font-weight:500;white-space:nowrap;}
.sl-done{color:var(--green)} .sl-act{color:var(--accent);font-weight:600} .sl-todo{color:var(--t3)}
.step-sep{width:36px;height:1px;background:var(--bd);margin:0 8px;flex-shrink:0;}

/* Content card */
.content-card{width:100%;background:var(--bg-r);border:1px solid var(--bd);border-radius:14px;padding:28px 32px 32px;
  margin-bottom:24px;box-shadow:var(--sha-s); transition:background .25s,border-color .25s;}

/* Two-col grid */
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px; margin-bottom:24px;align-items:start;}

/* JD textarea */
.jd-box{width:100%;height:260px;padding:14px 16px;border-radius:10px;border:1.5px solid var(--bd);background:var(--bg-c);
        color:var(--t1);font-family:'Instrument Sans',sans-serif;font-size:14px;line-height:1.7;resize:vertical;outline:none;
        display:block;transition:border-color .2s,background .25s,color .25s;}
.jd-box::placeholder{color:var(--t3)}
.jd-box:focus{border-color:var(--accent)}
.jd-box.success{border-color: var(--green) !important;background: var(--green-bg);}

/* Upload zone */
.up-zone{border:1.5px dashed var(--bd);border-radius:10px;cursor:pointer;background:var(--bg-c);transition:all .2s;height:260px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;}
.up-zone:hover,.up-zone.drag{border-color:var(--accent);background:var(--accent-s)}
.up-text{font-size:13px;color:var(--t2);text-align:center;}
.up-text strong{color:var(--accent);font-weight:600}
.up-hint{font-size:11px;color:var(--t3);font-family:'DM Mono',monospace}
                 
.file-chip{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--green-bg);
          border:1px solid var(--green-bd);border-radius:10px;padding:16px;height:260px;text-align:center;}
.fc-name{font-size:12px;font-weight:600;color:var(--green);font-family:'DM Mono',monospace;max-width:160px;white-space:nowrap;
          overflow:hidden;text-overflow:ellipsis;}
.fc-meta{font-size:11px;color:var(--t3)}

/* Buttons */
.btn-primary{display:inline-flex;align-items:center;gap:8px;padding:10px 24px;border-radius:8px;border:none;background:var(--accent);color:#fff;
  font-size:13px;font-weight:600;cursor:pointer;font-family:'Instrument Sans',sans-serif;box-shadow:0 2px 8px var(--accent-s);transition:all .2s;}
.btn-primary:hover{background:var(--accent-h);transform:translateY(-1px)}
.btn-primary:active{transform:translateY(0)}
.btn-primary:disabled{opacity:.45;cursor:not-allowed;transform:none;box-shadow:none}
.btn-ghost{display:inline-flex;align-items:center;gap:7px;padding:9px 18px;border-radius:8px;border:1px solid var(--bd);background:transparent;color:var(--t2);
  font-size:13px;font-weight:500;cursor:pointer;font-family:'Instrument Sans',sans-serif;transition:all .2s;}
.btn-ghost:hover{border-color:var(--t2);color:var(--t1);background:var(--bd-s)}

/* Spinner */
.spinner-bar{display:flex;align-items:center;gap:12px;padding:14px 18px;background:var(--bg-c);border:1px solid var(--bd);border-radius:10px;margin:16px 0;
  transition:background .25s,border-color .25s;}
.spin-dots{display:flex;gap:4px;align-items:center}
.spin-dot{width:7px;height:7px;border-radius:50%;background:var(--accent);
  animation:bounce 1.3s ease-in-out infinite;}
.spin-dot:nth-child(2){animation-delay:.18s}
.spin-dot:nth-child(3){animation-delay:.36s}
@keyframes bounce{0%,80%,100%{transform:scale(.55);opacity:.35}40%{transform:scale(1);opacity:1}}
.spin-text{font-size:12px;color:var(--t2);font-family:'DM Mono',monospace}

/* Metrics */
.metrics-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0;}
.m-card{background:var(--bg-c);border:1px solid var(--bd);border-radius:12px;
  padding:18px 20px;box-shadow:var(--sha-s);transition:background .25s,border-color .25s;}
.m-card:first-child{border-top:2px solid var(--accent)}
.m-lbl{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;
  color:var(--t3);margin-bottom:8px;font-family:'DM Mono',monospace;}
.m-val{font-size:30px;font-weight:700;font-family:'DM Mono',monospace;line-height:1;margin-bottom:6px;}
.m-den{font-size:16px;font-weight:400;color:var(--t3)}
.m-sub{font-size:11px;font-weight:500;color:var(--t2)}

/* Tabs */
.tab-row{display:flex;border-bottom:1px solid var(--bd);margin-bottom:22px;}
.tab-item{padding:9px 18px;font-size:13px;font-weight:500;color:var(--t3);cursor:pointer;
  border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s;}
.tab-item:hover{color:var(--t1)}
.tab-item.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}

/* Progress */
.prog-row{margin-bottom:16px}
.prog-head{display:flex;justify-content:space-between;margin-bottom:6px}
.prog-lbl{font-size:13px;font-weight:500;color:var(--t1)}
.prog-pct{font-size:12px;font-weight:600;color:var(--t2);font-family:'DM Mono',monospace}
.prog-track{height:6px;border-radius:99px;overflow:hidden;background:var(--bd-s)}
.prog-fill{height:100%;border-radius:99px}

/* Tags */
.gap-block{margin-bottom:18px}
.gap-lbl{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:var(--t3);margin-bottom:7px;}
.tags-row{display:flex;flex-wrap:wrap;gap:6px}
.tag{padding:4px 11px;border-radius:99px;font-size:11px;font-weight:600}
.tg{background:var(--green-bg);color:var(--green);border:1px solid var(--green-bd)}
.tr{background:var(--red-bg);color:var(--red);border:1px solid var(--red-bd)}
.ta{background:var(--amber-bg);color:var(--amber);border:1px solid var(--amber-bd)}
.tb{background:var(--blue-bg);color:var(--blue);border:1px solid var(--blue-bd)}

/* Callout */
.callout{border-radius:10px;padding:12px 16px;font-size:12px;line-height:1.6;display:flex;gap:10px;align-items:flex-start;
  background:var(--blue-bg);border:1px solid var(--blue-bd);color:var(--blue);margin-top:16px;}

/* Footer */
.foot-note{font-size:11px;color:var(--t3);font-family:'DM Mono',monospace;margin-top:36px;padding-top:18px;border-top:1px solid var(--bd);}

/* Animations */
@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.fade-in{animation:fadeUp .3s ease forwards}
.cg{color:var(--green)} .cr{color:var(--red)} .ca{color:var(--amber)} .cb{color:var(--blue)}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-thumb{background:var(--bd);border-radius:99px}
                 
</style>
""", shared=True)

# HELPERS

def prog_grad(v):
    if v >= 80: return "linear-gradient(90deg,var(--green),#5ae89a)"
    if v >= 60: return "linear-gradient(90deg,var(--blue),#7ac8ff)"
    if v >= 40: return "linear-gradient(90deg,var(--amber),#f5ca6a)"
    return             "linear-gradient(90deg,var(--red),#ff8878)"

def score_col(v):
    if v >= 80: return "var(--green)"
    if v >= 60: return "var(--blue)"
    if v >= 40: return "var(--amber)"
    return             "var(--red)"

def safe_html(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def make_tags(items, css):
    if not items:
        return '<span style="font-size:12px;color:var(--t3);">—</span>'
    return "".join(f'<span class="tag {css}">{safe_html(i)}</span>' for i in items)

def make_prog(label, val):
    return (f'<div class="prog-row"><div class="prog-head">'
            f'<span class="prog-lbl">{label}</span>'
            f'<span class="prog-pct">{val}%</span></div>'
            f'<div class="prog-track">'
            f'<div class="prog-fill" style="width:{val}%;background:{prog_grad(val)};"></div>'
            f'</div></div>')

def make_steps(current):
    labels = ["Upload", "Job Description", "Analysing", "Results"]
    parts  = []
    for i, lbl in enumerate(labels, 1):
        if   i < current:  nc,lc,txt = "s-done","sl-done","✓"
        elif i == current: nc,lc,txt = "s-act", "sl-act", str(i)
        else:              nc,lc,txt = "s-todo","sl-todo",str(i)
        parts.append(f'<div class="step-pill">'
                     f'<div class="step-num {nc}">{txt}</div>'
                     f'<span class="step-lbl {lc}">{lbl}</span></div>')
        if i < 4:
            parts.append('<div class="step-sep"></div>')
    return f'<div class="steps">{"".join(parts)}</div>'


# RESULTS RENDERER
def render_results(container, results, resume_json, jd_json):
    score  = results["final_score"]
    label  = results["label"]
    scores = results["scores"]
    sc = score_col(score)
    if   score >= 80: d_cls,d_txt = "cg","▲ Strong match"
    elif score >= 60: d_cls,d_txt = "cb","◆ Good match"
    elif score >= 40: d_cls,d_txt = "ca","◆ Partial match"
    else:             d_cls,d_txt = "cr","▼ Poor match"

    matched_req  = results["matched_required"]
    missing_req  = results["missing_required"]
    matched_pref = results["matched_preferred"]
    missing_pref = results["missing_preferred"]
    c_yrs   = results["candidate_years"]
    r_yrs   = results["required_years"]
    c_langs = ", ".join(results["candidate_langs"]) or "—"
    r_langs = ", ".join(results["required_langs"])  or "None specified"
    exp_note = f"{c_yrs} yrs vs {r_yrs} req." if r_yrs else f"{c_yrs} yrs found"

    prog_map = {
        "required_skills":"Required Skills","responsibilities":"Responsibilities",
        "experience":"Experience","education":"Education",
        "preferred_skills":"Preferred Skills","languages":"Languages",
    }
    progs = "".join(make_prog(prog_map[k], v) for k, v in scores.items())

    container.clear()
    with container:
        ui.html(f"""
        <div class="metrics-grid fade-in">
          <div class="m-card">
            <div class="m-lbl">Match Score</div>
            <div class="m-val" style="color:{sc};">{score}<span class="m-den">/100</span></div>
            <div class="m-sub {d_cls}">{d_txt}</div>
          </div>
          <div class="m-card">
            <div class="m-lbl">Required Skills</div>
            <div class="m-val cg">{len(matched_req)}<span class="m-den">/{len(matched_req)+len(missing_req)}</span></div>
            <div class="m-sub cg">matched</div>
          </div>
          <div class="m-card">
            <div class="m-lbl">Experience</div>
            <div class="m-val cb">{c_yrs}<span class="m-den"> yrs</span></div>
            <div class="m-sub">{exp_note}</div>
          </div>
        </div>""")
        ui.html("""<div class="tab-row">
          <div class="tab-item active">Match Breakdown</div>
          <div class="tab-item">Skills Gap</div>
          <div class="tab-item">Languages</div>
        </div>""")
        ui.html(f'<div class="fade-in">{progs}</div>')
        ui.html('<div class="divider"></div>')
        ui.html('<div class="sec-lbl">Skills Gap</div>')
        for lbl, items, css in [
            ("Required — Matched",  matched_req,  "tg"),
            ("Required — Missing",  missing_req,  "tr"),
            ("Preferred — Matched", matched_pref, "tg"),
            ("Preferred — Missing", missing_pref, "ta"),
        ]:
            ui.html(f'<div class="gap-block"><div class="gap-lbl">{lbl}</div>'
                    f'<div class="tags-row">{make_tags(items, css)}</div></div>')
        ui.html('<div class="divider"></div>')
        ui.html(f"""<div class="sec-lbl">Languages</div>
        <div style="font-size:13px;color:var(--t2);margin-bottom:5px;">
          Candidate &nbsp;<span style="color:var(--t1);font-weight:500;">{c_langs}</span>
        </div>
        <div style="font-size:13px;color:var(--t2);">
          Required &nbsp;&nbsp;<span style="color:var(--t1);font-weight:500;">{r_langs}</span>
        </div>""")
        ui.html('<div class="divider"></div>')
        ui.html("""<div class="callout"><span>ℹ️</span>
          <span>Results generated by qwen2.5:3b + sentence-transformers running locally.
          Scores are probabilistic — use as a guide, not a definitive judgement.</span>
        </div>""")
        ui.html('<div style="margin-top:24px;">'
                '<button class="btn-ghost" onclick="location.reload()">↩ Analyse Another</button></div>')
        ui.html(f'<div class="foot-note">{score}% · {label} · qwen2.5:3b · all-MiniLM-L6-v2 · CPU only</div>')


# PAGE
@ui.page("/")
def index():

    ollama_ok = check_ollama()
    bc  = "bon"  if ollama_ok else "boff"
    blb = "Ollama online" if ollama_ok else "Ollama offline"

    # Theme JS
    ui.add_body_html("""<script>

    function toggleTheme() {
      const r = document.documentElement;
      const b = document.getElementById('themechange');

      console.log("toggle clicked");

      if (r.classList.contains('dark')) {r.classList.remove('dark'); localStorage.setItem('jf','light');
                    if (b) b.textContent = '☀️';} else {r.classList.add('dark'); localStorage.setItem('jf','dark');
                    if (b) b.textContent = '🌙';}}

    /* wait until DOM exists */
    window.addEventListener('load', function() {const btn = document.getElementById('themechange');
                    if (btn) { btn.addEventListener('click', toggleTheme);}

      /* restore saved theme */
      const saved = localStorage.getItem('jf');if (saved === 'dark'){
                    document.documentElement.classList.add('dark');if (btn) btn.textContent = '🌙';
                    }
                  });

    </script>
    """)

    # LAYOUT
    # Step 1: render the full shell skeleton as raw HTML
    ui.html(f"""
    <div class="jfai-page">
      <div class="jfai-shell">

        <div class="jfai-topbar">
          <div class="logo-mark">J</div>
          <span class="logo-name">Job<em>Fit</em>AI</span>
          <div class="topbar-r">
            <div class="t-chip"><span class="t-bead {bc}"></span>{blb}</div>
            <div class="t-chip">qwen2.5:3b</div>

            <button class="theme-btn" id="themechange">☀️</button>
          </div>
        </div>

        <div class="jfai-body">
          <div class="jfai-sidebar">
            <div class="sb-sec">Navigation</div>
            <div class="sb-item active">🎯 Analyzer</div>
            <div class="sb-item">📊 History</div>
            <div class="sb-item">⚙️ Settings</div>
            <div class="sb-rule"></div>
            <div class="sb-sec">About</div>
            <div class="sb-meta">Resume match scoring<br>via local LLM +<br>semantic similarity</div>
            <div class="sb-foot">v1.0.0 · local</div>
          </div>
          <div class="jfai-main" id="jfai-main">
          </div>
        </div>

      </div>
    </div>
    """)

    # Step 2: render NiceGUI dynamic content into a named element
    # then immediately teleport it into #jfai-main via JS
    with ui.element("div").props('id="ng-main-content"').style(
        "padding:36px 44px;width:100%;min-width:0;"
    ):
        ui.html("""
        <div class="pg-title">AI Resume <em>Matcher</em></div>
        <div class="pg-sub">Upload a resume and paste a job description to get a semantic match score</div>
        """)

        steps_el = ui.html(make_steps(1))
        ui.html('<div class="divider"></div>')

        ui.html("""
        <div class="content-card">
          <input type="file" id="file-input" accept=".pdf,.docx,.doc"
                 style="display:none;" onchange="handleFileSelect(this.files[0])"/>
          <div class="two-col">
            <div>
              <div class="sec-lbl">Job Description</div>

              <textarea id="jd-input" class="jd-box" oninput="checkJD()" onpaste="setTimeout(checkJD, 10)" 
                placeholder="Paste the full job description here e.g. We are looking for a Data Scientist with Python, SQL and R experience. AWS knowledge preferred. Masters degree in Mathematics or Statistics required..."></textarea>
              </div>
            <div>
              <div class="sec-lbl">Resume File</div>
              <div class="up-zone" id="up-zone"
                  ondragover="event.preventDefault();this.classList.add('drag')"
                  ondragleave="this.classList.remove('drag')"
                  ondrop="event.preventDefault();this.classList.remove('drag');handleFileSelect(event.dataTransfer.files[0])">
                <svg width="36" height="44" viewBox="0 0 36 44" fill="none" style="opacity:0.3;">
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
          </div>
          <div style="margin-top:24px;">
            <button class="btn-primary" id="analyse-btn">
              &rarr; Analyse Match
            </button>
          </div>
        </div>""")

        ui.html("""
        <div class="spinner-bar" id="spinner" style="display:none;">
          <div class="spin-dots">
            <div class="spin-dot"></div><div class="spin-dot"></div><div class="spin-dot"></div>
          </div>
          <span class="spin-text" id="spin-text">Analysing&hellip;</span>
        </div>""")

        ui.html('<div class="divider"></div>')

        results_el = ui.element("div").style("display:none;")

    # Step 3: teleport the NiceGUI content block into the HTML shell
    ui.add_body_html("""<script>
    (function move(){
      var src = document.getElementById('ng-main-content');
      var dst = document.getElementById('jfai-main');
      if (src && dst) { dst.appendChild(src); }
      else { setTimeout(move, 30); }
    })();
    </script>""")

    ui.add_body_html("""<script>

    (function bindUpload(){
      const zone  = document.getElementById('up-zone');
      const input = document.getElementById('file-input');

      if (zone && input) {zone.addEventListener('click', function(){input.click();});

          input.addEventListener('change', function(){handleFileSelect(input.files[0]);});
          return;
      }
      setTimeout(bindUpload, 50);

    })();

    </script>
    """)

    # ── App JS ─────────────────────────────────────────────
    ui.add_body_html("""<script>
    window.handleFileSelect = function(file) {
      if (!file) return;
      var ext = file.name.split('.').pop().toLowerCase();
      if (!['pdf','docx','doc'].includes(ext)) { alert('Please upload PDF, DOCX or DOC.'); return; }
      
      var fd = new FormData();
      fd.append('file', file);
                     
      fetch('/api/upload', {method:'POST',body:fd})
        .then(function(r){ return r.json(); })
        .then(function(d){
                     
          if (!d.ok) { alert('Upload failed: '+(d.error||'unknown')); return; }
          window._resumeTmp  = d.tmp;
          window._resumeName = d.name;
          document.getElementById('up-zone').outerHTML =
            '<div class="file-chip" id="up-zone">' +
              '<span style="font-size:36px;">&#128196;</span>' +
              '<div style="text-align:center;">' +
                '<div class="fc-name" title="'+d.name+'">'+d.name+'</div>' +
                '<div class="fc-meta">'+d.kb+' KB &middot; '+d.ext+'</div>' +
              '</div>' +
              '<span style="color:var(--green);font-size:20px;font-weight:700;">&#10003;</span>' +
            '</div>';
          emitEvent('file_uploaded', {});
        })
        .catch(function(e){ alert('Upload error: '+e); });
    }
                     
    function checkJD() {
        const jd = document.getElementById('jd-input');
        if (!jd) return;

        const text = jd.value.trim();

        if (text.length > 30) {
            if (!jd.classList.contains('success')) {
                jd.classList.add('success');

                if (typeof emitEvent === 'function') {
                    emitEvent('jd_added', {});
                }
            }
        } else {
            jd.classList.remove('success');
        }
    }

    (function bindJD(){
        const jd = document.getElementById('jd-input');
        if (jd) {
            jd.addEventListener('input', checkJD);
            jd.addEventListener('paste', () => { setTimeout(checkJD, 10); });
        } else { setTimeout(bindJD, 50); }
    })();
                                             
    window.startAnalysis = function () {

        const jdEl = document.getElementById('jd-input');
        const jd = jdEl ? jdEl.value.trim() : '';

        if (jd.length < 50) {
            alert('Please paste a job description.');
            return;
        }

        if (!window._resumeTmp) {
            alert('Please upload a resume file first.');
            return;
        }

        window._jdText = jd;

        console.log("Check Analysis1");

        emitEvent('run_analysis');
    };
                     
    (function bindAnalyse(){
        const btn = document.getElementById('analyse-btn');
        if (btn) { btn.addEventListener('click', startAnalysis); }
        else { setTimeout(bindAnalyse, 50); }
    })();
    </script>""")


    def on_file_uploaded():
        steps_el.set_content(make_steps(2))
    ui.on("file_uploaded", on_file_uploaded)

    def on_jd_added():
      steps_el.set_content(make_steps(2))
    ui.on("jd_added", on_jd_added)

    async def run_analysis():
        jd_text  = await ui.run_javascript("window._jdText || ''")
        tmp_path = await ui.run_javascript("window._resumeTmp || ''")
        res_name = await ui.run_javascript("window._resumeName || ''")

        if not jd_text or len(jd_text.strip()) < 50:
            ui.notify("Paste a job description", type="warning"); return
        if not tmp_path:
            ui.notify("Upload a resume file first", type="warning"); return
        if not check_ollama():
            ui.notify("Ollama not running — start: ollama serve", type="negative"); return

        steps_el.set_content(make_steps(3))
        ui.run_javascript(
            'document.getElementById("spinner").style.display="flex";'
            'document.getElementById("analyse-btn").disabled=true;'
            'document.getElementById("analyse-btn").style.opacity=".45";')
        results_el.style("display:none;")

        try:
            ui.run_javascript('document.getElementById("spin-text").innerText="Parsing resume...";')

            # resume_text, status = extract_resume_text(_F(tmp_path, res_name))
            resume_text = extract_resume_text(tmp_path)
            if not resume_text or len(resume_text) < 50:
                ui.notify("Could not parse resume", type="negative"); return

            ui.run_javascript('document.getElementById("spin-text").innerText="Extracting with AI... (~2-3 mins on CPU)";')
            resume_json, jd_json = await asyncio.get_event_loop().run_in_executor(
                None, lambda: extract_all(resume_text, jd_text))
            if not resume_json or not jd_json:
                ui.notify("Extraction failed — check Ollama logs", type="negative"); return

            ui.run_javascript('document.getElementById("spin-text").innerText="Calculating match score...";')
            results = get_match_score(resume_json, jd_json)

            steps_el.set_content(make_steps(4))
            render_results(results_el, results, resume_json, jd_json)
            results_el.style("display:block;")

        except Exception as exc:
            ui.notify(f"Error: {exc}", type="negative")
            print(f"[JobFitAI] {exc}")

        finally:
            ui.run_javascript(
                'document.getElementById("spinner").style.display="none";'
                'document.getElementById("analyse-btn").disabled=false;'
                'document.getElementById("analyse-btn").style.opacity="1";')
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    ui.run_javascript("window._resumeTmp=null;window._resumeName=null;")
            except Exception:
                pass

    # ui.on("run_analysis", lambda: asyncio.create_task(run_analysis()))
    ui.on("run_analysis", run_analysis)

# ENTRYPOINT
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="JobFitAI", port=8080, reload=False, favicon="🎯")