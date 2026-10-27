"use strict";

// ---------------------------------------------------------------- ícones (traço 24x24)
const ICONS = {
  home: "M3 11l9-8 9 8v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  signal: "M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M7.8 7.8a6 6 0 0 0 0 8.4 M16.2 7.8a6 6 0 0 1 0 8.4 M4.9 4.9a10 10 0 0 0 0 14.2 M19.1 4.9a10 10 0 0 1 0 14.2",
  router: "M3 14h18v6H3z M7 17h.01 M11 17h.01 M8.5 10.5a5 5 0 0 1 7 0 M5.5 7.5a9.5 9.5 0 0 1 13 0",
  bolt: "M13 2L4 14h7l-1 8 9-12h-7z",
  wifi: "M5 12.5a10 10 0 0 1 14 0 M8.5 16a5 5 0 0 1 7 0 M2 9a15 15 0 0 1 20 0 M12 20h.01",
  gear: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z",
  help: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3 M12 17h.01",
  shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z",
  pulse: "M22 12h-4l-3 9L9 3l-3 9H2",
  search: "M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M21 21l-4.3-4.3",
  chev: "M9 18l6-6-6-6",
  power: "M18.4 6.6a9 9 0 1 1-12.8 0 M12 2v10",
  heart: "M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8z",
  play: "M6 4l14 8-14 8z",
  plus: "M12 5v14 M5 12h14",
  x: "M18 6L6 18 M6 6l12 12",
  broom: "M19 3l-7 7 M9.5 10.5l4 4 M4 21c0-4 2-8 5.5-10.5l4 4C11 18 7 20 4 21z",
  refresh: "M21 12a9 9 0 1 1-3-6.7L21 8 M21 3v5h-5",
  trash: "M3 6h18 M8 6V4h8v2 M19 6l-1 14H6L5 6",
  gamepad: "M6 12h4 M8 10v4 M15 13h.01 M18 11h.01 M17.3 5H6.7a4 4 0 0 0-4 3.6L2 15a3 3 0 0 0 5.3 2.1L9 15h6l1.7 2.1A3 3 0 0 0 22 15l-.7-6.4A4 4 0 0 0 17.3 5z",
  record: "M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  cpu: "M6 6h12v12H6z M9 9h6v6H9z M9 2v4 M15 2v4 M9 18v4 M15 18v4 M2 9h4 M2 15h4 M18 9h4 M18 15h4",
  gauge: "M12 14l4-4 M3.3 19a10 10 0 1 1 17.4 0z",
  target: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  gpu: "M2 7h18v10H2z M20 10h2 M20 14h2 M6 17v3 M10 17v3 M8 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M15 12h.01",
  mouse: "M12 2a6 6 0 0 0-6 6v8a6 6 0 0 0 12 0V8a6 6 0 0 0-6-6z M12 6v4",
  apps: "M4 4h6v6H4z M14 4h6v6h-6z M4 14h6v6H4z M14 14h6v6h-6z",
  network: "M9 3h6v5H9z M3 16h6v5H3z M15 16h6v5h-6z M12 8v4 M6 16v-4h12v4",
  speed: "M12 12l3-5 M4.9 19.1A10 10 0 1 1 19.1 19.1 M12 12h.01",
  upload: "M12 15V3 M7 8l5-5 5 5 M4 17v3h16v-3",
  route: "M6 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M18 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4z M8 17h8a3 3 0 0 0 0-6H8a3 3 0 0 1 0-6h8",
  tunnel: "M3 20v-8a9 9 0 0 1 18 0v8 M8 20v-7a4 4 0 0 1 8 0v7",
  eye: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 3l18 18",
  store: "M4 7h16l-1 13H5z M9 7a3 3 0 0 1 6 0",
  plug: "M9 2v6 M15 2v6 M6 8h12v4a6 6 0 0 1-12 0z M12 18v4",
  flag: "M4 22V4 M4 4h13l-2 4 2 4H4",
  chip: "M7 7h10v10H7z M10 2v5 M14 2v5 M10 17v5 M14 17v5 M2 10h5 M2 14h5 M17 10h5 M17 14h5",
  download: "M12 3v12 M7 10l5 5 5-5 M4 17v3h16v-3",
  memory: "M3 7h18v10H3z M7 7v10 M11 7v10 M15 7v10 M3 20h2 M19 20h2",
  check: "M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z M8 12l3 3 5-6",
  server: "M3 4h18v6H3z M3 14h18v6H3z M7 7h.01 M7 17h.01",
  "eye-open": "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  back: "M19 12H5 M12 19l-7-7 7-7",
  lang: "M4 5h8 M8 3v2 M5 9c1 3 4 5 6 6 M11 5c-1 4-4 7-7 9 M13 21l4-9 4 9 M14.5 18h5",
  window: "M3 5h18v14H3z M3 9h18",
  bell: "M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9 M10.3 21a1.9 1.9 0 0 0 3.4 0",
  palette: "M12 22a10 10 0 1 1 10-10c0 2.5-2 3.5-4 3.5h-2a2 2 0 0 0-1.5 3.3A2 2 0 0 1 12 22z M7.5 11h.01 M10.5 7h.01 M15 7.5h.01 M17 11h.01",
};
const svg = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="${ICONS[name] || ICONS.help}"/></svg>`;
function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((el) => { if (!el.firstChild) el.innerHTML = svg(el.dataset.icon); });
}

// ---------------------------------------------------------------- utilidades
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const ms = (v) => (v == null ? "—" : `${Math.round(v)} ms`);
const pct = (v) => (v == null ? "—" : `${Math.round(v)} %`);
const QUALITY = { good: "Bom", fair: "Regular", bad: "Ruim", down: "Sem resposta", none: "—" };
const PRIORITY = { High: "Alta", AboveNormal: "Acima do normal", Normal: "Normal" };
const sleep = (t) => new Promise((r) => setTimeout(r, t));

function duration(sec) {
  const h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
  return [h, m, s].map((n) => String(n).padStart(2, "0")).join(":");
}

function toast(msg, err = false) {
  const el = document.createElement("div");
  el.className = "toast" + (err ? " err" : "");
  el.textContent = msg;
  $("#toasts").appendChild(el);
  setTimeout(() => el.remove(), err ? 7000 : 3500);
}

// ponte com o Python: pywebview (janela) ou HTTP (modo --browser)
// O pywebview também serve a página por HTTP (servidor interno dele), então o protocolo não diz nada:
// só o servidor de testes (app.py --browser) marca <html data-pp-http="token">. Na janela, window.pywebview
// aparece antes de as funções da API serem injetadas, por isso espera até a função existir de fato.
const HTTP_TOKEN = document.documentElement.dataset.ppHttp || "";
const IN_WINDOW = !HTTP_TOKEN;
let bridgePromise = null;
function bridgeReady() {
  if (!IN_WINDOW) return Promise.resolve();
  bridgePromise ??= new Promise((resolve, reject) => {
    const started = Date.now();
    (function wait() {
      if (typeof window.pywebview?.api?.settings_get === "function") return resolve();
      if (Date.now() - started > 20000) return reject(new Error("A ponte com o PingPilot não respondeu."));
      setTimeout(wait, 50);
    })();
  });
  return bridgePromise;
}
function reportError(message, where) {
  try { window.pywebview?.api?.report_error(String(message), where); } catch { /* sem ponte, sem log */ }
}
window.addEventListener("error", (e) => reportError(`${e.message} (${e.filename}:${e.lineno})`, "js"));
window.addEventListener("unhandledrejection", (e) => reportError(e.reason?.stack || e.reason, "promise"));

async function call(name, ...args) {
  if (IN_WINDOW) {
    await bridgeReady();
    try { return await window.pywebview.api[name](...args); }
    catch (e) {
      if (name !== "report_error") reportError(e?.message || String(e), name);
      throw new Error(e?.message || String(e));
    }
  }
  const r = await fetch("/api/" + name, { method: "POST", body: JSON.stringify(args), headers: { "X-PP-Token": HTTP_TOKEN } });
  const j = await r.json();
  if (j.error) throw new Error(j.error);
  return j.result;
}
async function safe(name, ...args) {
  try { return await call(name, ...args); }
  catch (e) { toast(e.message, true); return undefined; }
}
async function waitJob(jid, onProgress) {
  for (;;) {
    const j = await call("job", jid);
    if (onProgress && j.progress != null) onProgress(j.progress);
    if (j.done) { if (j.error) throw new Error(j.error); return j.result; }
    await sleep(500);
  }
}
async function busy(btn, fn) {
  const html = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `<span class="spin"></span>${esc(btn.textContent.trim())}`;
  try { return await fn(); }
  catch (e) { toast(e.message, true); }
  finally { btn.disabled = false; btn.innerHTML = html; }
}

// ---------------------------------------------------------------- estado e navegação
const state = { overview: null, page: "home", group: "internet", range: 60, tweaks: null, profileSig: "", boostTab: "sistema" };

function go(page, scrollTo) {
  state.page = page;
  $$(".nav").forEach((b) => b.classList.toggle("active", b.dataset.page === page));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === "page-" + page));
  $("#search").value = "";
  applySearch();
  $("#content").scrollTop = 0;
  if (scrollTo) setTimeout(() => document.getElementById(scrollTo)?.scrollIntoView({ behavior: "smooth" }), 50);
  onPage(page);
}

function onPage(page) {
  if (page === "boost") { loadTweaks(); loadDns(); }
  if (page === "drivers") loadDrivers();
  if (page === "settings") { loadSettings(); refreshLogs(); }
  if (page === "about") loadTweaks();
  if (page === "analyzer") { refreshMonitor(); renderTargets(); }
  if (page === "connections") refreshConnections();
  if (page === "wifi") renderWifi();
}

function setupTabs() {
  $$(".tabs").forEach((tabs) => {
    const pane = tabs.parentElement;
    tabs.addEventListener("click", (e) => {
      const btn = e.target.closest(".tab");
      if (!btn) return;
      $$(".tab", tabs).forEach((t) => t.classList.toggle("active", t === btn));
      $$(".tabpane", pane).forEach((p) => p.classList.toggle("active", p.dataset.pane === btn.dataset.tab));
      if (tabs.dataset.tabs === "boost") {
        state.boostTab = btn.dataset.tab;
        $("#presetBar").classList.toggle("hidden", ["dns", "clean"].includes(btn.dataset.tab));
      }
      if (tabs.dataset.tabs === "analyzer" && btn.dataset.tab === "monitor") refreshMonitor();
    });
  });
}

function applySearch() {
  const q = $("#search").value.trim().toLowerCase();
  $$(`#page-${state.page} .card:not(.add), #page-${state.page} .dns-row, #page-${state.page} .setting, #page-${state.page} tbody tr`)
    .forEach((el) => el.classList.toggle("search-hide", !!q && !el.textContent.toLowerCase().includes(q)));
}

