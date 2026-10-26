"""Teste da janela real (pywebview): a ponte JS↔Python funciona sob a CSP e a tradução liga.

    python build/test_window.py

Abre a janela por ~20 s em inglês (sem mudar a configuração salva), confere e fecha. Sai com código 1 se falhar.
"""
import os
import sys
import threading
import time

APP = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pingpilot"))
sys.argv[0] = os.path.abspath(sys.argv[0])  # o pywebview calcula a pasta base a partir do argv[0]
sys.path.insert(0, APP)
os.chdir(APP)
import webview  # noqa: E402

import app  # noqa: E402

api = app.Api()
api._config["settings"]["lang"] = "en"  # só nesta execução; nada é salvo
api._save = lambda: None
app.i18n.load("en")
win = webview.create_window("PingPilot - teste", os.path.join(app.UI_DIR, "index.html"), js_api=api,
                            width=1200, height=800)
result = {}


def probe():
    time.sleep(10)
    js = ("JSON.stringify({lang: I18N.lang, bridge: typeof window.pywebview.api.settings_get, "
          "toasts: document.querySelector('#toasts').innerText, title: document.querySelector('#page-home h2').textContent, "
          "csp: !!document.querySelector('meta[http-equiv=\"Content-Security-Policy\"]'), "
          "profiles: document.querySelectorAll('.cards-grid.profiles .card').length})")
    result["load"] = win.evaluate_js(js)
    win.evaluate_js("location.reload()")
    time.sleep(8)
    result["reload"] = win.evaluate_js(js)
    ok = all('"lang":"en"' in (r or "") and '"toasts":""' in r and '"title":"For you"' in r for r in result.values())
    for k, v in result.items():
        print(f"{k}: {v}")
    print("OK" if ok else "FALHOU")
    sys.stdout.flush()
    os._exit(0 if ok else 1)


threading.Thread(target=probe, daemon=True).start()
webview.start(storage_path=os.path.join(app.DATA_DIR, ".webview-teste"))
