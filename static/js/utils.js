/* PayOptimise Suite — Shared JavaScript Utilities
   MS5132 Major ISM Project | University of Galway 2025-2026 */

'use strict';

// ─── API Client ───────────────────────────────────────────────────────────────
const API = {
  async get(endpoint) {
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  },
  async post(endpoint, data) {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }
};

// ─── Number formatting ────────────────────────────────────────────────────────
const fmt = {
  pct:  (v, d=1) => (v * 100).toFixed(d) + '%',
  num:  (v)      => v?.toLocaleString() ?? '—',
  dec:  (v, d=2) => v != null ? Number(v).toFixed(d) : '—',
  time: (v)      => v != null ? `${Math.round(v)}s` : '—',
  pval: (v)      => v < 0.001 ? '< 0.001' : Number(v).toFixed(4),
};

// ─── DOM helpers ──────────────────────────────────────────────────────────────
const $ = (sel, ctx=document) => ctx.querySelector(sel);
const $$ = (sel, ctx=document) => [...ctx.querySelectorAll(sel)];

function el(tag, attrs={}, ...children) {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k,v]) => {
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else e.setAttribute(k, v);
  });
  children.forEach(c => c && e.append(typeof c === 'string' ? document.createTextNode(c) : c));
  return e;
}

function setHTML(id, html)  { const e = document.getElementById(id); if(e) e.innerHTML = html; }
function setText(id, text)  { const e = document.getElementById(id); if(e) e.textContent = text; }
function show(id)  { const e = document.getElementById(id); if(e) e.style.display = ''; }
function hide(id)  { const e = document.getElementById(id); if(e) e.style.display = 'none'; }

// ─── Badge helpers ────────────────────────────────────────────────────────────
function badge(text, color='blue') {
  return `<span class="badge badge-${color}">${text}</span>`;
}

function resultBadge(significant, pValue) {
  return significant
    ? badge(`✓ Significant (p=${fmt.pval(pValue)})`, 'green')
    : badge(`✗ Not significant (p=${fmt.pval(pValue)})`, 'red');
}

function severityBadge(severity) {
  const map = { HIGH: 'red', MEDIUM: 'amber', LOW: 'blue' };
  return badge(severity, map[severity] || 'blue');
}

// ─── Loading state ────────────────────────────────────────────────────────────
function setLoading(id, msg='Loading...') {
  setHTML(id, `<div class="loading"><div class="spinner"></div></div>`);
}

function setError(id, msg='Failed to load.') {
  setHTML(id, `<div class="alert alert-red"><span class="alert-icon">⚠</span>${msg}</div>`);
}

// ─── Segment button helpers ───────────────────────────────────────────────────
function initSegButtons(containerSel, callback) {
  $$(containerSel + ' .seg-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      $$(containerSel + ' .seg-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      callback(this.dataset.value || this.textContent.trim());
    });
  });
}

// ─── Chart defaults ────────────────────────────────────────────────────────────
const CHART_DEFAULTS = {
  responsive:          true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#1e2235',
      borderColor:     '#3d4470',
      borderWidth:     1,
      titleColor:      '#e2e8f0',
      bodyColor:       '#94a3b8',
      padding:         10,
    }
  },
  scales: {
    x: {
      grid:  { color: '#2d3150' },
      ticks: { color: '#64748b', font: { size: 11 } }
    },
    y: {
      grid:  { color: '#2d3150' },
      ticks: { color: '#64748b', font: { size: 11 } },
      beginAtZero: true,
    }
  }
};

function makeChart(canvasId, type, labels, datasets, extraOptions={}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  if (ctx._chart) ctx._chart.destroy();
  const c = new Chart(ctx, {
    type,
    data: { labels, datasets },
    options: deepMerge(CHART_DEFAULTS, extraOptions)
  });
  ctx._chart = c;
  return c;
}

function deepMerge(target, source) {
  const out = Object.assign({}, target);
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      out[key] = deepMerge(target[key] || {}, source[key]);
    } else {
      out[key] = source[key];
    }
  }
  return out;
}

// ─── Colour palette ────────────────────────────────────────────────────────────
const COLOURS = {
  blue:   '#3b82f6',
  teal:   '#14b8a6',
  green:  '#22c55e',
  amber:  '#f59e0b',
  red:    '#ef4444',
  purple: '#8b5cf6',
  pink:   '#ec4899',
  grey:   '#64748b',
};
const PALETTE = Object.values(COLOURS);

// ─── Funnel colours ────────────────────────────────────────────────────────────
const FUNNEL_COLORS = {
  'Onboarding':         '#3b82f6',
  'Payment initiation': '#14b8a6',
  'Authentication':     '#ef4444',
  'Confirmation':       '#f59e0b',
  'Completion':         '#22c55e',
};

// ─── Render funnel bars ────────────────────────────────────────────────────────
function renderFunnelBars(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container || !data) return;
  container.innerHTML = data.map(d => {
    const color    = FUNNEL_COLORS[d.stage] || '#3b82f6';
    const dropBadge = d.drop_pct > 0
      ? `<span class="badge ${d.drop_pct > 25 ? 'badge-red' : d.drop_pct > 12 ? 'badge-amber' : 'badge-green'}">${d.drop_pct}% drop</span>`
      : `<span class="badge badge-green">✓ Completed</span>`;
    return `
      <div class="funnel-bar">
        <div class="funnel-label">
          <span>${d.stage}</span>
          <span style="display:flex;align-items:center;gap:8px">
            <span class="text-xs text-muted">${(d.sessions_in||0).toLocaleString()} sessions</span>
            ${dropBadge}
          </span>
        </div>
        <div class="funnel-track">
          <div class="funnel-fill" style="width:${d.pct_total}%;background:${color}">
            ${d.pct_total}%
          </div>
        </div>
      </div>`;
  }).join('');
}

// ─── Render alerts ─────────────────────────────────────────────────────────────
function renderAlerts(containerId, alerts) {
  const container = document.getElementById(containerId);
  if (!container) return;
  if (!alerts || alerts.length === 0) {
    container.innerHTML = `<div class="alert alert-green"><span class="alert-icon">✓</span>No friction alerts — all stages within threshold.</div>`;
    return;
  }
  container.innerHTML = alerts.map(a => `
    <div class="alert ${a.severity === 'HIGH' ? 'alert-red' : 'alert-amber'}">
      <span class="alert-icon">${a.severity === 'HIGH' ? '🔴' : '🟡'}</span>
      <div>
        <strong>${a.stage}</strong> — ${a.drop_off} drop-off
        <span style="margin-left:6px">${severityBadge(a.severity)}</span>
        <div class="text-xs" style="margin-top:3px;opacity:0.8">
          Suggested experiment: ${a.experiment}
        </div>
      </div>
    </div>`).join('');
}

// ─── Active nav highlight ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  $$('.nav-item').forEach(item => {
    const href = item.getAttribute('href') || '';
    if (path === href || (path !== '/' && href !== '/' && path.startsWith(href))) {
      item.classList.add('active');
    }
  });
});