// ---------------------------------------------------------------- visão geral (polling)
async function refreshOverview() {
  let o;
  try { o = await call("overview"); } catch { return; }
  state.overview = o;
  $("#version").textContent = "v" + o.version;
  $("#adminChip").classList.toggle("hidden", o.admin);
  $("#masterToggle").checked = o.settings.active !== false;
  $("#masterLabel").textContent = o.settings.active !== false ? "PingPilot ON" : "PingPilot OFF";
  $("#pingPill b").textContent = o.ping_now ?? "—";
  $("#pingPill").classList.toggle("hidden", !o.monitor);
  renderProfiles(o.profiles);
  $("#bellBadge").textContent = o.alerts_unread > 9 ? "9+" : o.alerts_unread;
  $("#bellBadge").classList.toggle("hidden", !o.alerts_unread);
  if (!$("#alertPanel").classList.contains("hidden") && o.alerts_unread !== state.lastUnread) loadAlerts();
  state.lastUnread = o.alerts_unread;
  renderSession(o);
  if (state.page === "home") refreshHomeHealth();
  if (state.page === "wifi") renderWifi();
}

// ---------------------------------------------------------------- jogos (Conexões)
function gameIcon(p, cls = "game-icon") {
  if (p.icon) return `<div class="${cls}"><img src="data:image/png;base64,${p.icon}" alt=""></div>`;
  const hue = [...p.name].reduce((a, c) => a + c.charCodeAt(0), 0) % 360;
  return `<div class="${cls} letter" style="background:linear-gradient(135deg,hsl(${hue} 60% 45%),hsl(${(hue + 40) % 360} 60% 30%))">${esc(p.name[0] || "?")}</div>`;
}

function renderProfiles(profiles) {
  const sig = JSON.stringify(profiles.map((p) => [p.id, p.enabled, p.running, p.name, !!p.icon]));
  if (sig === state.profileSig) return;
  state.profileSig = sig;
  const html = profiles.map((p) => `
    <div class="card profile" data-id="${p.id}" title="${esc(p.exes.join(", "))} — clique para ver os detalhes">
      ${gameIcon(p)}
      <div class="meta">
        <div class="name">${esc(p.name)}</div>
        <div class="state ${p.running ? "on" : ""}">${p.running ? "● Em execução" : "Automático"}</div>
      </div>
      <label class="switch"><input type="checkbox" class="en" ${p.enabled ? "checked" : ""}><span></span></label>
      <button class="icon-btn x" title="Remover"><i data-icon="x"></i></button>
    </div>`).join("") + `<div class="card add" title="Adicionar jogo"><span><i data-icon="plus"></i></span></div>`;
  $$(".cards-grid.profiles").forEach((g) => { g.innerHTML = html; hydrateIcons(g); });
  applySearch();
}

function setupProfiles() {
  document.addEventListener("change", async (e) => {
    const card = e.target.closest(".card.profile");
    if (!card || !e.target.classList.contains("en")) return;
    const res = await safe("update_profile", card.dataset.id, { enabled: e.target.checked });
    if (res) { state.profileSig = ""; renderProfiles(res); }
  });
  document.addEventListener("click", async (e) => {
    if (e.target.closest(".card.add")) return openModal();
    const x = e.target.closest(".card.profile .x");
    if (x) {
      const card = x.closest(".card");
      if (!confirm(`Remover ${card.querySelector(".name").textContent} da lista?`)) return;
      const res = await safe("remove_profile", card.dataset.id);
      if (res) { state.profileSig = ""; renderProfiles(res); }
      return;
    }
    const card = e.target.closest(".card.profile");
    if (card && !e.target.closest(".switch")) openDetail(card.dataset.id);
    const eye = e.target.closest(".conn-open");
    if (eye) openDetail(eye.dataset.id);
  });
}

