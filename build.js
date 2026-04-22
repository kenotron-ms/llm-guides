#!/usr/bin/env node
/**
 * Local LLM Guides — Static Site Generator
 * ─────────────────────────────────────────
 * Usage:
 *   npm install
 *   node build.js
 *
 * Serve output:
 *   cd dist && python3 -m http.server 3000
 */

'use strict';

const fs   = require('fs');
const path = require('path');

// ── Check deps ──────────────────────────────────────────────────────────────
let marked, hljs;
try {
  ({ marked } = require('marked'));
  hljs = require('highlight.js');
} catch {
  console.error('\n  Run \x1b[36mnpm install\x1b[0m first, then try again.\n');
  process.exit(1);
}

// ── Site config ─────────────────────────────────────────────────────────────
const SITE = {
  name:    'Local LLM Guides',
  tagline: 'Run powerful AI locally · Cut cloud costs · Own your data',
  github:  'https://github.com/your-org/local-llm-guides',
  logo:    '⚡',
};

/** All pages in nav order. slug becomes the output path (slug + '.html'). */
const PAGES = [
  // ── Getting Started
  { slug:'index',              file:'README.md',              title:'Overview',          section:'Getting Started', icon:'🏠' },
  { slug:'cost-comparison',    file:'cost-comparison.md',     title:'Cost Comparison',   section:'Getting Started', icon:'💰' },
  // ── Models
  { slug:'models/gemma4',      file:'models/gemma4.md',       title:'Gemma 4',           section:'Models',          icon:'✨' },
  { slug:'models/qwen3.5',     file:'models/qwen3.5.md',      title:'Qwen 3.5',          section:'Models',          icon:'🐉' },
  { slug:'models/qwen3.6',     file:'models/qwen3.6.md',      title:'Qwen 3.6',          section:'Models',          icon:'🐲' },
  // ── Backends
  { slug:'backends/ollama',    file:'backends/ollama.md',     title:'Ollama',            section:'Backends',        icon:'🦙' },
  { slug:'backends/llama-cpp', file:'backends/llama-cpp.md',  title:'llama.cpp',         section:'Backends',        icon:'⚡' },
  { slug:'backends/vllm',      file:'backends/vllm.md',       title:'vLLM',              section:'Backends',        icon:'🚀' },
  { slug:'backends/lmstudio',  file:'backends/lmstudio.md',   title:'LM Studio',         section:'Backends',        icon:'🖥️' },
  // ── Hardware
  { slug:'hardware/cuda',      file:'hardware/cuda.md',       title:'CUDA (NVIDIA)',      section:'Hardware',        icon:'🟢' },
  { slug:'hardware/rocm',      file:'hardware/rocm.md',       title:'ROCm (AMD)',         section:'Hardware',        icon:'🔴' },
  { slug:'hardware/mlx',       file:'hardware/mlx.md',        title:'MLX (Apple Silicon)',section:'Hardware',        icon:'🍎' },
  // ── Guides
  { slug:'agent-integration',  file:'agent-integration.md',   title:'Agent Integration', section:'Guides',          icon:'🤖' },
];

const SECTIONS = [...new Set(PAGES.map(p => p.section))];
const ROOT_DIR = path.resolve(__dirname);
const DIST_DIR = path.join(ROOT_DIR, 'dist');

// ── Path helpers ─────────────────────────────────────────────────────────────
function rootPfx(slug) {
  const d = slug.split('/').length - 1;
  return d > 0 ? '../'.repeat(d) : '';
}
function slugToHref(slug) { return slug + '.html'; }
function rel(fromSlug, toSlug) { return rootPfx(fromSlug) + slugToHref(toSlug); }

