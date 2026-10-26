"""PingPilot — otimizador local de rede e PC para jogos.

Uso:
  pythonw app.py              abre a janela (pede administrador)
  python app.py --browser     serve a interface em http://127.0.0.1:8765 (para testes)
  python app.py --no-elevate  abre sem pedir administrador
"""
import collections
import ctypes
import faulthandler
import ipaddress
import json
import logging
import logging.handlers
import os
import platform
import secrets
import re
import shutil
import socket
import statistics
import subprocess
import sys
import threading
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import core
import drivers
import i18n
import tweaks
import upstream
import winproc

VERSION = "1.0.0"
FROZEN = getattr(sys, "frozen", False)  # rodando como PingPilot.exe (PyInstaller)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(getattr(sys, "_MEIPASS", APP_DIR), "ui")
# no .exe a pasta do programa é temporária; os dados ficam em %LOCALAPPDATA%\PingPilot
DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA") or APP_DIR, "PingPilot") if FROZEN else APP_DIR
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
BACKUP_FILE = os.path.join(DATA_DIR, "backup.json")
LOG_DIR = os.path.join(DATA_DIR, "logs")
if FROZEN:  # no .exe, o estado revisado dos projetos de origem fica na pasta de dados (gravável)
    upstream.STATE_FILE = os.path.join(DATA_DIR, "upstream.json")
logger = logging.getLogger("pingpilot")


def setup_logging():
    """Grava ações, erros e travamentos em logs/ para os testadores poderem enviar."""
    os.makedirs(LOG_DIR, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(os.path.join(LOG_DIR, "pingpilot.log"), maxBytes=1_000_000,
                                                   backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s [%(name)s] %(message)s"))
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.WARNING)  # erros de bibliotecas (pywebview etc.) também entram
    logger.setLevel(logging.INFO)
    # no .exe sem console não existe stdout/stderr; manda para o log em vez de perder
    if sys.stdout is None or sys.stderr is None:
        stream = open(os.path.join(LOG_DIR, "saida.log"), "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or stream
        sys.stderr = sys.stderr or stream
    # travamento duro (falha no Python ou em DLL): faulthandler escreve o rastro antes de morrer
    faulthandler.enable(open(os.path.join(LOG_DIR, "crash.log"), "a", encoding="utf-8"))
    sys.excepthook = lambda t, v, tb: logger.critical("Erro não tratado", exc_info=(t, v, tb))
    threading.excepthook = lambda a: logger.error(f"Erro na thread {a.thread.name if a.thread else '?'}",
                                                  exc_info=(a.exc_type, a.exc_value, a.exc_traceback))
    logger.info("=" * 60)
    logger.info(f"PingPilot {VERSION} | {platform.platform()} | Python {platform.python_version()} | "
                f"{'exe' if FROZEN else 'script'} | admin={core.is_admin()}")
TASK_NAME = "PingPilot"

DNS_SERVERS = [
    ("OpenDNS", "208.67.222.222", "208.67.220.220"),
    ("Cloudflare", "1.1.1.1", "1.0.0.1"),
    ("NextDNS", "45.90.28.0", "45.90.30.0"),
    ("AdGuard", "94.140.14.14", "94.140.15.15"),
    ("Control D", "76.76.2.0", "76.76.10.0"),
    ("Quad9", "9.9.9.9", "149.112.112.112"),
    ("Google", "8.8.8.8", "8.8.4.4"),
    ("Verisign", "64.6.64.6", "64.6.65.6"),
    ("Neustar", "156.154.70.5", "156.154.71.5"),
    ("Comodo Secure", "8.26.56.26", "8.20.247.20"),
]
SETTING_CHOICES = {
    "lang": i18n.LANGS,
    "theme": ["dark", "light", "midnight", "pastel", "cyber", "glass", "material"],
    "dns_interval": [1800, 3600, 10800, 21600],
    "window_size": ["1280x720", "1360x840", "1440x810", "1600x900", "1920x1080"],
}
SETTING_BOOLS = {"auto_dns", "tray", "notify_game", "notify_unstable", "verbose_logs", "notify_upstream",
                 "notify_drivers", "notify_dns", "notify_session"}
# tipo de alerta -> configuração que liga/desliga (Configurações > Notificações)
ALERT_SETTINGS = {"game": "notify_game", "unstable": "notify_unstable", "upstream": "notify_upstream",
                  "drivers": "notify_drivers", "dns": "notify_dns", "session": "notify_session"}
DRIVER_CHECK_INTERVAL = 24 * 3600
ALERT_COOLDOWN = 300  # um alerta de conexão instável por jogo a cada 5 min, no máximo
TEST_DOMAINS = ["google.com", "steampowered.com", "riotgames.com", "epicgames.com", "discord.com"]

MONITOR_GROUPS = {
    "internet": [("Google", "8.8.8.8", "icmp"), ("Cloudflare", "1.1.1.1", "icmp")],
    "gateway": [("Roteador", "{gateway}", "icmp")],
    "aws": [("AWS São Paulo", "dynamodb.sa-east-1.amazonaws.com:443", "tcp"),
            ("AWS Virgínia", "dynamodb.us-east-1.amazonaws.com:443", "tcp")],
}

DEFAULT_CONFIG = {
    "profiles": [],
    "ping_targets": [["Cloudflare", "1.1.1.1"], ["Google", "8.8.8.8"]],
    "custom_dns": [],
    "dns_results": {},
    "settings": {"active": True, "monitor": True, "wifi": False, "auto_dns": False, "dns_interval": 3600,
                 "tray": True, "notify_game": False, "notify_unstable": True, "verbose_logs": False,
                 "notify_upstream": True, "notify_drivers": True, "notify_dns": True, "notify_session": False,
                 "window_size": "1360x840", "lang": None, "theme": "dark"},
    "last_session": None,
}


# ---------------------------------------------------------------- validação do que vem da interface
# Tudo que chega da interface é tratado como entrada não confiável (defesa caso algum texto de fora
# escape do esc() e rode script na página).

HOST_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,252})$")  # IP ou domínio; nunca começa com "-"
MAC_RE = re.compile(r"^[0-9A-F]{2}(?:-[0-9A-F]{2}){5}$")


def valid_ipv4(ip):
    try:
        return str(ipaddress.IPv4Address(str(ip).strip()))
    except ValueError:
        raise ValueError(f"IP inválido: {str(ip)[:40]}")


def valid_host(host):
    host = str(host).strip()
    if not HOST_RE.match(host):
        raise ValueError("Digite um IP ou domínio válido.")
    return host


def clamp_int(value, low, high, default):
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