let apps = [], selectedApp = null;
async function openModal() {
  $("#modal").classList.remove("hidden");
  $("#procFilter").value = "";
  $("#procManual").value = "";
  selectedApp = null;
  $("#procList").innerHTML = `<div class="empty"><span class="spin"></span> Procurando apps abertos…</div>`;
  apps = (await safe("list_processes")) || [];
  renderProcs();
  $("#procFilter").focus();
}
function renderProcs() {
  const q = $("#procFilter").value.toLowerCase();
  const list = apps.filter((a) => `${a.name} ${a.exes.join(" ")}`.toLowerCase().includes(q));
  $("#procList").innerHTML = list.map((a, i) => `
    <button class="proc ${a === selectedApp ? "sel" : ""}" data-i="${apps.indexOf(a)}">
      <b>${esc(a.name)}</b> ${a.added ? `<span class="tag green">já adicionado</span>` : ""}
      <small>${esc(a.exes.join(", "))}${a.company ? " · " + esc(a.company) : ""}</small>
    </button>`).join("") || `<div class="empty">Nenhum app encontrado. Abra o jogo e tente de novo.</div>`;
}
function setupModal() {
  $("#modalClose").onclick = () => $("#modal").classList.add("hidden");
  $("#modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("#modal").classList.add("hidden"); });
  $("#procFilter").oninput = renderProcs;
  $("#procList").onclick = (e) => {
    const b = e.target.closest(".proc");
    if (!b) return;
    selectedApp = apps[+b.dataset.i];
    $("#procManual").value = "";
    renderProcs();
  };
  $("#procList").ondblclick = () => $("#procAdd").click();
  $("#procManual").oninput = () => { selectedApp = null; renderProcs(); };
  $("#procAdd").onclick = () => busy($("#procAdd"), async () => {
    const manual = $("#procManual").value.trim();
    if (!selectedApp && !manual) return toast("Escolha um app da lista ou digite o nome do executável.", true);
    const res = selectedApp
      ? await call("add_profile", selectedApp.name, selectedApp.exes, selectedApp.path)
      : await call("add_profile", manual);
    $("#modal").classList.add("hidden");
    state.profileSig = "";
    renderProfiles(res);
    toast("Jogo adicionado com todos os executáveis dele. A prioridade é aplicada sempre que abrir.");
  });
}

async function refreshConnections() {
  if (state.page !== "connections") return;
  const rows = (await safe("connections")) || [];
  $("#connEmpty").classList.toggle("hidden", rows.length > 0);
  $("#connTable tbody").innerHTML = rows.map((r) => `
    <tr>
      <td><div class="app-cell">${gameIcon({ name: r.game, icon: r.icon }, "mini")}${esc(r.game)}</div></td>
      <td>${r.server ? `<div class="srv"><i data-icon="server"></i><span>${esc(r.host || "Servidor")}<br><b>${esc(r.server)}</b></span></div>` : `<span class="muted">sem servidor TCP</span>`}</td>
      <td><span class="proto"><i data-icon="network"></i>${r.proto}</span></td>
      <td class="muted">${r.tcp} TCP · ${r.udp} UDP</td>
      <td>${r.ping == null ? `<span class="muted">—</span>` : `<span class="proto"><i data-icon="pulse"></i><b>${r.ping} ms</b></span>`}</td>
      <td><button class="icon-btn conn-open" data-id="${r.id}" title="Detalhes"><i data-icon="eye-open"></i></button></td>
    </tr>`).join("");
  hydrateIcons($("#connTable"));
  applySearch();
}

// ---------------------------------------------------------------- detalhes da conexão
function openDetail(id) {
  state.detailId = id;
  state.detailTab = "chart";
  $$(".nav").forEach((b) => b.classList.toggle("active", b.dataset.page === "connections"));
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === "page-detail"));
  state.page = "detail";
  $("#content").scrollTop = 0;
  $$("#detailTabs .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.dt === "chart"));
  $$("#page-detail .dpane").forEach((p) => p.classList.toggle("hidden", p.dataset.dt !== "chart"));
  $("#routeList").innerHTML = `<div class="empty">Clique em “Traçar rota” para ver cada salto entre você e o servidor do jogo.</div>`;
  refreshDetail();
}

async function refreshDetail() {
  if (state.page !== "detail" || !state.detailId) return;
  let d;
  try { d = await call("connection_detail", state.detailId, +$("#detailRange").value); } catch { return; }
  const p = d.profile, st = d.stats;
  $("#detailHead").innerHTML = `${gameIcon(p, "game-icon")}<h1>${esc(p.name)} <span class="thin">Detalhes da Conexão</span></h1>`;
  const kv = (rows) => rows.map(([k, v]) => `<div class="kvr"><span>${k}</span><b>${v}</b></div>`).join("");
  $("#dStatus").innerHTML = kv([
    ["Situação", d.running ? `<span style="color:var(--green)">● Em execução</span>` : "Fechado"],
    ["Servidor de jogo", d.server ? `${esc(d.server.split(":")[0])}${d.host ? `<small>${esc(d.host)}</small>` : ""}` : "—"],
    ["Duração", duration(d.duration)],
    ["Protocolo / Porta", d.port ? `TCP / ${d.port}` : d.udp ? "UDP" : "—"],
  ]);
  $("#dPing").innerHTML = kv([["Último ping", ms(d.last)], ["Ping médio", ms(st.avg)], ["Maior ping", ms(st.max)], ["Menor ping", ms(st.min)]]);
  $("#dData").innerHTML = kv([
    ["Conexões", `${d.conns.length} TCP · ${d.udp} UDP`], ["Instabilidade (jitter)", ms(st.jitter)],
    ["Perda de pacotes", pct(st.loss)], ["Processos abertos", d.pids],
  ]);
  if (state.detailTab === "chart") {
    const avg = st.avg == null || !d.points.length ? [] : [[d.points[0][0], st.avg], [d.points.at(-1)[0], st.avg]];
    const css = getComputedStyle(document.documentElement);
    drawChart($("#detailChart"), [{ name: "Ping atual", points: d.points }, { name: "Ping médio", points: avg }], +$("#detailRange").value,
      [css.getPropertyValue("--accent").trim(), css.getPropertyValue("--text-2").trim()]);
    $("#detailChartEmpty").classList.toggle("hidden", d.points.length > 0);
    $("#detailChartEmpty").textContent = d.running
      ? "Sem servidor TCP para medir ainda. Jogos que só usam UDP não mostram o servidor no Windows."
      : "O app está fechado. Abra o jogo para medir o ping até o servidor dele.";
  }
  if (state.detailTab === "conns") {
    $("#dConns").innerHTML = d.conns.map((c) => `<tr class="${c.main ? "main-conn" : ""}"><td><b>${esc(c.server)}</b>${c.main ? ` <span class="tag green">principal</span>` : ""}</td><td class="muted">${esc(c.host || "—")}</td></tr>`).join("")
      || `<tr><td class="muted" colspan="2">Nenhuma conexão TCP aberta agora.</td></tr>`;
  }
  if (state.detailTab === "settings") {
    $("#dPriority").value = p.priority;
    $("#dName").value = document.activeElement === $("#dName") ? $("#dName").value : p.name;
    $("#dExes").innerHTML = p.exes.map((e) => `<span class="chip">${esc(e)}${p.exes.length > 1 ? `<button class="icon-btn rm-exe" data-exe="${esc(e)}" title="Tirar do grupo">${svg("x")}</button>` : ""}</span>`).join(" ");
  }
}

function setupDetail() {
  $("#detailBack").onclick = () => go("connections");
  $("#detailRange").onchange = refreshDetail;
  $("#detailTabs").onclick = (e) => {
    const b = e.target.closest(".seg-btn");
    if (!b) return;
    state.detailTab = b.dataset.dt;
    $$("#detailTabs .seg-btn").forEach((x) => x.classList.toggle("active", x === b));
    $$("#page-detail .dpane").forEach((p) => p.classList.toggle("hidden", p.dataset.dt !== b.dataset.dt));
    $("#detailRange").classList.toggle("hidden", b.dataset.dt !== "chart");
    refreshDetail();
  };
  $("#routeBtn").onclick = () => busy($("#routeBtn"), async () => {
    $("#routeList").innerHTML = `<div class="empty"><span class="spin"></span> Traçando a rota (até 30 s)…</div>`;
    const r = await waitJob(await call("route_trace", state.detailId));
    const worst = Math.max(1, ...r.hops.map((h) => h.avg || 0));
    $("#routeList").innerHTML = `<p class="muted small">Destino: <b>${esc(r.target)}</b>. Um salto com “*” só significa que aquele roteador não responde a teste — não é perda, se os seguintes respondem.</p>`
      + r.hops.map((h) => `
      <div class="hop">
        <span class="rank">${h.hop}</span>
        <span class="hip">${esc(h.ip || "* sem resposta")}</span>
        <div class="bar-track grow"><div class="bar-fill" style="width:${h.avg ? Math.max(3, (h.avg / worst) * 100) : 0}%"></div></div>
        <b>${h.avg == null ? "—" : h.avg + " ms"}</b>
      </div>`).join("");
  });
  $("#dPriority").onchange = async (e) => {
    if (await safe("update_profile", state.detailId, { priority: e.target.value })) toast("Prioridade salva.");
  };
  $("#dName").onchange = async (e) => {
    const res = await safe("update_profile", state.detailId, { name: e.target.value.trim() });
    if (res) { state.profileSig = ""; renderProfiles(res); refreshDetail(); }
  };
  $("#dExes").onclick = async (e) => {
    const b = e.target.closest(".rm-exe");
    if (b && (await safe("update_profile", state.detailId, { remove_exe: b.dataset.exe }))) refreshDetail();
  };
}

