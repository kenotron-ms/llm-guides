#!/usr/bin/env python3
"""
build.py — Static site generator for llm-guides
────────────────────────────────────────────────────────
Requires:  pip install markdown
Output:    ./dist/
Serve:     cd dist && python3 -m http.server 3000
           → open http://localhost:3000
"""
import os, re, json, shutil, sys, textwrap
from pathlib import Path

try:
    import markdown as md_module
    from markdown.extensions.toc import TocExtension
except ImportError:
    sys.exit("Missing dependency — run:  pip install markdown")

# ─── Site config ──────────────────────────────────────────────────────────────
SITE_NAME    = "LLM Guides"
SITE_TAGLINE = "Open-source models, local inference, real savings"
REPO_URL     = "https://github.com/kenotron-ms/llm-guides"
SRC_DIR      = Path(".")
DIST_DIR     = Path("dist")


PICKER_HTML = (
    '<div class="path-picker" id="path-picker">'
    '<span class="picker-label">Showing for</span>'
    '<div class="picker-group">'
    '<span class="picker-group-name">Hardware</span>'
    '<div class="picker-pills">'
    '<button class="picker-pill" data-dim="hardware" data-val="cuda">NVIDIA</button>'
    '<button class="picker-pill" data-dim="hardware" data-val="rocm">AMD</button>'
    '<button class="picker-pill" data-dim="hardware" data-val="apple">Apple Silicon</button>'
    '</div></div>'
    '<span class="picker-group-sep">&middot;</span>'
    '<div class="picker-group">'
    '<span class="picker-group-name">Backend</span>'
    '<div class="picker-pills">'
    '<button class="picker-pill" data-dim="backend" data-val="ollama">Ollama</button>'
    '<button class="picker-pill" data-dim="backend" data-val="llamacpp">llama-server</button>'
    '<button class="picker-pill" data-dim="backend" data-val="vllm">vLLM</button>'
    '<button class="picker-pill" data-dim="backend" data-val="lmstudio">LM Studio</button>'
    '</div></div>'
    '</div>'
)

PICKER_HTML_OS = (
    '<div class="path-picker" id="path-picker">'
    '<span class="picker-label">Showing for</span>'
    '<div class="picker-group">'
    '<span class="picker-group-name">OS</span>'
    '<div class="picker-pills">'
    '<button class="picker-pill" data-dim="os" data-val="mac">macOS</button>'
    '<button class="picker-pill" data-dim="os" data-val="linux">Linux</button>'
    '<button class="picker-pill" data-dim="os" data-val="windows">Windows</button>'
    '</div></div>'
    '</div>'
)

def is_guide_page(slug: str) -> bool:
    return slug == "agent-integration" or slug.startswith("backends/")


NAV = [
    {
        "section": "Getting Started",
        "items": [
            {"title": "Overview", "file": "README.md",          "slug": "index"},
            {"title": "Cost Comparison", "file": "cost-comparison.md", "slug": "cost-comparison"},
        ],
    },
    {
        "section": "Models",
        "items": [
            {"title": "Gemma 4", "file": "models/gemma4.md",  "slug": "models/gemma4"},
            {"title": "Qwen 3.5", "file": "models/qwen3.5.md", "slug": "models/qwen3.5"},
            {"title": "Qwen 3.6", "file": "models/qwen3.6.md", "slug": "models/qwen3.6"},
        ],
    },
    {
        "section": "Backends",
        "items": [
            {"title": "Ollama", "file": "backends/ollama.md",    "slug": "backends/ollama"},
            {"title": "llama.cpp", "file": "backends/llama-cpp.md", "slug": "backends/llama-cpp"},
            {"title": "vLLM", "file": "backends/vllm.md",      "slug": "backends/vllm"},
            {"title": "LM Studio", "file": "backends/lmstudio.md",  "slug": "backends/lmstudio"},
        ],
    },
    {
        "section": "Hardware",
        "items": [
            {"title": "CUDA (NVIDIA)", "file": "hardware/cuda.md", "slug": "hardware/cuda"},
            {"title": "ROCm (AMD)", "file": "hardware/rocm.md", "slug": "hardware/rocm"},
            {"title": "MLX (Apple Silicon)", "file": "hardware/mlx.md",  "slug": "hardware/mlx"},
        ],
    },
    {
        "section": "Guides",
        "items": [
            {"title": "Agent Integration", "file": "agent-integration.md", "slug": "agent-integration"},
        ],
    },
]

ALL_PAGES   = [item for sec in NAV for item in sec["items"]]
PAGE_BY_FILE = {p["file"]: p for p in ALL_PAGES}
PAGE_BY_SLUG = {p["slug"]: p for p in ALL_PAGES}

# ─── Helpers ──────────────────────────────────────────────────────────────────
def root_prefix(slug: str) -> str:
    depth = slug.count("/")
    return "../" * depth if depth else "./"

def href(from_slug: str, to_slug: str) -> str:
    root = root_prefix(from_slug)
    return f"{root}{to_slug}.html"

