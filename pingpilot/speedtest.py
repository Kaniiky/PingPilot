"""Teste de velocidade da internet, com dois tipos de servidor:

- M-Lab (Measurement Lab), protocolo NDT7 — o mesmo do teste de velocidade do Google. Servidores no Brasil,
  escolhidos pelo localizador do M-Lab. Uma conexão WebSocket por fase, como manda o protocolo.
  O M-Lab publica os resultados (incluindo o IP) como dados abertos de pesquisa — a interface avisa.
- LibreSpeed (código aberto): lista pública de servidores ou um servidor próprio (ex.: da operadora).

Mede download e upload com várias conexões em paralelo, o ping/jitter em repouso e o ping DURANTE o
download/upload (bufferbloat) — o atraso que aparece no jogo quando alguém da casa está baixando algo.

O ping em uso é medido até 1.1.1.1 (Cloudflare, sempre perto), não até o servidor do teste: assim ele mostra
a fila da SUA conexão, e não a distância até o servidor.
"""
import http.client
import json
import os
import ssl
import statistics
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import websocket

import core

SERVER_LIST = "https://librespeed.org/backend-servers/servers.php"
LATENCY_HOST = ("1.1.1.1", 443)
STREAMS = 6
DOWN_SECONDS, UP_SECONDS, WARMUP = 10, 8, 1.5
MAX_BYTES = 2_000_000_000  # trava de segurança por fase (conexões muito rápidas)
UA = {"User-Agent": "PingPilot-speedtest (+https://github.com/Kaniiky/PingPilot)"}
MLAB_LOCATE = "https://locate.measurementlab.net/v2/nearest/ndt/ndt7"
NDT7_PROTOCOL = "net.measurementlab.ndt.v7"


def _https(url):
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or not p.hostname:
        raise ValueError("o servidor precisa ser https://")
    return p