// ---------------------------------------------------------------- início
function renderSession(o) {
  const live = o.session, last = o.last_session, s = live || last;
  $("#sessionTitle").textContent = live ? "Sessão atual" : "Dados da última sessão";
  if (!s) {
    $("#sessionPanel").innerHTML = `<div class="empty">Adicione um jogo em Conexões. Quando ele abrir, o PingPilot registra o ping, o jitter e a perda de pacotes da partida aqui.</div>`;
    return;
  }
  const p = o.profiles.find((x) => x.name === s.game);
  $("#sessionPanel").innerHTML = `
    <div class="game">${p ? gameIcon(p, "session-icon") : ""}<span>${esc(s.game)}</span>${live ? ` <span class="tag green">ao vivo</span>` : ` <span class="tag">${esc(last.ended || "")}</span>`}</div>
    <div class="dur"><span>Duração</span><b>${duration(s.duration || 0)}</b></div>
    <div class="kpis">
      <div class="kh">Ping mais baixo</div><div class="kh">Ping médio</div><div class="kh">Jitter médio</div><div class="kh">Perda de pacotes</div>
      <div class="kd">${ms(s.min)}</div><div class="kd">${ms(s.avg)}</div><div class="kd">${ms(s.jitter)}</div><div class="kd">${pct(s.loss)}</div>
    </div>`;
}

async function refreshHomeHealth() {
  let d;
  try { d = await call("monitor_data", "internet", 60); } catch { return; }
  const st = aggregate(d.series);
  const a = state.overview?.adapter;
  $("#homeHealth").innerHTML = [
    ["Ping (último minuto)", st.avg == null ? "—" : Math.round(st.avg), "ms"],
    ["Jitter", st.jitter == null ? "—" : Math.round(st.jitter), "ms"],
    ["Perda de pacotes", st.loss == null ? "—" : Math.round(st.loss), "%"],
    ["Conexão", a ? (a.Wireless ? "Wi-Fi" : "Cabo") : "—", a ? a.Speed : ""],
  ].map(([l, v, u]) => `<div class="stat"><span>${l}</span><b>${esc(v)}</b><small>${esc(u)}</small></div>`).join("");
  if (!d.running) $("#homeHealth").insertAdjacentHTML("beforeend", `<div class="stat" style="grid-column:1/-1"><span>O monitoramento está desligado — ligue em Analisador de rede.</span></div>`);
}

// ---------------------------------------------------------------- analisador
const COLORS = ["#a855f7", "#f59e0b", "#22d3ee"];

function aggregate(series) {
  const withData = series.filter((s) => s.points.length);
  if (!withData.length) return { avg: null, jitter: null, loss: null, spikes: null, min: null, max: null, quality: "none" };
  const avgs = withData.map((s) => s.stats.avg).filter((v) => v != null);
  const rank = { none: 0, good: 1, fair: 2, bad: 3, down: 4 };
  return {
    avg: avgs.length ? avgs.reduce((a, b) => a + b, 0) / avgs.length : null,
    min: Math.min(...withData.map((s) => s.stats.min ?? Infinity)),
    max: Math.max(...withData.map((s) => s.stats.max ?? -Infinity)),
    jitter: Math.max(...withData.map((s) => s.stats.jitter ?? 0)),
    loss: Math.max(...withData.map((s) => s.stats.loss ?? 0)),
    spikes: withData.reduce((a, s) => a + (s.stats.spikes || 0), 0),
    quality: withData.map((s) => s.quality).sort((a, b) => rank[b] - rank[a])[0],
  };
}

async function refreshMonitor() {
  if (state.page !== "analyzer" || !$('[data-pane="monitor"]').classList.contains("active")) return;
  let d;
  try { d = await call("monitor_data", state.group, state.range); } catch { return; }
  const a = d.adapter;
  $("#localIp").textContent = a?.LocalIP || "—";
  $("#connKind").textContent = a ? `${a.Wireless ? "Wi-Fi" : "Cabo"} · ${a.Speed}` : "—";
  $("#monitorToggle span").textContent = d.running ? "Desligar" : "Ligar";
  $("#monitorToggle").classList.toggle("primary", !d.running);
  const st = aggregate(d.series);
  const local = state.group === "gateway";
  const badge = $("#healthBadge");
  badge.className = "status-badge " + st.quality;
  $("span", badge).textContent = { none: d.running ? "Coletando…" : "Desligado", good: "Estável", fair: "Instável", bad: "Ruim", down: "Sem conexão" }[st.quality];
  const lvl = (v, ok, warn) => (v == null ? "" : v <= ok ? "good" : v <= warn ? "fair" : "bad");
  const set = (id, txt, cls) => { $("#h" + id).textContent = txt; $("#d" + id).className = "dot " + cls; };
  set("Lat", ms(st.avg), lvl(st.avg, local ? 10 : 80, local ? 30 : 150));
  set("Loss", pct(st.loss), lvl(st.loss, 0, 2));
  set("Jit", ms(st.jitter), lvl(st.jitter, local ? 5 : 10, local ? 10 : 20));
  set("Spk", st.spikes ?? "—", lvl(st.spikes, 0, 3));
  $("#cAvg").textContent = ms(st.avg);
  $("#cMin").textContent = isFinite(st.min) ? ms(st.min) : "—";
  $("#cMax").textContent = isFinite(st.max) ? ms(st.max) : "—";
  $("#legend").innerHTML = d.series.map((s, i) => `<span><i style="background:${COLORS[i]}"></i>${esc(s.name)}</span>`).join("");
  drawChart($("#chart"), d.series, state.range);
}

function drawChart(canvas, series, range, colors = COLORS) {
  const dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth, H = canvas.clientHeight;
  canvas.width = W * dpr; canvas.height = H * dpr;
  const c = canvas.getContext("2d");
  c.scale(dpr, dpr);
  c.clearRect(0, 0, W, H);
  const L = 40, R = 16, T = 12, B = 30;
  const now = Date.now() / 1000, t0 = now - range;
  const vals = series.flatMap((s) => s.points.map((p) => p[1]).filter((v) => v != null));
  const maxV = Math.max(5, Math.ceil((vals.length ? Math.max(...vals) : 5) * 1.2));
  const x = (t) => L + ((t - t0) / range) * (W - L - R);
  const y = (v) => T + (1 - v / maxV) * (H - T - B);
  const css = getComputedStyle(document.documentElement);
  const v = (name) => css.getPropertyValue(name).trim();
  c.font = "11px Segoe UI"; c.fillStyle = v("--muted"); c.strokeStyle = v("--line"); c.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const v = (maxV / 4) * i, yy = y(v);
    c.beginPath(); c.moveTo(L, yy); c.lineTo(W - R, yy); c.stroke();
    c.textAlign = "right"; c.fillText(Math.round(v), L - 8, yy + 4);
  }
  c.textAlign = "center";
  for (let i = 0; i <= 6; i++) {
    const t = t0 + (range / 6) * i;
    c.fillText(new Date(t * 1000).toLocaleTimeString(I18N.lang), x(t), H - 8);
  }
  series.forEach((s, i) => {
    // perda de pacotes: barras vermelhas na base
    c.fillStyle = "rgba(229,52,74,.85)";
    s.points.forEach(([t, v]) => { if (v == null && t >= t0) c.fillRect(x(t) - 1.5, H - B - 14, 3, 14); });
    c.strokeStyle = colors[i]; c.lineWidth = i === 0 ? 1.8 : 1; c.setLineDash(i === 0 ? [] : [5, 4]); c.beginPath();
    let pen = false;
    s.points.forEach(([t, v]) => {
      if (t < t0 || v == null) { pen = false; return; }
      pen ? c.lineTo(x(t), y(v)) : c.moveTo(x(t), y(v));
      pen = true;
    });
    c.stroke();
  });
  // valor mais recente
  c.setLineDash([]);
  const last = [...series[0].points].reverse().find((p) => p[1] != null);
  if (last) {
    const lx = Math.min(x(last[0]), W - R - 30), ly = y(last[1]);
    const label = `${last[1]} ms`;
    const tw = c.measureText(label).width + 16;
    c.fillStyle = v("--panel-2"); c.strokeStyle = v("--line-2");
    c.beginPath(); c.roundRect(lx - tw / 2, ly - 34, tw, 22, 4); c.fill(); c.stroke();
    c.fillStyle = v("--text"); c.fillText(label, lx, ly - 19);
  }
  if (!vals.length) { c.fillStyle = v("--muted"); c.textAlign = "center"; c.fillText(t("Coletando dados…"), W / 2, H / 2); }
}

