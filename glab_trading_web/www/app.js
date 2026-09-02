/**
 * G-Lab Trading — paper demo (Faza 1)
 * Kasnije: sync sa Postgres/PostgREST na HA (kao Petko).
 */

const STORAGE_KEY = "glab_trading_paper_v1";
const START_BALANCE = 10000;
const LEVERAGE = 100;
const CONTRACT_SIZE = { XAUUSD: 100, EURUSD: 100000, GBPUSD: 100000 };
const SPREAD = { XAUUSD: 0.30, EURUSD: 0.00012, GBPUSD: 0.00015 };
const BASE_PRICES = { XAUUSD: 2650, EURUSD: 1.085, GBPUSD: 1.265 };

let selectedSide = "BUY";
let chart = null;
let candleSeries = null;
let priceLine = null;
let tickTimer = null;

const state = loadState();

function defaultState() {
  return {
    balance: START_BALANCE,
    realizedPnl: 0,
    positions: [],
    closed: [],
    nextId: 1,
    symbol: "XAUUSD",
    timeframe: "5",
    prices: { ...BASE_PRICES },
    candles: {},
  };
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw);
    return { ...defaultState(), ...parsed, prices: { ...BASE_PRICES, ...parsed.prices } };
  } catch {
    return defaultState();
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function symbol() {
  return document.getElementById("symbolSelect").value;
}

function fmt(n, digits = 2) {
  if (n == null || Number.isNaN(n)) return "—";
  return Number(n).toFixed(digits);
}

function fmtPnl(n) {
  const s = (n >= 0 ? "+" : "") + fmt(n, 2);
  return s;
}

function bidAsk(sym) {
  const mid = state.prices[sym] ?? BASE_PRICES[sym];
  const half = (SPREAD[sym] ?? 0.0001) / 2;
  return { bid: mid - half, ask: mid + half, mid };
}

function contractSize(sym) {
  return CONTRACT_SIZE[sym] ?? 100000;
}

function marginRequired(sym, lot, price) {
  return (lot * contractSize(sym) * price) / LEVERAGE;
}

function positionPnl(pos) {
  const { bid, ask } = bidAsk(pos.symbol);
  const exit = pos.side === "BUY" ? bid : ask;
  const diff = pos.side === "BUY" ? exit - pos.entry : pos.entry - exit;
  return diff * pos.lot * contractSize(pos.symbol);
}

function totalUnrealized() {
  return state.positions.reduce((sum, p) => sum + positionPnl(p), 0);
}

function totalMarginUsed() {
  return state.positions.reduce((sum, p) => sum + marginRequired(p.symbol, p.lot, p.entry), 0);
}

function equity() {
  return state.balance + totalUnrealized();
}

function freeMargin() {
  return equity() - totalMarginUsed();
}

function ensureCandles(sym, tf) {
  const key = `${sym}_${tf}`;
  if (state.candles[key]?.length) return state.candles[key];
  const bars = [];
  const now = Math.floor(Date.now() / 1000);
  const step = tf === "D" ? 86400 : Number(tf) * 60;
  let price = state.prices[sym] ?? BASE_PRICES[sym];
  for (let i = 120; i >= 0; i--) {
    const t = now - i * step;
    const o = price;
    const move = (Math.random() - 0.5) * (sym === "XAUUSD" ? 2 : 0.001);
    const c = o + move;
    const h = Math.max(o, c) + Math.random() * (sym === "XAUUSD" ? 0.8 : 0.0004);
    const l = Math.min(o, c) - Math.random() * (sym === "XAUUSD" ? 0.8 : 0.0004);
    bars.push({ time: t, open: o, high: h, low: l, close: c });
    price = c;
  }
  state.prices[sym] = price;
  state.candles[key] = bars;
  return bars;
}

function initChart() {
  const el = document.getElementById("chart");
  el.innerHTML = "";
  chart = LightweightCharts.createChart(el, {
    layout: { background: { color: "#12161c" }, textColor: "#8b97a8" },
    grid: { vertLines: { color: "#1f2733" }, horzLines: { color: "#1f2733" } },
    rightPriceScale: { borderColor: "#2a3340" },
    timeScale: { borderColor: "#2a3340" },
  });
  candleSeries = chart.addCandlestickSeries({
    upColor: "#26a69a", downColor: "#ef5350", borderVisible: false,
    wickUpColor: "#26a69a", wickDownColor: "#ef5350",
  });
  window.addEventListener("resize", () => chart.applyOptions({ width: el.clientWidth, height: 400 }));
}

function refreshChart() {
  const sym = symbol();
  const tf = document.getElementById("timeframeSelect").value;
  const bars = ensureCandles(sym, tf);
  candleSeries.setData(bars);
  chart.timeScale().fitContent();
}

function tickPrice() {
  const sym = symbol();
  const vol = sym === "XAUUSD" ? 0.35 : 0.00008;
  state.prices[sym] += (Math.random() - 0.5) * vol;
  const tf = document.getElementById("timeframeSelect").value;
  const key = `${sym}_${tf}`;
  const bars = ensureCandles(sym, tf);
  const last = bars[bars.length - 1];
  const now = Math.floor(Date.now() / 1000);
  const step = tf === "D" ? 86400 : Number(tf) * 60;
  const t = Math.floor(now / step) * step;
  if (last.time === t) {
    last.close = state.prices[sym];
    last.high = Math.max(last.high, last.close);
    last.low = Math.min(last.low, last.close);
  } else {
    bars.push({
      time: t,
      open: last.close,
      high: state.prices[sym],
      low: state.prices[sym],
      close: state.prices[sym],
    });
    if (bars.length > 200) bars.shift();
  }
  candleSeries.update(bars[bars.length - 1]);
  checkStops();
  renderAll();
}

function openPosition(side, lot, sl, tp) {
  const sym = symbol();
  const { bid, ask } = bidAsk(sym);
  const entry = side === "BUY" ? ask : bid;
  const need = marginRequired(sym, lot, entry);
  if (need > freeMargin() + 0.01) {
    setStatus("Nedovoljna slobodna margina za ovaj lot.");
    return;
  }
  state.positions.push({
    id: state.nextId++,
    symbol: sym,
    side,
    lot,
    entry,
    sl: sl || null,
    tp: tp || null,
    openedAt: new Date().toISOString(),
  });
  saveState();
  setStatus(`${side} ${sym} ${lot} lot @ ${fmt(entry)} otvoreno.`);
  renderAll();
}

function closePosition(id, reason = "Manual") {
  const idx = state.positions.findIndex((p) => p.id === id);
  if (idx < 0) return;
  const pos = state.positions[idx];
  const pnl = positionPnl(pos);
  const { bid, ask } = bidAsk(pos.symbol);
  const exit = pos.side === "BUY" ? bid : ask;
  state.balance += pnl;
  state.realizedPnl += pnl;
  state.closed.unshift({
    id: pos.id,
    symbol: pos.symbol,
    side: pos.side,
    lot: pos.lot,
    entry: pos.entry,
    exit,
    pnl,
    reason,
    closedAt: new Date().toISOString(),
  });
  state.positions.splice(idx, 1);
  if (state.closed.length > 100) state.closed.length = 100;
  saveState();
  setStatus(`Pozicija #${id} zatvorena (${reason}). P/L ${fmtPnl(pnl)}`);
  renderAll();
}

function checkStops() {
  for (const pos of [...state.positions]) {
    const { bid, ask } = bidAsk(pos.symbol);
    const px = pos.side === "BUY" ? bid : ask;
    if (pos.sl != null) {
      if (pos.side === "BUY" && px <= pos.sl) { closePosition(pos.id, "SL"); continue; }
      if (pos.side === "SELL" && px >= pos.sl) { closePosition(pos.id, "SL"); continue; }
    }
    if (pos.tp != null) {
      if (pos.side === "BUY" && px >= pos.tp) { closePosition(pos.id, "TP"); continue; }
      if (pos.side === "SELL" && px <= pos.tp) { closePosition(pos.id, "TP"); continue; }
    }
  }
}

function renderQuote() {
  const sym = symbol();
  const { bid, ask } = bidAsk(sym);
  const spread = ask - bid;
  const digits = sym === "XAUUSD" ? 2 : 5;
  document.getElementById("bidPrice").textContent = fmt(bid, digits);
  document.getElementById("askPrice").textContent = fmt(ask, digits);
  document.getElementById("spreadPrice").textContent = fmt(spread, digits);
}

function renderAccount() {
  const u = totalUnrealized();
  const eq = equity();
  document.getElementById("balanceVal").textContent = "$" + fmt(state.balance);
  document.getElementById("equityVal").textContent = "$" + fmt(eq);
  document.getElementById("marginVal").textContent = "$" + fmt(totalMarginUsed());
  document.getElementById("freeMarginVal").textContent = "$" + fmt(freeMargin());
  document.getElementById("headerEquity").textContent = "$" + fmt(eq);

  const uEl = document.getElementById("unrealizedVal");
  uEl.textContent = fmtPnl(u);
  uEl.className = "pnl " + (u >= 0 ? "positive" : "negative");

  const rEl = document.getElementById("realizedVal");
  rEl.textContent = fmtPnl(state.realizedPnl);
  rEl.className = "pnl " + (state.realizedPnl >= 0 ? "positive" : "negative");
}

function renderOpenTable() {
  const body = document.getElementById("openBody");
  body.innerHTML = "";
  document.getElementById("openCount").textContent = String(state.positions.length);
  const digits = (s) => (s === "XAUUSD" ? 2 : 5);

  for (const pos of state.positions) {
    const { bid, ask } = bidAsk(pos.symbol);
    const cur = pos.side === "BUY" ? bid : ask;
    const pnl = positionPnl(pos);
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${pos.symbol}</td>
      <td class="${pos.side === "BUY" ? "row-buy" : "row-sell"}">${pos.side}</td>
      <td>${fmt(pos.lot, 2)}</td>
      <td>${fmt(pos.entry, digits(pos.symbol))}</td>
      <td>${fmt(cur, digits(pos.symbol))}</td>
      <td>${pos.sl != null ? fmt(pos.sl, digits(pos.symbol)) : "—"}</td>
      <td>${pos.tp != null ? fmt(pos.tp, digits(pos.symbol)) : "—"}</td>
      <td class="${pnl >= 0 ? "row-buy" : "row-sell"}">${fmtPnl(pnl)}</td>
      <td><button class="btn-close" data-id="${pos.id}">Close</button></td>`;
    body.appendChild(tr);
  }
  body.querySelectorAll(".btn-close").forEach((btn) => {
    btn.addEventListener("click", () => closePosition(Number(btn.dataset.id), "Manual"));
  });
}

function renderClosedTable() {
  const body = document.getElementById("closedBody");
  body.innerHTML = "";
  const digits = (s) => (s === "XAUUSD" ? 2 : 5);
  for (const row of state.closed.slice(0, 50)) {
    const tr = document.createElement("tr");
    const t = new Date(row.closedAt).toLocaleString("sr-RS");
    tr.innerHTML = `
      <td>${t}</td>
      <td>${row.symbol}</td>
      <td class="${row.side === "BUY" ? "row-buy" : "row-sell"}">${row.side}</td>
      <td>${fmt(row.lot, 2)}</td>
      <td>${fmt(row.entry, digits(row.symbol))}</td>
      <td>${fmt(row.exit, digits(row.symbol))}</td>
      <td class="${row.pnl >= 0 ? "row-buy" : "row-sell"}">${fmtPnl(row.pnl)}</td>
      <td>${row.reason}</td>`;
    body.appendChild(tr);
  }
}

function renderAll() {
  renderQuote();
  renderAccount();
  renderOpenTable();
  renderClosedTable();
}

function setStatus(msg) {
  document.getElementById("statusLine").textContent = msg;
}

function bindUi() {
  document.querySelectorAll(".side-toggle button").forEach((btn) => {
    btn.addEventListener("click", () => {
      selectedSide = btn.dataset.side;
      document.querySelectorAll(".side-toggle button").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });

  document.getElementById("sendOrderBtn").addEventListener("click", () => {
    const lot = Number(document.getElementById("lotInput").value);
    const sl = document.getElementById("slInput").value ? Number(document.getElementById("slInput").value) : null;
    const tp = document.getElementById("tpInput").value ? Number(document.getElementById("tpInput").value) : null;
    if (!lot || lot <= 0) {
      setStatus("Unesi ispravan lot.");
      return;
    }
    openPosition(selectedSide, lot, sl, tp);
  });

  document.getElementById("symbolSelect").addEventListener("change", () => {
    refreshChart();
    renderAll();
  });
  document.getElementById("timeframeSelect").addEventListener("change", refreshChart);

  document.getElementById("resetBtn").addEventListener("click", () => {
    if (!confirm("Reset demo naloga na $10,000?")) return;
    Object.assign(state, defaultState());
    saveState();
    refreshChart();
    renderAll();
    setStatus("Demo nalog resetovan.");
  });
}

function start() {
  initChart();
  document.getElementById("symbolSelect").value = state.symbol || "XAUUSD";
  document.getElementById("timeframeSelect").value = state.timeframe || "5";
  bindUi();
  refreshChart();
  renderAll();
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = setInterval(tickPrice, 1500);
  setStatus("Paper trading aktivan — simulirana cena (Faza 1).");
}

start();