function stripMd(text) {
  return text
    .replace(/```[\s\S]*?```/gm, ' ')
    .replace(/`[^`]+`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/[|_~>#-]/g, ' ')
    .replace(/\s+/g, ' ').trim();
}

// ── Marked renderer ──────────────────────────────────────────────────────────
function makeRenderer(fromSlug) {
  const r   = new marked.Renderer();
  const pfx = rootPfx(fromSlug);

  r.heading = (text, level, raw) => {
    const id = raw.toLowerCase()
      .replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
    return `<h${level} id="${id}">${text}<a class="hlink" href="#${id}" aria-hidden="true">#</a></h${level}>\n`;
  };

  r.code = (code, lang) => {
    const safe = (lang || '').split(/\s/)[0].toLowerCase();
    let hi;
    try {
      hi = safe && hljs.getLanguage(safe)
        ? hljs.highlight(code, { language: safe }).value
        : hljs.highlightAuto(code).value;
    } catch (_) {
      hi = code.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
    const label = safe || 'code';
    return [
      `<div class="cb">`,
      `<div class="cb-hdr">`,
      `<span class="cb-lang">${label}</span>`,
      `<button class="cb-copy" onclick="copyCode(this)" aria-label="Copy">`,
      `<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">`,
      `<rect x="4" y="4" width="9" height="9" rx="1.5"/><path d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H12"/></svg>`,
      `Copy</button></div>`,
      `<pre><code class="hljs">${hi}</code></pre></div>\n`,
    ].join('');
  };

  r.image = (href, title, alt) => {
    let src = href || '';
    if (src && !src.startsWith('http') && !src.startsWith('/')) {
      // Strip leading ../ and re-root from dist root using pfx
      src = pfx + src.replace(/^(\.\.\/)+/, '');
    }
    return `<img src="${src}" alt="${alt || ''}"${title ? ` title="${title}"` : ''} loading="lazy">`;
  };

  r.link = (href, title, text) => {
    let h = href || '#';
    if (!h.startsWith('http') && !h.startsWith('#') && !h.startsWith('mailto:') && h.endsWith('.md')) {
      h = h.replace(/\.md$/, '.html');
    }
    const ext = h.startsWith('http');
    return `<a href="${h}"${title ? ` title="${title}"` : ''}${ext ? ' target="_blank" rel="noopener noreferrer"' : ''}>${text}</a>`;
  };

  return r;
}

marked.use({ gfm: true, breaks: false });

