# src/frontend/layout.py
# HTML shell — page, shell card, topbar, sidebar, main area

from src.utils.router import ACTIVE_PROVIDER
from src.utils.config import PROVIDER_CONFIGS

# Get model name for active provider
_MODEL = PROVIDER_CONFIGS.get(ACTIVE_PROVIDER, {}).get("model", "")


def render_topbar(llm_ok):
    bc     = "bon"    if llm_ok else "boff"
    status = "online" if llm_ok else "offline"
    blb    = f"{ACTIVE_PROVIDER} {status}"

    return f"""
    <div class="jfai-topbar">
      <div class="logo-mark">J</div>
      <span class="logo-name">Job<em>Fit</em>AI</span>
      <div class="topbar-r">
        <div class="t-chip">
          <span class="t-bead {bc}"></span>{blb}
        </div>
        <div class="t-chip">{_MODEL}</div>
        <button class="theme-btn" id="themechange">☀️</button>
      </div>
    </div>
    """


def render_sidebar():
    return """
    <div class="jfai-sidebar">
      <div class="sb-sec">Navigation</div>
      <div class="sb-item active">🎯 Analyzer</div>
      <div class="sb-item">📊 History</div>
      <div class="sb-item">⚙️ Settings</div>
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