function setupAnalyzer() {
  $("#groupSeg").onclick = (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    state.group = b.dataset.group;
    $$("#groupSeg button").forEach((x) => x.classList.toggle("active", x === b));
    refreshMonitor();
  };
  $("#rangeSel").onchange = (e) => { state.range = +e.target.value; refreshMonitor(); };
  $("#monitorToggle").onclick = async () => {
    const on = $("#monitorToggle span").textContent === "Ligar";
    await safe("monitor_set", on);
    toast(on ? "Monitoramento ligado" : "Monitoramento desligado");
    refreshMonitor();
  };
  $("#pingStart").onclick = () => busy($("#pingStart"), async () => {
    $("#verdict").classList.add("hidden");
    const jid = await call("ping_test", +$("#pingCount").value || 30);
    const res = await waitJob(jid, renderPingRows);
    renderPingRows(res.rows);
    const v = $("#verdict");
    const worst = res.rows.some((r) => ["bad", "down"].includes(r.quality)) ? "bad" : res.rows.some((r) => r.quality === "fair") ? "fair" : "";
    v.className = "verdict " + worst;
    $("b", v).textContent = res.verdict[0];
    $("span", v).textContent = res.verdict[1];
  });
  $("#tAdd").onclick = async () => {
    const host = $("#tHost").value.trim();
    if (!/^[\w.\-:]+$/.test(host)) return toast("Digite um IP ou domínio válido.", true);
    const targets = await call("ping_targets");
    targets.push([$("#tName").value.trim() || host, host]);
    await safe("set_ping_targets", targets);
    $("#tName").value = $("#tHost").value = "";
    renderTargets();
  };
  $("#pingTable").onclick = async (e) => {
    const b = e.target.closest(".rm");
    if (!b) return;
    const targets = (await call("ping_targets")).filter(([, h]) => h !== b.dataset.host);
    await safe("set_ping_targets", targets);
    renderTargets();
  };
}

async function renderTargets() {
  const targets = (await safe("ping_targets")) || [];
  const gw = state.overview?.adapter?.Gateway;
  renderPingRows([...(gw ? [{ name: "Seu roteador", host: gw }] : []), ...targets.map(([name, host]) => ({ name, host }))]);
}

function renderPingRows(rows) {
  $("#pingTable tbody").innerHTML = rows.map((r) => `
    <tr>
      <td>${esc(r.name)}</td><td class="muted">${esc(r.host)}</td>
      <td>${ms(r.avg)}</td><td>${ms(r.min)}</td><td>${ms(r.max)}</td><td>${ms(r.jitter)}</td>
      <td>${r.sent ? pct(r.loss) : "—"}</td>
      <td class="q ${r.quality || ""}">${r.sent != null && r.sent < r.total && r.quality !== undefined ? `${r.sent}/${r.total}` : QUALITY[r.quality] || "—"}</td>
      <td>${r.name === "Seu roteador" ? "" : `<button class="icon-btn rm" data-host="${esc(r.host)}" title="Remover"><i data-icon="x"></i></button>`}</td>
    </tr>`).join("");
  hydrateIcons($("#pingTable"));
}

// ---------------------------------------------------------------- PC Boost
async function loadTweaks() {
  const data = await safe("tweak_list");
  if (!data) return;
  state.tweaks = data;
  renderTweaks();
  $("#excludedList").innerHTML = data.excluded.map((x) => `
    <div class="excluded"><b>${esc(x.title)} <span class="tag">${esc(x.source)}</span></b><span class="muted small">${esc(x.why)}</span></div>`).join("");
}

function renderTweaks() {
  const items = state.tweaks.items;
  $$(".cards-grid.tweaks").forEach((grid) => {
    grid.innerHTML = items.filter((t) => t.group === grid.dataset.group).map((t) => `
      <div class="card tweak" data-id="${t.id}">
        <div class="top">
          <span class="ticon">${svg(t.icon)}</span>
          <label class="switch" title="${t.locked ? "Precisa de administrador" : !t.available ? "Indisponível nesta conexão" : ""}">
            <input type="checkbox" ${t.on ? "checked" : ""} ${t.locked || !t.available ? "disabled" : ""}><span></span></label>
        </div>
        <h3>${esc(t.title)} ${t.recommended ? `<span class="tag green">Recomendado</span>` : ""}</h3>
        <p>${esc(t.desc)}</p>
        <div class="foot">
          <button class="warn-link">Não recomendado se…</button>
          <div class="grow"></div>
          ${t.reboot ? `<span class="tag amber">Reiniciar</span>` : ""}
          ${t.locked ? `<span class="tag amber">Admin</span>` : ""}
          <span class="tag blue">${esc(t.source)}</span>
        </div>
        <div class="warn-text hidden">${esc(t.warn)}</div>
      </div>`).join("");
  });
  const avail = items.filter((t) => !t.locked && t.available);
  const mode = avail.every((t) => t.on === t.recommended) ? "performance" : avail.every((t) => !t.on) ? "default" : "custom";
  $$(".btn.preset").forEach((b) => b.classList.toggle("active", b.dataset.preset === mode));
  applySearch();
}

