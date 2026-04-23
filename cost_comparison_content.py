"""
cost_comparison_content.py
──────────────────────────────────────────────────────────────────────────────
Rich interactive HTML for the Cost Comparison page.
Called by build.py for the "cost-comparison" slug.

Exports
  build_cost_comparison_html() -> str   content HTML (goes inside <article>)
  TOC_TOKENS                            toc token list for sidebar TOC
  PLAIN_TEXT                            plain-text description for search index
"""

# ── TOC tokens (must match h2 id= attributes in the HTML below) ──────────────
TOC_TOKENS = [
    {"id": "tco-calculator",       "name": "TCO Calculator",           "level": 2, "children": []},
    {"id": "cost-per-1k-requests", "name": "Cost per 1,000 Requests",  "level": 2, "children": []},
    {"id": "36-month-cumulative",  "name": "36-Month Cumulative Cost", "level": 2, "children": []},
    {"id": "quality-vs-price",     "name": "Quality vs. Price",        "level": 2, "children": []},
    {"id": "all-api-models",       "name": "All API Models",           "level": 2, "children": []},
    {"id": "local-hardware-tco",   "name": "Local Hardware TCO",       "level": 2, "children": []},
]

PLAIN_TEXT = (
    "Cost Comparison: Local Hardware vs Cheap Cloud APIs. "
    "Practical cost and benchmark analysis — DeepSeek, Kimi, GLM, Mistral. "
    "Interactive TCO calculator, break-even analysis, quality vs price scatter chart. "
    "Hardware: Mac Mini M4 Pro, Mac Studio M4 Max, RTX 3090, RTX 4090, RTX 5090, AMD Ryzen AI Max+ 395, NVIDIA DGX Spark. "
    "APIs: GLM-4.5 Airx, Devstral Small, Mistral Small 3.2, DeepSeek V3, DeepSeek R1, "
    "Kimi K2, Kimi K2.5. Prices April 2026."
)


