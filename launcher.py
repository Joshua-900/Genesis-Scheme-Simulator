"""
GenesisScheme Script Launcher
Run this, then open http://localhost:5000 in your browser.
"""

import os
import sys
import json
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, Response

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = ROOT / ".venv" / "bin" / "python"  # Linux/macOS fallback
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

METADATA_FILE = ROOT / "scripts_metadata.json"

# ---------------------------------------------------------------------------
# Metadata store — reads/writes scripts_metadata.json
# ---------------------------------------------------------------------------

def _load_metadata() -> dict:
    if METADATA_FILE.exists():
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"scripts": {}}


def _save_metadata(data: dict) -> None:
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _empty_meta() -> dict:
    """Default metadata shape for files that have no entry yet."""
    return {
        "description": "",
        "category": "Uncategorized",
        "status": "",
        "quality": "",
        "notes": "",
        "findings": [],
        "last_modified": "",
    }


def _get_script_meta(name: str) -> dict:
    data = _load_metadata()
    return data["scripts"].get(name, _empty_meta())


def _set_script_meta(name: str, meta: dict) -> None:
    """Merge incoming meta into the existing entry rather than overwriting.

    Preserves fields the frontend doesn't know about (e.g. `findings`,
    `status` if the UI didn't send it) so they don't get clobbered on save.
    """
    data = _load_metadata()
    existing = data["scripts"].get(name, {})
    merged = {**existing, **meta}
    merged["last_modified"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["scripts"][name] = merged
    _save_metadata(data)


def _discover_scripts() -> list[str]:
    """Find all .py scripts in root that aren't launcher.py itself."""
    return sorted(
        p.name for p in ROOT.glob("*.py")
        if p.name != "launcher.py" and not p.name.startswith("_")
    )


# ---------------------------------------------------------------------------
# Process manager — one script at a time
# ---------------------------------------------------------------------------

class ProcessManager:
    def __init__(self):
        self.process = None
        self.output_lines = []
        self.lock = threading.Lock()
        self.running_script = None
        self.start_time = None

    def start(self, script_name):
        with self.lock:
            if self.process and self.process.poll() is None:
                return False, "Another script is already running"

            script_path = ROOT / script_name
            if not script_path.exists():
                return False, f"Script not found: {script_name}"

            self.output_lines = []
            self.running_script = script_name
            self.start_time = time.time()

            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"

            self.process = subprocess.Popen(
                [str(VENV_PYTHON), "-u", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(ROOT),
                text=True,
                bufsize=1,
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                if sys.platform == "win32" else 0,
            )

            thread = threading.Thread(target=self._read_output, daemon=True)
            thread.start()
            return True, f"Started {script_name}"

    def _read_output(self):
        try:
            for line in self.process.stdout:
                with self.lock:
                    self.output_lines.append(line.rstrip("\n"))
        except Exception:
            pass
        finally:
            with self.lock:
                exit_code = self.process.wait()
                elapsed = time.time() - self.start_time
                self.output_lines.append(
                    f"\n--- Process exited with code {exit_code} "
                    f"(ran for {elapsed:.1f}s) ---"
                )
                self.running_script = None

    def stop(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                if sys.platform == "win32":
                    self.process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.process.terminate()
                self.output_lines.append("\n--- Process stopped by user ---")
                self.running_script = None
                return True, "Stopped"
            return False, "No running process"

    def status(self):
        with self.lock:
            return {
                "running": self.running_script,
                "output": list(self.output_lines),
            }


pm = ProcessManager()

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

app = Flask(__name__)


@app.route("/")
def index():
    scripts = _discover_scripts()
    metadata = _load_metadata()

    groups = {}
    for name in scripts:
        meta = {**_empty_meta(), **metadata["scripts"].get(name, {})}
        cat = meta.get("category", "Uncategorized") or "Uncategorized"
        groups.setdefault(cat, []).append({"name": name, **meta})

    groups = dict(sorted(groups.items()))
    return render_template_string(HTML_TEMPLATE, categories=groups)


@app.route("/api/run/<path:script_name>", methods=["POST"])
def run_script(script_name):
    ok, msg = pm.start(script_name)
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/stop", methods=["POST"])
def stop_script():
    ok, msg = pm.stop()
    return jsonify({"ok": ok, "message": msg})


@app.route("/api/status")
def status():
    return jsonify(pm.status())


@app.route("/api/stream")
def stream():
    """SSE endpoint — pushes output lines to the browser in real time."""
    def generate():
        last_idx = 0
        while True:
            s = pm.status()
            lines = s["output"]
            if len(lines) > last_idx:
                for line in lines[last_idx:]:
                    yield f"data: {json.dumps(line)}\n\n"
                last_idx = len(lines)
            if s["running"] is None and last_idx >= len(lines):
                yield f"data: {json.dumps('__DONE__')}\n\n"
                break
            time.sleep(0.25)
    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/meta/<path:script_name>")
def get_meta(script_name):
    return jsonify(_get_script_meta(script_name))


@app.route("/api/meta/<path:script_name>", methods=["PUT"])
def set_meta(script_name):
    meta = request.get_json()
    _set_script_meta(script_name, meta)
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# HTML / CSS / JS — single-page UI with metadata editing
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GenesisScheme Launcher</title>
<style>
  :root {
    --bg: #0e1117;
    --surface: #161b22;
    --border: #30363d;
    --text: #e6edf3;
    --muted: #8b949e;
    --accent: #58a6ff;
    --green: #3fb950;
    --red: #f85149;
    --orange: #d29922;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }

  header {
    border-bottom: 1px solid var(--border);
    padding: 0.8rem 2rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  header h1 { font-size: 1.3rem; font-weight: 600; }
  .status-badge {
    font-size: 0.78rem;
    padding: 0.2rem 0.7rem;
    border-radius: 12px;
    font-weight: 500;
  }
  .status-idle    { background: var(--border); color: var(--muted); }
  .status-running { background: #1a4b2e; color: var(--green); }

  .filter-bar {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--muted);
  }
  .filter-bar select {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.25rem 0.5rem;
    font-size: 0.78rem;
    font-family: inherit;
  }

  .layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    height: calc(100vh - 52px);
  }

  .panel-scripts {
    border-right: 1px solid var(--border);
    overflow-y: auto;
    padding: 1rem 1.5rem;
  }
  .category-title {
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin: 1.2rem 0 0.4rem;
  }
  .category-title:first-child { margin-top: 0; }

  .script-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    transition: border-color 0.15s;
  }
  .script-card:hover { border-color: var(--accent); }
  .script-card.is-selected { border-color: var(--accent); background: #1c2333; }
  .script-card.is-running  { border-color: var(--green); }
  .script-card.is-hidden   { display: none; }
  .script-info { flex: 1; min-width: 0; }
  .script-info h3 {
    font-size: 0.85rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .script-info p {
    font-size: 0.75rem;
    color: var(--muted);
    margin-top: 0.1rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .script-info .quality-badge {
    display: inline-block;
    font-size: 0.68rem;
    color: var(--orange);
    margin-left: 0.4rem;
  }

  .status-pill {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.08rem 0.45rem;
    border-radius: 10px;
    margin-left: 0.45rem;
    vertical-align: middle;
    border: 1px solid transparent;
  }
  .status-active     { background: #1a4b2e; color: #3fb950; border-color: #2ea043; }
  .status-reference  { background: #1a2f4b; color: #58a6ff; border-color: #1f6feb; }
  .status-exploratory{ background: #3a2e1c; color: #d29922; border-color: #9e6a03; }
  .status-superseded { background: #2d2d35; color: #8b949e; border-color: #484f58; }
  .status-broken     { background: #4a1d22; color: #f85149; border-color: #8e1519; }

  .btn {
    border: none;
    border-radius: 6px;
    padding: 0.35rem 0.9rem;
    font-size: 0.78rem;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
    margin-left: 0.5rem;
  }
  .btn:hover { opacity: 0.85; }
  .btn-run  { background: var(--green); color: #000; }
  .btn-stop { background: var(--red); color: #fff; }
  .btn-save { background: var(--accent); color: #000; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }

  .panel-right { display: flex; flex-direction: column; overflow: hidden; }
  .tabs { display: flex; border-bottom: 1px solid var(--border); }
  .tab {
    padding: 0.5rem 1.2rem;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--muted);
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: color 0.15s, border-color 0.15s;
  }
  .tab:hover { color: var(--text); }
  .tab.active { color: var(--accent); border-bottom-color: var(--accent); }
  .tab-actions {
    margin-left: auto;
    display: flex;
    align-items: center;
    padding-right: 1rem;
    gap: 0.5rem;
  }
  .tab-pane { display: none; flex: 1; overflow: hidden; }
  .tab-pane.active { display: flex; flex-direction: column; flex: 1; }

  #console {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 1.5rem;
    font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
    font-size: 0.8rem;
    white-space: pre-wrap;
    word-break: break-all;
    background: #010409;
    color: #c9d1d9;
  }
  #console .line-error { color: var(--red); }
  #console .line-info  { color: var(--muted); font-style: italic; }

  .details-pane { flex: 1; overflow-y: auto; padding: 1.2rem 1.5rem; }
  .details-empty {
    color: var(--muted);
    font-size: 0.85rem;
    font-style: italic;
    padding-top: 2rem;
    text-align: center;
  }
  .field-group { margin-bottom: 1rem; }
  .field-group label {
    display: block;
    font-size: 0.72rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 0.3rem;
  }
  .field-group input,
  .field-group textarea,
  .field-group select {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem 0.7rem;
    color: var(--text);
    font-family: inherit;
    font-size: 0.85rem;
    resize: vertical;
    transition: border-color 0.15s;
  }
  .field-group input:focus,
  .field-group textarea:focus,
  .field-group select:focus { outline: none; border-color: var(--accent); }
  .field-group textarea { min-height: 80px; }
  .save-bar {
    padding: 0.7rem 1.5rem;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    align-items: center;
  }
  .save-status {
    font-size: 0.75rem;
    color: var(--green);
    opacity: 0;
    transition: opacity 0.3s;
  }
  .save-status.visible { opacity: 1; }
</style>
</head>
<body>

<header>
  <h1>GenesisScheme Launcher</h1>
  <span id="status-badge" class="status-badge status-idle">Idle</span>
  <div class="filter-bar">
    <label for="status-filter">Show:</label>
    <select id="status-filter" onchange="applyStatusFilter()">
      <option value="default" selected>Default (hide superseded &amp; broken)</option>
      <option value="active-only">Active only</option>
      <option value="all">All</option>
      <option value="legacy-only">Legacy only (superseded &amp; broken)</option>
    </select>
  </div>
</header>

<div class="layout">
  <div class="panel-scripts">
    {% for category, scripts in categories.items() %}
    <div class="category-title">{{ category }}</div>
    {% for s in scripts %}
    <div class="script-card" data-script="{{ s.name }}" data-status="{{ s.status or 'unset' }}" onclick="selectScript('{{ s.name }}')">
      <div class="script-info">
        <h3>{{ s.name }}{% if s.status %}<span class="status-pill status-{{ s.status }}">{{ s.status }}</span>{% endif %}{% if s.quality %}<span class="quality-badge">{{ s.quality }}</span>{% endif %}</h3>
        <p>{{ s.description }}</p>
      </div>
      <button class="btn btn-run" onclick="event.stopPropagation(); runScript('{{ s.name }}')">Run</button>
    </div>
    {% endfor %}
    {% endfor %}
  </div>

  <div class="panel-right">
    <div class="tabs">
      <div class="tab active" data-tab="output" onclick="switchTab('output')">Output</div>
      <div class="tab" data-tab="details" onclick="switchTab('details')">Details</div>
      <div class="tab-actions">
        <button class="btn btn-stop" id="btn-stop" onclick="stopScript()" disabled>Stop</button>
      </div>
    </div>

    <div class="tab-pane active" id="pane-output">
      <div id="console"><span class="line-info">Select a script to run...</span></div>
    </div>

    <div class="tab-pane" id="pane-details">
      <div class="details-pane" id="details-form">
        <div class="details-empty">Click a script to view and edit its details.</div>
      </div>
      <div class="save-bar" id="save-bar" style="display:none;">
        <span class="save-status" id="save-status">Saved</span>
        <button class="btn btn-save" onclick="saveMeta()">Save</button>
      </div>
    </div>
  </div>
</div>

<script>
  let evtSource = null;
  let currentScript = null;
  let selectedScript = null;

  function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `pane-${tab}`));
  }

  function selectScript(name) {
    selectedScript = name;
    document.querySelectorAll('.script-card').forEach(c =>
      c.classList.toggle('is-selected', c.dataset.script === name)
    );
    loadDetails(name);
    switchTab('details');
  }

  function loadDetails(name) {
    fetch(`/api/meta/${name}`)
      .then(r => r.json())
      .then(meta => {
        const form = document.getElementById('details-form');
        const statusOptions = ['', 'active', 'reference', 'exploratory', 'superseded', 'broken'];
        const statusSelect = statusOptions.map(v =>
          `<option value="${v}" ${meta.status === v ? 'selected' : ''}>${v || '(unset)'}</option>`
        ).join('');
        const findings = Array.isArray(meta.findings) ? meta.findings : [];
        const findingsHtml = findings.length
          ? `<div class="field-group">
               <label>Findings</label>
               <ul style="font-size:0.82rem; padding-left:1.1rem; color:var(--muted);">
                 ${findings.map(f => `<li><code>${esc(f)}</code></li>`).join('')}
               </ul>
             </div>`
          : '';
        form.innerHTML = `
          <h2 style="font-size:1rem; margin-bottom:1rem; color:var(--accent);">${name}</h2>
          <div class="field-group">
            <label>Status (lifecycle)</label>
            <select id="meta-status">${statusSelect}</select>
          </div>
          <div class="field-group">
            <label>Description</label>
            <input type="text" id="meta-description" value="${esc(meta.description || '')}" placeholder="What does this script do?">
          </div>
          <div class="field-group">
            <label>Category</label>
            <input type="text" id="meta-category" value="${esc(meta.category || '')}" placeholder="e.g. Animations, Quiver / Particles, Demos">
          </div>
          <div class="field-group">
            <label>Quality (correctness/confidence — reserved)</label>
            <input type="text" id="meta-quality" value="${esc(meta.quality || '')}" placeholder="e.g. stable, calibrated, suspect">
          </div>
          <div class="field-group">
            <label>Notes</label>
            <textarea id="meta-notes" placeholder="Short metadata-grade context. Longer writeups belong in findings/.">${esc(meta.notes || '')}</textarea>
          </div>
          ${findingsHtml}
          ${meta.last_modified ? `<p style="font-size:0.7rem; color:var(--muted); margin-top:0.5rem;">Last edited: ${meta.last_modified}</p>` : ''}
        `;
        document.getElementById('save-bar').style.display = 'flex';
        document.getElementById('save-status').classList.remove('visible');
      });
  }

  function saveMeta() {
    if (!selectedScript) return;
    const meta = {
      description: document.getElementById('meta-description').value,
      category: document.getElementById('meta-category').value,
      status: document.getElementById('meta-status').value,
      quality: document.getElementById('meta-quality').value,
      notes: document.getElementById('meta-notes').value,
    };
    fetch(`/api/meta/${selectedScript}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(meta),
    })
    .then(r => r.json())
    .then(() => {
      const s = document.getElementById('save-status');
      s.classList.add('visible');
      setTimeout(() => s.classList.remove('visible'), 2000);

      const card = document.querySelector(`[data-script="${selectedScript}"]`);
      if (card) {
        card.querySelector('p').textContent = meta.description;
        const h3 = card.querySelector('h3');
        h3.innerHTML = selectedScript;
        if (meta.status) {
          h3.innerHTML += `<span class="status-pill status-${esc(meta.status)}">${esc(meta.status)}</span>`;
        }
        if (meta.quality) {
          h3.innerHTML += `<span class="quality-badge">${esc(meta.quality)}</span>`;
        }
        card.dataset.status = meta.status || 'unset';
        applyStatusFilter();
      }
    });
  }

  function applyStatusFilter() {
    const mode = document.getElementById('status-filter').value;
    const visibleFor = {
      'default':     ['active', 'reference', 'exploratory', 'unset'],
      'active-only': ['active'],
      'all':         ['active', 'reference', 'exploratory', 'superseded', 'broken', 'unset'],
      'legacy-only': ['superseded', 'broken'],
    }[mode];
    document.querySelectorAll('.script-card').forEach(card => {
      const s = card.dataset.status || 'unset';
      card.classList.toggle('is-hidden', !visibleFor.includes(s));
    });
    document.querySelectorAll('.category-title').forEach(title => {
      let next = title.nextElementSibling;
      let anyVisible = false;
      while (next && next.classList.contains('script-card')) {
        if (!next.classList.contains('is-hidden')) { anyVisible = true; break; }
        next = next.nextElementSibling;
      }
      title.style.display = anyVisible ? '' : 'none';
    });
  }

  function runScript(name) {
    fetch(`/api/run/${name}`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (!data.ok) { alert(data.message); return; }
        currentScript = name;
        updateRunUI(true);
        document.getElementById('console').innerHTML = '';
        switchTab('output');
        listenStream();
      });
  }

  function stopScript() {
    fetch('/api/stop', { method: 'POST' })
      .then(r => r.json())
      .then(() => updateRunUI(false));
  }

  function listenStream() {
    if (evtSource) evtSource.close();
    evtSource = new EventSource('/api/stream');
    evtSource.onmessage = (e) => {
      const line = JSON.parse(e.data);
      if (line === '__DONE__') {
        evtSource.close();
        evtSource = null;
        updateRunUI(false);
        return;
      }
      const con = document.getElementById('console');
      const span = document.createElement('span');
      if (line.toLowerCase().includes('error') || line.toLowerCase().includes('traceback')) {
        span.className = 'line-error';
      } else if (line.startsWith('---')) {
        span.className = 'line-info';
      }
      span.textContent = line + '\n';
      con.appendChild(span);
      con.scrollTop = con.scrollHeight;
    };
  }

  function updateRunUI(running) {
    const badge = document.getElementById('status-badge');
    const stopBtn = document.getElementById('btn-stop');

    if (running) {
      badge.textContent = `Running: ${currentScript}`;
      badge.className = 'status-badge status-running';
      stopBtn.disabled = false;
    } else {
      badge.textContent = 'Idle';
      badge.className = 'status-badge status-idle';
      stopBtn.disabled = true;
      currentScript = null;
    }

    document.querySelectorAll('.script-card').forEach(card => {
      card.classList.toggle('is-running', card.dataset.script === currentScript);
    });
  }

  function esc(s) {
    const d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML.replace(/"/g, '&quot;');
  }

  applyStatusFilter();

  fetch('/api/status').then(r => r.json()).then(s => {
    if (s.running) {
      currentScript = s.running;
      updateRunUI(true);
      listenStream();
    }
  });
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    scripts = _discover_scripts()
    print(f"  Python:  {VENV_PYTHON}")
    print(f"  Root:    {ROOT}")
    print(f"  Scripts: {len(scripts)}")
    print(f"  Metadata: {METADATA_FILE}")
    print()
    app.run(debug=True, port=5000)