function setupBoost() {
  document.addEventListener("click", (e) => {
    const w = e.target.closest(".warn-link");
    if (w) w.closest(".card").querySelector(".warn-text").classList.toggle("hidden");
  });
  document.addEventListener("change", async (e) => {
    const card = e.target.closest(".card.tweak");
    if (!card) return;
    const input = e.target;
    input.disabled = true;
    try {
      const on = await call("tweak_set", card.dataset.id, input.checked);
      state.tweaks.items.find((t) => t.id === card.dataset.id).on = on;
      const t = state.tweaks.items.find((x) => x.id === card.dataset.id);
      toast(`${t.title}: ${on ? "ativado" : "desativado"}${t.reboot ? " — reinicie o PC para valer" : ""}`);
    } catch (err) {
      input.checked = !input.checked;
      toast(err.message, true);
    }
    input.disabled = false;
    renderTweaks();
  });
  $$(".btn.preset").forEach((b) => (b.onclick = () => {
    if (b.dataset.preset === "custom") return;
    const msg = b.dataset.preset === "performance"
      ? "Aplicar todos os ajustes recomendados? Os valores atuais ficam salvos em backup."
      : "Voltar todos os ajustes ao padrão do Windows?";
    if (!confirm(msg)) return;
    busy(b, async () => {
      const n = await waitJob(await call("tweak_preset", b.dataset.preset));
      toast(`${n} ajuste(s) alterado(s).`);
      await loadTweaks();
    });
  }));
  $("#quickBoost").onclick = () => {
    if (!confirm("Aplicar a otimização recomendada (rede + sistema)? Tudo pode ser desfeito em PC Boost ou Configurações.")) return;
    busy($("#quickBoost"), async () => {
      const n = await waitJob(await call("tweak_preset", "performance"));
      toast(`Otimização aplicada: ${n} ajuste(s) alterado(s). Reinicie o PC quando puder.`);
    });
  };
  $("#dnsTest").onclick = () => busy($("#dnsTest"), async () => {
    const res = await waitJob(await call("dns_benchmark"), (p) => {
      $("#dnsTested").textContent = `Medindo… ${p.done}/${p.total} servidores`;
    });
    renderDns(res);
    if (res.applied) { toast(`DNS trocado automaticamente para ${res.applied}.`); refreshOverview(); }
  });
  $("#autoDns").onchange = async (e) => {
    const res = await safe("setting_set", "auto_dns", e.target.checked);
    e.target.checked = !!res;
    if (res) toast("Ligado: o PingPilot testa periodicamente (fora das partidas) e usa o DNS mais rápido.");
  };
  $("#cdAdd").onclick = async () => {
    const res = await safe("dns_add_custom", $("#cdName").value.trim(), $("#cdP1").value.trim(), $("#cdP2").value.trim());
    if (!res) return;
    $("#cdName").value = $("#cdP1").value = $("#cdP2").value = "";
    renderDns(res);
    toast("DNS adicionado. Rode o teste para medir.");
  };
  $("#page-boost").addEventListener("click", (e) => {
    const rm = e.target.closest(".rm-dns");
    if (rm) return safe("dns_remove_custom", rm.dataset.p1).then((r) => r && renderDns(r));
    const b = e.target.closest(".use-dns");
    if (!b) return;
    busy(b, async () => {
      if (b.dataset.auto) await call("dns_reset");
      else await call("dns_apply", b.dataset.p1, b.dataset.p2);
      toast(`DNS alterado para ${b.dataset.name}.`);
      await refreshOverview();
      renderDns(await call("dns_list"));
    });
  });
}

async function loadDns() {
  const res = await safe("dns_list");
  if (res) renderDns(res);
}

function dnsRow(r, rank, best) {
  const lvl = r.ms == null ? "none" : r.ms < 30 ? "good" : r.ms < 80 ? "fair" : "bad";
  const ips = r.auto ? (r.primary || "DHCP") : `${r.primary}${r.secondary ? " / " + r.secondary : ""}`;
  return `
    <div class="dns-row">
      <span class="rank">${rank}</span>
      <span class="dn">${esc(r.name)}</span>
      <span class="ips" title="${esc(ips)}">${esc(ips)}</span>
      ${best ? `<span class="fast">${svg("bolt")}Mais rápido</span>` : ""}
      ${r.current ? `<span class="tag green">Em uso</span>` : ""}
      <div class="resp">Resp. média <span class="sep"></span><i class="dot s ${lvl}"></i><b>${r.ms == null ? "Não medido" : Math.round(r.ms) + " ms"}</b></div>
      <div class="act">
        ${r.custom ? `<button class="icon-btn rm-dns" data-p1="${esc(r.primary)}" title="Remover">${svg("x")}</button>` : ""}
        <button class="btn choose use-dns" ${r.current ? "disabled" : ""} data-p1="${esc(r.primary)}" data-p2="${esc(r.secondary)}" data-name="${esc(r.name)}" ${r.auto ? 'data-auto="1"' : ""}>Escolher</button>
      </div>
    </div>`;
}

function renderDns(data) {
  $("#autoDns").checked = !!data.auto_dns;
  $("#dnsTested").textContent = data.tested ? `Último teste: ${data.tested}` : "Ainda não testado — clique em “Testar servidores”.";
  const rows = data.rows.filter((r) => !r.auto);
  const auto = data.rows.find((r) => r.auto);
  const measured = rows[0]?.ms != null;
  $("#dnsBest").innerHTML = measured ? dnsRow(rows[0], 1, true) : "";
  $("#dnsList").innerHTML = (measured ? rows.slice(1) : rows).map((r, i) => dnsRow(r, i + (measured ? 2 : 1), false)).join("")
    + (auto ? dnsRow(auto, "-", false) : "");
  applySearch();
}

function setupTools() {
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-tool]");
    if (!b) return;
    if (b.dataset.confirm && !confirm(b.dataset.confirm)) return;
    busy(b, async () => toast(await waitJob(await call("tool_job", b.dataset.tool))));
  });
}

// ---------------------------------------------------------------- dispositivos na rede
function renderLan(data) {
  state.lan = data;
  const devs = data.devices;
  $("#lanTitle").textContent = `${devs.length} dispositivo(s) conectados em ${data.network}`;
  $("#lanEmpty").classList.toggle("hidden", devs.length > 0);
  $("#lanTable tbody").innerHTML = devs.map((d) => {
    const name = d.label || (d.me ? "Este PC" : d.gateway ? "Roteador" : d.name || "Dispositivo desconhecido");
    const tags = [d.me && `<span class="tag green">Este PC</span>`, d.gateway && `<span class="tag blue">Roteador</span>`,
      d.random_mac && `<span class="tag">MAC aleatório</span>`].filter(Boolean).join(" ");
    return `<tr>
      <td><button class="link lan-name" data-mac="${esc(d.mac)}" title="Dar um apelido">${esc(name)}</button>
        ${d.name && d.label ? `<span class="muted small">${esc(d.name)}</span>` : ""} ${tags}</td>
      <td><b>${esc(d.ip)}</b></td>
      <td class="muted">${esc(d.mac || "—")}</td>
      <td>${d.ping == null ? `<span class="muted">não responde a ping</span>` : `${d.ping} ms`}</td>
    </tr>`;
  }).join("");
  applySearch();
}

function setupLan() {
  $("#lanScan").onclick = () => busy($("#lanScan"), async () => {
    renderLan(await waitJob(await call("lan_scan"), (p) => {
      $("#lanTitle").textContent = `Escaneando… ${p.done}/${p.total} endereços`;
    }));
  });
  $("#lanTable").onclick = async (e) => {
    const b = e.target.closest(".lan-name");
    if (!b) return;
    const name = prompt("Apelido para este aparelho (deixe vazio para remover):", b.textContent.trim());
    if (name === null) return;
    const res = await safe("lan_rename", b.dataset.mac, name);
    if (res) renderLan(res);
  };
}

// ---------------------------------------------------------------- drivers
const fmtDate = (d) => (d ? d.split("-").reverse().join("/") : "—");
const fmtSize = (b) => (b > 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);

async function loadDrivers() {
  const data = await safe("drivers_cached");
  if (data) renderDrivers(data);
}

function renderDrivers(data) {
  state.drivers = data;
  const ups = data.updates;
  $("#drvTitle").innerHTML = ups.length
    ? `<span style="color:var(--red)">${ups.length} driver(s) de dispositivos</span> desatualizado(s)`
    : "Todos os drivers estão atualizados";
  $("#drvOutdated").textContent = `Drivers desatualizados (${ups.length})`;
  $("#drvInstallAll").disabled = !ups.length;
  $("#drvUpdates").innerHTML = ups.map((u) => `
    <div class="drv-row update">
      <input type="checkbox" class="drv-sel" value="${esc(u.Id)}" checked>
      <span class="dicon">${svg("chip")}</span>
      <div class="dname">${esc(u.Device)}<small>${esc(u.Title)} · ${fmtSize(u.Size)}</small></div>
      <div class="ddate">Atual: ${fmtDate(u.CurrentDate)}<br><b style="color:var(--text)">Disponível: ${fmtDate(u.Date)}</b></div>
      <button class="btn outline small drv-one" data-id="${esc(u.Id)}">Atualizar</button>
    </div>`).join("") || `<div class="empty">Nenhuma atualização de driver no Windows Update (verificado em ${esc(data.time)}).</div>`;
  renderInstalled();
}