def build_cost_comparison_html() -> str:
    """Return standalone content HTML for the cost-comparison page.
    Goes inside <article class='prose'> — no outer wrapper needed."""

    # Using r-string so JS \uXXXX escapes are passed through verbatim to the browser.
    return r"""
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>

<style>
/* ══ Cost Comparison page components ══════════════════════════════════════════
   All selectors prefixed cc- to avoid collisions with prose styles.
   CSS variables come from the site root: --accent, --fg, --fg-2, --fg-3,
   --bg, --bg-raised, --bg-hover, --border, --border-mid, --green, --font,
   --mono, --r, --r-lg.
═══════════════════════════════════════════════════════════════════════════════ */

/* Kill .prose h2 margin-top inside our sections — sections carry their own margin */
.cc-chart-section > h2,
.cc-table-section > h2 {
  margin-top: 0 !important;
}

/* Panel heading — flush, no bottom border */
.cc-panel > h2 {
  font-size: 1em !important;
  margin-top: 0 !important;
  margin-bottom: 4px !important;
  padding-bottom: 0 !important;
  border-bottom: none !important;
}

.cc-lead {
  font-size: 1.05em;
  color: var(--fg-2);
  margin: 0 0 28px;
  line-height: 1.7;
}

/* ── TL;DR grid ─────────────────────────────────────────────────────────────── */
.cc-tldr-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 24px 0 36px;
}
@media (max-width: 600px) { .cc-tldr-grid { grid-template-columns: 1fr; } }

.cc-tldr-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 18px 20px 16px;
}
.cc-tldr-card h3 {
  font-size: .93em;
  font-weight: 600;
  margin: 0 0 10px;
  color: var(--fg);
}
.cc-tldr-card.local   h3 { color: var(--green); }
.cc-tldr-card.api-card h3 { color: var(--accent); }

.cc-tldr-card ul {
  margin: 0;
  padding: 0 0 0 18px;
  font-size: .87em;
  color: var(--fg-2);
}
.cc-tldr-card li { margin-bottom: 5px; }

/* ── Stat Row ────────────────────────────────────────────────────────────────── */
.cc-stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 0 0 40px;
}
@media (max-width: 760px) { .cc-stat-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 420px) { .cc-stat-row { grid-template-columns: 1fr; } }

.cc-stat-card {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 16px 14px;
}
.cc-stat-label {
  font-size: 10.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--fg-3);
  margin-bottom: 6px;
}
.cc-stat-value {
  font-size: 1.75em;
  font-weight: 700;
  color: var(--fg);
  line-height: 1.1;
  margin-bottom: 4px;
}
.cc-stat-unit {
  font-size: .42em;
  font-weight: 500;
  color: var(--fg-3);
}
.cc-stat-meta { font-size: 11.5px; color: var(--fg-3); }

/* ── Calculator Panel ────────────────────────────────────────────────────────── */
.cc-panel {
  background: var(--bg-raised);
  border: 1px solid var(--border-mid);
  border-radius: var(--r-lg);
  padding: 24px 24px 20px;
  margin: 32px 0 40px;
}
.cc-panel-desc {
  font-size: .87em;
  color: var(--fg-3);
  margin: 0 0 20px;
}
.cc-calc-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px 28px;
  margin-bottom: 20px;
}
@media (max-width: 600px) { .cc-calc-grid { grid-template-columns: 1fr; } }

.cc-field { display: flex; flex-direction: column; gap: 6px; }
.cc-field-lbl {
  font-size: 12px;
  font-weight: 500;
  color: var(--fg-2);
}
.cc-field-lbl strong { color: var(--accent); font-weight: 600; }

.cc-slider {
  width: 100%;
  height: 4px;
  accent-color: var(--accent);
  cursor: pointer;
  margin-top: 2px;
}
.cc-select {
  width: 100%;
  padding: 7px 30px 7px 10px;
  background: var(--bg);
  border: 1px solid var(--border-mid);
  border-radius: var(--r);
  color: var(--fg);
  font-family: var(--font);
  font-size: 13px;
  cursor: pointer;
  -webkit-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%239ca3af'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}
.cc-select:focus { outline: none; border-color: var(--accent); }

/* Result metrics */
.cc-results-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
@media (max-width: 720px) { .cc-results-row { grid-template-columns: repeat(2, 1fr); } }

.cc-res-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 12px;
  text-align: center;
  transition: border-color .2s, background .2s;
}
.cc-res-card.win {
  border-color: rgba(22, 163, 74, .35);
  background: rgba(22, 163, 74, .05);
}
.cc-res-lbl {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: var(--fg-3);
  margin-bottom: 5px;
}
.cc-res-val {
  font-size: 1.3em;
  font-weight: 700;
  color: var(--fg);
  line-height: 1.2;
  margin-bottom: 3px;
  transition: color .2s;
}
.cc-res-val.green { color: var(--green); }
.cc-res-val.muted { color: var(--fg-3); }
.cc-res-hint { font-size: 10px; color: var(--fg-3); }

/* ── Chart & Table sections ──────────────────────────────────────────────────── */
.cc-chart-section,
.cc-table-section { margin: 40px 0; }

.cc-chart-desc,
.cc-table-desc {
  font-size: .87em;
  color: var(--fg-3);
  margin: 4px 0 14px;
  line-height: 1.6;
}

.cc-chart-wrap {
  background: var(--bg-raised);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 16px 12px 12px;
  position: relative;
  overflow: hidden;
}

/* ── Comparison Tables ───────────────────────────────────────────────────────── */
.cc-table-wrap { overflow-x: auto; }

.cc-tbl {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  overflow: hidden;
}
.cc-tbl thead th {
  background: var(--bg-raised);
  padding: 9px 12px;
  text-align: left;
  font-size: 10.5px;
  font-weight: 600;
  color: var(--fg-3);
  border-bottom: 1px solid var(--border-mid);
  letter-spacing: .04em;
  text-transform: uppercase;
  white-space: nowrap;
}
.cc-tbl tbody td {
  padding: 8px 12px;
  color: var(--fg-2);
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.cc-tbl tbody tr:last-child td { border-bottom: none; }
.cc-tbl tbody tr:hover td      { background: var(--bg-hover); }
.cc-tbl td.num {
  font-variant-numeric: tabular-nums;
  font-family: var(--mono);
  font-size: .84em;
}
.cc-tbl td strong { color: var(--fg); }

.cc-badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .04em;
  white-space: nowrap;
}
.cc-badge.mistral  { background: rgba(37,99,235,.12); color: #1d4ed8; }
.cc-badge.deepseek { background: rgba(124,58,237,.12); color: #6d28d9; }
.cc-badge.kimi     { background: rgba(8,145,178,.12);  color: #0e7490; }
.cc-badge.glm      { background: rgba(217,119,6,.12);  color: #b45309; }


.cc-qwrap { display: inline-flex; align-items: center; gap: 6px; }
.cc-qbar  {
  width: 44px;
  height: 5px;
  background: var(--border);
  border-radius: 3px;
  display: inline-block;
  overflow: hidden;
  vertical-align: middle;
  flex-shrink: 0;
}
.cc-qfill {
  height: 100%;
  border-radius: 3px;
  background: var(--accent);
  display: block;
}
.cc-open-yes { color: var(--green); font-size: .84em; }
.cc-open-no  { color: var(--fg-3);  font-size: .84em; }
.cc-params   { font-size: .79em; color: var(--fg-3); font-family: var(--mono); margin-top: 1px; }
.cc-hw-runs  { font-size: .82em; color: var(--fg-3); max-width: 200px; line-height: 1.5; }

/* ── Footnote ─────────────────────────────────────────────────────────────────── */
.cc-footnote {
  margin-top: 40px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  font-size: 11.5px;
  color: var(--fg-3);
  line-height: 1.65;
}
</style>

<!-- ══════════════════════════════════════════════════════════════
     Page heading + lead
══════════════════════════════════════════════════════════════════ -->
<h1 id="cost-comparison">Cost Comparison: Local Hardware vs. Cheap Cloud APIs</h1>
<p class="cc-lead">
  Practical cost and benchmark analysis for teams choosing between self-hosted local models
  and low-cost cloud APIs &mdash; DeepSeek, Kimi, GLM, and Mistral.
  Prices and benchmarks current as of <strong>April 2026</strong>. All prices USD.
</p>

<!-- ── TL;DR Decision Cards ── -->
<div class="cc-tldr-grid">
  <div class="cc-tldr-card local">
    <h3>&#x2714;&ensp;Go Local when&hellip;</h3>
    <ul>
      <li>Privacy or air-gap required &mdash; data never leaves your network</li>
      <li>Volume &gt;&nbsp;~3M tokens/day (cheaper than most APIs at scale)</li>
      <li>First-token latency &lt;&nbsp;50&thinsp;ms needed (LAN = single-digit ms)</li>
      <li>CI/CD pipeline with 100K+ daily requests</li>
      <li>Fine-tuning control needed (LoRA/QLoRA on consumer hardware)</li>
      <li>Regulated industry &mdash; healthcare, finance, government</li>
      <li>You already own compatible hardware (zero marginal cost)</li>
    </ul>
  </div>
  <div class="cc-tldr-card api-card">
    <h3>&#x2714;&ensp;Go API when&hellip;</h3>
    <ul>
      <li>Volume &lt;&nbsp;1M tokens/day &mdash; pay-as-you-go beats upfront hardware</li>
      <li>No upfront capital available (&lt;&nbsp;$1,400 to start)</li>
      <li>Need frontier quality: DeepSeek R1 (97% MATH-500), Kimi K2.5 (77% SWE)</li>
      <li>Rapid prototyping &mdash; instant access, zero setup</li>
      <li>Solo dev or small team with light usage (&lt;&nbsp;500 req/day)</li>
      <li>Need 262K token context windows (Kimi K2.5)</li>
      <li>EU GDPR compliance required &mdash; Mistral (Paris) is the safe choice</li>
    </ul>
  </div>
</div>

<!-- ── Stat Cards ── -->
<div class="cc-stat-row">
  <div class="cc-stat-card">
    <div class="cc-stat-label">Cheapest API</div>
    <div class="cc-stat-value">$0.02<span class="cc-stat-unit">&thinsp;/M tokens in</span></div>
    <div class="cc-stat-meta">GLM-4.5 Airx &mdash; 106B/12B MoE</div>
  </div>
  <div class="cc-stat-card">
    <div class="cc-stat-label">Lowest Local TCO</div>
    <div class="cc-stat-value">$40<span class="cc-stat-unit">&thinsp;/month</span></div>
    <div class="cc-stat-meta">Mac Mini M4 Pro 24&thinsp;GB (3-yr amortized)</div>
  </div>
  <div class="cc-stat-card">
    <div class="cc-stat-label">Break-even vs. DeepSeek V3</div>
    <div class="cc-stat-value">1.5M<span class="cc-stat-unit">&thinsp;tok/day</span></div>
    <div class="cc-stat-meta">Mac Mini M4 Pro cheaper above this</div>
  </div>
  <div class="cc-stat-card">
    <div class="cc-stat-label">Cheapest / 1K Requests</div>
    <div class="cc-stat-value">$0.07</div>
    <div class="cc-stat-meta">GLM-4.5 Airx (2,048&thinsp;+&thinsp;512 tokens)</div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     TCO Calculator
══════════════════════════════════════════════════════════════════ -->
<div class="cc-panel">
  <h2 id="tco-calculator">TCO Calculator</h2>
  <p class="cc-panel-desc">Adjust your monthly volume and hardware to see break-even. All metrics update live.</p>

  <div class="cc-calc-grid">
    <div class="cc-field">
      <div class="cc-field-lbl">Monthly input volume:&ensp;<strong id="cc-vol-disp">10M tokens/mo</strong></div>
      <input type="range" id="cc-vol-slider" class="cc-slider" min="0" max="100" value="67">
    </div>
    <div class="cc-field">
      <div class="cc-field-lbl">Input&thinsp;:&thinsp;Output ratio:&ensp;<strong id="cc-ratio-disp">4&thinsp;:&thinsp;1</strong></div>
      <input type="range" id="cc-ratio-slider" class="cc-slider" min="1" max="8" value="4" step="1">
    </div>
    <div class="cc-field">
      <div class="cc-field-lbl">Local hardware</div>
      <select id="cc-hw-sel" class="cc-select"></select>
    </div>
    <div class="cc-field">
      <div class="cc-field-lbl">API to compare</div>
      <select id="cc-api-sel" class="cc-select"></select>
    </div>
  </div>

  <div class="cc-results-row">
    <div class="cc-res-card" id="cc-card-local">
      <div class="cc-res-lbl">Local cost&thinsp;/&thinsp;month</div>
      <div class="cc-res-val" id="cc-val-local">&mdash;</div>
      <div class="cc-res-hint">fixed TCO (amortized)</div>
    </div>
    <div class="cc-res-card" id="cc-card-api">
      <div class="cc-res-lbl">API cost&thinsp;/&thinsp;month</div>
      <div class="cc-res-val" id="cc-val-api">&mdash;</div>
      <div class="cc-res-hint">at this volume</div>
    </div>
    <div class="cc-res-card" id="cc-card-savings">
      <div class="cc-res-lbl">Monthly savings</div>
      <div class="cc-res-val" id="cc-val-savings">&mdash;</div>
      <div class="cc-res-hint">with local vs. API</div>
    </div>
    <div class="cc-res-card" id="cc-card-be">
      <div class="cc-res-lbl">Break-even</div>
      <div class="cc-res-val" id="cc-val-be">&mdash;</div>
      <div class="cc-res-hint">months to recoup hardware</div>
    </div>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     Chart 1 — Cost per 1K requests (static horizontal bar)
══════════════════════════════════════════════════════════════════ -->
<div class="cc-chart-section">
  <h2 id="cost-per-1k-requests">Cost per 1,000 Requests</h2>
  <p class="cc-chart-desc">
    Assuming 2,048 input + 512 output tokens per request, sorted cheapest &#8594; most expensive.
    <span style="color:#16a34a;font-weight:600">&#9679; Green = local</span> (zero marginal cost once hardware purchased),
    <span style="color:#2563eb;font-weight:600">&#9679; Blue = Mistral</span>,
    <span style="color:#7c3aed;font-weight:600">&#9679; violet = DeepSeek</span>,
    <span style="color:#0891b2;font-weight:600">&#9679; teal = Kimi</span>,
    <span style="color:#d97706;font-weight:600">&#9679; amber = GLM</span>.
  </p>
  <div class="cc-chart-wrap" style="height:470px">
    <canvas id="cc-ch-cost1k"></canvas>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     Chart 2 — 36-month cumulative cost (reactive line chart)
══════════════════════════════════════════════════════════════════ -->
<div class="cc-chart-section">
  <h2 id="36-month-cumulative">36-Month Cumulative Cost</h2>
  <p class="cc-chart-desc">
    <span style="color:#16a34a;font-weight:600">Green</span> = local hardware (upfront + monthly TCO).
    <span style="color:#2563eb;font-weight:600">Blue</span> = API (pure usage, no upfront cost).
    Where the lines cross = break-even month.
    <strong>Use the calculator above</strong> to change hardware and API selection &mdash; this chart updates live.
  </p>
  <div class="cc-chart-wrap" style="height:310px">
    <canvas id="cc-ch-cumul"></canvas>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     Chart 3 — Quality vs Price bubble chart (static)
══════════════════════════════════════════════════════════════════ -->
<div class="cc-chart-section">
  <h2 id="quality-vs-price">Quality vs. Price</h2>
  <p class="cc-chart-desc">
    Composite quality score (0&ndash;100) vs. cost per 1,000 requests.
    Top-left = ideal: high quality, low cost.
    Hover any bubble for model name and exact values.
  </p>
  <div class="cc-chart-wrap" style="height:350px">
    <canvas id="cc-ch-qual"></canvas>
  </div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     Full API comparison table (built from JS data)
══════════════════════════════════════════════════════════════════ -->
<div class="cc-table-section">
  <h2 id="all-api-models">All API Models</h2>
  <p class="cc-table-desc">
    Sorted by cost per 1,000 requests (2,048 input + 512 output tokens).
    Quality is a composite 0&ndash;100 score from MMLU-Pro, SWE-bench Verified, MATH-500, and LiveCodeBench v6.
  </p>
  <div id="cc-api-tbl"></div>
</div>

<!-- ══════════════════════════════════════════════════════════════
     Hardware TCO table (built from JS data)
══════════════════════════════════════════════════════════════════ -->
<div class="cc-table-section">
  <h2 id="local-hardware-tco">Local Hardware TCO</h2>
  <p class="cc-table-desc">
    Monthly TCO = upfront cost amortized over 36 months + electricity ($0.14/kWh, 8 h/day active inference).
    Token speed at Q4 quantization on the listed model.
  </p>
  <div id="cc-hw-tbl"></div>
</div>

<div class="cc-footnote">
  Prices verified April 2026 via official provider docs, OpenRouter, and PricePerToken.com.
  Hardware prices from eBay sold listings (used) and Apple Store (new).
  Electricity at US average $0.14/kWh (EIA 2025). Benchmark quality scores are composites &mdash;
  see the full benchmark table in the source markdown for per-benchmark breakdowns.
</div>

<!-- ══════════════════════════════════════════════════════════════
     JavaScript — single IIFE, Chart.js already loaded above
══════════════════════════════════════════════════════════════════ -->
<script>
(function () {
  'use strict';

  /* ── Data ─────────────────────────────────────────────────────────────────── */
  var APIS = [
    {id:'glm-airx',    name:'GLM-4.5 Airx',        inp:0.020, out:0.060, quality:70, ctx:'128K', params:'106B/12B MoE',  open:true,  lic:'Apache 2.0',  provider:'glm'},
    {id:'devstral',    name:'Devstral Small',        inp:0.060, out:0.120, quality:76, ctx:'128K', params:'24B dense',    open:true,  lic:'Apache 2.0',  provider:'mistral'},
    {id:'mistral-sm',  name:'Mistral Small 3.2',     inp:0.075, out:0.200, quality:78, ctx:'128K', params:'24B dense',    open:true,  lic:'Apache 2.0',  provider:'mistral'},
    {id:'glm-air',     name:'GLM-4.5 Air',           inp:0.160, out:1.070, quality:74, ctx:'128K', params:'106B/12B MoE', open:true,  lic:'Apache 2.0',  provider:'glm'},
    {id:'ds-v3-hit',   name:'DeepSeek V3 (cached)',  inp:0.070, out:1.100, quality:82, ctx:'128K', params:'671B/37B MoE', open:true,  lic:'MIT',         provider:'deepseek'},
    {id:'ds-v3',       name:'DeepSeek V3',           inp:0.270, out:1.100, quality:82, ctx:'128K', params:'671B/37B MoE', open:true,  lic:'MIT',         provider:'deepseek'},
    {id:'kimi-k2',     name:'Kimi K2',               inp:0.150, out:2.000, quality:83, ctx:'128K', params:'~1T/32B MoE',  open:true,  lic:'MIT',         provider:'kimi'},
    {id:'mistral-med', name:'Mistral Medium 3',       inp:0.400, out:2.000, quality:80, ctx:'128K', params:'~56B dense',   open:true,  lic:'Apache 2.0',  provider:'mistral'},
    {id:'glm-std',     name:'GLM-4.5 Standard',      inp:0.480, out:1.920, quality:86, ctx:'128K', params:'355B/32B MoE', open:true,  lic:'Apache 2.0',  provider:'glm'},
    {id:'mistral-lg',  name:'Mistral Large 3',        inp:0.500, out:1.500, quality:83, ctx:'128K', params:'~123B MoE',    open:true,  lic:'Apache 2.0',  provider:'mistral'},
    {id:'ds-r1-hit',   name:'DeepSeek R1 (cached)',  inp:0.140, out:2.190, quality:90, ctx:'64K',  params:'671B/37B MoE', open:true,  lic:'MIT',         provider:'deepseek'},
    {id:'ds-r1',       name:'DeepSeek R1',           inp:0.550, out:2.190, quality:90, ctx:'64K',  params:'671B/37B MoE', open:true,  lic:'MIT',         provider:'deepseek'},
    {id:'kimi-k25',    name:'Kimi K2.5',             inp:0.600, out:2.800, quality:87, ctx:'262K', params:'~1T/32B MoE',  open:false, lic:'Proprietary', provider:'kimi'}
  ];

  var HW = [
    {id:'mac-mini',     name:'Mac Mini M4 Pro (24 GB)',   monthly:40,  upfront:1399, vram:24,  tps:40,  runs:'Gemma 4 26B Q4 \u00b7 Qwen3.5 27B Q4'},
    {id:'mac-mini48',   name:'Mac Mini M4 Pro (48 GB)',   monthly:51,  upfront:1799, vram:48,  tps:42,  runs:'Qwen3.6 35B-A3B Q6'},
    {id:'mac-studio',   name:'Mac Studio M4 Max (36 GB)', monthly:59,  upfront:1999, vram:36,  tps:50,  runs:'Qwen3.6 35B-A3B Q4 \u00b7 Qwen3.5 27B Q8'},
    {id:'mac-studio64', name:'Mac Studio M4 Max (64 GB)', monthly:82,  upfront:2799, vram:64,  tps:55,  runs:'Qwen3.6 35B-A3B Q8 \u00b7 122B Q2'},
    {id:'rtx3090',      name:'RTX 3090 build (24 GB)',    monthly:56,  upfront:1400, vram:24,  tps:65,  runs:'Qwen3.5 27B Q4 \u00b7 Gemma 4 26B Q4'},
    {id:'rtx4090',      name:'RTX 4090 build (24 GB)',    monthly:72,  upfront:1800, vram:24,  tps:75,  runs:'Qwen3.5 27B Q4 \u00b7 Gemma 4 26B Q4'},
    {id:'rtx5090',      name:'RTX 5090 build (32 GB)',    monthly:102, upfront:2700, vram:32,  tps:100, runs:'Qwen3.6 35B-A3B Q4 \u2014 full GPU offload'},
    {id:'amd-max395',   name:'AMD Ryzen AI Max+ 395 (128 GB)', monthly:87,  upfront:3000, vram:128, tps:50,  runs:'Qwen3.6 35B-A3B Q6 \u00b7 Qwen3.6-27B Q8 \u2014 Strix Halo APU'},
    {id:'dgx-spark',    name:'NVIDIA DGX Spark (128 GB)',       monthly:139, upfront:4699, vram:128, tps:80,  runs:'70B Q4 \u00b7 Qwen3.6-27B Q8 \u00b7 up to 200B (GB10 Blackwell)'}
  ];

  /* ── Helpers ──────────────────────────────────────────────────────────────── */

  function fmt(n) {
    if (n === 0) return '$0';
    if (n < 0.001) return '$' + n.toFixed(5);
    if (n < 1)     return '$' + n.toFixed(3);
    if (n < 100)   return '$' + n.toFixed(2);
    if (n < 1000)  return '$' + Math.round(n);
    return '$' + n.toLocaleString('en-US', {maximumFractionDigits: 0});
  }

  function fmtVol(v) {
    if (v >= 10e6)  return Math.round(v / 1e6) + 'M tokens/mo';
    if (v >= 1e6)   return (Math.round(v / 1e5) / 10) + 'M tokens/mo';
    return Math.round(v / 1e3) + 'K tokens/mo';
  }

  /* 2,048 input + 512 output tokens per 1,000 requests */
  function cost1k(api) {
    return api.inp * 2.048 + api.out * 0.512;
  }

  function apiMonthlyCost(api, inputVol, ratio) {
    return (inputVol / 1e6) * api.inp + ((inputVol / ratio) / 1e6) * api.out;
  }

  /* log-scale: slider 0-100 maps to 100K-100M tokens */
  function volFromSlider(v) {
    return Math.pow(10, 5 + (v / 100) * 3);
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function findBy(arr, id) {
    for (var i = 0; i < arr.length; i++) {
      if (arr[i].id === id) return arr[i];
    }
    return arr[0];
  }

  /* ── Populate selects ─────────────────────────────────────────────────────── */
  var hwSel  = document.getElementById('cc-hw-sel');
  var apiSel = document.getElementById('cc-api-sel');

  HW.forEach(function (h) {
    var o = document.createElement('option');
    o.value = h.id;
    o.textContent = h.name + '  \u2014  $' + h.monthly + '/mo';
    hwSel.appendChild(o);
  });

  APIS.forEach(function (a) {
    var o = document.createElement('option');
    o.value = a.id;
    o.textContent = a.name + '  ($' + a.inp.toFixed(3) + ' / $' + a.out.toFixed(3) + ' per M)';
    apiSel.appendChild(o);
  });

  hwSel.value  = 'mac-mini';
  apiSel.value = 'ds-v3';

  /* ── Chart helpers ────────────────────────────────────────────────────────── */
  var CHART_OPTS = {
    gridColor:   'rgba(0,0,0,0.04)',
    tickColor:   '#6b7280',
    labelColor:  '#9ca3af',
    tickFont:    {size: 11},
    labelFont:   {size: 11},
    legendFont:  {size: 12}
  };

  /* ── Chart 1: Cost per 1K requests — horizontal bar (static) ─────────────── */
  (function () {
    var sorted = APIS.slice().sort(function (a, b) { return cost1k(a) - cost1k(b); });

    var labels = ['Local (marginal $0)'].concat(
      sorted.map(function (a) { return a.name; })
    );
    var values = [0].concat(sorted.map(cost1k));
    var bgCols = ['rgba(22,163,74,0.85)'].concat(
      sorted.map(function (a) {
        var pc={deepseek:'rgba(124,58,237,0.82)',kimi:'rgba(8,145,178,0.82)',glm:'rgba(217,119,6,0.82)',mistral:'rgba(37,99,235,0.82)'}; return pc[a.provider]||'rgba(150,150,150,0.82)';
      })
    );
    var bdCols = ['#16a34a'].concat(
      sorted.map(function (a) {
        var pc={deepseek:'#7c3aed',kimi:'#0891b2',glm:'#d97706',mistral:'#2563eb'}; return pc[a.provider]||'#888';
      })
    );

    var ctx = document.getElementById('cc-ch-cost1k').getContext('2d');
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: bgCols,
          borderColor: bdCols,
          borderWidth: 1,
          borderRadius: 3,
          borderSkipped: false
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {display: false},
          tooltip: {
            callbacks: {
              label: function (ctx) {
                var v = ctx.raw;
                return v === 0
                  ? '  Free \u2014 zero marginal cost once hardware purchased'
                  : '  $' + v.toFixed(3) + ' per 1,000 requests';
              }
            }
          }
        },
        scales: {
          x: {
            grid: {color: CHART_OPTS.gridColor},
            ticks: {
              callback: function (v) { return '$' + v.toFixed(2); },
              color: CHART_OPTS.tickColor,
              font: CHART_OPTS.tickFont
            },
            title: {
              display: true,
              text: 'Cost per 1,000 requests  (2,048 input + 512 output tokens)',
              color: CHART_OPTS.labelColor,
              font: CHART_OPTS.labelFont
            }
          },
          y: {
            grid: {display: false},
            ticks: {color: '#374151', font: {size: 11.5}}
          }
        }
      }
    });
  }());

  /* ── Chart 2: 36-month cumulative cost — line chart (reactive) ───────────── */
  var cumulChart;
  (function () {
    var labels = [];
    for (var i = 0; i <= 36; i++) { labels.push(i); }

    var ctx = document.getElementById('cc-ch-cumul').getContext('2d');
    cumulChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Local hardware',
            data: new Array(37).fill(0),
            borderColor: '#16a34a',
            backgroundColor: 'rgba(22,163,74,0.08)',
            fill: true,
            tension: 0.05,
            pointRadius: 0,
            borderWidth: 2.5
          },
          {
            label: 'API cost',
            data: new Array(37).fill(0),
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37,99,235,0.08)',
            fill: true,
            tension: 0.05,
            pointRadius: 0,
            borderWidth: 2.5
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {intersect: false, mode: 'index'},
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              boxWidth: 10,
              padding: 16,
              font: CHART_OPTS.legendFont
            }
          },
          tooltip: {
            callbacks: {
              title: function (items) { return 'Month ' + items[0].label; },
              label: function (ctx) {
                return '  ' + ctx.dataset.label + ': $' +
                  Math.round(ctx.raw).toLocaleString('en-US');
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Month',
              color: CHART_OPTS.labelColor,
              font: CHART_OPTS.labelFont
            },
            grid: {color: CHART_OPTS.gridColor},
            ticks: {color: CHART_OPTS.tickColor, font: CHART_OPTS.tickFont}
          },
          y: {
            title: {
              display: true,
              text: 'Cumulative cost (USD)',
              color: CHART_OPTS.labelColor,
              font: CHART_OPTS.labelFont
            },
            grid: {color: CHART_OPTS.gridColor},
            ticks: {
              callback: function (v) {
                if (v >= 1000) return '$' + (v / 1000).toFixed(0) + 'K';
                return '$' + v;
              },
              color: CHART_OPTS.tickColor,
              font: CHART_OPTS.tickFont
            }
          }
        }
      }
    });
  }());

  /* ── Chart 3: Quality vs Price — bubble chart (static) ───────────────────── */
  (function () {
    var eu = APIS.filter(function (a) { return a.provider === 'mistral'; })
        .map(function (a) { return { x: cost1k(a), y: a.quality, r: 8, _name: a.name }; });

    var ds = APIS.filter(function (a) { return a.provider === 'deepseek'; })
        .map(function (a) { return { x: cost1k(a), y: a.quality, r: 8, _name: a.name }; });
    var kimi = APIS.filter(function (a) { return a.provider === 'kimi'; })
        .map(function (a) { return { x: cost1k(a), y: a.quality, r: 8, _name: a.name }; });
                 .map(function (a) { return {x: cost1k(a), y: a.quality, r: 8, name: a.name}; });

    var ctx = document.getElementById('cc-ch-qual').getContext('2d');
    new Chart(ctx, {
      type: 'bubble',
      data: {
        datasets: [
          {label:'Mistral',  data:eu,   backgroundColor:'rgba(37,99,235,0.78)',  borderColor:'#2563eb', borderWidth:1.5},
          {label:'DeepSeek', data:ds,   backgroundColor:'rgba(124,58,237,0.78)', borderColor:'#7c3aed', borderWidth:1.5},
          {label:'Kimi',     data:kimi, backgroundColor:'rgba(8,145,178,0.78)',  borderColor:'#0891b2', borderWidth:1.5},
          {label:'GLM',      data:glm,  backgroundColor:'rgba(217,119,6,0.78)',  borderColor:'#d97706', borderWidth:1.5}
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {boxWidth: 10, padding: 16, font: CHART_OPTS.legendFont}
          },
          tooltip: {
            callbacks: {
              label: function (ctx) {
                return '  ' + ctx.raw.name +
                  '  \u2014  $' + ctx.raw.x.toFixed(3) + '/1K req' +
                  '  \u00b7  quality ' + ctx.raw.y + '/100';
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Cost per 1,000 requests ($)',
              color: CHART_OPTS.labelColor,
              font: CHART_OPTS.labelFont
            },
            grid: {color: CHART_OPTS.gridColor},
            ticks: {
              callback: function (v) { return '$' + v.toFixed(2); },
              color: CHART_OPTS.tickColor,
              font: CHART_OPTS.tickFont
            }
          },
          y: {
            min: 65,
            max: 95,
            title: {
              display: true,
              text: 'Quality Score (0\u2013100 composite)',
              color: CHART_OPTS.labelColor,
              font: CHART_OPTS.labelFont
            },
            grid: {color: CHART_OPTS.gridColor},
            ticks: {color: CHART_OPTS.tickColor, font: CHART_OPTS.tickFont}
          }
        }
      }
    });
  }());

  /* ── Build API comparison table ───────────────────────────────────────────── */
  (function () {
    var sorted = APIS.slice().sort(function (a, b) { return cost1k(a) - cost1k(b); });

    var rows = sorted.map(function (a) {
      var c   = cost1k(a);
      var qn  = a.quality;
      /* normalise quality 65-95 to 0-100% for the bar */
      var qp  = Math.min(100, Math.max(0, Math.round((qn - 65) / 30 * 100)));
      var badge = '<span class="cc-badge ' + a.type + '">' +
        ({'mistral':'Mistral','deepseek':'DeepSeek','kimi':'Kimi','glm':'GLM'}[a.provider]||a.provider) + '</span>';
      var openHtml = a.open
        ? '<span class="cc-open-yes">Open &middot; ' + esc(a.lic) + '</span>'
        : '<span class="cc-open-no">Closed</span>';
      return '<tr>' +
        '<td><strong>' + esc(a.name) + '</strong>' +
          '<div class="cc-params">' + esc(a.params) + '</div></td>' +
        '<td>' + badge + '</td>' +
        '<td class="num">$' + a.inp.toFixed(3) + '</td>' +
        '<td class="num">$' + a.out.toFixed(3) + '</td>' +
        '<td class="num"><strong>$' + c.toFixed(3) + '</strong></td>' +
        '<td>' +
          '<span class="cc-qwrap">' +
            '<span style="min-width:22px;display:inline-block;font-variant-numeric:tabular-nums;font-size:.87em">' +
              qn +
            '</span>' +
            '<span class="cc-qbar"><span class="cc-qfill" style="width:' + qp + '%"></span></span>' +
          '</span>' +
        '</td>' +
        '<td class="num">' + esc(a.ctx) + '</td>' +
        '<td>' + openHtml + '</td>' +
        '</tr>';
    }).join('');

    document.getElementById('cc-api-tbl').innerHTML =
      '<div class="cc-table-wrap">' +
      '<table class="cc-tbl">' +
      '<thead><tr>' +
        '<th>Model</th>' +
        '<th>Type</th>' +
        '<th>Input&nbsp;$/M</th>' +
        '<th>Output&nbsp;$/M</th>' +
        '<th>Cost&nbsp;/&nbsp;1K&nbsp;req</th>' +
        '<th>Quality</th>' +
        '<th>Context</th>' +
        '<th>Weights</th>' +
      '</tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
      '</table></div>';
  }());

  /* ── Build hardware TCO table ─────────────────────────────────────────────── */
  (function () {
    var rows = HW.map(function (h) {
      return '<tr>' +
        '<td><strong>' + esc(h.name) + '</strong></td>' +
        '<td class="num">' + h.vram + '&thinsp;GB</td>' +
        '<td class="num">$' + h.upfront.toLocaleString('en-US') + '</td>' +
        '<td class="num"><strong>$' + h.monthly + '/mo</strong></td>' +
        '<td class="num">~' + h.tps + '&thinsp;tok/s</td>' +
        '<td><div class="cc-hw-runs">' + esc(h.runs) + '</div></td>' +
        '</tr>';
    }).join('');

    document.getElementById('cc-hw-tbl').innerHTML =
      '<div class="cc-table-wrap">' +
      '<table class="cc-tbl">' +
      '<thead><tr>' +
        '<th>Hardware</th>' +
        '<th>VRAM</th>' +
        '<th>Upfront</th>' +
        '<th>Monthly TCO</th>' +
        '<th>Token Speed</th>' +
        '<th>What it runs</th>' +
      '</tr></thead>' +
      '<tbody>' + rows + '</tbody>' +
      '</table></div>';
  }());

  /* ── Calculator update (reactive) ────────────────────────────────────────── */
  function updateCalc() {
    var volV   = parseInt(document.getElementById('cc-vol-slider').value,   10);
    var ratioV = parseInt(document.getElementById('cc-ratio-slider').value, 10);
    var hw  = findBy(HW,   hwSel.value);
    var api = findBy(APIS, apiSel.value);

    var vol = volFromSlider(volV);
    document.getElementById('cc-vol-disp').textContent   = fmtVol(vol);
    document.getElementById('cc-ratio-disp').textContent = ratioV + '\u2009:\u20091';

    var apiCost   = apiMonthlyCost(api, vol, ratioV);
    var localCost = hw.monthly;
    var savings   = apiCost - localCost;
    var localWins = savings > 0;

    document.getElementById('cc-val-local').textContent = fmt(localCost) + '/mo';
    document.getElementById('cc-val-api').textContent   = fmt(apiCost)   + '/mo';

    var savEl   = document.getElementById('cc-val-savings');
    var beEl    = document.getElementById('cc-val-be');
    var savCard = document.getElementById('cc-card-savings');
    var beCard  = document.getElementById('cc-card-be');

    if (localWins) {
      savEl.textContent = fmt(savings) + '/mo';
      savEl.className   = 'cc-res-val green';
      savCard.className = 'cc-res-card win';

      var beMos  = hw.upfront / savings;
      var beText = beMos < 1   ? '< 1 month'
                 : beMos < 1.5 ? '1 month'
                 : Math.ceil(beMos) + ' months';
      beEl.textContent = beText;
      beEl.className   = 'cc-res-val' + (beMos <= 6 ? ' green' : '');
      beCard.className = 'cc-res-card' + (beMos <= 6 ? ' win' : '');
    } else {
      savEl.textContent = 'API wins';
      savEl.className   = 'cc-res-val muted';
      savCard.className = 'cc-res-card';
      beEl.textContent  = '\u2014';
      beEl.className    = 'cc-res-val muted';
      beCard.className  = 'cc-res-card';
    }

    /* ── update cumulative break-even chart ── */
    if (cumulChart) {
      var ld = [], ad = [];
      for (var m = 0; m <= 36; m++) {
        ld.push(hw.upfront + m * hw.monthly);
        ad.push(m * apiCost);
      }
      cumulChart.data.datasets[0].data  = ld;
      cumulChart.data.datasets[0].label = hw.name + ' (local)';
      cumulChart.data.datasets[1].data  = ad;
      cumulChart.data.datasets[1].label = api.name + ' (API)';
      cumulChart.update('none');
    }
  }

  /* ── Wire up event listeners ──────────────────────────────────────────────── */
  document.getElementById('cc-vol-slider').addEventListener('input',   updateCalc);
  document.getElementById('cc-ratio-slider').addEventListener('input', updateCalc);
  hwSel.addEventListener('change',  updateCalc);
  apiSel.addEventListener('change', updateCalc);

  /* ── Initial render ───────────────────────────────────────────────────────── */
  updateCalc();

}()); /* end IIFE */
</script>
"""
