"""Multi Internet: usa duas conexões (ex.: cabo + Wi-Fi, ou cabo + celular roteado) com prioridade e failover.

O Windows escolhe a saída pela "métrica" de cada adaptador (menor = preferido). Ele já troca sozinho quando o
cabo é desconectado, mas NÃO percebe quando o link continua de pé e a internet daquele provedor cai — o caso
mais comum. Aqui cada conexão é testada de verdade (TCP saindo por ela) e, se a principal parar de responder,
a reserva assume trocando as métricas; quando a principal volta e fica estável, ela retoma.

Não soma a velocidade das duas nem duplica pacotes: isso exige um servidor intermediário (Speedify, OpenMPTCProuter,
engarde). As métricas originais são guardadas e devolvidas ao desligar.
"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor

import core

TARGETS = [("1.1.1.1", 443), ("8.8.8.8", 443), ("9.9.9.9", 443)]
VPN_RE = r"TAP|Wintun|WireGuard|OpenVPN|VPN|Tunnel|Proton|Nord|Surfshark|ExpressVPN|Cloudflare WARP|Hyper-V|VirtualBox|VMware"
FAIL_CHECKS = 3     # falhas seguidas (a cada 5 s) para trocar para a reserva
RECOVER_CHECKS = 6  # sucessos seguidos (30 s) para a principal voltar


def adapters():
    """Adaptadores ligados que têm gateway (saída para a internet), sem VPNs e máquinas virtuais."""
    rows = core.ps_json(
        "Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up' -and "
        f"$_.InterfaceDescription -notmatch '{VPN_RE}' }} | ForEach-Object {{ "
        "$i = Get-NetIPInterface -InterfaceIndex $_.InterfaceIndex -AddressFamily IPv4; "
        "[pscustomobject]@{ index = [int]$_.InterfaceIndex; alias = $_.InterfaceAlias; desc = $_.InterfaceDescription; "
        "ip = @($_.IPv4Address)[0].IPAddress; gateway = @($_.IPv4DefaultGateway)[0].NextHop; "
        "metric = [int]$i.InterfaceMetric; auto = [string]$i.AutomaticMetric; "
        "media = [string]$_.NetAdapter.PhysicalMediaType; speed = [string]$_.NetAdapter.LinkSpeed } }")
    out = []
    for r in rows:
        desc = (r.get("desc") or "").lower()
        media = (r.get("media") or "").lower()
        kind = ("mobile" if any(w in desc for w in ("rndis", "remote ndis", "mobile", "wwan", "broadband", "android", "iphone"))
                else "wifi" if "802.11" in media or "wi-fi" in desc or "wireless" in desc
                else "ethernet")
        out.append({"index": int(r["index"]), "alias": r.get("alias") or "?", "desc": r.get("desc") or "",
                    "ip": r.get("ip"), "gateway": r.get("gateway"), "metric": r.get("metric"),
                    "auto": r.get("auto") == "Enabled", "kind": kind, "speed": r.get("speed")})
    return sorted(out, key=lambda a: a["metric"] or 0)


def _connect_ms(src_ip, target, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.bind((src_ip, 0))  # o Windows envia pelo adaptador dono deste IP (modelo de host forte)
        t = time.perf_counter()
        s.connect(target)
        return (time.perf_counter() - t) * 1000
    except OSError:
        return None
    finally:
        s.close()


def probe(src_ip, timeout=1.5):
    """Ping (TCP) saindo por este adaptador até 3 servidores públicos. ok = pelo menos um respondeu."""
    if not src_ip:
        return {"ok": False, "ping": None, "loss": 100}
    with ThreadPoolExecutor(len(TARGETS)) as pool:
        times = list(pool.map(lambda t: _connect_ms(src_ip, t, timeout), TARGETS))
    good = [x for x in times if x is not None]
    return {"ok": bool(good), "ping": round(min(good)) if good else None,
            "loss": round(100 * (len(times) - len(good)) / len(times))}


def probe_all(items):
    if not items:
        return {}
    with ThreadPoolExecutor(len(items)) as pool:
        return dict(zip([a["index"] for a in items], pool.map(lambda a: probe(a["ip"]), items)))


def set_order(indexes):
    """Primeiro da lista = preferido. Métricas 10, 20, 30… (definir a métrica desliga a automática)."""
    cmds = [f"Set-NetIPInterface -InterfaceIndex {int(ix)} -AddressFamily IPv4 -InterfaceMetric {10 + 10 * n}"
            for n, ix in enumerate(indexes)]
    code, out = core.ps("; ".join(cmds))
    if code != 0:
        raise RuntimeError(out.strip() or "o Windows recusou mudar a prioridade")


def restore(backup):
    """Devolve as métricas guardadas antes do PingPilot mexer (adaptadores que sumiram são ignorados)."""
    cmds = []
    for ix, b in backup.items():
        ix = int(ix)
        if b.get("auto"):
            cmds.append(f"Set-NetIPInterface -InterfaceIndex {ix} -AddressFamily IPv4 -AutomaticMetric Enabled -EA SilentlyContinue")
        elif b.get("metric") is not None:
            cmds.append(f"Set-NetIPInterface -InterfaceIndex {ix} -AddressFamily IPv4 -InterfaceMetric {int(b['metric'])} -EA SilentlyContinue")
    if cmds:
        core.ps("; ".join(cmds))


def offline():
    """Placas de rede físicas que existem mas não estão com internet agora (para sugerir conectar)."""
    rows = core.ps_json("Get-NetAdapter -Physical | Where-Object { $_.Status -ne 'Up' -or -not "
                        "(Get-NetIPConfiguration -InterfaceIndex $_.ifIndex -EA SilentlyContinue).IPv4DefaultGateway } | "
                        "Select-Object Name, InterfaceDescription, Status")
    return [{"alias": r.get("Name"), "desc": r.get("InterfaceDescription"), "status": str(r.get("Status"))} for r in rows]