class Monitor:
    """Ping contínuo para os alvos de todos os grupos, guardando os últimos 10 minutos."""

    def __init__(self):
        self.series = {}
        self._stop = threading.Event()
        self.threads = []
        self.gateway = None

    def running(self):
        return any(t.is_alive() for t in self.threads)

    def start(self, gateway):
        if self.running():
            return
        self.gateway = gateway
        self._stop.clear()
        self.threads = []
        for group, targets in MONITOR_GROUPS.items():
            for name, host, kind in targets:
                host = host.replace("{gateway}", gateway or "")
                if not host:
                    continue
                key = f"{group}:{name}"
                self.series.setdefault(key, collections.deque(maxlen=600))
                t = threading.Thread(target=self._loop, args=(key, host, kind), daemon=True)
                t.start()
                self.threads.append(t)

    def stop_all(self):
        self._stop.set()

    def _add(self, key, ms):
        self.series[key].append((time.time(), ms))

    def _loop(self, key, host, kind):
        if kind == "icmp":
            while not self._stop.is_set():
                core.ping_stream(host, 0, lambda ms: self._add(key, ms), self._stop)
                self._stop.wait(1)
        else:
            h, port = host.rsplit(":", 1)
            while not self._stop.is_set():
                t0 = time.time()
                self._add(key, core.tcp_ping(h, port))
                self._stop.wait(max(0.0, 1 - (time.time() - t0)))

    def group(self, group, seconds):
        cutoff = time.time() - seconds
        out = []
        for name, _, _ in MONITOR_GROUPS[group]:
            data = [(t, ms) for t, ms in self.series.get(f"{group}:{name}", ()) if t >= cutoff]
            st = core.ping_stats([ms for _, ms in data])
            out.append({"name": name, "points": [[round(t, 1), ms] for t, ms in data], "stats": st,
                        "quality": core.quality(st, local=(group == "gateway")) if data else "none"})
        return out

    def latest(self, key, seconds=3):
        cutoff = time.time() - seconds
        vals = [ms for t, ms in self.series.get(key, ()) if t >= cutoff]
        return vals[-1] if vals else None