def strip_md(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`[^`\n]+`", " ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~|>#\-=]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# ─── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}

    :root{
      --bg:        #ffffff;
      --bg-nav:    #f9fafb;
      --bg-raised: #f3f4f6;
      --bg-code:   #f8fafc;
      --bg-hover:  rgba(0,0,0,0.03);
      --bg-active: rgba(37,99,235,0.06);
      --border:    #e5e7eb;
      --border-mid:#d1d5db;
      --fg:        #111827;
      --fg-2:      #374151;
      --fg-3:      #9ca3af;
      --accent:    #2563eb;
      --accent-hi: #1d4ed8;
      --accent-lo: rgba(37,99,235,0.08);
      --code-fg:   #0369a1;
      --green:     #16a34a;
      --nav-w:     240px;
      --toc-w:     200px;
      --hdr-h:     52px;
      --r:         5px;
      --r-lg:      8px;
      --font:      'Inter',system-ui,-apple-system,sans-serif;
      --mono:      'JetBrains Mono','Fira Code',ui-monospace,monospace;
    }

    html{scroll-behavior:smooth;scroll-padding-top:68px}
    body{font-family:var(--font);background:var(--bg);color:var(--fg);font-size:15px;line-height:1.7;min-height:100vh;overflow-x:hidden}

    ::-webkit-scrollbar{width:4px;height:4px}
    ::-webkit-scrollbar-track{background:transparent}
    ::-webkit-scrollbar-thumb{background:var(--border-mid);border-radius:2px}
    ::-webkit-scrollbar-thumb:hover{background:var(--fg-3)}

    /* ─── Header ────────────────────────────────────── */
    .site-header{
      position:fixed;top:0;left:0;right:0;z-index:100;
      height:var(--hdr-h);
      display:flex;align-items:center;gap:16px;padding:0 20px;
      background:rgba(255,255,255,.96);
      backdrop-filter:blur(8px);
      border-bottom:1px solid var(--border);
    }
    .logo{
      display:flex;align-items:center;
      text-decoration:none;flex-shrink:0;
      width:calc(var(--nav-w) - 20px);
    }
    .logo-name{font-size:14px;font-weight:600;color:var(--fg);white-space:nowrap;letter-spacing:-.01em}
    .hdr-center{flex:1;display:flex;justify-content:center}
    .search-pill{
      display:flex;align-items:center;gap:8px;
      padding:6px 12px;max-width:380px;width:100%;
      background:var(--bg-raised);border:1px solid var(--border-mid);border-radius:var(--r);
      cursor:pointer;transition:.12s border-color;
      color:var(--fg-3);font-size:13px;font-family:var(--font);
      text-align:left;
    }
    .search-pill:hover{border-color:var(--accent)}
    .search-pill svg{flex-shrink:0}
    .search-pill-text{flex:1}
    .search-kbds{display:flex;gap:3px;margin-left:auto;flex-shrink:0}
    .kbd{
      font-size:10px;font-family:var(--mono);
      background:var(--bg);border:1px solid var(--border-mid);
      border-radius:3px;padding:1px 5px;color:var(--fg-3);
    }
    .hdr-links{display:flex;align-items:center;gap:4px;margin-left:auto}
    .hdr-link{
      display:flex;align-items:center;gap:6px;
      padding:5px 10px;border-radius:var(--r);
      color:var(--fg-3);font-size:13px;font-weight:500;
      text-decoration:none;transition:.1s;
    }
    .hdr-link:hover{color:var(--fg);background:var(--bg-hover)}
    .menu-btn{
      display:none;background:none;border:none;
      padding:8px;cursor:pointer;color:var(--fg-3);border-radius:var(--r);
    }
    .menu-btn:hover{background:var(--bg-hover);color:var(--fg)}

    /* ─── Layout ────────────────────────────────────── */
    .layout{display:flex;padding-top:var(--hdr-h);min-height:100vh}

    /* ─── Sidebar ───────────────────────────────────── */
    .sidebar{
      position:fixed;top:var(--hdr-h);left:0;bottom:0;
      width:var(--nav-w);overflow-y:auto;
      background:var(--bg-nav);border-right:1px solid var(--border);
      padding:20px 0 48px;z-index:80;
      transition:transform .2s ease;
    }
    .nav-section{margin-bottom:8px}
    .nav-label{
      display:block;padding:10px 16px 4px;
      font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
      color:var(--fg-3);
    }
    .nav-item{
      display:block;
      padding:6px 16px;margin:0 8px;border-radius:var(--r);
      font-size:13.5px;font-weight:400;color:var(--fg-2);
      text-decoration:none;transition:.1s;
    }
    .nav-item:hover{background:var(--bg-hover);color:var(--fg)}
    .nav-item.active{background:var(--bg-active);color:var(--accent);font-weight:500}
    .sidebar-footer{
      position:absolute;bottom:0;left:0;right:0;
      padding:12px 16px;border-top:1px solid var(--border);
      font-size:11.5px;color:var(--fg-3);
    }
    .sidebar-footer a{color:var(--accent);text-decoration:none}
    .sidebar-footer a:hover{text-decoration:underline}
    .sidebar-overlay{
      display:none;position:fixed;inset:0;z-index:70;
      background:rgba(0,0,0,.4);
    }

    /* ─── Content ───────────────────────────────────── */
    .content-wrap{flex:1;margin-left:var(--nav-w);margin-right:var(--toc-w);min-width:0}
    .content{max-width:760px;margin:0 auto;padding:44px 40px 80px}

    /* breadcrumb */
    .breadcrumb{
      display:flex;align-items:center;gap:6px;
      font-size:12.5px;color:var(--fg-3);margin-bottom:24px;
    }
    .breadcrumb a{color:var(--fg-3);text-decoration:none}
    .breadcrumb a:hover{color:var(--fg-2)}
    .bc-sep{opacity:.5}
    .bc-cur{color:var(--fg-2)}

    /* ─── Prose ──────────────────────────────────────── */
    .prose h1{
      font-size:1.85em;font-weight:700;letter-spacing:-.03em;line-height:1.2;
      color:var(--fg);margin-bottom:12px;
    }
    .prose h2{
      font-size:1.2em;font-weight:600;letter-spacing:-.015em;
      margin-top:48px;margin-bottom:14px;padding-bottom:10px;
      border-bottom:1px solid var(--border);color:var(--fg);
    }
    .prose h2:first-child,.prose h1+h2{margin-top:24px}
    .prose h3{font-size:1.0em;font-weight:600;margin-top:28px;margin-bottom:8px;color:var(--fg)}
    .prose h4{font-size:.85em;font-weight:600;margin-top:20px;margin-bottom:6px;color:var(--fg-2);text-transform:uppercase;letter-spacing:.04em}

    .prose p{color:var(--fg-2);margin-bottom:16px}
    .prose strong{color:var(--fg);font-weight:600}
    .prose em{color:var(--fg-2)}

    .prose a{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(37,99,235,.25);transition:.1s}
    .prose a:hover{color:var(--accent-hi);border-color:var(--accent)}

    .prose hr{border:none;border-top:1px solid var(--border);margin:36px 0}

    .prose ul,.prose ol{padding-left:20px;margin-bottom:16px;color:var(--fg-2)}
    .prose li{margin-bottom:5px}
    .prose li::marker{color:var(--fg-3)}
    .prose ul ul,.prose ol ol{margin-top:5px;margin-bottom:5px}

    /* callout */
    .prose blockquote{
      border-left:3px solid var(--border-mid);
      background:var(--bg-raised);
      border-radius:0 var(--r) var(--r) 0;
      padding:12px 16px;margin:20px 0;
    }
    .prose blockquote p{margin:0;color:var(--fg-2)}
    .prose blockquote strong{color:var(--fg)}

    /* inline code */
    .prose :not(pre)>code{
      font-family:var(--mono);font-size:.83em;
      background:var(--bg-raised);border:1px solid var(--border);
      border-radius:3px;padding:1px 5px;color:var(--code-fg);
    }

    /* code blocks */
    .prose pre{
      position:relative;background:var(--bg-code);
      border:1px solid var(--border-mid);border-radius:var(--r-lg);
      margin:20px 0;overflow:hidden;
    }
    .prose pre code{
      display:block;padding:18px 20px;overflow-x:auto;
      font-family:var(--mono);font-size:13px;line-height:1.6;
      background:none!important;tab-size:2;color:var(--fg);
    }
    .code-header{
      display:flex;align-items:center;justify-content:space-between;
      padding:7px 14px;background:var(--bg-raised);
      border-bottom:1px solid var(--border);
    }
    .lang-badge{
      font-family:var(--mono);font-size:10px;font-weight:500;
      color:var(--fg-3);letter-spacing:.05em;text-transform:uppercase;
    }
    .copy-btn{
      display:flex;align-items:center;gap:4px;
      background:none;border:1px solid var(--border);border-radius:4px;
      padding:2px 8px;font-family:var(--font);font-size:11px;font-weight:500;
      color:var(--fg-3);cursor:pointer;transition:.1s;
    }
    .copy-btn:hover{background:var(--bg-hover);color:var(--fg);border-color:var(--border-mid)}
    .copy-btn.ok{color:var(--green);border-color:var(--green)}

    /* tables */
    .prose table{
      width:100%;border-collapse:collapse;margin:20px 0;
      font-size:13.5px;border:1px solid var(--border);border-radius:var(--r-lg);overflow:hidden;
    }
    .prose thead th{
      background:var(--bg-raised);padding:9px 12px;
      text-align:left;font-size:11px;font-weight:600;
      color:var(--fg-3);border-bottom:1px solid var(--border-mid);
      letter-spacing:.04em;text-transform:uppercase;
    }
    .prose tbody td{padding:8px 12px;color:var(--fg-2);border-bottom:1px solid var(--border)}
    .prose tbody tr:last-child td{border-bottom:none}
    .prose tbody tr:hover td{background:var(--bg-hover)}
    .prose tbody td strong{color:var(--fg)}
    .prose tbody td code{font-size:.82em}

    /* images */
    .prose img{max-width:100%;border-radius:var(--r-lg);border:1px solid var(--border);margin:8px 0;display:block}
    .prose p>em:only-child{display:block;text-align:center;font-size:12px;color:var(--fg-3);margin-top:-4px;margin-bottom:12px}

    /* ─── TOC ────────────────────────────────────────── */
    .toc{
      position:fixed;top:var(--hdr-h);right:0;bottom:0;
      width:var(--toc-w);overflow-y:auto;
      padding:24px 12px 40px;border-left:1px solid var(--border);
      background:var(--bg);
    }
    .toc-title{
      font-size:10.5px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
      color:var(--fg-3);margin-bottom:10px;padding-left:4px;
    }
    .toc-list{list-style:none}
    .toc-list li{margin:1px 0}
    .toc-list li a{
      display:block;padding:4px 8px;
      font-size:12.5px;color:var(--fg-3);text-decoration:none;
      border-left:2px solid transparent;border-radius:0 4px 4px 0;
      transition:.1s;line-height:1.4;
    }
    .toc-list li a:hover{color:var(--fg-2);background:var(--bg-hover)}
    .toc-list li.active a{color:var(--accent);border-left-color:var(--accent);background:var(--accent-lo)}
    .toc-list li.h3 a{padding-left:16px;font-size:12px}

    /* ─── Prev / Next ───────────────────────────────── */
    .page-nav{
      display:flex;gap:12px;margin-top:48px;
      padding-top:28px;border-top:1px solid var(--border);
    }
    .pn-btn{
      flex:1;display:flex;flex-direction:column;gap:4px;
      padding:14px 16px;border-radius:var(--r-lg);
      background:var(--bg-raised);border:1px solid var(--border);
      text-decoration:none;transition:.12s;
    }
    .pn-btn:hover{border-color:var(--accent)}
    .pn-btn.right{align-items:flex-end;text-align:right}
    .pn-label{font-size:10px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--fg-3)}
    .pn-title{font-size:14px;font-weight:500;color:var(--fg)}

    /* ─── Search ──────────────────────────────────────────── */
    .search-overlay{
      display:none;position:fixed;inset:0;z-index:200;
      background:rgba(0,0,0,.4);backdrop-filter:blur(4px);
      align-items:flex-start;justify-content:center;padding-top:100px;
    }
    .search-overlay.open{display:flex}
    .search-modal{
      width:100%;max-width:540px;
      background:var(--bg);border:1px solid var(--border-mid);
      border-radius:var(--r-lg);box-shadow:0 16px 48px rgba(0,0,0,.12);
      overflow:hidden;
    }
    .search-row{
      display:flex;align-items:center;gap:10px;
      padding:13px 16px;border-bottom:1px solid var(--border);
    }
    .search-row svg{flex-shrink:0;color:var(--fg-3)}
    #search-input{
      flex:1;background:none;border:none;outline:none;
      font-family:var(--font);font-size:15px;color:var(--fg);
    }
    #search-input::placeholder{color:var(--fg-3)}
    #search-results{max-height:360px;overflow-y:auto}
    .sr{
      display:block;padding:11px 16px;text-decoration:none;
      border-bottom:1px solid var(--border);transition:.1s;cursor:pointer;
    }
    .sr:last-child{border-bottom:none}
    .sr:hover,.sr.on{background:var(--bg-raised)}
    .sr-sec{font-size:9.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--fg-3);margin-bottom:2px}
    .sr-title{font-size:14px;font-weight:500;color:var(--fg)}
    .sr-ex{font-size:12px;color:var(--fg-3);margin-top:2px;line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .sr-ex mark{background:rgba(37,99,235,.12);color:var(--accent);border-radius:2px;padding:0 2px}
    .search-empty{padding:32px;text-align:center;color:var(--fg-3);font-size:14px}
    .search-footer{
      display:flex;align-items:center;gap:14px;padding:9px 16px;
      border-top:1px solid var(--border);font-size:11px;color:var(--fg-3);
    }
    .sf-hint{display:flex;align-items:center;gap:4px}

    /* ─── Responsive ─────────────────────────────────── */
    @media(max-width:1180px){
      .toc{display:none}
      .content-wrap{margin-right:0}
    }
    @media(max-width:860px){
      .sidebar{transform:translateX(-100%);box-shadow:0 4px 24px rgba(0,0,0,.08)}
      .sidebar.open{transform:translateX(0)}
      .sidebar-overlay.open{display:block}
      .content-wrap{margin-left:0}
      .menu-btn{display:flex}
      .logo{width:auto}
      .search-kbds{display:none}
      .hdr-center{display:none}
      .content{padding:32px 24px 60px}
    }
    @media(max-width:540px){
      .content{padding:24px 16px 56px}
      .prose h1{font-size:1.5em}
      .prose h2{font-size:1.1em}
      .prose table{font-size:12px}
      .prose thead th,.prose tbody td{padding:7px 10px}
      .page-nav{flex-direction:column}
    }

    /* ─── Path Picker (Pattern A) ─────────────────────────────────────────────── */
    .path-picker{
      position:sticky;top:var(--hdr-h);z-index:85;
      background:rgba(255,255,255,.97);backdrop-filter:blur(8px);
      border-bottom:1px solid var(--border);
      padding:8px 40px;
      display:flex;align-items:center;gap:16px;flex-wrap:wrap;
    }
    .picker-label{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--fg-3);white-space:nowrap}
    .picker-group{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
    .picker-group-sep{color:var(--border-mid);font-size:18px;line-height:1;flex-shrink:0}
    .picker-group-name{font-size:11px;font-weight:600;color:var(--fg-3);text-transform:uppercase;letter-spacing:.05em;white-space:nowrap}
    .picker-pills{display:flex;gap:4px;flex-wrap:wrap}
    .picker-pill{
      font-size:12.5px;font-weight:500;padding:3px 11px;border-radius:20px;
      border:1px solid var(--border-mid);background:var(--bg);color:var(--fg-2);
      cursor:pointer;transition:.1s;white-space:nowrap;font-family:var(--font);
    }
    .picker-pill:hover{border-color:var(--accent);color:var(--accent)}
    .picker-pill.active{background:var(--accent);border-color:var(--accent);color:#fff}
    @media(max-width:860px){.path-picker{padding:8px 16px;gap:10px}}

    /* ─── Stepper (Pattern B) ────────────────────────────────────────────────── */
    .step-progress-bar{height:3px;background:var(--border);border-radius:2px;margin-bottom:32px;overflow:hidden}
    .step-progress-fill{height:100%;background:var(--accent);border-radius:2px;width:0%;transition:width .4s ease}
    .step-summary{display:none;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}
    .step-summary.visible{display:flex}
    .step-done-icon{
      width:18px;height:18px;border-radius:50%;
      background:var(--accent);color:#fff;
      display:flex;align-items:center;justify-content:center;
      font-size:10px;font-weight:700;flex-shrink:0;
    }
    .step-done-title{font-size:13.5px;font-weight:500;color:var(--fg-2);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .step-redo-btn{
      background:none;border:1px solid var(--border-mid);border-radius:4px;
      padding:2px 8px;font-size:11px;font-family:var(--font);
      color:var(--fg-3);cursor:pointer;transition:.1s;white-space:nowrap;flex-shrink:0;
    }
    .step-redo-btn:hover{color:var(--accent);border-color:var(--accent)}
    .step-body.hidden{display:none}
    .step-label{
      display:flex;align-items:center;gap:8px;margin-bottom:10px;
      font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--fg-3);
    }
    .step-badge{
      display:inline-flex;align-items:center;justify-content:center;
      width:20px;height:20px;border-radius:50%;
      background:var(--accent);color:#fff;font-size:10px;font-weight:700;flex-shrink:0;
    }
    .step-next-btn{
      display:inline-flex;align-items:center;gap:8px;
      margin:28px 0 40px;padding:10px 20px;
      background:var(--accent);color:#fff;border:none;
      border-radius:var(--r-lg);font-size:14px;font-weight:500;
      font-family:var(--font);cursor:pointer;transition:.1s;
    }
    .step-next-btn:hover{background:var(--accent-hi)}
    .step-next-btn.step-final{background:var(--bg-raised);color:var(--accent);border:1px solid rgba(37,99,235,.3)}
    .step-next-btn.step-final:hover{background:var(--accent-lo)}
""".strip()

# ─── JavaScript ───────────────────────────────────────────────────────────────
JS_TEMPLATE = """
(function(){
'use strict';

/* ── Search index (injected at build time) ── */
var INDEX = __SEARCH_INDEX__;

/* ── Detect platform ── */
var isMac = /mac/i.test(navigator.platform);
document.querySelectorAll('.mod-key').forEach(function(el){
  el.textContent = isMac ? '⌘' : 'Ctrl';
});

/* ── Code blocks: add header with lang badge + copy button ── */
document.querySelectorAll('pre').forEach(function(pre){
  var code = pre.querySelector('code');
  if(!code) return;
  var cls = code.className || '';
  var lang = (cls.match(/language-([\\w-]+)/) || [])[1] || '';
  var header = document.createElement('div');
  header.className = 'code-header';
  header.innerHTML =
    '<span class="lang-badge">'+(lang||'code')+'</span>'+
    '<button class="copy-btn" aria-label="Copy code">'+
      '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="9" height="9" rx="1.5"/><path d="M3 11V3a1 1 0 0 1 1-1h8"/></svg>'+
      'Copy'+
    '</button>';
  pre.insertBefore(header, code);
  header.querySelector('.copy-btn').addEventListener('click', function(){
    var btn = this;
    navigator.clipboard.writeText(code.textContent).then(function(){
      btn.classList.add('ok');
      btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="2,9 6,13 14,3"/></svg>Copied';
      setTimeout(function(){
        btn.classList.remove('ok');
        btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="9" height="9" rx="1.5"/><path d="M3 11V3a1 1 0 0 1 1-1h8"/></svg>Copy';
      }, 2200);
    });
  });
});

/* ── Syntax highlight ── */
if(window.hljs){
  hljs.highlightAll();
}

/* ── TOC scroll-spy ── */
var tocItems = document.querySelectorAll('.toc-list li');
if(tocItems.length){
  var heads = Array.from(document.querySelectorAll('.prose h2,.prose h3'));
  var obs = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(!e.isIntersecting) return;
      tocItems.forEach(function(li){
        var a = li.querySelector('a');
        li.classList.toggle('active', a && a.getAttribute('href')==='#'+e.target.id);
      });
    });
  },{rootMargin:'-8% 0px -78% 0px'});
  heads.forEach(function(h){ obs.observe(h); });
}

/* ── Mobile sidebar ── */
var sidebar = document.querySelector('.sidebar');
var overlay = document.querySelector('.sidebar-overlay');
var menuBtn = document.querySelector('.menu-btn');
if(menuBtn){
  menuBtn.addEventListener('click', function(){
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
  });
  overlay.addEventListener('click', function(){
    sidebar.classList.remove('open');
    overlay.classList.remove('open');
  });
}

/* ── Search ── */
var searchOverlay = document.querySelector('.search-overlay');
var searchInput = document.getElementById('search-input');
var searchResults = document.getElementById('search-results');
var focusIdx = -1;

function openSearch(){
  searchOverlay.classList.add('open');
  searchInput.focus();
  renderResults('');
}
function closeSearch(){
  searchOverlay.classList.remove('open');
  searchInput.value='';
  focusIdx=-1;
}

document.querySelectorAll('.search-pill').forEach(function(el){
  el.addEventListener('click', openSearch);
});
searchOverlay.addEventListener('click', function(e){
  if(e.target===searchOverlay) closeSearch();
});

document.addEventListener('keydown', function(e){
  if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();searchOverlay.classList.contains('open')?closeSearch():openSearch();}
  if(e.key==='Escape') closeSearch();
});

searchInput.addEventListener('input', function(){
  focusIdx=-1;
  renderResults(searchInput.value);
});
searchInput.addEventListener('keydown', function(e){
  var items = searchResults.querySelectorAll('.sr');
  if(e.key==='ArrowDown'){e.preventDefault();focusIdx=Math.min(focusIdx+1,items.length-1);}
  else if(e.key==='ArrowUp'){e.preventDefault();focusIdx=Math.max(focusIdx-1,-1);}
  else if(e.key==='Enter'&&focusIdx>=0){e.preventDefault();items[focusIdx].click();return;}
  items.forEach(function(el,i){el.classList.toggle('on',i===focusIdx);});
  if(focusIdx>=0) items[focusIdx].scrollIntoView({block:'nearest'});
});

function esc(s){return s.replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function hilite(text,terms){
  var t=esc(text);
  terms.forEach(function(q){
    if(!q) return;
    t=t.replace(new RegExp('('+q.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&')+')','gi'),'<mark>$1</mark>');
  });
  return t;
}

function renderResults(q){
  var terms = q.toLowerCase().split(/\\s+/).filter(Boolean);
  var results;
  if(!q.trim()){
    results = INDEX.slice(0,12);
  } else {
    results = INDEX.map(function(doc){
      var hay = (doc.title+' '+(doc.headings||[]).join(' ')+' '+doc.text).toLowerCase();
      var score = terms.reduce(function(s,t){return s+(hay.includes(t)?hay.split(t).length-1:0);},0);
      if(!score) return null;
      var idx = doc.text.toLowerCase().indexOf(terms[0]||'');
      var ex = idx>=0 ? doc.text.slice(Math.max(0,idx-40),idx+120) : doc.text.slice(0,140);
      return Object.assign({},doc,{score:score,ex:ex});
    }).filter(Boolean).sort(function(a,b){return b.score-a.score;}).slice(0,10);
  }
  if(!results.length){
    searchResults.innerHTML='<div class="search-empty">No results for "<strong>'+esc(q)+'</strong>"</div>';
    return;
  }
  searchResults.innerHTML = results.map(function(r){
    return '<a class="sr" href="'+r.href+'">'+
      (r.section?'<div class="sr-sec">'+esc(r.section)+'</div>':'')+
      '<div class="sr-title">'+hilite(r.title,terms)+'</div>'+
      (r.ex?'<div class="sr-ex">'+hilite(r.ex,terms)+'</div>':'')+
      '</a>';
  }).join('');
}



    /* ─── Path Picker — Pattern A ─────────────────────────────────────────── */
    var PP_KEY='llmg.prefs';
    var pprefs=(function(){try{return JSON.parse(localStorage.getItem(PP_KEY)||'{}');}catch(e){return {};}})();
    function ppSave(){localStorage.setItem(PP_KEY,JSON.stringify(pprefs));}
    function ppApply(){
      document.querySelectorAll('.picker-pill').forEach(function(p){
        p.classList.toggle('active',pprefs[p.dataset.dim]===p.dataset.val);
      });
      document.querySelectorAll('[data-when]').forEach(function(el){
        var conds=el.dataset.when.split(' ');
        var anySet=conds.some(function(c){return pprefs[c.split(':')[0]];});
        if(!anySet){el.style.display='';return;}
        var match=conds.every(function(c){var p=c.split(':');return !pprefs[p[0]]||pprefs[p[0]]===p[1];});
        el.style.display=match?'':'none';
      });
    }
    var ppEl=document.getElementById('path-picker');
    if(ppEl){
      ppEl.querySelectorAll('.picker-pill').forEach(function(pill){
        pill.addEventListener('click',function(){
          var dim=pill.dataset.dim,val=pill.dataset.val;
          pprefs[dim]=(pprefs[dim]===val)?null:val;
          if(pprefs[dim]===null)delete pprefs[dim];
          ppSave();ppApply();
        });
      });
      ppApply();
    }

    /* ─── Stepper — Pattern B ─────────────────────────────────────────────── */
    (function(){
      var prose=document.querySelector('.prose');
      if(!prose)return;
      var stepH2s=Array.from(prose.querySelectorAll('h2')).filter(function(h){
        return /^Step\s*\d+/i.test(h.textContent.trim());
      });
      if(stepH2s.length<1)return;

      var PAGE_KEY='llmg.step.'+location.pathname;
      var done={};try{done=JSON.parse(localStorage.getItem(PAGE_KEY)||'{}');}catch(e){}

      /* collect nodes per step */
      var steps=stepH2s.map(function(h,i){
        var nodes=[],node=h.nextSibling,stop=stepH2s[i+1]||null;
        while(node&&node!==stop){nodes.push(node);node=node.nextSibling;}
        return{num:i+1,heading:h,title:h.textContent.trim(),bodyNodes:nodes};
      });

      /* progress bar */
      var bar=document.createElement('div');
      bar.className='step-progress-bar';
      bar.innerHTML='<div class="step-progress-fill"></div>';
      stepH2s[0].parentNode.insertBefore(bar,stepH2s[0]);

      /* wrap each step */
      steps.forEach(function(step,i){
        var wrapper=document.createElement('div');
        wrapper.className='step-wrapper';
        wrapper.dataset.step=step.num;

        /* summary (done state) */
        var summary=document.createElement('div');
        summary.className='step-summary';
        summary.innerHTML=
          '<div class="step-done-icon">\u2713</div>'+
          '<span class="step-done-title">'+step.title+'</span>'+
          '<button class="step-redo-btn" data-step="'+step.num+'">Redo</button>';

        /* body */
        var body=document.createElement('div');
        body.className='step-body';
        var label=document.createElement('div');
        label.className='step-label';
        label.innerHTML='<span class="step-badge">'+step.num+'</span>Step '+step.num+' of '+steps.length;
        body.appendChild(label);

        /* next/done button */
        var btn=document.createElement('button');
        btn.className='step-next-btn'+(i===steps.length-1?' step-final':'');
        btn.dataset.step=step.num;
        btn.innerHTML=i<steps.length-1
          ?'Done \u2014 '+steps[i+1].title+' \u2192'
          :'\u2713 Setup complete';

        wrapper.appendChild(summary);
        wrapper.appendChild(body);

        /* insert wrapper FIRST (while heading.parentNode still points to .prose),
           then move heading + body nodes into step-body */
        step.heading.parentNode.insertBefore(wrapper,step.heading);
        body.appendChild(step.heading);
        step.bodyNodes.forEach(function(n){body.appendChild(n);});
        body.appendChild(btn);
      });

      function updateDisplay(){
        var count=Object.values(done).filter(Boolean).length;
        var fill=document.querySelector('.step-progress-fill');
        if(fill)fill.style.width=Math.round(count/steps.length*100)+'%';
        steps.forEach(function(step){
          var w=document.querySelector('.step-wrapper[data-step="'+step.num+'"]');
          if(!w)return;
          var isDone=!!done[step.num];
          w.querySelector('.step-summary').classList.toggle('visible',isDone);
          w.querySelector('.step-body').classList.toggle('hidden',isDone);
        });
      }

      document.addEventListener('click',function(e){
        var nextBtn=e.target.closest&&e.target.closest('.step-next-btn');
        if(nextBtn){
          var n=parseInt(nextBtn.dataset.step);
          done[n]=true;localStorage.setItem(PAGE_KEY,JSON.stringify(done));
          updateDisplay();
          var nxt=document.querySelector('.step-wrapper[data-step="'+(n+1)+'"]');
          if(nxt)setTimeout(function(){nxt.scrollIntoView({behavior:'smooth',block:'start'});},60);
        }
        var redoBtn=e.target.closest&&e.target.closest('.step-redo-btn');
        if(redoBtn){
          delete done[parseInt(redoBtn.dataset.step)];
          localStorage.setItem(PAGE_KEY,JSON.stringify(done));
          updateDisplay();
        }
      });

      updateDisplay();
    })();
})();
""".strip()

# ─── Build sidebar HTML ────────────────────────────────────────────────────────
def build_sidebar(current_slug: str) -> str:
    lines = []
    for sec in NAV:
        lines.append(f'<div class="nav-section">')
        lines.append(f'  <span class="nav-label">{sec["section"]}</span>')
        for item in sec["items"]:
            active = "active" if item["slug"] == current_slug else ""
            link = href(current_slug, item["slug"])
            lines.append(
                f'  <a class="nav-item {active}" href="{link}">'  # no emoji
                f'{item["title"]}</a>'
            )
        lines.append("</div>")
    return "\n".join(lines)

# ─── Build TOC HTML ───────────────────────────────────────────────────────────
def build_toc(toc_tokens) -> str:
    if not toc_tokens:
        return ""
    lines = ['<ul class="toc-list">']

    def render_tokens(tokens, depth=0):
        for tok in tokens:
            level = tok.get("level", 2)
            cls = "h3" if level >= 3 else ""
            lines.append(f'<li class="{cls}"><a href="#{tok["id"]}">{tok["name"]}</a></li>')
            if tok.get("children"):
                render_tokens(tok["children"], depth + 1)

    render_tokens(toc_tokens)
    lines.append("</ul>")
    return "\n".join(lines)

# ─── Build breadcrumb ─────────────────────────────────────────────────────────
def build_breadcrumb(page: dict, from_slug: str) -> str:
    root = href(from_slug, "index")
    parts = [f'<a href="{root}">Docs</a>']
    for sec in NAV:
        for item in sec["items"]:
            if item["slug"] == page["slug"]:
                if sec["section"] != "Getting Started":
                    parts.append(f'<span class="bc-sep">/</span>')
                    parts.append(f'<span class="bc-cur">{sec["section"]}</span>')
                parts.append('<span class="bc-sep">/</span>')
                parts.append(f'<span class="bc-cur">{page["title"]}</span>')
    return " ".join(parts)

# ─── Build prev/next ──────────────────────────────────────────────────────────
def build_page_nav(page: dict, from_slug: str) -> str:
    idx = next((i for i, p in enumerate(ALL_PAGES) if p["slug"] == page["slug"]), -1)
    if idx < 0:
        return ""
    prev_p = ALL_PAGES[idx - 1] if idx > 0 else None
    next_p = ALL_PAGES[idx + 1] if idx < len(ALL_PAGES) - 1 else None
    html = '<div class="page-nav">'
    if prev_p:
        html += f'<a class="pn-btn left" href="{href(from_slug, prev_p["slug"])}"><span class="pn-label">← Previous</span><span class="pn-title">{prev_p['title']}</span></a>'
    else:
        html += '<div></div>'
    if next_p:
        html += f'<a class="pn-btn right" href="{href(from_slug, next_p["slug"])}"><span class="pn-label">Next →</span><span class="pn-title">{next_p['title']}</span></a>'
    html += '</div>'
    return html

# ─── Post-process markdown HTML ───────────────────────────────────────────────
def fix_md_links(html: str) -> str:
    """Convert .md hrefs to .html"""
    return re.sub(r'href="([^"#][^"]*?)\.md"', r'href="\1.html"', html)

# ─── Render full HTML page ────────────────────────────────────────────────────
def render_page(page: dict, content_html: str, toc_tokens, search_index: list) -> str:
    slug = page["slug"]
    root = root_prefix(slug)
    sidebar_html = build_sidebar(slug)
    toc_html     = build_toc(toc_tokens)
    bc_html      = build_breadcrumb(page, slug)
    pnav_html    = build_page_nav(page, slug)
    search_json  = json.dumps(search_index, ensure_ascii=False)
    if slug == "agent-integration":
        path_picker_html = PICKER_HTML
    elif slug.startswith("backends/"):
        path_picker_html = PICKER_HTML_OS
    else:
        path_picker_html = ""
    js_code      = JS_TEMPLATE.replace("__SEARCH_INDEX__", search_json)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page['title']} — {SITE_NAME}</title>
<meta name="description" content="{SITE_TAGLINE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.10.0/styles/github.min.css">
<style>{CSS}</style>
</head>
<body>

<!-- Header -->
<header class="site-header">
  <button class="menu-btn" aria-label="Open menu">
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
      <line x1="2" y1="5" x2="16" y2="5"/><line x1="2" y1="9" x2="16" y2="9"/><line x1="2" y1="13" x2="16" y2="13"/>
    </svg>
  </button>
  <a href="{root}index.html" class="logo">
    <span class="logo-name">{SITE_NAME}</span>
  </a>
  <div class="hdr-center">
    <button class="search-pill" aria-label="Search">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <circle cx="6.5" cy="6.5" r="4.5"/><line x1="10.5" y1="10.5" x2="14" y2="14"/>
      </svg>
      <span class="search-pill-text">Search documentation…</span>
      <span class="search-kbds"><span class="kbd mod-key">⌘</span><span class="kbd">K</span></span>
    </button>
  </div>
  <nav class="hdr-links">
    <a href="{REPO_URL}" target="_blank" rel="noopener" class="hdr-link">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.11.82-.26.82-.58v-2.03c-3.34.72-4.04-1.61-4.04-1.61-.54-1.38-1.33-1.75-1.33-1.75-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.13 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/></svg>
      GitHub
    </a>
  </nav>
</header>

<!-- Sidebar overlay (mobile) -->
<div class="sidebar-overlay"></div>

<!-- Sidebar -->
<aside class="sidebar">
  {sidebar_html}
  <div class="sidebar-footer">
    Built for <a href="https://amplifier.ai" target="_blank">Amplifier</a>
  </div>
</aside>

<!-- Main layout -->
<div class="layout">
  <div class="content-wrap">
    {path_picker_html}
    <main class="content">
      <div class="breadcrumb">{bc_html}</div>
      <article class="prose">
        {content_html}
      </article>
      {pnav_html}
    </main>
  </div>

  <!-- Right TOC -->
  <aside class="toc">
    <p class="toc-title">On this page</p>
    {toc_html}
  </aside>
</div>

<!-- Search Modal -->
<div class="search-overlay" role="dialog" aria-modal="true" aria-label="Search">
  <div class="search-modal">
    <div class="search-row">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <circle cx="6.5" cy="6.5" r="4.5"/><line x1="10.5" y1="10.5" x2="14" y2="14"/>
      </svg>
      <input id="search-input" placeholder="Search docs…" autocomplete="off" spellcheck="false">
    </div>
    <div id="search-results"></div>
    <div class="search-footer">
      <span class="sf-hint"><span class="kbd">↑↓</span> navigate</span>
      <span class="sf-hint"><span class="kbd">↵</span> open</span>
      <span class="sf-hint"><span class="kbd">Esc</span> close</span>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.10.0/highlight.min.js"></script>
<script>{js_code}</script>
</body>
</html>"""

    # ─── Markdown processor ───────────────────────────────────────────────────────

def post_process_when_blocks(html: str) -> str:
    """Wrap <!-- when:dim=val --> ... <!-- /when --> pairs in data-when divs."""
    def _replace(m):
        raw = m.group(1).strip()
        conds = ' '.join(c.strip().replace('=', ':') for c in raw.split(','))
        return f'<div data-when="{conds}">' + m.group(2) + '</div>'
    return re.sub(
        r'<!--\s*when:([^-]+?)\s*-->(.*?)<!--\s*/when\s*-->',
        _replace, html, flags=re.DOTALL
    )


def process_markdown(md_text: str, src_file: str):
    """Returns (content_html, toc_tokens, plain_text, headings)"""
    # Fix relative image paths: strip leading ../ levels for files in subdirs
    src_depth = src_file.count("/")
    if src_depth > 0:
        # Images in subdirs reference ../diagrams/... which is correct relative to output
        pass  # paths are preserved as-is

    toc_ext = TocExtension(toc_depth="2-3", permalink=False)
    processor = md_module.Markdown(
        extensions=["tables", "fenced_code", "attr_list", "sane_lists", toc_ext],
        output_format="html",
    )
    html = processor.convert(md_text)
    html = fix_md_links(html)
    html = post_process_when_blocks(html)
    toc_tokens = getattr(processor, "toc_tokens", [])

    # Extract headings for search
    headings = re.findall(r"<h[23][^>]*>([^<]+)</h[23]>", html)
    plain    = strip_md(md_text)

    return html, toc_tokens, plain, headings


# ─── Build search index ───────────────────────────────────────────────────────
def build_search_index(entries: list, from_slug: str) -> list:
    """Convert collected entries to search index records with hrefs relative to from_slug."""
    result = []
    for e in entries:
        page = PAGE_BY_SLUG.get(e["slug"])
        if not page:
            continue
        section = next((s["section"] for s in NAV if any(i["slug"] == e["slug"] for i in s["items"])), "")
        result.append({
            "title":    e["title"],
            "slug":     e["slug"],
            "section":  section,
            "href":     href(from_slug, e["slug"]),
            "headings": e.get("headings", []),
            "text":     e.get("text", "")[:400],
        })
    return result

# ─── Main build ───────────────────────────────────────────────────────────────
def main():
    print(f"Building {SITE_NAME}…")

    # Clean + create dist
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True)

    # Copy asset directories (diagrams, etc.)
    for asset_dir in ["diagrams"]:
        src = SRC_DIR / asset_dir
        if src.exists():
            shutil.copytree(src, DIST_DIR / asset_dir)
            print(f"  Copied {asset_dir}/")

    # Process all pages and collect search index entries
    index_entries = []

    # Import the rich interactive cost-comparison content generator
    try:
        from cost_comparison_content import (
            build_cost_comparison_html,
            TOC_TOKENS as CC_TOC_TOKENS,
            PLAIN_TEXT as CC_PLAIN_TEXT,
        )
        _cc_available = True
    except ImportError:
        _cc_available = False

    for page in ALL_PAGES:
        md_path = SRC_DIR / page["file"]
        if not md_path.exists():
            print(f"  WARN  {page['file']} not found — skipping")
            continue

        if _cc_available and page["slug"] == "cost-comparison":
            content_html = build_cost_comparison_html()
            toc_tokens   = CC_TOC_TOKENS
            plain        = CC_PLAIN_TEXT
            headings     = [t["name"] for t in CC_TOC_TOKENS]
        else:
            md_text = md_path.read_text(encoding="utf-8")
            content_html, toc_tokens, plain, headings = process_markdown(md_text, page["file"])

        index_entries.append({
            "slug":     page["slug"],
            "title":    page["title"],
            "text":     plain,
            "headings": headings,
        })

        # Determine output path
        out_path = DIST_DIR / (page["slug"] + ".html")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Build search index relative to this page
        search_idx = build_search_index(index_entries, page["slug"])

        page_html = render_page(page, content_html, toc_tokens, search_idx)
        out_path.write_text(page_html, encoding="utf-8")
        print(f"  ✓  {page['slug']}.html")

    # Write a root redirect index if needed (dist/index.html is already the overview)
    print(f"\n✓ Done → {DIST_DIR}/")
    print(f"  Serve: cd {DIST_DIR} && python3 -m http.server 3000")

if __name__ == "__main__":
    main()