function renderInstalled() {
  const data = state.drivers;
  if (!data) return;
  const q = $("#drvFilter").value.trim().toLowerCase();
  const list = data.installed.filter((d) => !q || `${d.Name} ${d.Maker} ${d.ClassName}`.toLowerCase().includes(q));
  $("#drvOkTitle").textContent = `Instalados (${data.installed.length})`;
  $("#drvInstalled").innerHTML = list.slice(0, 400).map((d) => `
    <div class="drv-row">
      <span class="dicon">${svg(d.Class === "DISPLAY" ? "gpu" : d.Class === "NET" ? "network" : "chip")}</span>
      <div class="dname">${esc(d.Name)}<small>${esc(d.ClassName)} · ${esc(d.Maker || "")} · v${esc(d.Version)}</small></div>
      ${d.Vendor ? `<button class="btn outline small vendor" data-url="${esc(d.Vendor.url)}">Site da ${esc(d.Vendor.name)}</button>` : ""}
      <div class="ddate">Atual: ${fmtDate(d.Date)}</div>
      <span class="ok">${svg("check")}Atualizado</span>
    </div>`).join("");
}

async function installDrivers(ids, btn) {
  if (!ids.length) return toast("Selecione ao menos um driver.", true);
  if (!confirm(`Baixar e instalar ${ids.length} driver(s) pelo Windows Update?`)) return;
  await busy(btn, async () => {
    const res = await waitJob(await call("drivers_install", ids, $("#drvRestore").checked), (p) => toast(p));
    const ok = res.filter((r) => r.ok).length;
    toast(`${ok} de ${res.length} driver(s) instalado(s).${res.some((r) => r.reboot) ? " Reinicie o PC para concluir." : ""}`, ok < res.length);
    renderDrivers(await call("drivers_cached"));
  });
}

function setupDrivers() {
  $("#drvScan").onclick = () => busy($("#drvScan"), async () => {
    $("#drvUpdates").innerHTML = `<div class="empty"><span class="spin"></span> <span id="drvProg">Procurando…</span></div>`;
    renderDrivers(await waitJob(await call("drivers_scan"), (p) => { const el = $("#drvProg"); if (el) el.textContent = p; }));
  });
  $("#drvFilter").oninput = renderInstalled;
  $("#drvAll").onchange = (e) => $$(".drv-sel").forEach((c) => (c.checked = e.target.checked));
  $("#drvInstallAll").onclick = () => installDrivers($$(".drv-sel").filter((c) => c.checked).map((c) => c.value), $("#drvInstallAll"));
  $("#page-drivers").addEventListener("click", (e) => {
    const one = e.target.closest(".drv-one");
    if (one) return installDrivers([one.dataset.id], one);
    const v = e.target.closest(".vendor");
    if (v) safe("open_url", v.dataset.url);
  });
}

// ---------------------------------------------------------------- projetos de origem
function setupUpstream() {
  $("#upCheck").onclick = () => busy($("#upCheck"), async () => {
    $("#upList").innerHTML = `<div class="empty"><span class="spin"></span> Consultando o GitHub…</div>`;
    let res;
    try { res = await waitJob(await call("upstream_check")); }
    catch (e) { $("#upList").innerHTML = `<div class="empty">Não foi possível consultar o GitHub agora.</div>`; throw e; }
    $("#upList").innerHTML = res.map((r) => {
      const changed = r.status.startsWith("mudou");
      const details = [
        ...r.files.map((f) => `arquivo alterado: ${esc(f)}`),
        ...r.tweaks.map((t) => `ajuste usado pelo PingPilot mudou: <b>${esc(t)}</b>`),
        ...(r.new_tweaks.length ? [`${r.new_tweaks.length} ajuste(s) novo(s): ${esc(r.new_tweaks.slice(0, 8).join(", "))}`] : []),
      ];
      return `<div class="up-item">
        <span class="tag ${changed ? "amber" : r.status === "ok" ? "green" : ""}">${changed ? "Mudou" : r.status === "ok" ? "Em dia" : esc(r.status)}</span>
        <div class="grow"><b>${esc(r.title)}</b>${details.map((d) => `<small>${d}</small>`).join("")}</div>
        ${changed && r.url ? `<button class="btn outline small up-url" data-url="${esc(r.url)}">Ver mudanças no GitHub</button>` : ""}
        ${changed ? `<button class="btn outline small up-ok" data-name="${esc(r.name)}">Marcar como revisado</button>` : ""}
      </div>`;
    }).join("");
  });
  $("#upList").onclick = async (e) => {
    const u = e.target.closest(".up-url");
    if (u) return safe("open_url", u.dataset.url);
    const b = e.target.closest(".up-ok");
    if (b && (await safe("upstream_mark_reviewed", b.dataset.name))) { b.closest(".up-item").querySelector(".tag").textContent = "Revisado"; b.remove(); }
  };
}

// ---------------------------------------------------------------- Wi-Fi
function renderWifi() {
  const o = state.overview;
  if (!o) return;
  const on = !!o.settings.wifi;
  $("#wifiBtn").classList.toggle("on", on);
  $("#wifiTitle").textContent = on ? "Otimizador de Wi-Fi ativo" : "Clique para ativar o otimizador de Wi-Fi";
  const cable = o.adapter && !o.adapter.Wireless;
  $("#wifiStatus").textContent = on ? `Status: ${o.wifi}` : cable ? "Você está no cabo — o otimizador só age quando há Wi-Fi conectado." : "";
  $("#wifiStatus").classList.toggle("hidden", !$("#wifiStatus").textContent);
}
function setupWifi() {
  $("#wifiBtn").onclick = async () => {
    const on = !state.overview.settings.wifi;
    const res = await safe("wifi_set", on);
    if (res === undefined) return;
    state.overview.settings.wifi = on;
    state.overview.wifi = res;
    renderWifi();
    toast(on ? `Otimizador de Wi-Fi: ${res}` : "Otimizador de Wi-Fi desligado");
  };
}

// ---------------------------------------------------------------- configurações
function fillSettings(data) {
  const s = data.settings;
  $$("[data-setting]").forEach((el) => {
    if (el.type === "checkbox") el.checked = !!s[el.dataset.setting];
    else el.value = String(s[el.dataset.setting]);
  });
  $("#setMonitor").checked = !!s.monitor;
  $("#setAutostart").checked = !!data.autostart;
}