// ── CSS ───────────────────────────────────────────────────────────────────────
const CSS = `
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#09090b;--bg-nav:#0d0d11;--bg-card:#111118;--bg-code:#0a0a14;--bg-hover:rgba(255,255,255,.04);--bg-active:rgba(168,85,247,.1);
  --b:rgba(255,255,255,.07);--b2:rgba(255,255,255,.12);
  --tx:#f4f4f6;--tx2:#a1a1aa;--tx3:#71717a;
  --pu:#a855f7;--pu2:rgba(168,85,247,.15);--bl:#60a5fa;--tl:#2dd4bf;--gn:#34d399;--am:#fbbf24;--rd:#f87171;
  --grad:linear-gradient(135deg,#a855f7 0%,#60a5fa 100%);
  --sw:260px;--tw:224px;--hh:56px;--cx:760px;
  --r:6px;--rl:12px;
  --fn:'Inter',system-ui,sans-serif;--fm:'JetBrains Mono','Fira Code',ui-monospace,monospace;
  --sh:0 8px 32px rgba(0,0,0,.6);
}
html{scroll-behavior:smooth}
body{font-family:var(--fn);background:var(--bg);color:var(--tx);font-size:15px;line-height:1.7;min-height:100vh;overflow-x:hidden}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:rgba(255,255,255,.1);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:rgba(255,255,255,.2)}

/* ── Header ── */
.site-header{position:fixed;top:0;left:0;right:0;height:var(--hh);z-index:100;
  background:rgba(9,9,11,.88);backdrop-filter:blur(16px) saturate(160%);
  border-bottom:1px solid var(--b)}
.header-inner{display:flex;align-items:center;gap:12px;height:100%;padding:0 20px}
.menu-btn{display:none;background:none;border:none;padding:8px;border-radius:var(--r);
  cursor:pointer;color:var(--tx2);transition:background .15s,color .15s}
.menu-btn:hover{background:var(--bg-hover);color:var(--tx)}
.site-logo{display:flex;align-items:center;gap:10px;text-decoration:none;
  width:calc(var(--sw) - 24px);flex-shrink:0}
.logo-mark{font-size:22px;line-height:1;filter:drop-shadow(0 0 8px rgba(168,85,247,.5))}
.logo-name{font-size:14.5px;font-weight:600;color:var(--tx);letter-spacing:-.01em;white-space:nowrap}
.search-trigger{flex:1;max-width:420px;display:flex;align-items:center;gap:10px;
  background:var(--bg-card);border:1px solid var(--b2);border-radius:8px;
  padding:7px 12px;cursor:pointer;color:var(--tx3);font-size:13px;
  transition:border-color .15s,box-shadow .15s}
.search-trigger:hover{border-color:rgba(168,85,247,.4);box-shadow:0 0 0 3px rgba(168,85,247,.08)}
.search-placeholder{flex:1;text-align:left}
.search-kbds{display:flex;gap:3px;margin-left:auto;flex-shrink:0}
.kbd{font-family:var(--fm);font-size:10.5px;background:rgba(255,255,255,.07);
  border:1px solid var(--b2);border-radius:4px;padding:1px 5px;color:var(--tx3)}
.header-links{display:flex;align-items:center;gap:4px;margin-left:auto}
.header-link{display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:var(--r);
  text-decoration:none;color:var(--tx2);font-size:13px;font-weight:500;
  transition:background .15s,color .15s}
.header-link:hover{background:var(--bg-hover);color:var(--tx)}

/* ── Sidebar ── */
.sidebar-overlay{display:none;position:fixed;inset:0;z-index:89;background:rgba(0,0,0,.6)}
.sidebar-overlay.open{display:block}
.sidebar{position:fixed;top:var(--hh);left:0;bottom:0;width:var(--sw);z-index:90;
  background:var(--bg-nav);border-right:1px solid var(--b);
  display:flex;flex-direction:column;overflow-y:auto;
  transition:transform .25s ease}
.sidebar-inner{flex:1;padding:12px 0 20px}
.nav-section{margin-bottom:2px}
.nav-section-label{display:block;padding:14px 20px 3px;
  font-size:10.5px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--tx3)}
.nav-section:first-child .nav-section-label{padding-top:4px}
.nav-item{display:flex;align-items:center;gap:9px;
  padding:7px 12px 7px 20px;margin:1px 8px;border-radius:var(--r);
  text-decoration:none;font-size:13.5px;font-weight:400;color:var(--tx2);
  position:relative;transition:background .12s,color .12s}
.nav-item:hover{background:var(--bg-hover);color:var(--tx)}
.nav-item.active{background:var(--bg-active);color:var(--pu);font-weight:500}
.nav-item.active::before{content:'';position:absolute;left:0;top:22%;bottom:22%;
  width:2px;border-radius:2px;background:var(--pu);margin-left:-8px}
.nav-icon{font-size:14px;flex-shrink:0;line-height:1}
.sidebar-footer{padding:14px 20px;border-top:1px solid var(--b);
  font-size:11.5px;color:var(--tx3);letter-spacing:.01em}

/* ── Layout ── */
.layout{display:flex;padding-top:var(--hh);margin-left:var(--sw);min-height:100vh}
.main{flex:1;min-width:0;margin-right:var(--tw)}
.content{max-width:var(--cx);margin:0 auto;padding:44px 40px 80px}

/* ── Breadcrumb ── */
.breadcrumb{display:flex;align-items:center;gap:6px;margin-bottom:22px;
  font-size:13px;color:var(--tx3)}
.bc-sep{opacity:.4}
.bc-current{color:var(--tx2)}

/* ── Prose ── */
.prose h1{font-size:2.05rem;font-weight:700;letter-spacing:-.03em;line-height:1.22;
  background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;
  background-clip:text;margin-bottom:18px}
.prose h2{font-size:1.35rem;font-weight:600;letter-spacing:-.02em;color:var(--tx);
  margin:48px 0 14px;padding-bottom:10px;border-bottom:1px solid var(--b)}
.prose h3{font-size:1.05rem;font-weight:600;color:var(--tx);margin:30px 0 10px}
.prose h4{font-size:.875rem;font-weight:600;color:var(--tx2);margin:22px 0 8px;
  letter-spacing:.05em;text-transform:uppercase}
.prose p{color:var(--tx2);margin-bottom:16px;line-height:1.76}
.prose strong{color:var(--tx);font-weight:600}
.prose em{color:var(--tx2)}
.prose hr{border:none;border-top:1px solid var(--b);margin:40px 0}
.prose a{color:var(--bl);text-decoration:none;border-bottom:1px solid rgba(96,165,250,.3);
  transition:color .15s,border-color .15s}
.prose a:hover{color:var(--pu);border-color:var(--pu)}
.prose ul,.prose ol{padding-left:24px;margin-bottom:16px;color:var(--tx2)}
.prose li{margin-bottom:5px}
.prose li::marker{color:var(--pu)}
.prose blockquote{border-left:3px solid var(--pu);background:rgba(168,85,247,.06);
  border-radius:0 var(--r) var(--r) 0;padding:14px 18px;margin:22px 0;color:var(--tx2)}
.prose blockquote p{margin:0}
.prose blockquote strong{color:var(--pu)}
.prose :not(pre)>code{font-family:var(--fm);font-size:.84em;color:var(--tl);
  background:rgba(45,212,191,.1);border:1px solid rgba(45,212,191,.2);
  border-radius:4px;padding:1px 5px}
.prose img{max-width:100%;border-radius:var(--rl);border:1px solid var(--b2);
  margin:8px 0;display:block}
.prose p>em:only-child{color:var(--tx3);font-size:12.5px;display:block;
  text-align:center;margin-top:-4px;margin-bottom:14px}

/* ── Heading anchor ── */
.hlink{opacity:0;margin-left:8px;font-size:.8em;color:var(--tx3);
  text-decoration:none;border:none!important;transition:opacity .15s}
h2:hover .hlink,h3:hover .hlink{opacity:1}

/* ── Code blocks ── */
.cb{border:1px solid var(--b2);border-radius:var(--rl);margin:20px 0;overflow:hidden;
  background:var(--bg-code)}
.cb-hdr{display:flex;align-items:center;justify-content:space-between;
  padding:8px 16px;background:rgba(255,255,255,.025);border-bottom:1px solid var(--b)}
.cb-lang{font-family:var(--fm);font-size:11px;font-weight:500;color:var(--tx3);
  letter-spacing:.06em;text-transform:uppercase}
.cb-copy{display:flex;align-items:center;gap:5px;background:none;
  border:1px solid var(--b2);border-radius:var(--r);padding:3px 10px;
  font-family:var(--fn);font-size:11px;font-weight:500;color:var(--tx3);
  cursor:pointer;transition:all .15s}
.cb-copy:hover{background:rgba(255,255,255,.05);color:var(--tx)}
.cb-copy.copied{color:var(--gn);border-color:var(--gn)}
.cb pre{margin:0;overflow-x:auto}
.cb pre code{display:block;padding:18px 20px;font-family:var(--fm);
  font-size:13px;line-height:1.7;background:none!important}

/* ── Tables ── */
.prose table{width:100%;border-collapse:collapse;margin:20px 0;font-size:13.5px;
  border:1px solid var(--b2);border-radius:var(--rl);overflow:hidden}
.prose thead th{background:rgba(255,255,255,.04);padding:10px 14px;text-align:left;
  font-weight:600;font-size:11.5px;color:var(--tx3);letter-spacing:.05em;
  text-transform:uppercase;border-bottom:1px solid var(--b2);white-space:nowrap}
.prose tbody td{padding:9px 14px;color:var(--tx2);border-bottom:1px solid var(--b)}
.prose tbody tr:last-child td{border-bottom:none}
.prose tbody tr:hover td{background:rgba(255,255,255,.02)}
.prose tbody td strong{color:var(--tx)}
.prose tbody td code{font-size:.82em}

/* ── TOC ── */
.toc-sidebar{position:fixed;top:var(--hh);right:0;bottom:0;width:var(--tw);
  overflow-y:auto;border-left:1px solid var(--b);z-index:80}
.toc-inner{padding:24px 16px 40px}
.toc-label{font-size:11px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;
  color:var(--tx3);margin-bottom:12px;padding-left:4px}
.toc-list{list-style:none}
.toc-list li a{display:block;padding:4px 8px;font-size:12.5px;color:var(--tx3);
  text-decoration:none;border-left:2px solid transparent;border-radius:0 4px 4px 0;
  line-height:1.42;transition:color .12s,background .12s,border-color .12s}
.toc-list li a:hover{color:var(--tx);background:var(--bg-hover)}
.toc-list li.active a{color:var(--pu);border-left-color:var(--pu);background:var(--bg-active)}
.toc-2 a{padding-left:8px}
.toc-3 a{padding-left:22px;font-size:12px}

/* ── Page nav ── */
.page-nav{display:flex;gap:14px;margin-top:56px;padding-top:32px;border-top:1px solid var(--b)}
.pnav-btn{flex:1;display:flex;flex-direction:column;gap:4px;padding:16px 20px;
  border-radius:var(--rl);background:var(--bg-card);border:1px solid var(--b2);
  text-decoration:none;transition:all .15s}
.pnav-btn:hover{border-color:rgba(168,85,247,.4);box-shadow:0 0 0 3px rgba(168,85,247,.08);
  background:rgba(168,85,247,.05)}
.pnav-next{align-items:flex-end}
.pnav-dir{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--tx3)}
.pnav-title{font-size:14px;font-weight:500;color:var(--tx)}

/* ── Search ── */
.search-overlay{display:none;position:fixed;inset:0;z-index:200;
  background:rgba(0,0,0,.75);backdrop-filter:blur(6px);
  align-items:flex-start;justify-content:center;padding-top:100px}
.search-overlay.open{display:flex}
.search-modal{width:100%;max-width:560px;background:#18181f;border:1px solid var(--b2);
  border-radius:var(--rl);box-shadow:var(--sh);overflow:hidden}
.search-input-row{display:flex;align-items:center;gap:12px;padding:14px 18px;
  border-bottom:1px solid var(--b)}
#search-input{flex:1;background:none;border:none;outline:none;
  font-family:var(--fn);font-size:16px;color:var(--tx)}
#search-input::placeholder{color:var(--tx3)}
.search-esc-btn{background:none;border:none;cursor:pointer;padding:2px}
#search-results{max-height:360px;overflow-y:auto}
.search-result{display:block;padding:12px 18px;text-decoration:none;
  border-bottom:1px solid var(--b);transition:background .1s;cursor:pointer}
.search-result:hover,.search-result.focused{background:var(--bg-hover)}
.search-result:last-child{border-bottom:none}
.sr-section{font-size:10px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--pu);margin-bottom:3px}
.sr-title{font-size:14px;font-weight:500;color:var(--tx)}
.sr-excerpt{font-size:12.5px;color:var(--tx3);margin-top:3px;line-height:1.4;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sr-excerpt mark{background:rgba(168,85,247,.25);color:var(--pu);border-radius:2px;padding:0 2px}
.search-empty{padding:32px;text-align:center;color:var(--tx3);font-size:14px}
.search-footer{display:flex;align-items:center;gap:16px;padding:10px 18px;
  border-top:1px solid var(--b);font-size:11px;color:var(--tx3)}
.search-hint{display:flex;align-items:center;gap:5px}

/* ── Responsive ── */
@media(max-width:1180px){.toc-sidebar{display:none}.main{margin-right:0}}
@media(max-width:900px){
  :root{--sw:272px}
  .sidebar{transform:translateX(-100%);box-shadow:var(--sh)}
  .sidebar.open{transform:translateX(0)}
  .sidebar-overlay.open{display:block}
  .layout{margin-left:0}
  .menu-btn{display:flex}
  .site-logo{width:auto}
  .search-kbds{display:none}
  .content{padding:32px 24px 60px}
}
@media(max-width:560px){
  .content{padding:24px 16px 60px}
  .prose h1{font-size:1.7rem}
  .prose h2{font-size:1.2rem}
  .prose table{font-size:12px}
  .prose thead th,.prose tbody td{padding:7px 10px}
  .page-nav{flex-direction:column}
}
`;

