"""Tradução do lado Python (notificações do Windows e menu da bandeja), com os mesmos
dicionários da interface (ui/i18n-en.js, ui/i18n-es.js)."""
import ctypes
import json
import os
import re
import sys

UI_DIR = os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), "ui")
LANGS = ["pt-BR", "en", "es"]
_state = {"dict": {}, "patterns": []}


def detect_lang():
    """Idioma da interface do Windows: português -> pt-BR, espanhol -> es, o resto -> en."""
    try:
        primary = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
    except (AttributeError, OSError):
        return "pt-BR"
    return {0x16: "pt-BR", 0x0A: "es"}.get(primary, "en")


def load(lang):
    _state["dict"], _state["patterns"] = {}, []
    if lang not in ("en", "es"):
        return
    try:
        src = open(os.path.join(UI_DIR, f"i18n-{lang}.js"), encoding="utf-8").read()
        data = json.loads(src[src.index("{"):src.rindex("}") + 1])
    except (OSError, ValueError):
        return
    for pt, out in data.items():
        if re.search(r"\{\d\}", pt):
            parts = re.split(r"(\{\d\})", pt)
            source = "".join("(.+?)" if re.fullmatch(r"\{\d\}", p) else re.escape(p) for p in parts)
            order = [int(p[1]) for p in parts if re.fullmatch(r"\{\d\}", p)]
            _state["patterns"].append((re.compile(f"^{source}$", re.S), out, order))
        else:
            _state["dict"][pt] = out


def tr(text):
    if not text or (not _state["dict"] and not _state["patterns"]):
        return text
    if text in _state["dict"]:
        return _state["dict"][text]
    for rx, out, order in _state["patterns"]:
        m = rx.match(text)
        if m:
            return re.sub(r"\{(\d)\}", lambda g: tr(m.group(order.index(int(g.group(1))) + 1))
                          if int(g.group(1)) in order else "", out)
    return text