async function loadSettings() {
  const o = state.overview;
  const data = await safe("settings_get");
  if (data) fillSettings(data);
  const a = o?.adapter;
  $("#netInfo").innerHTML = a ? [
    ["Adaptador", `${a.Alias} (${a.Wireless ? "Wi-Fi" : "Cabo"})`], ["Placa", a.Desc], ["Velocidade", a.Speed],
    ["IP local", a.LocalIP], ["Roteador", a.Gateway], ["DNS", (a.Dns || []).join(", ") || "automático"],
  ].map(([k, v]) => `<span>${k}</span><b>${esc(v)}</b>`).join("") : `<span>Sem conexão</span><b></b>`;
}
async function refreshLogs() {
  if (state.page !== "settings") return;
  const logs = (await safe("get_logs")) || [];
  const box = $("#logBox");
  const atBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 30;
  box.innerHTML = logs.map((l) => `<div><span class="t">${l.t}</span>${esc(l.msg)}</div>`).join("");
  if (atBottom) box.scrollTop = box.scrollHeight;
}
function setupSettings() {
  $("#setAutostart").onchange = async (e) => {
    const res = await safe("autostart_set", e.target.checked);
    e.target.checked = !!res;
  };
  $("#setMonitor").onchange = async (e) => { await safe("monitor_set", e.target.checked); refreshOverview(); };
  $$("[data-setting]").forEach((el) => (el.onchange = async () => {
    const key = el.dataset.setting;
    const value = el.type === "checkbox" ? el.checked : el.value;
    const res = await safe("setting_set", key, value);
    if (res === undefined) { if (el.type === "checkbox") el.checked = !value; return loadSettings(); }
    if (key === "verbose_logs" && res) toast("Logs detalhados ligados. Lembre de desligar depois de reportar o problema.");
    if (key === "tray") toast(res ? "Fechar a janela agora esconde o PingPilot na bandeja." : "Fechar a janela agora encerra o PingPilot.");
    if (key === "auto_dns" || key === "dns_interval") loadDns();
    if (key === "lang") location.reload();
    if (key === "theme") { applyTheme(res); refreshMonitor(); }
  }));
  $("#resetSettings").onclick = async () => {
    if (!confirm("Voltar as preferências do app ao padrão? A lista de jogos e os ajustes do Windows não mudam.")) return;
    const res = await safe("reset_settings");
    if (res) { fillSettings(res); refreshOverview(); toast("Preferências redefinidas."); }
  };
  $("#netReset").onclick = () => {
    if (!confirm("Redefinir Winsock, TCP/IP e cache DNS do Windows? A internet pode cair por alguns segundos e será preciso reiniciar o PC.")) return;
    busy($("#netReset"), async () => toast(await waitJob(await call("network_reset"), (p) => toast(p))));
  };
  $("#openLogs").onclick = () => safe("open_logs");
  $("#exportLogs").onclick = () => busy($("#exportLogs"), async () => {
    const path = await call("export_logs");
    toast(`Logs salvos em ${path}. Mande esse .zip para quem está avaliando.`);
  });
  $("#copyLogs").onclick = () => {
    navigator.clipboard.writeText($("#logBox").innerText).then(() => toast("Registro copiado."));
  };
  $("#restoreAll").onclick = () => {
    if (!confirm("Desfazer TODOS os ajustes feitos pelo PingPilot e voltar aos valores originais?")) return;
    busy($("#restoreAll"), async () => {
      const n = await waitJob(await call("restore_all"));
      toast(`Ajustes desfeitos (${n}). Reinicie o PC para concluir.`);
    });
  };
}

// ---------------------------------------------------------------- central de notificações
const ALERT_ICONS = { upstream: "refresh", drivers: "chip", dns: "route", game: "gamepad", unstable: "pulse", session: "flag" };
const ALERT_KINDS = { upstream: "Projetos de origem", drivers: "Drivers", dns: "DNS", game: "Jogo detectado",
  unstable: "Conexão instável", session: "Partida" };

function ago(ts) {
  const rtf = new Intl.RelativeTimeFormat(I18N.lang, { numeric: "auto" });
  const s = Math.round(ts - Date.now() / 1000);
  for (const [unit, size] of [["day", 86400], ["hour", 3600], ["minute", 60]]) {
    if (Math.abs(s) >= size) return rtf.format(Math.round(s / size), unit);
  }
  return rtf.format(0, "second");
}

async function loadAlerts() {
  const list = (await safe("alerts_list")) || [];
  $("#alertList").innerHTML = list.map((a) => `
    <div class="alert ${a.read ? "" : "unread"}" data-id="${a.id}" data-target="${esc(a.page || "")}">
      <span class="a-ic ${a.kind}">${svg(ALERT_ICONS[a.kind] || "bell")}</span>
      <div class="a-body">
        <div class="a-top"><span class="grow">${esc(ALERT_KINDS[a.kind] || "")}</span><span>${esc(ago(a.time))}</span></div>
        <b>${esc(a.title)}</b>
        <div class="a-msg">${esc(a.message)}</div>
      </div>
    </div>`).join("") || `<div class="empty">Nenhuma notificação por enquanto.</div>`;
}

function setupAlerts() {
  $("#bellBtn").onclick = (e) => {
    e.stopPropagation();
    const panel = $("#alertPanel");
    panel.classList.toggle("hidden");
    if (!panel.classList.contains("hidden")) loadAlerts();
  };
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".bell-wrap")) $("#alertPanel").classList.add("hidden");
  });
  $("#alertList").onclick = async (e) => {
    const item = e.target.closest(".alert");
    if (!item) return;
    await safe("alerts_read", [item.dataset.id]);
    $("#alertPanel").classList.add("hidden");
    if (item.dataset.target) go(item.dataset.target);
    refreshOverview();
  };
  $("#alertsRead").onclick = async () => { await safe("alerts_read"); loadAlerts(); refreshOverview(); };
  $("#alertsClear").onclick = async () => { await safe("alerts_clear"); loadAlerts(); refreshOverview(); };
  $("#alertPanel .alert-foot").addEventListener("click", () => $("#alertPanel").classList.add("hidden"));
}

// ---------------------------------------------------------------- balão de ajuda dos "?"
function setupHelp() {
  const pop = document.createElement("div");
  pop.className = "help-pop hidden";
  document.body.appendChild(pop);
  document.addEventListener("click", (e) => {
    const h = e.target.closest(".help");
    if (!h) return pop.classList.add("hidden");
    e.preventDefault();
    e.stopPropagation();
    if (!pop.classList.contains("hidden") && pop.dataset.for === h.title) return pop.classList.add("hidden");
    pop.textContent = h.title;  // o title já vem traduzido pelo i18n
    pop.dataset.for = h.title;
    pop.classList.remove("hidden");
    const r = h.getBoundingClientRect();
    const left = Math.min(Math.max(12, r.left + r.width / 2 - 170), window.innerWidth - 352);
    const below = r.bottom + pop.offsetHeight + 16 < window.innerHeight;
    pop.style.left = `${left}px`;
    pop.style.top = `${below ? r.bottom + 10 : r.top - pop.offsetHeight - 10}px`;
  }, true);
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") pop.classList.add("hidden"); });
  $("#content").addEventListener("scroll", () => pop.classList.add("hidden"));
}

// ---------------------------------------------------------------- tema
function applyTheme(theme) {
  const root = document.documentElement;
  root.dataset.theme = theme || "dark";
  // Material: a cor de destaque é a do Windows
  if (theme === "material" && state.accent) root.style.setProperty("--accent", state.accent);
  else root.style.removeProperty("--accent");
  try { localStorage.setItem("pp-theme", root.dataset.theme); } catch { /* sem armazenamento local */ }
}

// ---------------------------------------------------------------- início do app
async function main() {
  hydrateIcons();
  $$(".nav").forEach((b) => (b.onclick = () => go(b.dataset.page)));
  document.addEventListener("click", (e) => {
    const g = e.target.closest("[data-goto]");
    if (g) go(g.dataset.goto, g.dataset.scroll);
  });
  $("#search").oninput = applySearch;
  setupTabs(); setupProfiles(); setupModal(); setupAnalyzer(); setupBoost(); setupTools(); setupWifi(); setupSettings(); setupDrivers(); setupUpstream(); setupLan(); setupDetail(); setupAlerts(); setupHelp();
  await bridgeReady();
  const boot = await safe("settings_get");
  if (boot) {
    state.accent = boot.accent;
    applyTheme(boot.settings.theme);
    setupI18n(boot.settings.lang || "pt-BR");
    startI18n();
    safe("ui_ready", { version: boot.version, lang: I18N.lang, theme: document.documentElement.dataset.theme,
      size: `${innerWidth}x${innerHeight}` });
  }
  $("#elevateBtn").onclick = async () => { if (!(await safe("relaunch_admin"))) toast("A permissão de administrador foi recusada.", true); };
  $("#masterToggle").onchange = async (e) => {
    await safe("set_active", e.target.checked);
    toast(e.target.checked ? "Otimização de jogos ligada" : "Otimização de jogos pausada");
    refreshOverview();
  };
  await refreshOverview();
  setInterval(refreshOverview, 3000);
  setInterval(refreshMonitor, 1000);
  setInterval(refreshConnections, 3000);
  setInterval(refreshDetail, 2000);
  setInterval(refreshLogs, 2000);
  window.addEventListener("resize", refreshMonitor);
}
main();
