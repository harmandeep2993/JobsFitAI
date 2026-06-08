# src/frontend/layout.py
# HTML shell — page, shell card, topbar, sidebar, main area

from src.utils import session


def render_topbar(llm_ok):
    provider = session.get_provider()
    model    = session.get_model()

    bc     = "bon"    if llm_ok else "boff"
    status = "online" if llm_ok else "offline"

    return f"""
    <div class="jfai-topbar">
      <div class="logo-mark">J</div>
      <span class="logo-name">Job<em>Fit</em>AI</span>
      <div class="topbar-r">
        <div class="t-chip">
          <span class="t-bead {bc}" id="tb-bead"></span><span id="tb-provider">{provider} {status}</span>
        </div>
        <div class="t-chip" id="tb-model">{model}</div>
        <button class="theme-btn" id="themechange">☀️</button>
      </div>
    </div>
    """


def render_sidebar():
    return """
    <div class="jfai-sidebar">
      <div class="sb-sec">Navigation</div>
      <div class="sb-item active" id="nav-analyzer" onclick="showView('analyzer')">🎯 Analyzer</div>
      <div class="sb-item" id="nav-matches" onclick="showView('matches')">📈 Job Matches</div>
      <div class="sb-item" id="nav-history" onclick="showView('history')">📊 History</div>
      <div class="sb-item" id="nav-settings" onclick="showView('settings')">⚙️ Settings</div>
      <div class="sb-rule"></div>
      <div class="sb-sec">About</div>
      <div class="sb-meta">
        Resume match scoring<br>via local LLM +<br>semantic similarity
      </div>
      <div class="sb-foot">v1.0.0 · local</div>
    </div>
    """


def render_shell(llm_ok):
    return f"""
    <div class="jfai-page">
      <div class="jfai-shell">
        {render_topbar(llm_ok)}
        <div class="jfai-body">
          {render_sidebar()}
          <div class="jfai-main" id="jfai-main"></div>
        </div>
      </div>
    </div>
    """


TELEPORT_JS = """
<script>
(function move() {
  var src = document.getElementById("ng-main-content");
  var dst = document.getElementById("jfai-main");
  if (src && dst) {
    dst.appendChild(src);
  } else {
    setTimeout(move, 30);
  }
})();
</script>
"""