// ── Client JS (embedded in each page) ────────────────────────────────────────
const CLIENT_JS = `
(function(){
  'use strict';

  /* mobile menu */
  var menuBtn = document.getElementById('menu-btn');
  var sidebar = document.getElementById('sidebar');
  var overlay = document.getElementById('sidebar-overlay');
  if(menuBtn){
    menuBtn.addEventListener('click',function(){
      sidebar.classList.toggle('open');
      overlay.classList.toggle('open');
    });
    overlay.addEventListener('click',function(){
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
    });
  }

  /* copy code */
  window.copyCode = function(btn){
    var code = btn.closest('.cb').querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(function(){
      btn.classList.add('copied');
      btn.textContent = '✓ Copied';
      setTimeout(function(){
        btn.classList.remove('copied');
        btn.innerHTML = '<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="9" height="9" rx="1.5"/><path d="M3 11V3.5A1.5 1.5 0 0 1 4.5 2H12"/></svg>Copy';
      }, 2000);
    });
  };

  /* TOC scroll-spy */
  (function(){
    var items = document.querySelectorAll('.toc-list li');
    if(!items.length) return;
    var obs = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(e.isIntersecting){
          var id = '#' + e.target.id;
          items.forEach(function(li){
            li.classList.toggle('active', li.querySelector('a').getAttribute('href') === id);
          });
        }
      });
    },{rootMargin:'-8% 0px -84% 0px'});
    document.querySelectorAll('.prose h2[id],.prose h3[id]').forEach(function(h){obs.observe(h)});
  })();

  /* search */
  var searchIndex = null;
  var searchFocused = -1;
  var searchOverlay = document.getElementById('search-overlay');
  var searchInput   = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');
  var searchTrigger = document.getElementById('search-trigger');

  var ROOT_PATH = typeof SEARCH_INDEX_URL !== 'undefined'
    ? SEARCH_INDEX_URL.replace('search-index.json','') : '';

  function loadIndex(){
    if(searchIndex) return Promise.resolve();
    return fetch(SEARCH_INDEX_URL)
      .then(function(r){return r.json()})
      .then(function(d){searchIndex=d})
      .catch(function(){searchIndex=[]});
  }

  function openSearch(){
    searchOverlay.classList.add('open');
    loadIndex().then(function(){
      searchInput.focus();
      renderResults('');
    });
  }
  function closeSearch(){
    searchOverlay.classList.remove('open');
    searchInput.value='';
    searchFocused=-1;
  }

  function doSearch(q){
    if(!q.trim()) return (searchIndex||[]).slice(0,7).map(function(p){return Object.assign({},p,{score:0,excerpt:''})});
    var terms = q.toLowerCase().split(/\\s+/).filter(Boolean);
    return (searchIndex||[]).map(function(doc){
      var hay = [doc.title].concat(doc.headings||[]).concat([doc.text]).join(' ').toLowerCase();
      var score = terms.reduce(function(s,t){return s+(hay.split(t).length-1)},0);
      if(!score) return null;
      var idx = doc.text.toLowerCase().indexOf(terms[0]);
      var exc = idx>=0 ? doc.text.slice(Math.max(0,idx-30),idx+110) : doc.text.slice(0,140);
      return Object.assign({},doc,{score:score,excerpt:exc});
    }).filter(Boolean).sort(function(a,b){return b.score-a.score}).slice(0,8);
  }

  function esc(s){ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') }

  function hi(text, terms){
    var t = esc(text);
    terms.forEach(function(term){
      if(!term) return;
      try{ t = t.replace(new RegExp('('+term+')','gi'),'<mark>$1</mark>'); }catch(e){}
    });
    return t;
  }

  function renderResults(q){
    var terms = q.toLowerCase().split(/\\s+/).filter(Boolean);
    var res = doSearch(q);
    if(!res.length){
      searchResults.innerHTML = '<div class="search-empty">'+(q?'No results for <strong>'+esc(q)+'</strong>':'Start typing…')+'</div>';
      return;
    }
    searchResults.innerHTML = res.map(function(r){
      var href = ROOT_PATH + r.href;
      return '<a class="search-result" href="'+href+'">'
        +'<div class="sr-section">'+esc(r.section||'Docs')+'</div>'
        +'<div class="sr-title">'+hi(r.title,terms)+'</div>'
        +(r.excerpt?'<div class="sr-excerpt">'+hi(r.excerpt,terms)+'</div>':'')
        +'</a>';
    }).join('');
  }

  if(searchTrigger) searchTrigger.addEventListener('click',openSearch);
  if(searchOverlay) searchOverlay.addEventListener('click',function(e){if(e.target===searchOverlay)closeSearch()});
  if(searchInput){
    searchInput.addEventListener('input',function(){searchFocused=-1;renderResults(searchInput.value)});
    searchInput.addEventListener('keydown',function(e){
      var items=searchResults.querySelectorAll('.search-result');
      if(e.key==='ArrowDown'){e.preventDefault();searchFocused=Math.min(searchFocused+1,items.length-1)}
      else if(e.key==='ArrowUp'){e.preventDefault();searchFocused=Math.max(searchFocused-1,-1)}
      else if(e.key==='Enter'&&searchFocused>=0){window.location=items[searchFocused].href;closeSearch();return}
      items.forEach(function(el,i){el.classList.toggle('focused',i===searchFocused)});
      if(searchFocused>=0) items[searchFocused].scrollIntoView({block:'nearest'});
    });
  }

  /* kbd shortcut */
  var modKey = document.getElementById('mod-key');
  if(modKey && !/mac/i.test(navigator.platform||'')) modKey.textContent='Ctrl';
  document.addEventListener('keydown',function(e){
    if((e.metaKey||e.ctrlKey)&&e.key==='k'){e.preventDefault();searchOverlay.classList.contains('open')?closeSearch():openSearch()}
    if(e.key==='Escape') closeSearch();
  });
})();
`;

