"""Verifica se os projetos de origem mudaram desde a última revisão.

Os ajustes foram reescritos à mão em tweaks.py, então uma mudança lá fora nunca
entra sozinha no PingPilot: este módulo só avisa o que mudou, para alguém revisar
e portar. Depois da revisão, "marcar como revisado" grava o commit novo.

Usa só a API pública do GitHub (sem git), então funciona também no .exe.
Linha de comando:  python upstream.py
"""
import json
import os
import shutil
import sys
import urllib.error
import urllib.request

APP_DIR = os.path.dirname(os.path.abspath(__file__))
# versões revisadas que acompanham o app (dentro do .exe ficam em _MEIPASS, só leitura)
BUNDLED_STATE = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "upstream.json")
STATE_FILE = os.path.join(APP_DIR, "upstream.json")  # o app troca para a pasta de dados no .exe

SOURCES = {
    "winutil": {"title": "WinUtil", "repo": "ChrisTitusTech/winutil", "files": ["config/tweaks.json"],
                "tweaks": ["WPFToggleGameMode", "WPFToggleMouseAcceleration", "WPFTweaksDisableBGapps",
                           "WPFTweaksDeliveryOptimization", "WPFTweaksIPv46", "WPFTweaksTeredo",
                           "WPFTweaksActivity", "WPFTweaksConsumerFeatures", "WPFTweaksDeleteTempFiles",
                           "WPFTweaksRestorePoint"]},
    "koalaoptimizer": {"title": "KOALA Gaming Optimizer", "repo": "koalaaufpillen/koalaoptimizer",
                       "files": ["koalaoptimizerps1.ps1"]},
    "WLANOptimizer": {"title": "WLANOptimizer", "repo": "catid/WLANOptimizer",
                      "files": ["WLANOptimizer.cpp", "WLANOptimizer.h"]},
}


def _get(url, raw=False):
    if not url.startswith(("https://api.github.com/", "https://raw.githubusercontent.com/")):
        raise ValueError("URL fora do GitHub")
    req = urllib.request.Request(url, headers={"User-Agent": "PingPilot", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=20) as r:  # nosec B310 - só https do GitHub (conferido acima)
        data = r.read()
    return data if raw else json.loads(data)


def _load():
    if not os.path.exists(STATE_FILE) and os.path.exists(BUNDLED_STATE) and BUNDLED_STATE != STATE_FILE:
        shutil.copyfile(BUNDLED_STATE, STATE_FILE)
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _tweak_diff(repo, old, new, ids):
    def entries(sha):
        try:
            return json.loads(_get(f"https://raw.githubusercontent.com/{repo}/{sha}/config/tweaks.json", raw=True)
                              .decode("utf-8"), strict=False)
        except (urllib.error.URLError, ValueError):
            return {}
    a, b = entries(old), entries(new)
    return [i for i in ids if a.get(i) != b.get(i)], sorted(set(b) - set(a))


def check():
    state = _load()
    report = []
    for name, src in SOURCES.items():
        repo = src["repo"]
        item = {"name": name, "title": src["title"], "status": "ok", "files": [], "tweaks": [], "new_tweaks": [],
                "url": f"https://github.com/{repo}"}
        report.append(item)
        try:
            latest = _get(f"https://api.github.com/repos/{repo}/commits?per_page=1")[0]["sha"]
        except (urllib.error.URLError, ValueError, KeyError, IndexError) as e:
            item["status"] = "sem conexão com o GitHub" if isinstance(e, urllib.error.URLError) else "erro ao consultar"
            continue
        reviewed = state.setdefault(name, {}).get("reviewed") or latest
        state[name].update(reviewed=reviewed, latest=latest)
        if latest == reviewed:
            continue
        item["url"] = f"https://github.com/{repo}/compare/{reviewed[:12]}...{latest[:12]}"
        try:
            changed = {f["filename"] for f in _get(f"https://api.github.com/repos/{repo}/compare/{reviewed}...{latest}")
                       .get("files", [])}
            item["files"] = [f for f in src["files"] if f in changed]
        except (urllib.error.URLError, ValueError):
            item["files"] = src["files"]  # não deu para ver o detalhe: avisa como se tivesse mudado
        item["status"] = "mudou" if item["files"] else "mudou, mas não nos arquivos usados"
        if "tweaks" in src and item["files"]:
            item["tweaks"], item["new_tweaks"] = _tweak_diff(repo, reviewed, latest, src["tweaks"])
    _save(state)
    report.append({"name": "honectrl", "title": "HoneCTRL", "status": "mantido por vocês",
                   "files": [], "tweaks": [], "new_tweaks": [], "url": None})
    return report


def mark_reviewed(name):
    state = _load()
    if name not in state or not state[name].get("latest"):
        raise ValueError("rode a verificação antes")
    state[name]["reviewed"] = state[name]["latest"]
    _save(state)
    return True


if __name__ == "__main__":
    for r in check():
        print(f"{r['title']}: {r['status']}")
        for f in r["files"]:
            print("   arquivo alterado:", f)
        for t in r["tweaks"]:
            print("   ajuste usado pelo PingPilot mudou:", t)
        if r["new_tweaks"]:
            print(f"   {len(r['new_tweaks'])} ajuste(s) novo(s):", ", ".join(r["new_tweaks"][:10]))
        if r.get("url") and r["status"].startswith("mudou"):
            print("   ver:", r["url"])
