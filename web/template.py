HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⚡ Financial Intelligence Center</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  body { background:#0a0e1a; color:#e2e8f0; font-family:'Inter',system-ui,sans-serif; }
  .glass { background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08); backdrop-filter:blur(12px); }
  .signal-buy-strong  { color:#22c55e; font-weight:700; }
  .signal-buy         { color:#4ade80; }
  .signal-buy-spec    { color:#38bdf8; }
  .signal-watch       { color:#facc15; }
  .signal-wait        { color:#64748b; }
  .signal-partial     { color:#fb923c; }
  .signal-sell        { color:#f87171; }
  .signal-stop        { color:#ef4444; font-weight:700; }
  .signal-hedge       { color:#c084fc; }
  .score-bar { height:6px; border-radius:3px; background:#1e293b; overflow:hidden; }
  .score-fill { height:100%; border-radius:3px; transition:width .5s; }
  tr:hover { background:rgba(255,255,255,0.04) !important; cursor:pointer; }
  .badge { display:inline-flex; align-items:center; padding:2px 8px; border-radius:9999px; font-size:0.7rem; font-weight:600; }
  .badge-dt  { background:#4c1d95; color:#c4b5fd; }
  .badge-sw  { background:#0c4a6e; color:#7dd3fc; }
  .badge-pos { background:#14532d; color:#86efac; }
  .badge-acao{ background:#1e293b; color:#94a3b8; }
  .badge-fii { background:#422006; color:#fed7aa; }
  .badge-etf { background:#0f3460; color:#93c5fd; }
  .badge-bdr { background:#3b0764; color:#e9d5ff; }
  .badge-crp { background:#431407; color:#fdba74; }
  .badge-dol { background:#064e3b; color:#6ee7b7; }
  .badge-opc { background:#1c1917; color:#d4d4aa; }
  ::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-track { background:#0a0e1a; }
  ::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }
  .glow-green { box-shadow:0 0 12px rgba(34,197,94,.25); }
  .glow-red   { box-shadow:0 0 12px rgba(239,68,68,.25); }
  .ticker-pulse { animation: pulse 2s ease-in-out infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
  .tab-btn { padding:6px 14px; border-radius:6px; font-size:.8rem; cursor:pointer; border:1px solid transparent; transition:all .2s; }
  .tab-btn.active { background:#1e40af; border-color:#3b82f6; color:white; }
  .tab-btn:not(.active) { color:#64748b; }
  .tab-btn:not(.active):hover { color:#94a3b8; background:rgba(255,255,255,.04); }
</style>
</head>
<body class="min-h-screen">

<!-- HEADER -->
<header class="glass sticky top-0 z-50 px-4 py-2 border-b border-white/10">
  <div class="flex flex-wrap items-center justify-between gap-2">
    <div class="flex items-center gap-3">
      <span class="text-yellow-400 text-xl">⚡</span>
      <span class="font-bold text-white tracking-wide text-sm">FINANCIAL INTELLIGENCE CENTER</span>
      <span id="ts" class="text-xs text-slate-500"></span>
    </div>
    <div class="flex flex-wrap gap-4 text-xs">
      <div class="flex items-center gap-1">
        <span class="text-slate-500">SELIC</span>
        <span id="selic" class="text-orange-400 font-mono font-bold">--</span>
      </div>
      <div class="flex items-center gap-1">
        <span class="text-slate-500">IBOV</span>
        <span id="ibov" class="font-mono font-bold">--</span>
        <span id="ibov_var" class="font-mono text-xs"></span>
      </div>
      <div class="flex items-center gap-1">
        <span class="text-slate-500">USD</span>
        <span id="dolar" class="font-mono font-bold">--</span>
        <span id="dolar_var" class="font-mono text-xs"></span>
      </div>
      <div class="flex items-center gap-1">
        <span class="text-slate-500">IPCA</span>
        <span id="ipca" class="text-red-400 font-mono font-bold">--</span>
      </div>
    </div>
    <div class="flex items-center gap-2 text-xs">
      <div class="w-32 bg-slate-800 rounded-full h-2">
        <div id="scan-bar" class="h-2 rounded-full bg-blue-500 transition-all duration-500" style="width:0%"></div>
      </div>
      <span id="scan-txt" class="text-slate-500 ticker-pulse">Carregando...</span>
    </div>
  </div>
</header>

<!-- FILTERS -->
<div class="px-4 py-2 flex flex-wrap gap-2 items-center border-b border-white/5">
  <span class="text-slate-500 text-xs mr-1">Mercado:</span>
  <button class="tab-btn active" data-ftype="cls" data-fval="">Todos</button>
  <button class="tab-btn" data-ftype="cls" data-fval="Ação">Ações</button>
  <button class="tab-btn" data-ftype="cls" data-fval="FII">FIIs</button>
  <button class="tab-btn" data-ftype="cls" data-fval="ETF">ETFs</button>
  <button class="tab-btn" data-ftype="cls" data-fval="BDR">BDRs</button>
  <button class="tab-btn" data-ftype="cls" data-fval="Cripto">Cripto</button>
  <button class="tab-btn" data-ftype="cls" data-fval="Dólar">💵 Dólar</button>
  <button class="tab-btn" data-ftype="cls" data-fval="Opção">📋 Opções</button>
  <span class="text-slate-600 mx-1">|</span>
  <span class="text-slate-500 text-xs mr-1">Tipo:</span>
  <button class="tab-btn active" data-ftype="op" data-fval="">Todos</button>
  <button class="tab-btn" data-ftype="op" data-fval="DT">Day Trade</button>
  <button class="tab-btn" data-ftype="op" data-fval="SW">Swing</button>
  <button class="tab-btn" data-ftype="op" data-fval="POS">Posição</button>
  <span class="text-slate-600 mx-1">|</span>
  <span class="text-slate-500 text-xs mr-1">Sinal:</span>
  <button class="tab-btn active" data-ftype="sig" data-fval="">Todos</button>
  <button class="tab-btn" data-ftype="sig" data-fval="buy">🟢 Compra</button>
  <button class="tab-btn" data-ftype="sig" data-fval="sell">🔴 Venda/Stop</button>
</div>

<!-- MAIN GRID -->
<div class="flex gap-3 p-4" style="height:calc(100vh - 110px)">

  <!-- TABLE -->
  <div class="flex-1 glass rounded-xl overflow-hidden flex flex-col min-w-0">
    <div class="px-4 py-2 border-b border-white/10 flex items-center gap-2">
      <span class="text-yellow-400">🏆</span>
      <span class="font-semibold text-sm text-white">TOP OPORTUNIDADES — AO VIVO</span>
      <span id="opp-count" class="text-xs text-slate-500 ml-auto"></span>
    </div>
    <div class="overflow-auto flex-1">
      <table class="w-full text-xs">
        <thead class="sticky top-0 z-10" style="background:#0f172a">
          <tr class="text-slate-400 text-left">
            <th class="px-2 py-2 w-6">#</th>
            <th class="px-2 py-2 w-10">Cls</th>
            <th class="px-2 py-2 w-10">Tipo</th>
            <th class="px-2 py-2">Ticker</th>
            <th class="px-2 py-2">Nome</th>
            <th class="px-2 py-2">Sinal</th>
            <th class="px-2 py-2 text-right">Preço</th>
            <th class="px-2 py-2 text-right">Var%</th>
            <th class="px-2 py-2 text-right">RSI</th>
            <th class="px-2 py-2 text-right">Entrada</th>
            <th class="px-2 py-2 text-right">Stop</th>
            <th class="px-2 py-2 text-right">Alvo</th>
            <th class="px-2 py-2 text-right">R:R</th>
            <th class="px-2 py-2 w-28">Score</th>
            <th class="px-2 py-2 text-center">Conf</th>
          </tr>
        </thead>
        <tbody id="opp-table"></tbody>
      </table>
    </div>
  </div>

  <!-- DETAIL PANEL -->
  <div id="detail" class="w-72 glass rounded-xl flex-col hidden lg:flex overflow-y-auto">
    <div class="px-4 py-3 border-b border-white/10">
      <span class="text-slate-400 text-xs">Clique em uma linha para detalhes</span>
    </div>
    <div id="detail-body" class="p-4 flex flex-col gap-4 text-xs">
      <div class="text-slate-600 text-center mt-8">Selecione um ativo</div>
    </div>
  </div>

</div>

<!-- LEGEND -->
<div class="px-4 py-1 text-xs text-slate-600 border-t border-white/5 flex flex-wrap gap-4">
  <span>Score: <span class="text-green-400">85+ Muito forte</span> <span class="text-green-600">70+ Relevante</span> <span class="text-yellow-500">55+ Moderada</span> <span class="text-orange-400">40+ Observação</span> <span class="text-red-500">&lt;40 Descartar</span></span>
  <span>Tipo: <span class="text-purple-400">DT</span>=Day Trade <span class="text-blue-400">SW</span>=Swing <span class="text-green-600">POS</span>=Posição</span>
  <span>Conf: ●●●=Alto ●●○=Médio ●○○=Baixo</span>
  <span class="ml-auto">⚠️ Não constitui recomendação de investimento</span>
</div>

<script>
const MEDALS = ['🥇','🥈','🥉','④','⑤','⑥','⑦','⑧','⑨','⑩','⑪','⑫','⑬','⑭','⑮','⑯','⑰','⑱','⑲','⑳'];
let allOpps = [];
let filters = { cls:'', op:'', sig:'' };
let selectedTicker = null;
let scoreChart = null;
let prevPrices = {};

// ── FILTROS ──────────────────────────────────────────────────────────────────
// Usar data-attributes para evitar problemas de encoding com 'Ação'
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.dataset.ftype;
      const val  = btn.dataset.fval;
      if (!type) return;
      filters[type] = val;
      document.querySelectorAll(`.tab-btn[data-ftype="${type}"]`).forEach(b =>
        b.classList.toggle('active', b.dataset.fval === val));
      renderTable();
    });
  });
});

function setFilter(type, val) {
  filters[type] = val;
  document.querySelectorAll(`.tab-btn[data-ftype="${type}"]`).forEach(b =>
    b.classList.toggle('active', b.dataset.fval === val));
  renderTable();
}

function signalClass(sig) {
  if (sig.includes('FORTE'))      return 'signal-buy-strong';
  if (sig.includes('COMPRA ESPEC')) return 'signal-buy-spec';
  if (sig.includes('COMPRA'))     return 'signal-buy';
  if (sig.includes('OBSERV'))     return 'signal-watch';
  if (sig.includes('VENDA PARC')) return 'signal-partial';
  if (sig.includes('VENDA'))      return 'signal-sell';
  if (sig.includes('STOP'))       return 'signal-stop';
  if (sig.includes('HEDGE'))      return 'signal-hedge';
  return 'signal-wait';
}

function clsBadge(cls) {
  const map = {
    'Ação':'badge-acao','FII':'badge-fii','ETF':'badge-etf',
    'BDR':'badge-bdr','Cripto':'badge-crp',
    'Dólar':'badge-dol','Opção':'badge-opc'
  };
  const lbl = {
    'Ação':'AÇÃo','FII':'FII','ETF':'ETF','BDR':'BDR',
    'Cripto':'CRP','Dólar':'DOL','Opção':'OPC'
  };
  return `<span class="badge ${map[cls]||'badge-acao'}">${lbl[cls]||cls.substring(0,3)}</span>`;
}

function opBadge(op) {
  const map = {'DT':'badge-dt','SW':'badge-sw','POS':'badge-pos'};
  return `<span class="badge ${map[op]||'badge-acao'}">${op}</span>`;
}

function scoreColor(s) {
  if (s >= 85) return '#22c55e';
  if (s >= 70) return '#4ade80';
  if (s >= 55) return '#facc15';
  if (s >= 40) return '#fb923c';
  return '#f87171';
}

function varColor(v) { return v >= 0 ? '#22c55e' : '#f87171'; }

function rsiColor(r) {
  if (!r) return '#94a3b8';
  if (r < 30) return '#22c55e';
  if (r > 70) return '#f87171';
  return '#94a3b8';
}

function confDots(c) {
  if (c === 'Alto')  return '<span style="color:#22c55e">●●●</span>';
  if (c === 'Médio') return '<span style="color:#facc15">●●</span><span style="color:#334155">●</span>';
  return '<span style="color:#f87171">●</span><span style="color:#334155">●●</span>';
}

function fmt(v, prefix='R$', dec=2) {
  if (v == null) return '<span class="text-slate-600">-</span>';
  return `${prefix}${Number(v).toFixed(dec)}`;
}

function filterOpps() {
  return allOpps
    .filter(o => {
      if (filters.cls && o.cls !== filters.cls) return false;
      if (filters.op  && o.op_type !== filters.op)  return false;
      if (filters.sig === 'buy'  && !o.signal.includes('COMPRA')) return false;
      if (filters.sig === 'sell' && !o.signal.match(/VENDA|STOP/))return false;
      return true;
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 20);
}

function renderTable() {
  const opps = filterOpps();
  document.getElementById('opp-count').textContent = `${opps.length} ativos`;
  const tb = document.getElementById('opp-table');
  if (!opps.length) {
    tb.innerHTML = `<tr><td colspan="15" class="text-center py-12 text-slate-600">Nenhuma oportunidade encontrada com os filtros selecionados</td></tr>`;
    return;
  }
  tb.innerHTML = opps.map((o, i) => {
    const sc   = o.score;
    const scC  = scoreColor(sc);
    const sel  = o.ticker === selectedTicker ? 'background:rgba(59,130,246,.12)!important;' : '';
    return `<tr data-ticker="${o.ticker}" onclick="selectTicker('${o.ticker}')" style="${sel}">
      <td class="px-2 py-2 text-slate-500">${MEDALS[i]||i+1}</td>
      <td class="px-2 py-2">${clsBadge(o.cls)}</td>
      <td class="px-2 py-2">${opBadge(o.op_type)}</td>
      <td class="px-2 py-2 font-mono font-bold text-white">${o.ticker}</td>
      <td class="px-2 py-2 text-slate-400 max-w-[120px] truncate">${o.name}</td>
      <td class="px-2 py-2"><span class="${signalClass(o.signal)}">${o.signal_emoji} ${o.signal}</span></td>
      <td class="px-2 py-2 text-right font-mono text-white">R$${Number(o.price).toFixed(2)}</td>
      <td class="px-2 py-2 text-right font-mono" style="color:${varColor(o.var_day)}">${o.var_day >= 0 ? '+' : ''}${o.var_day.toFixed(2)}%</td>
      <td class="px-2 py-2 text-right font-mono" style="color:${rsiColor(o.rsi)}">${o.rsi ?? '-'}</td>
      <td class="px-2 py-2 text-right font-mono text-slate-300">${o.entry != null ? 'R$'+Number(o.entry).toFixed(2) : '-'}</td>
      <td class="px-2 py-2 text-right font-mono text-red-400">${o.stop != null ? 'R$'+Number(o.stop).toFixed(2) : '-'}</td>
      <td class="px-2 py-2 text-right font-mono text-green-400">${o.target != null ? 'R$'+Number(o.target).toFixed(2) : '-'}</td>
      <td class="px-2 py-2 text-right font-mono" style="color:${o.rr >= 2 ? '#22c55e' : o.rr >= 1.5 ? '#facc15' : '#f87171'}">${o.rr > 0 ? o.rr.toFixed(1)+'x' : '-'}</td>
      <td class="px-2 py-2 w-28">
        <div class="flex items-center gap-1">
          <div class="score-bar flex-1"><div class="score-fill" style="width:${sc}%;background:${scC}"></div></div>
          <span class="font-bold font-mono text-xs w-7 text-right" style="color:${scC}">${sc.toFixed(0)}</span>
        </div>
      </td>
      <td class="px-2 py-2 text-center text-xs">${confDots(o.confidence)}</td>
    </tr>`;
  }).join('');
}

function selectTicker(ticker) {
  selectedTicker = ticker;
  const o = allOpps.find(x => x.ticker === ticker);
  if (!o) return;
  renderTable();
  renderDetail(o);
}

function renderDetail(o) {
  const scC = scoreColor(o.score);
  const riskPct = o.entry && o.stop ? Math.abs((o.entry - o.stop) / o.entry * 100).toFixed(2) : null;
  const gainPct = o.entry && o.target ? Math.abs((o.target - o.entry) / o.entry * 100).toFixed(2) : null;

  // Se já está mostrando o mesmo ticker, apenas atualiza os valores dinâmicos sem recriar o gráfico
  if (document.getElementById('detail-ticker')?.textContent === o.ticker) {
    document.getElementById('detail-price').textContent    = 'R$' + Number(o.price).toFixed(2);
    document.getElementById('detail-var').textContent      = (o.var_day >= 0 ? '+' : '') + o.var_day.toFixed(2) + '%';
    document.getElementById('detail-var').style.color      = varColor(o.var_day);
    document.getElementById('detail-rsi').textContent      = o.rsi ?? '-';
    document.getElementById('detail-rsi').style.color      = rsiColor(o.rsi);
    document.getElementById('detail-updated').textContent  = 'Atualizado: ' + o.updated;
    return;
  }

  const reasonsHtml = (o.reasons || []).map(r => `<li class="text-green-400">+ ${r}</li>`).join('');
  const risksHtml   = (o.risks   || []).map(r => `<li class="text-red-400">− ${r}</li>`).join('');

  document.getElementById('detail-body').innerHTML = `
    <div>
      <div class="flex items-center justify-between mb-1">
        <span id="detail-ticker" class="text-xl font-bold text-white">${o.ticker}</span>
        <span class="${signalClass(o.signal)} text-sm">${o.signal_emoji} ${o.signal}</span>
      </div>
      <div class="text-slate-500 text-xs">${o.name}</div>
      <div class="flex gap-2 mt-2">${clsBadge(o.cls)} ${opBadge(o.op_type)}</div>
    </div>

    <div class="glass rounded-lg p-3 grid grid-cols-2 gap-2 text-xs">
      <div><div class="text-slate-500">Preço</div><div id="detail-price" class="font-mono font-bold text-white">R$${Number(o.price).toFixed(2)}</div></div>
      <div><div class="text-slate-500">Var dia</div><div id="detail-var" class="font-mono" style="color:${varColor(o.var_day)}">${o.var_day >= 0 ? '+' : ''}${o.var_day.toFixed(2)}%</div></div>
      <div><div class="text-slate-500">Entrada</div><div class="font-mono text-white">${o.entry ? 'R$'+Number(o.entry).toFixed(2) : '-'}</div></div>
      <div><div class="text-slate-500">Stop${riskPct ? ' ('+riskPct+'%)' : ''}</div><div class="font-mono text-red-400">${o.stop ? 'R$'+Number(o.stop).toFixed(2) : '-'}</div></div>
      <div><div class="text-slate-500">Alvo${gainPct ? ' ('+gainPct+'%)' : ''}</div><div class="font-mono text-green-400">${o.target ? 'R$'+Number(o.target).toFixed(2) : '-'}</div></div>
      <div><div class="text-slate-500">R:R</div><div class="font-mono" style="color:${o.rr >= 2 ? '#22c55e' : '#facc15'}">${o.rr > 0 ? o.rr.toFixed(1)+'x' : '-'}</div></div>
      <div><div class="text-slate-500">RSI</div><div id="detail-rsi" class="font-mono" style="color:${rsiColor(o.rsi)}">${o.rsi ?? '-'}</div></div>
      <div><div class="text-slate-500">Tendência</div><div class="font-mono">${o.trend || '-'}</div></div>
    </div>

    <div>
      <div class="text-slate-400 font-semibold mb-2">Score: <span style="color:${scC}">${o.score.toFixed(0)}/100</span></div>
      <canvas id="scoreChart" height="160"></canvas>
    </div>

    <div>
      <div class="text-slate-400 font-semibold mb-1">Motivos</div>
      <ul class="space-y-1 text-xs">${reasonsHtml || '<li class="text-slate-600">Nenhum detectado</li>'}</ul>
    </div>
    <div>
      <div class="text-slate-400 font-semibold mb-1">Riscos</div>
      <ul class="space-y-1 text-xs">${risksHtml || '<li class="text-slate-600">Nenhum detectado</li>'}</ul>
    </div>
    ${o.pattern ? `<div class="glass rounded p-2 text-center text-xs text-blue-300">📊 ${o.pattern}</div>` : ''}
    <div id="detail-updated" class="text-slate-600 text-center text-xs">Atualizado: ${o.updated}</div>
  `;

  // Radar chart com campos flat do backend
  if (scoreChart) { scoreChart.destroy(); scoreChart = null; }
  setTimeout(() => {
    const ctx = document.getElementById('scoreChart');
    if (!ctx) return;
    scoreChart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Técnica','Fundam.','Macro','Sentim.','Liquidez','R:R','Backtest','Timing'],
        datasets: [{
          data: [
            o.score_tech  || 0,
            o.score_fund  || 0,
            o.score_macro || 0,
            o.score_sent  || 0,
            o.score_liq   || 0,
            o.score_rr    || 0,
            o.score_bt    || 0,
            o.score_time  || 0,
          ],
          backgroundColor: 'rgba(59,130,246,.2)',
          borderColor: '#3b82f6',
          pointBackgroundColor: '#3b82f6',
          borderWidth: 2,
        }]
      },
      options: {
        responsive:true, maintainAspectRatio:true,
        plugins:{ legend:{display:false} },
        scales: {
          r: {
            min:0, max:20,
            ticks:{ display:false },
            grid:{ color:'rgba(255,255,255,.08)' },
            pointLabels:{ color:'#94a3b8', font:{size:9} },
            angleLines:{ color:'rgba(255,255,255,.08)' },
          }
        }
      }
    });
  }, 50);
}

function updateMacro(d) {
  document.getElementById('ts').textContent = d.ts;
  if (d.selic)  document.getElementById('selic').textContent = d.selic.toFixed(2) + '%';
  if (d.ipca)   document.getElementById('ipca').textContent  = d.ipca.toFixed(2) + '%';
  if (d.ibov) {
    document.getElementById('ibov').textContent = Number(d.ibov).toLocaleString('pt-BR', {maximumFractionDigits:0});
    if (d.ibov_var != null) {
      const el = document.getElementById('ibov_var');
      el.textContent = (d.ibov_var >= 0 ? '+' : '') + d.ibov_var.toFixed(2) + '%';
      el.style.color = varColor(d.ibov_var);
    }
  }
  if (d.dolar) {
    document.getElementById('dolar').textContent = 'R$' + Number(d.dolar).toFixed(2);
    if (d.dolar_var != null) {
      const el = document.getElementById('dolar_var');
      el.textContent = (d.dolar_var >= 0 ? '+' : '') + d.dolar_var.toFixed(2) + '%';
      el.style.color = varColor(d.dolar_var);
    }
  }
  const pct = d.total ? d.scanned / d.total * 100 : 0;
  document.getElementById('scan-bar').style.width = pct + '%';
  document.getElementById('scan-txt').textContent = `${d.scanned}/${d.total} (${pct.toFixed(0)}%) — ${d.current}`;
}

// WebSocket
function connect() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws`);
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    updateMacro(d);
    // detectar preços mudados e piscar a linha
    (d.opps || []).forEach(o => {
      if (prevPrices[o.ticker] != null && prevPrices[o.ticker] !== o.price) {
        const row = document.querySelector(`tr[data-ticker="${o.ticker}"]`);
        if (row) {
          row.style.transition = 'background .3s';
          row.style.background = o.price > prevPrices[o.ticker]
            ? 'rgba(34,197,94,.18)' : 'rgba(239,68,68,.18)';
          setTimeout(() => row.style.background = '', 800);
        }
      }
      prevPrices[o.ticker] = o.price;
    });
    allOpps = d.opps || [];
    renderTable();
    if (selectedTicker) {
      const o = allOpps.find(x => x.ticker === selectedTicker);
      if (o) renderDetail(o);
    }
  };
  ws.onclose = () => setTimeout(connect, 3000);
}

connect();
</script>
</body>
</html>"""