// ── HTML template ─────────────────────────────────────────────────────────────
function renderPage({ page, prevPage, nextPage, contentHtml, headings }) {
  const root  = rootPfx(page.slug);
  const title = `${page.title} — ${SITE.name}`;

  /* sidebar */
  const sidebarHtml = SECTIONS.map(section => {
    const items = PAGES.filter(p => p.section === section).map(p => {
      const active = p.slug === page.slug;
      return `<a href="${rel(page.slug, p.slug)}" class="nav-item${active ? ' active' : ''}">` +
        `<span class="nav-icon">${p.icon}</span>${p.title}</a>`;
    }).join('\n    ');
    return `<div class="nav-section">\n  <span class="nav-section-label">${section}</span>\n    ${items}\n</div>`;
  }).join('\n\n');

  /* breadcrumb */
  const bcHtml = page.section
    ? `<span>${page.section}</span><span class="bc-sep"> / </span><span class="bc-current">${page.title}</span>`
    : `<span class="bc-current">${page.title}</span>`;

  /* on-page TOC */
  const tocHtml = headings.length
    ? headings.map(h => `<li class="toc-${h.level}"><a href="#${h.id}">${h.text}</a></li>`).join('\n')
    : '';

  /* prev / next */
  const prevHtml = prevPage
    ? `<a class="pnav-btn pnav-prev" href="${rel(page.slug, prevPage.slug)}">
    <span class="pnav-dir">← Previous</span>
    <span class="pnav-title">${prevPage.icon} ${prevPage.title}</span></a>`
    : '<span></span>';

  const nextHtml = nextPage
    ? `<a class="pnav-btn pnav-next" href="${rel(page.slug, nextPage.slug)}">
    <span class="pnav-dir">Next →</span>
    <span class="pnav-title">${nextPage.icon} ${nextPage.title}</span></a>`
    : '<span></span>';

  const searchIndexUrl = root + 'search-index.json';

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="${page.title} — ${SITE.tagline}">
<meta property="og:title" content="${title}">
<meta property="og:description" content="${SITE.tagline}">
<title>${title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>${CSS}</style>
</head>
<body>

<header class="site-header" id="header">
  <div class="header-inner">
    <button class="menu-btn" id="menu-btn" aria-label="Toggle sidebar">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <line x1="2" y1="5" x2="16" y2="5"/><line x1="2" y1="9" x2="16" y2="9"/><line x1="2" y1="13" x2="16" y2="13"/>
      </svg>
    </button>
    <a href="${root}index.html" class="site-logo">
      <span class="logo-mark">${SITE.logo}</span>
      <span class="logo-name">${SITE.name}</span>
    </a>
    <button class="search-trigger" id="search-trigger" aria-label="Search documentation">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6.5" cy="6.5" r="4.5"/><line x1="10.5" y1="10.5" x2="14" y2="14"/></svg>
      <span class="search-placeholder">Search docs…</span>
      <span class="search-kbds"><kbd class="kbd" id="mod-key">⌘</kbd><kbd class="kbd">K</kbd></span>
    </button>
    <nav class="header-links">
      <a href="${SITE.github}" target="_blank" rel="noopener noreferrer" class="header-link">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.2 11.38.6.11.82-.26.82-.58v-2.03c-3.34.72-4.04-1.61-4.04-1.61-.54-1.38-1.33-1.75-1.33-1.75-1.09-.74.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.8 1.3 3.49 1 .11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 3-.4c1.02 0 2.04.13 3 .4 2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.25 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58C20.57 21.8 24 17.3 24 12c0-6.63-5.37-12-12-12z"/></svg>
        GitHub
      </a>
    </nav>
  </div>
</header>

<div class="sidebar-overlay" id="sidebar-overlay"></div>
<aside class="sidebar" id="sidebar">
  <div class="sidebar-inner">
${sidebarHtml}
  </div>
  <div class="sidebar-footer">Built with ⚡ Amplifier</div>
</aside>

<div class="layout">
  <main class="main">
    <div class="content">
      <div class="breadcrumb">${bcHtml}</div>
      <article class="prose">
${contentHtml}
      </article>
      <div class="page-nav">
        ${prevHtml}
        ${nextHtml}
      </div>
    </div>
  </main>
  <aside class="toc-sidebar" id="toc">
    <div class="toc-inner">
      <p class="toc-label">On this page</p>
      <ul class="toc-list">${tocHtml}</ul>
    </div>
  </aside>
</div>

<div class="search-overlay" id="search-overlay" role="dialog" aria-modal="true" aria-label="Search">
  <div class="search-modal">
    <div class="search-input-row">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" style="flex-shrink:0;opacity:.45"><circle cx="6.5" cy="6.5" r="4.5"/><line x1="10.5" y1="10.5" x2="14" y2="14"/></svg>
      <input id="search-input" type="search" placeholder="Search…" autocomplete="off" spellcheck="false">
      <button class="search-esc-btn" onclick="(function(){document.getElementById('search-overlay').classList.remove('open');document.getElementById('search-input').value=''})()" aria-label="Close search"><kbd class="kbd">Esc</kbd></button>
    </div>
    <div id="search-results"></div>
    <div class="search-footer">
      <span class="search-hint"><kbd class="kbd">↑↓</kbd> navigate</span>
      <span class="search-hint"><kbd class="kbd">↵</kbd> open</span>
      <span class="search-hint"><kbd class="kbd">Esc</kbd> close</span>
    </div>
  </div>
</div>

<script>var SEARCH_INDEX_URL='${searchIndexUrl}';${CLIENT_JS}</script>
</body>
</html>`;
}

// ── Build helpers ─────────────────────────────────────────────────────────────
function ensureDir(d) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  ensureDir(dest);
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

function extractTocFromHtml(html) {
  const headings = [];
  const re = /<h([23])[^>]+id="([^"]+)"[^>]*>([\s\S]*?)<\/h[23]>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    headings.push({
      level: parseInt(m[1]),
      id:    m[2],
      text:  m[3].replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim(),
    });
  }
  return headings;
}

// ── Main build ────────────────────────────────────────────────────────────────
function build() {
  const t0 = Date.now();

  /* clean dist */
  if (fs.existsSync(DIST_DIR)) fs.rmSync(DIST_DIR, { recursive: true });
  ensureDir(DIST_DIR);

  /* copy static assets */
  const assets = ['diagrams'];
  for (const a of assets) {
    const src = path.join(ROOT_DIR, a);
    if (fs.existsSync(src)) {
      copyDir(src, path.join(DIST_DIR, a));
      console.log(`  Copied  ${a}/`);
    }
  }

  const searchIndex = [];

  /* render pages */
  for (let i = 0; i < PAGES.length; i++) {
    const page     = PAGES[i];
    const prevPage = i > 0 ? PAGES[i - 1] : null;
    const nextPage = i < PAGES.length - 1 ? PAGES[i + 1] : null;
    const srcPath  = path.join(ROOT_DIR, page.file);

    if (!fs.existsSync(srcPath)) {
      console.warn(`  ⚠  Missing ${page.file}, skipping`);
      continue;
    }

    const mdText = fs.readFileSync(srcPath, 'utf8');

    /* render markdown */
    const renderer  = makeRenderer(page.slug);
    const contentHtml = marked.parse(mdText, { renderer });
    const headings    = extractTocFromHtml(contentHtml);

    /* output path */
    const outRel  = slugToHref(page.slug);          // e.g. models/gemma4.html
    const outPath = path.join(DIST_DIR, outRel);
    ensureDir(path.dirname(outPath));

    const html = renderPage({ page, prevPage, nextPage, contentHtml, headings });
    fs.writeFileSync(outPath, html, 'utf8');
    console.log(`  Built   ${outRel}`);

    /* search index entry */
    searchIndex.push({
      title:    page.title,
      section:  page.section,
      slug:     page.slug,
      href:     outRel,
      headings: headings.map(h => h.text),
      text:     stripMd(mdText).slice(0, 2000),
    });
  }

  /* write search index */
  const siPath = path.join(DIST_DIR, 'search-index.json');
  fs.writeFileSync(siPath, JSON.stringify(searchIndex, null, 2), 'utf8');
  console.log(`  Built   search-index.json`);

  const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
  console.log(`\n  ✓ Done in ${elapsed}s → dist/\n`);
  console.log(`  Serve: \x1b[36mcd dist && python3 -m http.server 3000\x1b[0m\n`);
}

build();