class Api:
    def __init__(self):
        self._admin = core.is_admin()
        self._config = {**DEFAULT_CONFIG, **load_json(CONFIG_FILE, {})}
        self._config["settings"] = {**DEFAULT_CONFIG["settings"], **self._config.get("settings", {})}
        self._logs = collections.deque(maxlen=300)
        self._jobs = {}
        self._adapter = None
        self._engine = tweaks.TweakEngine(BACKUP_FILE, self._log)
        self._monitor = Monitor()
        self._wifi = core.WlanOptimizer()
        self._session = None
        self._running_games = {}
        self._conn_cache = {}
        self._conn = {}
        self._rdns = {}
        self._stop = threading.Event()
        self._drivers = None
        self._log(f"PingPilot {VERSION} iniciado" + (" como administrador" if self._admin else " sem administrador"))
        self._refresh_adapter()
        if self._config["settings"]["monitor"]:
            self._monitor.start((self._adapter or {}).get("Gateway"))
        if self._config["settings"]["wifi"]:
            self._log("Otimizador de Wi-Fi: " + self._wifi.start())
        self._migrate_profiles()
        self._sync_exes()
        if not self._config["settings"].get("lang"):  # primeira vez: segue o idioma do Windows
            self._config["settings"]["lang"] = i18n.detect_lang()
            self._save()
        i18n.load(self._config["settings"]["lang"])
        if self._config["settings"]["verbose_logs"]:
            logger.setLevel(logging.DEBUG)
        threading.Thread(target=self._watcher, daemon=True).start()
        threading.Thread(target=self._startup_checks, name="verificacoes", daemon=True).start()

    # ---- infraestrutura

    def _log(self, msg):
        self._logs.append({"t": time.strftime("%H:%M:%S"), "msg": msg})
        logger.info(msg)

    def report_error(self, message, where=""):
        """Erros da interface (JavaScript) chegam aqui para entrar no arquivo de log."""
        where = re.sub(r"[^\w.-]", "", str(where))[:40]
        logger.error(f"[interface{' ' + where if where else ''}] {str(message)[:2000]}")
        return True

    def ui_ready(self, info):
        """A interface avisa que carregou (versão, idioma, tema) — ajuda a diagnosticar cache antigo."""
        info = info if isinstance(info, dict) else {}
        clean = {k: re.sub(r"[^\w.-]", "", str(info.get(k, "")))[:20] for k in ("version", "lang", "theme", "size")}
        logger.info(f"Interface carregada: versão {clean['version']}, idioma {clean['lang']}, "
                    f"tema {clean['theme']}, janela {clean['size']}")
        return True

    def open_logs(self):
        os.startfile(LOG_DIR)
        return True

    def export_logs(self):
        """Junta logs e configuração num .zip para o testador enviar."""
        path = os.path.join(DATA_DIR, f"PingPilot-logs-{time.strftime('%Y%m%d-%H%M')}.zip")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name in os.listdir(LOG_DIR):
                z.write(os.path.join(LOG_DIR, name), "logs/" + name)
            for f in (CONFIG_FILE, BACKUP_FILE):
                if os.path.exists(f):
                    z.write(f, os.path.basename(f))
            z.writestr("sistema.txt", f"PingPilot {VERSION}\n{platform.platform()}\nadmin={self._admin}\n"
                                      f"adaptador={json.dumps(self._adapter, ensure_ascii=False)}\n")
        subprocess.Popen(["explorer", "/select,", path])
        self._log(f"Logs exportados: {path}")
        return path

    def _save(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def _job(self, fn, *args):
        jid = uuid.uuid4().hex[:8]
        logger.debug(f"tarefa {jid} iniciada: {getattr(fn, '__qualname__', fn)}")
        self._jobs[jid] = {"done": False, "progress": None, "result": None, "error": None}

        def runner():
            try:
                self._jobs[jid]["result"] = fn(jid, *args)
            except Exception as e:
                self._jobs[jid]["error"] = str(e)
                self._logs.append({"t": time.strftime("%H:%M:%S"), "msg": f"Erro: {e}"})
                logger.exception(f"Erro na tarefa {getattr(fn, '__name__', '?')}")
            self._jobs[jid]["done"] = True
        threading.Thread(target=runner, daemon=True).start()
        return jid

    def job(self, jid):
        return self._jobs.get(str(jid)) or {"done": True, "error": "tarefa não encontrada"}

    def _refresh_adapter(self):
        self._adapter = core.active_adapter()
        self._engine.guid = (self._adapter or {}).get("Guid")
        self._engine.wireless = bool((self._adapter or {}).get("Wireless"))
        self._engine.nic = core.nic_class_path(self._adapter["Index"]) if self._adapter else None
        return self._adapter

    # ---- visão geral

    def overview(self):
        groups = self._monitor.group("internet", 60)
        avg = [g["stats"]["avg"] for g in groups if g["stats"]["avg"] is not None]
        return {
            "version": VERSION, "admin": self._admin, "adapter": self._adapter,
            "monitor": self._monitor.running(), "settings": self._config["settings"],
            "ping_now": round(min(avg)) if avg else None,
            "profiles": self._profiles(), "last_session": self._config.get("last_session"),
            "session": self._session_view(), "wifi": self._wifi.last_result,
            "alerts_unread": sum(1 for a in self._config.get("alerts", []) if not a["read"]),
        }

    def set_active(self, on):
        self._config["settings"]["active"] = bool(on)
        self._save()
        self._log("Otimização de jogos " + ("ligada" if on else "pausada"))
        return bool(on)

    def get_logs(self):
        return list(self._logs)

    # ---- perfis de jogo (Conexões)
    #
    # Um perfil agrupa todos os .exe de um app (ex.: Riot Client = Riot Client.exe + RiotClientServices.exe).
    # O vínculo é pelo nome do executável, nunca pelo PID: quando o jogo fecha e abre de novo (PID novo),
    # o watcher encontra o processo novo sozinho a cada 3 s.

    def _migrate_profiles(self):
        """Perfis antigos (um .exe cada) viram perfis agrupados pela pasta de instalação."""
        merged = {}
        changed = False
        for p in self._config["profiles"]:
            if "exes" not in p:
                p["exes"] = [p.pop("exe")]
                changed = True
            if p.get("path") and not p.get("root"):
                p["root"] = winproc.install_root(p["path"])
                changed = True
            key = (p.get("root") or p["name"]).casefold()
            if key in merged:
                base = merged[key]
                base["exes"] = sorted(set(base["exes"]) | set(p["exes"]), key=str.casefold)
                base["enabled"] = base.get("enabled") or p.get("enabled")
                changed = True
            else:
                merged[key] = p
        for p in merged.values():
            if p.get("root"):
                title = winproc.app_title(p["root"], [p["path"]])
                # troca só nomes automáticos (nome do .exe); um nome que o usuário escolheu fica
                auto = {e.casefold() for e in p["exes"]} | {e[:-4].casefold() for e in p["exes"]}
                if title != p["name"] and (p["name"].casefold() in auto or p.get("auto_name", True)):
                    p["name"] = title
                exes = sorted({e for e in set(p["exes"]) | set(winproc.sibling_exes(p["root"]))
                               if not any(w in e.casefold() for w in winproc.SKIP_WORDS)}, key=str.casefold)
                changed = changed or exes != p["exes"]
                p["exes"] = exes
            if p.get("path") and (not p.get("icon") or p.get("icon_v") != 2):
                p["icon"], p["icon_v"] = winproc.icon_png(p["path"]), 2
                changed = True
        if changed:
            self._config["profiles"] = list(merged.values())
            self._save()
            self._log(f"Perfis de jogo reorganizados: {len(self._config['profiles'])} app(s)")

    def _profiles(self):
        return [{k: v for k, v in p.items() if k != "icon_v"} | {"running": p["id"] in self._running_games}
                for p in self._config["profiles"]]

    def list_processes(self):
        """Apps abertos agora, já agrupados (os que já estão na lista ficam marcados)."""
        known = {e.casefold() for p in self._config["profiles"] for e in p["exes"]}
        apps = winproc.running_apps()
        for a in apps:
            a["added"] = any(e.casefold() in known for e in a["exes"])
            a.pop("paths", None)
        return apps

    def add_profile(self, name, exes=None, path=None):
        """Adiciona um app (vindo da lista de abertos) ou um .exe digitado à mão."""
        if not exes:  # digitado à mão
            exe = core.clean_exe_name(name)
            if not exe:
                raise ValueError("nome de executável inválido")
            exes, name = [exe + ".exe"], exe
            pids = winproc.pids_by_name().get(exes[0].casefold(), [])
            path = next((p for p in map(winproc.exe_path, pids) if p), None)
        exes = [str(e) for e in list(exes)[:50] if core.clean_exe_name(str(e))]
        name = str(name)[:40]
        # o caminho vem da interface: só aceita um .exe que existe de verdade
        if path and not (str(path).lower().endswith(".exe") and os.path.isfile(str(path))):
            path = None
        root = winproc.install_root(path) if path else None
        if root:
            name = winproc.app_title(root, [path])
            exes = sorted(set(exes) | set(winproc.sibling_exes(root)), key=str.casefold)
        existing = next((p for p in self._config["profiles"]
                         if (root and (p.get("root") or "").casefold() == root.casefold())
                         or p["name"].casefold() == name.casefold()), None)
        if existing:
            existing["exes"] = sorted(set(existing["exes"]) | set(exes), key=str.casefold)
            existing["path"] = existing.get("path") or path
            self._log(f"{existing['name']}: executáveis atualizados ({', '.join(existing['exes'])})")
        else:
            self._config["profiles"].append({
                "id": uuid.uuid4().hex[:8], "name": name[:40], "exes": exes, "path": path, "root": root,
                "icon": winproc.icon_png(path), "icon_v": 2, "enabled": True, "priority": "High"})
            self._log(f"Jogo adicionado: {name} ({', '.join(exes)})")
        self._save()
        self._sync_exes()
        return self._profiles()

    def _sync_exes(self):
        """Mantém as regras de QoS dos jogos em dia com a lista de perfis."""
        self._engine.exes = [e for p in self._config["profiles"] if p.get("enabled") for e in p["exes"]]
        qos = next(t for t in tweaks.CATALOG if t["id"] == "qos_dscp")
        if self._admin and self._engine.exes and self._engine.state(qos):
            threading.Thread(target=self._engine.set, args=("qos_dscp", True), daemon=True).start()

    def remove_profile(self, pid):
        self._config["profiles"] = [p for p in self._config["profiles"] if p["id"] != pid]
        self._save()
        self._sync_exes()
        return self._profiles()

    def update_profile(self, pid, changes):
        for p in self._config["profiles"]:
            if p["id"] == pid:
                if "enabled" in changes:
                    p["enabled"] = bool(changes["enabled"])
                if changes.get("priority") in ("High", "AboveNormal", "Normal"):
                    p["priority"] = changes["priority"]
                if "name" in changes:
                    p["name"] = str(changes["name"]).strip()[:40] or p["name"]
                if "name" in changes:
                    p["auto_name"] = False
                if "remove_exe" in changes and len(p["exes"]) > 1:
                    p["exes"] = [e for e in p["exes"] if e != changes["remove_exe"]]
                self._log(f"{p['name']}: {'otimização ligada' if p['enabled'] else 'otimização desligada'}"
                         f", prioridade {p['priority']}")
        self._save()
        self._sync_exes()
        return self._profiles()

    # ---- conexões dos jogos abertos

    def connections(self):
        """Uma linha por app aberto: servidor principal, protocolo, nº de conexões e ping."""
        rows = []
        for p in self._config["profiles"]:
            st = self._conn.get(p["id"])
            if p["id"] not in self._running_games or not st:
                continue
            main = st.get("main")
            last = st["samples"][-1][1] if st["samples"] else None
            rows.append({"id": p["id"], "game": p["name"], "icon": p.get("icon"),
                         "server": f"{main[0]}:{main[1]}" if main else None,
                         "host": self._rdns.get(main[0]) if main else None,
                         "proto": "TCP" if main else ("UDP" if st["udp"] else "—"),
                         "tcp": len(st["conns"]), "udp": st["udp"], "ping": last})
        return rows

    def connection_detail(self, pid, seconds=60):
        p = self._profile(pid)
        st = self._conn.get(pid)
        running = pid in self._running_games
        cutoff = time.time() - clamp_int(seconds, 10, 3600, 60)
        samples = [(t, ms) for t, ms in (st["samples"] if st else ()) if t >= cutoff]
        stats = core.ping_stats([ms for _, ms in samples])
        main = st.get("main") if st else None
        return {
            "profile": {k: v for k, v in p.items() if k != "icon_v"}, "running": running,
            "duration": int(time.time() - st["since"]) if st and running else 0,
            "server": f"{main[0]}:{main[1]}" if main else None, "port": main[1] if main else None,
            "host": self._rdns.get(main[0]) if main else None,
            "last": samples[-1][1] if samples else None, "stats": stats,
            "points": [[round(t, 1), ms] for t, ms in samples],
            "conns": [{"server": f"{c['remote']}:{c['port']}", "host": self._rdns.get(c["remote"]),
                       "exe": c.get("exe"), "main": main == (c["remote"], c["port"])}
                      for c in (st["conns"] if st else [])],
            "udp": st["udp"] if st else 0, "pids": len(self._running_games.get(pid, [])),
        }

    def route_trace(self, pid):
        st = self._conn.get(pid)
        if not st or not st.get("main"):
            raise RuntimeError("Nenhum servidor TCP deste app para traçar a rota agora.")
        ip = st["main"][0]

        def work(jid):
            self._jobs[jid]["progress"] = f"Traçando a rota até {ip}…"
            return {"target": ip, "hops": core.traceroute(ip)}
        return self._job(work)

    def _update_connections(self):
        """Coleta as conexões dos apps abertos e mede o ping do servidor principal de cada um."""
        if not self._running_games:
            self._conn = {k: v for k, v in self._conn.items() if k in self._running_games}
            return
        tcp, udp = winproc.tcp_connections(), winproc.udp_endpoints()
        for pid, pids in self._running_games.items():
            pidset = set(pids)
            st = self._conn.setdefault(pid, {"since": time.time(), "samples": collections.deque(maxlen=1200),
                                             "main": None, "conns": [], "udp": 0})
            seen, conns = set(), []
            for c in tcp:
                if c["pid"] in pidset and (c["remote"], c["port"]) not in seen:
                    seen.add((c["remote"], c["port"]))
                    conns.append(c)
            st["conns"], st["udp"] = conns, sum(1 for u in udp if u["pid"] in pidset)
            st["main"] = self._pick_main(st["main"], conns)
            for c in conns[:30]:
                self._resolve(c["remote"])
            if st["main"]:
                ms = core.tcp_ping(*st["main"], timeout=1)
                st["samples"].append((time.time(), None if ms is None else round(ms)))
        for pid in [k for k in self._conn if k not in self._running_games]:
            del self._conn[pid]

    @staticmethod
    def _pick_main(current, conns):
        """Servidor "do jogo": mantém o atual enquanto existir; senão prefere portas que não sejam web."""
        keys = [(c["remote"], c["port"]) for c in conns if not c["remote"].startswith(("10.", "192.168."))]
        if current in keys:
            return current
        game = [k for k in keys if k[1] not in (80, 443)]
        return (game or keys or [None])[0]

    def _resolve(self, ip):
        if ip in self._rdns:
            return
        self._rdns[ip] = None

        def work():
            try:
                self._rdns[ip] = socket.gethostbyaddr(ip)[0]
            except OSError:
                pass
        threading.Thread(target=work, daemon=True).start()

    def _watcher(self):
        """A cada 3 s: acha os processos de cada perfil (pelo nome, então PID novo é pego sozinho),
        aplica a prioridade, coleta as conexões e registra a sessão. Um erro nunca derruba o laço."""
        warned = set()
        while not self._stop.wait(3):
            try:
                names = winproc.pids_by_name()
                running = {}
                for p in self._config["profiles"]:
                    pids = [pid for e in p["exes"] for pid in names.get(e.casefold(), [])]
                    if not pids:
                        continue
                    running[p["id"]] = pids
                    if not p.get("root"):  # adicionado sem caminho (ex.: jogo com anti-cheat): resolve agora
                        path = next((x for x in map(winproc.exe_path, pids) if x), None)
                        if path:
                            p.update(path=path, root=winproc.install_root(path), icon=winproc.icon_png(path), icon_v=2)
                            self._migrate_profiles()  # junta com outros perfis do mesmo app e acha os .exe irmãos
                            self._save()
                    if p.get("enabled") and self._config["settings"]["active"]:
                        changed, errors = winproc.ensure_priority(pids, p.get("priority", "High"))
                        if changed:
                            self._log(f"{p['name']}: prioridade {p.get('priority')} aplicada em {len(changed)} processo(s)")
                        for pid_, err in errors:
                            if pid_ not in warned:
                                warned.add(pid_)
                                self._log(f"{p['name']}: o Windows recusou mudar a prioridade do processo {pid_} "
                                         f"(erro {err}; anti-cheat ou falta de administrador)")
                for pid in running.keys() - self._running_games.keys():
                    p = self._profile(pid)
                    self._log(f"Jogo detectado: {p['name']}")
                    on = p.get("enabled") and self._config["settings"]["active"]
                    self._add_alert("game", f"{p['name']} detectado", "Otimização ativa: prioridade e monitoramento ligados."
                                   if on else "Otimização desligada para este jogo.", page="connections", os_notify=True)
                for pid in self._running_games.keys() - running.keys():
                    self._log(f"Jogo fechado: {self._profile(pid)['name']}")
                self._running_games = running
                self._update_connections()
                self._check_alerts()
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug("jogos abertos: " + ", ".join(
                        f"{self._profile(k)['name']} ({len(v)} proc, servidor {self._conn.get(k, {}).get('main')}, "
                        f"ping {self._conn[k]['samples'][-1][1] if self._conn.get(k) and self._conn[k]['samples'] else '-'})"
                        for k, v in running.items()) if running else "jogos abertos: nenhum")
                self._track_session()
                self._auto_dns_tick()
            except Exception:
                logger.exception("Erro no monitoramento dos jogos (o laço continua)")

    def _auto_dns_tick(self):
        """DNS automático: novo teste a cada 1 h com o app aberto, nunca durante uma partida."""
        if not (self._config["settings"]["auto_dns"] and self._admin) or self._session:
            return
        if time.time() - self._config.get("dns_tested_ts", 0) < self._config["settings"]["dns_interval"]:
            return
        if any(not j["done"] for j in self._jobs.values()):
            return  # outro teste/tarefa em andamento
        self._config["dns_tested_ts"] = time.time()  # evita disparar de novo antes de terminar
        self.dns_benchmark()

    def _profile(self, pid):
        return next((p for p in self._config["profiles"] if p["id"] == pid), {"name": "?"})

    def _track_session(self):
        active = [pid for pid in self._running_games if self._profile(pid).get("enabled")]
        if active and not self._session:
            self._session = {"game": self._profile(active[0])["name"], "id": active[0], "start": time.time(),
                             "samples": []}
        if self._session:
            # ping do servidor do próprio jogo quando houver; senão, o da internet em geral
            st = self._conn.get(self._session["id"])
            if st and st["samples"] and time.time() - st["samples"][-1][0] < 4:
                ms = st["samples"][-1][1]
            else:
                ms = self._monitor.latest("internet:Cloudflare") if self._monitor.running() else core.ping_once("1.1.1.1")
            self._session["samples"].append(ms)
            if not active:
                st = core.ping_stats(self._session["samples"])
                self._config["last_session"] = {"game": self._session["game"],
                                               "duration": int(time.time() - self._session["start"]),
                                               "ended": time.strftime("%d/%m %H:%M"), **st}
                self._save()
                self._log(f"Sessão encerrada: {self._session['game']}")
                if st["avg"] is not None:
                    self._add_alert("session", f"Partida encerrada: {self._session['game']}",
                                   f"Ping médio {st['avg']:.0f} ms · jitter {st['jitter']:.0f} ms · perda {st['loss']:.0f}%",
                                   page="home")
                self._session = None

    def _session_view(self):
        if not self._session:
            return None
        return {"game": self._session["game"], "duration": int(time.time() - self._session["start"]),
                **core.ping_stats(self._session["samples"])}

    # ---- analisador de rede

    def monitor_data(self, group, seconds):
        if group not in MONITOR_GROUPS:
            raise ValueError("grupo desconhecido")
        return {"running": self._monitor.running(), "series": self._monitor.group(group, clamp_int(seconds, 10, 600, 60)),
                "adapter": self._adapter}

    def monitor_set(self, on):
        self._config["settings"]["monitor"] = bool(on)
        self._save()
        if on:
            self._monitor.start((self._adapter or {}).get("Gateway"))
        else:
            self._monitor.stop_all()
        return self._monitor.running() or bool(on)

    def ping_targets(self):
        return self._config["ping_targets"]

    def set_ping_targets(self, targets):
        self._config["ping_targets"] = [[str(n)[:40], valid_host(h)] for n, h in list(targets)[:30] if h]
        self._save()
        return self._config["ping_targets"]

    def ping_test(self, count):
        count = max(5, min(200, int(count)))
        targets = list(self._config["ping_targets"])
        gw = (self._adapter or {}).get("Gateway")
        if gw:
            targets.insert(0, ["Seu roteador", gw])
        return self._job(self._ping_job, targets, count)

    def _ping_job(self, jid, targets, count):
        samples = {h: [] for _, h in targets}

        def progress():
            self._jobs[jid]["progress"] = [
                {"name": n, "host": h, "sent": len(samples[h]), "total": count, **core.ping_stats(samples[h]),
                 "quality": core.quality(core.ping_stats(samples[h]), local=(n == "Seu roteador"))
                 if samples[h] else "none"} for n, h in targets]

        threads = [threading.Thread(target=core.ping_stream,
                                    args=(h, count, lambda ms, h=h: (samples[h].append(ms), progress())),
                                    daemon=True) for _, h in targets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        progress()
        rows = self._jobs[jid]["progress"]
        local = next((r for r in rows if r["name"] == "Seu roteador"), None)
        remote = [r for r in rows if r["name"] != "Seu roteador"]
        bad = [r for r in remote if r["quality"] in ("bad", "down")]
        if local and local["quality"] != "good":
            verdict = ("Problema na sua rede local", "A conexão até o seu próprio roteador já está instável. "
                       "Use cabo, aproxime-se do roteador ou use 5 GHz, e pause downloads em outros aparelhos.")
        elif remote and len(bad) == len(remote):
            verdict = ("Problema na operadora", "Sua rede local está boa, mas todos os destinos na internet "
                       "estão ruins. Teste em outro horário; se continuar, abra chamado relatando perda/jitter.")
        elif bad:
            verdict = ("Problema de rota", "Só alguns destinos estão ruins — provavelmente a rota até esses "
                       "servidores. Um túnel por VPS resolveria esse tipo de caso.")
        elif any(r["quality"] == "fair" for r in remote):
            verdict = ("Pequenas oscilações", "Sem perda de pacotes, mas o ping oscilou um pouco. Normal em "
                       "horário de pico; rode com mais pacotes para confirmar.")
        else:
            verdict = ("Conexão excelente", "Rede local estável e internet sem perda nem jitter relevante.")
        self._log(f"Teste de ping: {verdict[0]}")
        return {"rows": rows, "verdict": verdict}

    def _dns_servers(self):
        servers = [{"name": n, "primary": p1, "secondary": p2, "custom": False} for n, p1, p2 in DNS_SERVERS]
        servers += [dict(s, custom=True) for s in self._config["custom_dns"]]
        return servers

    def dns_list(self):
        """Servidores na ordem do último teste, mais a opção automática (DHCP do roteador)."""
        current = (self._adapter or {}).get("Dns") or []
        results = self._config["dns_results"]
        rows = [s | {"ms": results.get(s["primary"]), "current": s["primary"] in current} for s in self._dns_servers()]
        rows.sort(key=lambda r: r["ms"] if r["ms"] is not None else 1e9)
        gw = (self._adapter or {}).get("Gateway") or ""
        known = {s["primary"] for s in self._dns_servers()}
        auto_current = bool(current) and current[0] not in known
        rows.append({"name": "Automático (roteador)", "primary": ", ".join(current) if auto_current else gw,
                     "secondary": "", "ms": results.get("auto"), "current": auto_current, "auto": True})
        return {"rows": rows, "auto_dns": self._config["settings"]["auto_dns"],
                "tested": self._config.get("dns_tested")}

    def lan_scan(self):
        if not self._adapter:
            raise RuntimeError("sem conexão de rede")

        def work(jid):
            def progress(done, total):
                self._jobs[jid]["progress"] = {"done": done, "total": total}
            result = core.scan_lan(self._adapter, progress)
            self._last_scan = result
            self._log(f"Rede {result['network']}: {len(result['devices'])} dispositivo(s) encontrados")
            return self._label_devices(result)
        return self._job(work)

    def lan_rename(self, mac, name):
        mac = str(mac).upper()
        if not MAC_RE.match(mac):
            raise ValueError("endereço MAC inválido")
        name = str(name)
        names = self._config.setdefault("device_names", {})
        if name.strip():
            names[mac] = name.strip()[:40]
        else:
            names.pop(mac, None)
        self._save()
        return self._label_devices(getattr(self, "_last_scan", {"network": "", "devices": []}))

    def _label_devices(self, result):
        names = self._config.get("device_names", {})
        return {"network": result["network"], "time": time.strftime("%H:%M:%S"),
                "devices": [d | {"label": names.get(d["mac"])} for d in result["devices"]]}

    def dns_benchmark(self):
        return self._job(self._dns_job)

    def _dns_job(self, jid):
        servers = self._dns_servers()
        current = (self._adapter or {}).get("Dns") or []
        known = {s["primary"] for s in servers}
        auto_ip = current[0] if current and current[0] not in known else (self._adapter or {}).get("Gateway")
        targets = [(s["primary"], s["primary"]) for s in servers] + ([("auto", auto_ip)] if auto_ip else [])
        results, done = {}, []

        def worker(key, ip):
            times, misses = [], 0
            for d in TEST_DOMAINS * 3:
                ms = core.dns_query_ms(ip, d)
                if ms is None:
                    misses += 1
                    if misses >= 3 and not times:
                        break  # servidor fora do ar ou bloqueado: não vale esperar as 15 consultas
                else:
                    times.append(ms)
            results[key] = round(statistics.median(times), 1) if len(times) >= 5 else None
            done.append(key)
            self._jobs[jid]["progress"] = {"done": len(done), "total": len(targets)}

        threads = [threading.Thread(target=worker, args=t, daemon=True) for t in targets]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self._config["dns_results"] = results
        self._config["dns_tested"] = time.strftime("%d/%m %H:%M")
        self._config["dns_tested_ts"] = time.time()
        self._save()
        ranked = sorted((s for s in servers if results.get(s["primary"]) is not None),
                        key=lambda s: results[s["primary"]])
        applied = None
        if ranked:
            best = ranked[0]
            self._log(f"Teste de DNS: mais rápido {best['name']} ({results[best['primary']]} ms)")
            if self._config["settings"]["auto_dns"] and self._admin and best["primary"] not in current:
                now = results.get(next((s["primary"] for s in servers if s["primary"] in current), "auto"))
                # só troca se o ganho for real: pelo menos 2 ms e 10% mais rápido que o atual
                if now is None or results[best["primary"]] < min(now - 2, now * 0.9):
                    self.dns_apply(best["primary"], best["secondary"])
                    applied = best["name"]
                    self._add_alert("dns", f"DNS trocado para {best['name']}",
                                   f"{results[best['primary']]:.0f} ms contra {now:.0f} ms do anterior" if now else
                                   f"Resposta média de {results[best['primary']]:.0f} ms", page="boost")
        return self.dns_list() | {"applied": applied}

    def dns_add_custom(self, name, primary, secondary):
        for ip in (primary, secondary):
            if ip:
                ipaddress.IPv4Address(ip)
        if not primary:
            raise ValueError("informe ao menos o DNS primário")
        self._config["custom_dns"] = [s for s in self._config["custom_dns"] if s["primary"] != primary]
        self._config["custom_dns"].append({"name": (name or primary)[:30], "primary": primary,
                                           "secondary": secondary or ""})
        self._save()
        self._log(f"DNS personalizado adicionado: {name or primary}")
        return self.dns_list()

    def dns_remove_custom(self, primary):
        self._config["custom_dns"] = [s for s in self._config["custom_dns"] if s["primary"] != primary]
        self._save()
        return self.dns_list()

    def settings_get(self):
        return {"settings": self._config["settings"], "choices": SETTING_CHOICES, "autostart": self.autostart_get(),
                "accent": core.windows_accent(),
                "admin": self._admin, "data_dir": DATA_DIR, "version": VERSION}

    def setting_set(self, key, value):
        if key in SETTING_BOOLS:
            value = bool(value)
            if key == "auto_dns" and value:
                self._need_admin()
        elif key in SETTING_CHOICES:
            value = type(SETTING_CHOICES[key][0])(value)
            if value not in SETTING_CHOICES[key]:
                raise ValueError("valor inválido")
        else:
            raise ValueError("configuração desconhecida")
        self._config["settings"][key] = value
        self._save()
        self._apply_setting(key, value)
        self._log(f"Configuração {key}: {value}")
        return value

    def _apply_setting(self, key, value):
        if key == "lang":
            i18n.load(value)
        elif key == "verbose_logs":
            logger.setLevel(logging.DEBUG if value else logging.INFO)
        elif key == "window_size" and getattr(self, "_window", None):
            w, h = map(int, value.split("x"))
            self._window.resize(w, h)

    def reset_settings(self):
        """Volta as preferências do app ao padrão (não mexe nos ajustes do Windows nem na lista de jogos)."""
        old = self._config["settings"]
        self._config["settings"] = dict(DEFAULT_CONFIG["settings"], lang=i18n.detect_lang())
        self._save()
        for key, value in self._config["settings"].items():
            if old.get(key) != value:
                self._apply_setting(key, value)
        if old.get("monitor") != self._config["settings"]["monitor"]:
            self.monitor_set(self._config["settings"]["monitor"])
        if old.get("wifi"):
            self._log("Otimizador de Wi-Fi: " + self._wifi.stop())
        self._log("Configurações do app redefinidas para o padrão")
        return self.settings_get()

    def network_reset(self):
        """Restaura a pilha de rede do Windows (Winsock, TCP/IP, DNS) — útil quando a internet fica estranha."""
        self._need_admin()

        def work(jid):
            steps = [(["netsh", "winsock", "reset"], "Winsock"), (["netsh", "int", "ip", "reset"], "TCP/IP"),
                     (["netsh", "int", "ipv6", "reset"], "IPv6"), (["ipconfig", "/flushdns"], "cache DNS")]
            done = []
            for cmd, name in steps:
                self._jobs[jid]["progress"] = f"Redefinindo {name}…"
                code, out = core.run(cmd, timeout=120)
                done.append(name if code == 0 else f"{name} (falhou)")
                logger.debug(f"{' '.join(cmd)} -> {code}: {out.strip()[:300]}")
            self._log("Configurações de rede redefinidas: " + ", ".join(done))
            return "Rede redefinida. Reinicie o PC para concluir."
        return self._job(work)

    # ---- central de notificações (o sino no topo)

    def _add_alert(self, kind, title, message, page=None, os_notify=False):
        """Guarda um alerta na central (se o tipo estiver ligado) e, opcionalmente, mostra a notificação do Windows."""
        if not self._config["settings"].get(ALERT_SETTINGS[kind]):
            return
        alerts = self._config.setdefault("alerts", [])
        alerts.insert(0, {"id": uuid.uuid4().hex[:8], "kind": kind, "title": title, "message": message,
                          "page": page, "time": time.time(), "read": False})
        del alerts[60:]
        self._save()
        if os_notify:
            self._notify(title, message)

    def alerts_list(self):
        return self._config.get("alerts", [])

    def alerts_read(self, ids=None):
        ids = None if ids is None else {str(i) for i in list(ids)[:100]}
        for a in self._config.get("alerts", []):
            if ids is None or a["id"] in ids:
                a["read"] = True
        self._save()
        return self.alerts_list()

    def alerts_clear(self):
        self._config["alerts"] = []
        self._save()
        return []

    def _startup_checks(self):
        """Ao abrir: confere os projetos de origem e, uma vez por dia, os drivers — e avisa no sino."""
        if self._stop.wait(15):
            return
        if self._config["settings"]["notify_upstream"]:
            try:
                seen = self._config.setdefault("alerted_upstream", {})
                for r in upstream.check():
                    sha = upstream._load().get(r["name"], {}).get("latest")
                    if r["status"].startswith("mudou") and r["files"] and seen.get(r["name"]) != sha:
                        seen[r["name"]] = sha
                        detail = ", ".join(r["tweaks"]) or ", ".join(r["files"])
                        self._add_alert("upstream", f"{r['title']} mudou no GitHub", f"Revise e porte o que valer a pena: {detail}",
                                       page="about")
                self._save()
            except Exception:
                logger.exception("Falha ao verificar os projetos de origem")
        if self._config["settings"]["notify_drivers"] and                 time.time() - self._config.get("drivers_checked_ts", 0) > DRIVER_CHECK_INTERVAL:
            try:
                inst = drivers.installed()
                updates = drivers.match(inst, drivers.available())
                self._drivers = {"installed": inst, "updates": updates, "time": time.strftime("%d/%m %H:%M")}
                self._config["drivers_checked_ts"] = time.time()
                key = ",".join(sorted(u["Id"] for u in updates))
                if updates and key != self._config.get("alerted_drivers"):
                    self._config["alerted_drivers"] = key
                    names = ", ".join(u["Device"] for u in updates[:3]) + ("…" if len(updates) > 3 else "")
                    self._add_alert("drivers", f"{len(updates)} driver(s) podem ser atualizados", names, page="drivers")
                self._save()
            except Exception:
                logger.exception("Falha ao verificar os drivers")

    def _notify(self, title, message):
        tray = getattr(self, "_tray", None)
        return tray.notify(i18n.tr(title), i18n.tr(message)) if tray else False

    def _check_alerts(self):
        """Avisa (notificação do Windows) quando o servidor do jogo para de responder ou fica instável."""
        if not self._config["settings"]["notify_unstable"]:
            return
        now = time.time()
        for pid in self._running_games:
            st = self._conn.get(pid)
            last = [ms for t, ms in list(st["samples"])[-10:]] if st else []
            if len(last) < 10 or now - st.get("alerted", 0) < ALERT_COOLDOWN:
                continue
            lost = sum(ms is None for ms in last)
            stats = core.ping_stats(last)
            name = self._profile(pid)["name"]
            if lost >= 6:
                msg = (f"Servidor de {name} sem resposta", f"{lost} de 10 medições falharam nos últimos 30 s.")
            elif lost >= 2 or (stats["jitter"] or 0) > 30:
                msg = (f"Conexão instável em {name}",
                       f"Perda de {stats['loss']:.0f}% e oscilação de {stats['jitter'] or 0:.0f} ms nos últimos 30 s.")
            else:
                continue
            st["alerted"] = now
            self._log(f"Alerta: {msg[0]} — {msg[1]}")
            self._add_alert("unstable", *msg, page="connections", os_notify=True)

    def dns_apply(self, primary, secondary):
        self._need_admin()
        primary = valid_ipv4(primary)
        secondary = valid_ipv4(secondary) if secondary else ""
        idx = self._adapter["Index"]
        servers = ",".join(core.ps_quote(s) for s in (primary, secondary) if s)
        code, out = core.ps(f"Set-DnsClientServerAddress -InterfaceIndex {int(idx)} -ServerAddresses {servers};"
                            " Clear-DnsClientCache")
        if code != 0:
            raise RuntimeError(out.strip())
        self._log(f"DNS alterado para {primary} {secondary}")
        return self._refresh_adapter()

    def dns_reset(self):
        self._need_admin()
        idx = self._adapter["Index"]
        code, out = core.ps(f"Set-DnsClientServerAddress -InterfaceIndex {int(idx)} -ResetServerAddresses;"
                            " Clear-DnsClientCache")
        if code != 0:
            raise RuntimeError(out.strip())
        self._log("DNS voltou para automático")
        return self._refresh_adapter()

    # ---- ferramentas

    def _tool(self, name):
        if name == "flush_dns":
            code, out = core.run(["ipconfig", "/flushdns"])
            msg = "Cache DNS limpo"
        elif name == "renew_ip":
            self._need_admin()
            core.run(["ipconfig", "/release"], timeout=60)
            code, out = core.run(["ipconfig", "/renew"], timeout=90)
            self._refresh_adapter()
            msg = "Endereço IP renovado"
        elif name == "temp":
            code, out = core.ps("$n=0; foreach ($d in @($Env:Temp, \"$Env:SystemRoot\\Temp\")) {"
                                " Get-ChildItem $d -Force -EA SilentlyContinue | ForEach-Object {"
                                " try { Remove-Item $_.FullName -Recurse -Force -EA Stop; $n++ } catch {} } }; $n",
                                timeout=180)
            msg = f"Arquivos temporários removidos ({out.strip().splitlines()[-1] if out.strip() else 0} itens)"
        elif name == "ram":
            self._need_admin()
            before = core.standby_mb()
            core.purge_standby_list()
            after = core.standby_mb()
            code, out = 0, ""
            msg = ("Memória em espera liberada" +
                   (f": {before - after} MB" if before is not None and after is not None else ""))
        elif name == "restore_point":
            self._need_admin()
            code, out = core.ps("Enable-ComputerRestore -Drive $Env:SystemDrive -EA SilentlyContinue;"
                                " Checkpoint-Computer -Description 'PingPilot' -RestorePointType MODIFY_SETTINGS",
                                timeout=300)
            msg = "Ponto de restauração criado" if code == 0 else "Windows recusou: só é permitido 1 ponto a cada 24 h"
            code = 0
        else:
            raise ValueError("ferramenta desconhecida")
        if code != 0:
            raise RuntimeError(out.strip() or "falhou")
        self._log(msg)
        return msg

    def tool_job(self, name):
        if name not in ("flush_dns", "renew_ip", "temp", "restore_point", "ram"):
            raise ValueError("ferramenta desconhecida")
        return self._job(lambda jid: self._tool(name))

    # ---- drivers

    def drivers_cached(self):
        return self._drivers

    def drivers_scan(self):
        def work(jid):
            self._jobs[jid]["progress"] = "Lendo os drivers instalados…"
            inst = drivers.installed()
            self._jobs[jid]["progress"] = "Procurando atualizações no Windows Update…"
            updates = drivers.match(inst, drivers.available())
            self._drivers = {"installed": inst, "updates": updates, "time": time.strftime("%d/%m %H:%M")}
            self._log(f"Drivers: {len(updates)} atualização(ões) disponível(is) de {len(inst)} instalados")
            return self._drivers
        return self._job(work)

    def drivers_install(self, ids, restore_point=True):
        self._need_admin()

        def work(jid):
            if restore_point:
                self._jobs[jid]["progress"] = "Criando ponto de restauração…"
                try:
                    self._log(self._tool("restore_point"))
                except Exception as e:
                    self._log(f"Ponto de restauração não criado: {e}")
            self._jobs[jid]["progress"] = "Baixando e instalando pelo Windows Update…"
            results = drivers.install(ids, self._log)
            done = {r["title"] for r in results if r["ok"]}
            if self._drivers:
                self._drivers["updates"] = [u for u in self._drivers["updates"] if u["Title"] not in done]
            return results
        return self._job(work)

    def open_url(self, url):
        allowed = {v[1] for v in drivers.VENDOR_PAGES.values()}
        repos = tuple(f"https://github.com/{s['repo']}" for s in upstream.SOURCES.values())
        if url not in allowed and not url.startswith(repos):
            raise ValueError("endereço não permitido")
        os.startfile(url)
        return True

    def upstream_check(self):
        return self._job(lambda jid: upstream.check())

    def upstream_mark_reviewed(self, name):
        if name not in upstream.SOURCES:
            raise ValueError("projeto desconhecido")
        return upstream.mark_reviewed(name)

    # ---- PC Boost

    def tweak_list(self):
        return {"items": self._engine.listing(self._admin),
                "excluded": [{"title": t, "source": s, "why": w} for t, s, w in tweaks.EXCLUDED]}

    def tweak_set(self, tid, on):
        t = next((x for x in tweaks.CATALOG if x["id"] == tid), None)
        if not t:
            raise ValueError("ajuste desconhecido")
        if t.get("admin"):
            self._need_admin()
        return self._engine.set(tid, bool(on))

    def tweak_preset(self, name):
        def work(jid):
            changed = 0
            for t in tweaks.CATALOG:
                if t.get("admin") and not self._admin:
                    continue
                want = name == "performance" and bool(t.get("recommended"))
                try:
                    if self._engine.state(t) != want:
                        self._engine.set(t["id"], want)
                        changed += 1
                except Exception as e:
                    self._log(f"Falha em {t['title']}: {e}")
            return changed
        return self._job(work)

    def restore_all(self):
        self._need_admin()
        return self._job(lambda jid: self._engine.restore_all())

    # ---- Wi-Fi

    def wifi_set(self, on):
        self._config["settings"]["wifi"] = bool(on)
        self._save()
        result = self._wifi.start() if on else self._wifi.stop()
        self._log("Otimizador de Wi-Fi: " + result)
        return result

    # ---- configurações

    def autostart_get(self):
        code, _ = core.run(["schtasks", "/query", "/tn", TASK_NAME])
        return code == 0

    def autostart_set(self, on):
        self._need_admin()
        if on:
            exe, args = launch_command("--minimized")
            code, out = core.ps(
                f"$a = New-ScheduledTaskAction -Execute {core.ps_quote(exe)} -Argument {core.ps_quote(args)}"
                f" -WorkingDirectory {core.ps_quote(os.path.dirname(exe) if FROZEN else APP_DIR)};"
                "$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME;"
                "$p = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest -LogonType Interactive;"
                "$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0;"
                f"Register-ScheduledTask -TaskName '{TASK_NAME}' -Action $a -Trigger $t -Principal $p -Settings $s -Force | Out-Null")
        else:
            code, out = core.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"])
        if code != 0:
            raise RuntimeError(out.strip())
        self._log("Iniciar com o Windows: " + ("ligado" if on else "desligado"))
        return self.autostart_get()

    def relaunch_admin(self):
        if relaunch_elevated():
            threading.Timer(0.5, lambda: os._exit(0)).start()
            return True
        return False

    def _need_admin(self):
        if not self._admin:
            raise PermissionError("Precisa de administrador — use o botão 'Reabrir como administrador'.")


def launch_command(extra=""):
    """Executável e argumentos para abrir o PingPilot de novo (no .exe ou pelo Python)."""
    if FROZEN:
        return sys.executable, extra.strip()
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    exe = pyw if os.path.exists(pyw) else sys.executable
    return exe, f'"{os.path.join(APP_DIR, "app.py")}" {extra}'.strip()


def relaunch_elevated(extra=""):
    exe, args = launch_command(f"--no-elevate {extra}")
    return ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, args, os.path.dirname(exe), 1) > 32


# ---------------------------------------------------------------- servidor HTTP (modo navegador)

def make_handler(api, port):
    """Servidor do modo navegador (só para desenvolvimento). Protegido contra sites abertos no mesmo
    navegador: só aceita Host local (barra DNS rebinding) e a API exige um token por execução, que só
    a página servida aqui conhece (um site de fora não consegue ler esta página nem mandar o cabeçalho)."""
    public = {n for n in dir(api) if not n.startswith("_") and callable(getattr(api, n))}
    types = {".html": "text/html", ".css": "text/css", ".js": "application/javascript", ".svg": "image/svg+xml",
             ".png": "image/png"}
    token = secrets.token_urlsafe(24)
    hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
    ui_root = os.path.normcase(os.path.abspath(UI_DIR))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _host_ok(self):
            return self.headers.get("Host", "") in hosts

        def do_GET(self):
            if not self._host_ok():
                return self._send(403, {"error": "host não permitido"})
            name = self.path.split("?")[0].lstrip("/") or "index.html"
            path = os.path.normcase(os.path.abspath(os.path.join(UI_DIR, name)))
            if os.path.commonpath([path, ui_root]) != ui_root or not os.path.isfile(path):
                return self._send(404, {"error": "não encontrado"})
            with open(path, "rb") as f:
                data = f.read()
            if name == "index.html":  # avisa a interface que a API é por HTTP e entrega o token desta execução
                data = data.replace(b'<html lang="pt-BR">', f'<html lang="pt-BR" data-pp-http="{token}">'.encode(), 1)
            self._send(200, data, types.get(os.path.splitext(path)[1], "application/octet-stream"))

        def do_POST(self):
            if not self._host_ok() or not secrets.compare_digest(self.headers.get("X-PP-Token", ""), token):
                return self._send(403, {"error": "acesso negado"})
            method = self.path.strip("/").removeprefix("api/")
            if method not in public:
                return self._send(404, {"error": "método desconhecido"})
            length = int(self.headers.get("Content-Length") or 0)
            args = json.loads(self.rfile.read(length) or b"[]") if length else []
            try:
                self._send(200, {"result": getattr(api, method)(*args)})
            except Exception as e:
                logger.exception(f"Erro em {method}")
                self._send(200, {"error": str(e)})

    return Handler


def clear_stale_ui_cache():
    """O WebView2 guarda HTML/JS/CSS em cache na pasta de dados. Quando o PingPilot muda de versão,
    apaga esse cache — senão o .exe novo abre com a interface da versão anterior."""
    webview_dir = os.path.join(DATA_DIR, ".webview")
    marker = os.path.join(webview_dir, "ui_version.txt")
    try:
        with open(marker, encoding="utf-8") as f:
            if f.read().strip() == VERSION:
                return
    except OSError:
        pass
    profile = os.path.join(webview_dir, "EBWebView", "Default")
    for sub in ("Cache", "Code Cache", "GPUCache", os.path.join("Service Worker", "CacheStorage")):
        shutil.rmtree(os.path.join(profile, sub), ignore_errors=True)
    os.makedirs(webview_dir, exist_ok=True)
    with open(marker, "w", encoding="utf-8") as f:
        f.write(VERSION)
    logger.info(f"Cache da interface limpo para a versão {VERSION}")


def main():
    argv = sys.argv[1:]
    setup_logging()
    if "--browser" not in argv and "--no-elevate" not in argv and not core.is_admin():
        if relaunch_elevated(" ".join(argv)):
            return
    api = Api()
    if "--browser" in argv:
        port = 8765
        print(f"PingPilot em http://127.0.0.1:{port}")
        ThreadingHTTPServer(("127.0.0.1", port), make_handler(api, port)).serve_forever()
        return

    import webview

    from tray import Tray

    settings = api._config["settings"]
    width, height = map(int, settings["window_size"].split("x"))
    # iniciado com o Windows: vai direto para a bandeja (ou minimizado, se a bandeja estiver desligada)
    background = "--minimized" in argv
    window = webview.create_window("PingPilot", os.path.join(UI_DIR, "index.html"), js_api=api,
                                   width=width, height=height, min_size=(1080, 680), background_color="#0e1014",
                                   hidden=background and settings["tray"],
                                   minimized=background and not settings["tray"])
    api._window = window
    quitting = threading.Event()

    def show():
        window.show()
        window.restore()

    def quit_app():
        quitting.set()
        tray.stop()
        window.destroy()

    def on_closing():
        if quitting.is_set() or not api._config["settings"]["tray"]:
            return True
        window.hide()
        if not getattr(api, "_tray_hint", False):
            api._tray_hint = True
            api._notify("O PingPilot continua rodando", "Ele está na bandeja, perto do relógio. "
                                                       "Clique no ícone para abrir ou use Sair no menu para fechar.")
        return False  # cancela o fechamento: só esconde

    clear_stale_ui_cache()
    tray = Tray(os.path.join(UI_DIR, "icon.png"), show, quit_app, labels=(i18n.tr("Abrir PingPilot"), i18n.tr("Sair")))
    api._tray = tray
    window.events.closing += on_closing
    webview.start(private_mode=False, storage_path=os.path.join(DATA_DIR, ".webview"))
    tray.stop()
    api._stop.set()
    os._exit(0)  # encerra também as threads de ping e monitoramento


if __name__ == "__main__":
    main()
