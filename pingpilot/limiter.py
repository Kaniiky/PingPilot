"""Limitador de tráfego: teto de UPLOAD por programa, com as políticas de QoS do próprio Windows.

Upload saturado (backup na nuvem, torrent, OneDrive) é a causa nº 1 de ping alto em casa — o roteador enfileira
os pacotes do jogo atrás dos do upload (bufferbloat). O Windows só consegue limitar o que SAI do PC; o download
de outros programas não tem como ser limitado sem um driver de rede (é o que o ExitLag faz).

As políticas têm o prefixo "PPLimit-", separado das de prioridade DSCP ("PingPilot-") do PC Boost.
"""
import core

PREFIX = "PPLimit-"
# programas que costumam encher o upload; aparecem como sugestão
SUGGESTIONS = ["OneDrive.exe", "GoogleDriveFS.exe", "Dropbox.exe", "qbittorrent.exe", "uTorrent.exe", "BitTorrent.exe",
               "steam.exe", "EpicGamesLauncher.exe", "Battle.net.exe", "MEGAsync.exe", "iCloudDrive.exe", "obs64.exe"]


def _exe(name):
    base = core.clean_exe_name(name)
    if not base:
        raise ValueError("nome de programa inválido")
    return base + ".exe"


def list_limits():
    rows = core.ps_json(f"Get-NetQosPolicy -EA SilentlyContinue | Where-Object Name -like '{PREFIX}*' | "
                        "Select-Object Name, AppPathName, ThrottleRateAction")
    out = []
    for r in rows:
        rate = r.get("ThrottleRateAction") or 0
        out.append({"exe": r.get("AppPathName") or r["Name"][len(PREFIX):], "mbps": round(int(rate) / 1e6, 2)})
    return sorted(out, key=lambda x: x["exe"].lower())


def set_limit(name, mbps):
    exe = _exe(name)
    mbps = float(mbps)
    if not 0.1 <= mbps <= 1000:
        raise ValueError("o limite precisa ficar entre 0,1 e 1000 Mbps")
    q = core.ps_quote(PREFIX + exe)
    code, out = core.ps(f"Remove-NetQosPolicy -Name {q} -Confirm:$false -EA SilentlyContinue; "
                        f"New-NetQosPolicy -Name {q} -AppPathNameMatchCondition {core.ps_quote(exe)} "
                        f"-ThrottleRateActionBitsPerSecond {int(mbps * 1e6)} -NetworkProfile All | Out-Null")
    if code != 0:
        raise RuntimeError(out.strip() or "o Windows recusou criar o limite")
    return exe


def remove_limit(name):
    exe = _exe(name)
    core.ps(f"Remove-NetQosPolicy -Name {core.ps_quote(PREFIX + exe)} -Confirm:$false -EA SilentlyContinue")
    return exe


def remove_all():
    core.ps(f"Get-NetQosPolicy -EA SilentlyContinue | Where-Object Name -like '{PREFIX}*' | Remove-NetQosPolicy -Confirm:$false")