def servers():
    """Lista pública de servidores LibreSpeed (só os https)."""
    req = urllib.request.Request(SERVER_LIST, headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:  # nosec B310 - URL fixa https
        data = json.loads(r.read())
    out = []
    for s in data:
        try:
            _https(s["server"])
        except (KeyError, ValueError):
            continue
        out.append({"id": int(s["id"]), "name": str(s["name"])[:80], "server": s["server"].rstrip("/") + "/",
                    "dl": s.get("dlURL", "garbage.php"), "ul": s.get("ulURL", "empty.php"),
                    "sponsor": str(s.get("sponsorName", ""))[:60]})
    return out


def custom_server(url):
    """Servidor LibreSpeed próprio (ex.: da sua operadora)."""
    p = _https(url.strip())
    base = f"https://{p.netloc}{p.path.rstrip('/')}/"
    return {"id": 0, "name": p.hostname, "server": base, "dl": "garbage.php", "ul": "empty.php", "sponsor": ""}


def mlab_locate(version):
    """Servidores M-Lab mais próximos (do mais perto ao mais longe), já com os endereços de uso único de
    download e upload. Vários, porque um servidor lotado recusa o teste (503) e aí tentamos o seguinte."""
    q = urllib.parse.urlencode({"client_name": "pingpilot", "client_version": version})
    req = urllib.request.Request(f"{MLAB_LOCATE}?{q}", headers=UA)
    with urllib.request.urlopen(req, timeout=15) as r:  # nosec B310 - URL fixa https
        results = json.loads(r.read()).get("results") or []
    out = []
    for res in results:
        urls = res.get("urls") or {}
        down, up = urls.get("wss:///ndt/v7/download"), urls.get("wss:///ndt/v7/upload")
        if not (down and up and down.startswith("wss://") and up.startswith("wss://")):
            continue
        host = urllib.parse.urlparse(down).hostname
        loc = res.get("location") or {}
        place = ", ".join(x for x in (loc.get("city"), loc.get("country")) if x)
        out.append({"id": "mlab", "kind": "ndt7", "name": f"M-Lab · {place}"[:80] if place else "M-Lab",
                    "server": f"https://{host}/", "down": down, "up": up, "sponsor": "Measurement Lab"})
    if not out:
        raise RuntimeError("o M-Lab não indicou nenhum servidor agora — tente outro servidor")
    return out


def server_ping(s):
    host = urllib.parse.urlparse(s["server"]).hostname
    vals = [v for v in (core.tcp_ping(host, 443, timeout=2) for _ in range(3)) if v is not None]
    return min(vals) if vals else None


def pick_server(candidates):
    """O de menor ping entre os candidatos (medido em paralelo)."""
    with ThreadPoolExecutor(12) as pool:
        pings = list(pool.map(server_ping, candidates))
    ranked = sorted((p, i) for i, p in enumerate(pings) if p is not None)
    if not ranked:
        raise RuntimeError("nenhum servidor de teste respondeu")
    p, i = ranked[0]
    return dict(candidates[i], ping=round(p))


def bloat_grade(increase_ms):
    """Nota de bufferbloat pelo aumento do ping com a conexão ocupada (mesma escala do teste da Waveform)."""
    if increase_ms is None:
        return "—"
    for limit, grade in ((5, "A+"), (30, "A"), (60, "B"), (200, "C"), (400, "D")):
        if increase_ms < limit:
            return grade
    return "F"


class _Meter:
    """Conta bytes de várias threads e calcula a velocidade atual (janela de 1 s) e a média sem o aquecimento."""

    def __init__(self):
        self.lock = threading.Lock()
        self.total = 0
        self.samples = [(time.perf_counter(), 0)]
        self.start = time.perf_counter()

    def add(self, n):
        with self.lock:
            self.total += n

    def sample(self):
        now = time.perf_counter()
        with self.lock:
            self.samples.append((now, self.total))
        old = next((s for s in self.samples if now - s[0] <= 1.0), self.samples[0])
        dt = now - old[0]
        return (self.total - old[1]) * 8 / dt / 1e6 if dt > 0 else 0.0

    def average(self):
        # o aquecimento conta a partir do primeiro byte (abrir as conexões TLS pode levar uns segundos)
        first = next((s[0] for s in self.samples if s[1] > 0), None)
        if first is None:
            return None
        base = next((s for s in self.samples if s[0] - first >= WARMUP), self.samples[-1])
        end = self.samples[-1]
        dt = end[0] - base[0]
        return (end[1] - base[1]) * 8 / dt / 1e6 if dt > 0.5 else None


def _connection(server):
    p = urllib.parse.urlparse(server["server"])
    return http.client.HTTPSConnection(p.hostname, p.port or 443, timeout=15, context=ssl.create_default_context()), p.path


def _download_worker(server, meter, deadline, errors):
    try:
        conn, path = _connection(server)
        while time.perf_counter() < deadline and meter.total < MAX_BYTES:
            conn.request("GET", f"{path}{server['dl']}?ckSize=100&r={time.time_ns()}", headers=UA)
            resp = conn.getresponse()
            if resp.status != 200:
                raise RuntimeError(f"servidor respondeu {resp.status}")
            while time.perf_counter() < deadline:
                chunk = resp.read(65536)
                if not chunk:
                    break
                meter.add(len(chunk))
            else:
                break
        conn.close()
    except Exception as e:  # uma conexão que cai não derruba o teste
        errors.append(str(e))


_UPLOAD_BLOCK = os.urandom(1 << 20)  # dados aleatórios (não comprimíveis), reaproveitados


def _upload_worker(server, meter, deadline, errors):
    try:
        conn, path = _connection(server)
        size = 25 << 20
        while time.perf_counter() < deadline and meter.total < MAX_BYTES:
            conn.putrequest("POST", f"{path}{server['ul']}?r={time.time_ns()}")
            conn.putheader("User-Agent", UA["User-Agent"])
            conn.putheader("Content-Type", "application/octet-stream")
            conn.putheader("Content-Length", str(size))
            conn.endheaders()
            sent = 0
            while sent < size and time.perf_counter() < deadline:
                block = _UPLOAD_BLOCK[: min(len(_UPLOAD_BLOCK), size - sent)]
                conn.send(block)
                sent += len(block)
                meter.add(len(block))
            if sent < size:
                break
            conn.getresponse().read()
        conn.close()
    except Exception as e:
        errors.append(str(e))


def _ndt7_connect(url):
    return websocket.create_connection(url, subprotocols=[NDT7_PROTOCOL], timeout=15, header=[
        f"User-Agent: {UA['User-Agent']}"], sslopt={"context": ssl.create_default_context()})


def _ndt7_download(server, meter, deadline, errors):
    """O servidor manda mensagens binárias por ~10 s; as de texto são medições dele (ignoradas)."""
    try:
        ws = _ndt7_connect(server["down"])
        try:
            while time.perf_counter() < deadline:
                op, data = ws.recv_data()
                if op == websocket.ABNF.OPCODE_BINARY:
                    meter.add(len(data))
                elif op == websocket.ABNF.OPCODE_CLOSE:
                    break
        except websocket.WebSocketConnectionClosedException:
            pass  # o servidor encerra a fase sozinho
        finally:
            ws.close()
    except Exception as e:
        errors.append(str(e))


def _ndt7_upload(server, meter, deadline, errors):
    """Manda mensagens binárias crescendo de 8 KB até 16 MB, como recomenda a especificação do NDT7."""
    try:
        ws = _ndt7_connect(server["up"])
        size = 1 << 13
        try:
            while time.perf_counter() < deadline and meter.total < MAX_BYTES:
                block = (_UPLOAD_BLOCK * (1 + size // len(_UPLOAD_BLOCK)))[:size]
                ws.send_binary(block)
                meter.add(size)
                if size < (1 << 24) and size < meter.total / 16:
                    size *= 2
        except websocket.WebSocketConnectionClosedException:
            pass
        finally:
            ws.close()
    except Exception as e:
        errors.append(str(e))


def _latency_series(n, gap):
    out = []
    for _ in range(n):
        out.append(core.tcp_ping(*LATENCY_HOST, timeout=1.5))
        time.sleep(gap)
    return out


def _phase(name, worker, seconds, server, progress, streams=STREAMS):
    meter, errors, loaded = _Meter(), [], []
    deadline = time.perf_counter() + seconds
    threads = [threading.Thread(target=worker, args=(server, meter, deadline, errors), daemon=True) for _ in range(streams)]
    for t in threads:
        t.start()
    next_ping = time.perf_counter() + 1.0
    while any(t.is_alive() for t in threads):
        time.sleep(0.25)
        now = time.perf_counter()
        if now >= next_ping and now < deadline:  # ping com a conexão ocupada
            loaded.append(core.tcp_ping(*LATENCY_HOST, timeout=1.5))
            next_ping = now + 0.5
        progress({"phase": name, "mbps": round(meter.sample(), 1),
                  "elapsed": round(min(seconds, seconds - (deadline - now)), 1), "seconds": seconds})
    meter.sample()
    avg = meter.average()
    if avg is None and errors:
        raise RuntimeError(f"falha no {name}: {errors[0]}")
    ok = [v for v in loaded if v is not None]
    return {"mbps": round(avg, 1) if avg else None, "bytes": meter.total,
            "loaded_ping": round(statistics.median(ok)) if ok else None}


def run(server, progress=lambda p: None, fallbacks=()):
    """fallbacks: outros servidores M-Lab para tentar, em ordem, se o download for recusado logo de cara."""
    progress({"phase": "ping", "mbps": 0, "elapsed": 0, "seconds": 3})
    idle = [v for v in _latency_series(12, 0.15) if v is not None]
    if not idle:
        raise RuntimeError("sem resposta de ping — confira a conexão")
    idle_ping = statistics.median(idle)
    jitter = statistics.mean(abs(a - b) for a, b in zip(idle, idle[1:])) if len(idle) > 1 else 0.0
    if server.get("kind") == "ndt7":  # protocolo NDT7: uma conexão por fase
        candidates = [server, *fallbacks]
        for n, candidate in enumerate(candidates):
            try:
                down = _phase("download", _ndt7_download, DOWN_SECONDS, candidate, progress, streams=1)
                server = candidate
                break
            except RuntimeError:
                if n == len(candidates) - 1:
                    raise
                progress({"phase": "server", "mbps": 0, "elapsed": 0, "seconds": 1})
        up = _phase("upload", _ndt7_upload, UP_SECONDS, server, progress, streams=1)
    else:
        down = _phase("download", _download_worker, DOWN_SECONDS, server, progress)
        up = _phase("upload", _upload_worker, UP_SECONDS, server, progress)
    worst = max([v for v in (down["loaded_ping"], up["loaded_ping"]) if v is not None], default=None)
    increase = None if worst is None else max(0, worst - idle_ping)
    return {
        "time": time.time(), "server": server["name"], "server_ping": server.get("ping"),
        "download": down["mbps"], "upload": up["mbps"], "ping": round(idle_ping), "jitter": round(jitter, 1),
        "ping_down": down["loaded_ping"], "ping_up": up["loaded_ping"],
        "bloat": None if increase is None else round(increase), "grade": bloat_grade(increase),
        "data_mb": round((down["bytes"] + up["bytes"]) / 1e6),
    }
