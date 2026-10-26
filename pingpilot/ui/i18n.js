"use strict";
// Tradução da interface. O app é escrito em português; os dicionários (i18n-en.js, i18n-es.js)
// mapeiam o texto em português para o outro idioma. Um MutationObserver traduz tudo que aparece
// na tela — HTML fixo, conteúdo gerado pelo JavaScript, avisos e mensagens vindas do Python.
// Chaves com {0}, {1}… são modelos: "Último teste: {0}" traduz "Último teste: 26/10 09:26".

const I18N = { lang: "pt-BR", dict: new Map(), patterns: [] };
const I18N_DONE = new WeakMap();  // nó -> texto que nós mesmos escrevemos (evita traduzir em laço)

function setupI18n(lang) {
  I18N.lang = lang;
  I18N.dict = new Map();
  I18N.patterns = [];
  document.documentElement.lang = lang;
  const data = { en: window.I18N_EN, es: window.I18N_ES }[lang];
  if (!data) return;
  for (const [pt, out] of Object.entries(data)) {
    if (!/\{\d\}/.test(pt)) {
      I18N.dict.set(pt, out);
      continue;
    }
    const parts = pt.split(/(\{\d\})/);
    const source = parts.map((p) => (/^\{\d\}$/.test(p) ? "(.+?)" : p.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))).join("");
    I18N.patterns.push({ re: new RegExp(`^${source}$`, "s"), out, order: parts.filter((p) => /^\{\d\}$/.test(p)).map((p) => +p[1]) });
  }
}

function tr(text) {
  if (text == null || (!I18N.dict.size && !I18N.patterns.length)) return text;
  const m = String(text).match(/^(\s*)([\s\S]*?)(\s*)$/);
  const core = m[2];
  if (!core || !/[A-Za-zÀ-ÿ]/.test(core)) return text;
  let res = I18N.dict.get(core);
  if (res === undefined) {
    for (const p of I18N.patterns) {
      const mm = core.match(p.re);
      if (mm) {
        res = p.out.replace(/\{(\d)\}/g, (_, n) => {
          const i = p.order.indexOf(+n);
          return i >= 0 ? tr(mm[i + 1]) : "";
        });
        break;
      }
    }
  }
  return res === undefined ? text : m[1] + res + m[3];
}

// traduz texto com {0}, {1}… preenchidos (para textos montados no JavaScript, ex.: canvas)
function t(text, ...args) {
  let out = tr(text);
  args.forEach((a, i) => { out = out.replace(`{${i}}`, a); });
  return out;
}

const I18N_ATTRS = ["title", "placeholder"];

function translateNode(node) {
  if (node.nodeType === Node.TEXT_NODE) {
    const cur = node.nodeValue;
    if (!cur.trim() || I18N_DONE.get(node) === cur) return;
    const out = tr(cur);
    if (out !== cur) {
      I18N_DONE.set(node, out);
      node.nodeValue = out;
    }
    return;
  }
  if (node.nodeType !== Node.ELEMENT_NODE || ["SCRIPT", "STYLE", "CANVAS", "TEXTAREA"].includes(node.tagName)) return;
  if (node.hasAttribute("data-i18n") && !node.dataset.i18nDone) {
    // trecho com formatação no meio (<b>, <code>…): traduz o HTML inteiro de uma vez
    const html = node.innerHTML.trim().replace(/\s+/g, " ");
    const out = tr(html);
    node.dataset.i18nDone = "1";
    if (out !== html) { node.innerHTML = out; return; }
  }
  for (const a of I18N_ATTRS) {
    const v = node.getAttribute(a);
    if (v) {
      const out = tr(v);
      if (out !== v) node.setAttribute(a, out);
    }
  }
  node.childNodes.forEach(translateNode);
}

function startI18n() {
  if (I18N.lang === "pt-BR") return;
  translateNode(document.body);
  new MutationObserver((muts) => {
    for (const m of muts) {
      if (m.type === "childList") m.addedNodes.forEach(translateNode);
      else if (m.type === "characterData") translateNode(m.target);
      else if (m.type === "attributes") {
        const v = m.target.getAttribute(m.attributeName);
        const out = tr(v);
        if (v && out !== v) m.target.setAttribute(m.attributeName, out);
      }
    }
  }).observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: I18N_ATTRS });
  // diálogos nativos também passam pelo dicionário
  const { confirm: c, prompt: p, alert: a } = window;
  window.confirm = (msg) => c.call(window, tr(msg));
  window.prompt = (msg, def) => p.call(window, tr(msg), def);
  window.alert = (msg) => a.call(window, tr(msg));
}
