"""Funções de sistema do PingPilot: rede, processos, DNS, Wi-Fi e registro."""
import concurrent.futures
import csv
import ctypes
import io
import ipaddress
import json
import os
import secrets
import re
import socket
import statistics
import struct
import subprocess
import threading
import time
import winreg
from ctypes import wintypes

NO_WINDOW = subprocess.CREATE_NO_WINDOW

REPLY_RE = re.compile(r"(?:time|tempo)\s*[=<]\s*(\d+)\s*ms", re.I)
PACKET_LINE_RE = re.compile(r"resposta de|reply from|esgotado|timed out|falha|failure|inacess|unreachable", re.I)


# ---------------------------------------------------------------- processos e comandos

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run(cmd, timeout=30, encoding="oem"):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding=encoding,
                           errors="replace", creationflags=NO_WINDOW, timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "tempo esgotado"
    except OSError as e:
        return -1, str(e)


def ps(script, timeout=30):
    prefix = "$ProgressPreference='SilentlyContinue';[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
    return run(["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                "-Command", prefix + script], timeout, "utf-8")


def ps_json(script, timeout=30):
    """Roda PowerShell que termina em ConvertTo-Json e devolve sempre uma lista."""
    _, out = ps("& { " + script + " } | ConvertTo-Json -Compress -Depth 4", timeout)
    out = out.strip()
    start = min([i for i in (out.find("["), out.find("{")) if i >= 0], default=-1)
    if start < 0:
        return []
    try:
        data = json.loads(out[start:])
    except ValueError:
        return []
    return data if isinstance(data, list) else [data]


def ps_quote(text):
    return "'" + str(text).replace("'", "''") + "'"


def clean_exe_name(name):
    name = (name or "").strip()
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return name if re.fullmatch(r"[\w\-. ]+", name) else ""


def running_processes():
    _, out = run(["tasklist", "/fo", "csv", "/nh"])
    names = {row[0] for row in csv.reader(io.StringIO(out)) if row and row[0].lower().endswith(".exe")}
    return sorted(names, key=str.lower)


def process_pids(exe):
    name = clean_exe_name(exe)
    if not name:
        return []
    _, out = run(["tasklist", "/fo", "csv", "/nh", "/fi", f"IMAGENAME eq {name}.exe"])
    return [int(row[1]) for row in csv.reader(io.StringIO(out)) if len(row) > 1 and row[1].isdigit()]


def process_details(exe):
    """Caminho e ícone (PNG base64) de um processo em execução."""
    name = clean_exe_name(exe)
    if not name:
        return {}
    rows = ps_json(
        f"$p = Get-Process -Name {ps_quote(name)} -EA SilentlyContinue | Where-Object Path | Select-Object -First 1;"
        "if ($p) { Add-Type -AssemblyName System.Drawing;"
        " $ico = [System.Drawing.Icon]::ExtractAssociatedIcon($p.Path); $ms = New-Object IO.MemoryStream;"
        " $ico.ToBitmap().Save($ms, [System.Drawing.Imaging.ImageFormat]::Png);"
        " $title = $p.MainModule.FileVersionInfo.FileDescription;"
        " [pscustomobject]@{ Path=$p.Path; Title=$title; Icon=[Convert]::ToBase64String($ms.ToArray()) } }")
    return rows[0] if rows else {}


def set_priority(exe, priority):
    name = clean_exe_name(exe)
    if not name or priority not in ("High", "AboveNormal", "Normal"):
        return []
    _, out = ps(
        f"Get-Process -Name {ps_quote(name)} -EA SilentlyContinue |"
        f" Where-Object {{ $_.PriorityClass -ne '{priority}' }} |"
        f" ForEach-Object {{ try {{ $_.PriorityClass = '{priority}'; \"OK $($_.Id)\" }}"
        f" catch {{ \"ERRO $($_.Id): $($_.Exception.Message)\" }} }}")
    return [l for l in out.strip().splitlines() if l.startswith(("OK", "ERRO"))]


def process_connections(pids):
    """Conexões TCP estabelecidas e portas UDP abertas dos processos."""
    if not pids:
        return []
    ids = ",".join(str(int(p)) for p in pids)
    return ps_json(
        f"$ids = @({ids});"
        "$tcp = Get-NetTCPConnection -State Established -OwningProcess $ids -EA SilentlyContinue |"
        " Where-Object { $_.RemoteAddress -notmatch '^(127\\.|::1|0\\.0\\.0\\.0)' } |"
        " ForEach-Object { [pscustomobject]@{ Proto='TCP'; Remote=$_.RemoteAddress; Port=$_.RemotePort; Local=$_.LocalPort } };"
        "$udp = Get-NetUDPEndpoint -OwningProcess $ids -EA SilentlyContinue |"
        " Where-Object { $_.LocalAddress -notmatch '^(127\\.|::1)' } |"
        " ForEach-Object { [pscustomobject]@{ Proto='UDP'; Remote=''; Port=0; Local=$_.LocalPort } };"
        "@($tcp) + @($udp)")


# ---------------------------------------------------------------- rede

def active_adapter():
    rows = ps_json(
        "$r = Get-NetRoute -DestinationPrefix '0.0.0.0/0' -EA SilentlyContinue |"
        " Sort-Object { $_.RouteMetric + (Get-NetIPInterface -InterfaceIndex $_.ifIndex -AddressFamily IPv4).InterfaceMetric } |"
        " Select-Object -First 1;"
        "if ($r) { $a = Get-NetAdapter -InterfaceIndex $r.ifIndex;"
        " $ipo = Get-NetIPAddress -InterfaceIndex $r.ifIndex -AddressFamily IPv4 -EA SilentlyContinue | Select-Object -First 1;"
        " [pscustomobject]@{ Index=$r.ifIndex; Alias=$a.Name; Guid=$a.InterfaceGuid; Gateway=$r.NextHop;"
        " LocalIP=$ipo.IPAddress; Prefix=$ipo.PrefixLength; Mac=$a.MacAddress;"
        " Media=[string]$a.PhysicalMediaType; Desc=$a.InterfaceDescription; Speed=$a.LinkSpeed;"
        " Dns=@((Get-DnsClientServerAddress -InterfaceIndex $r.ifIndex -AddressFamily IPv4).ServerAddresses) } }")
    if not rows:
        return None
    info = rows[0]
    dns = info.get("Dns") or []
    info["Dns"] = [dns] if isinstance(dns, str) else list(dns)
    media = (info.get("Media") or "") + " " + (info.get("Desc") or "")
    info["Wireless"] = bool(re.search(r"802\.11|wireless|wi-?fi", media, re.I))
    return info


def nic_class_path(index):
    """Chave do driver do adaptador em Control/Class, onde ficam as opções avançadas da placa."""
    _, out = ps(f"$a = Get-NetAdapter -InterfaceIndex {int(index)} -EA SilentlyContinue;"
                r" if ($a) { (Get-ItemProperty ('HKLM:\SYSTEM\CurrentControlSet\Enum\' + $a.PnPDeviceID)).Driver }")
    driver = out.strip().splitlines()[-1].strip() if out.strip() else ""
    if not re.fullmatch(r"\{[\w-]+\}\\\d{4}", driver):
        return None
    return "SYSTEM\\CurrentControlSet\\Control\\Class\\" + driver


class _PDH_VALUE(ctypes.Structure):
    _fields_ = [("CStatus", wintypes.DWORD), ("largeValue", ctypes.c_longlong)]


def standby_mb():
    """Memória em espera (cache) em MB, via PDH com nomes em inglês (funciona em qualquer idioma)."""
    pdh = ctypes.windll.pdh
    query = wintypes.HANDLE()
    if pdh.PdhOpenQueryW(None, None, ctypes.byref(query)) != 0:
        return None
    try:
        counters = []
        for name in ("Standby Cache Normal Priority Bytes", "Standby Cache Reserve Bytes", "Standby Cache Core Bytes"):
            c = wintypes.HANDLE()
            if pdh.PdhAddEnglishCounterW(query, "\\Memory\\" + name, None, ctypes.byref(c)) == 0:
                counters.append(c)
        if not counters or pdh.PdhCollectQueryData(query) != 0:
            return None
        total = 0
        for c in counters:
            v = _PDH_VALUE()
            if pdh.PdhGetFormattedCounterValue(c, 0x400, None, ctypes.byref(v)) == 0:  # PDH_FMT_LARGE
                total += v.largeValue
        return int(total / 1024 / 1024)
    finally:
        pdh.PdhCloseQuery(query)


class _LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]


class _TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", wintypes.DWORD), ("Luid", _LUID), ("Attributes", wintypes.DWORD)]


def purge_standby_list():
    """Esvazia a lista de memória em espera (mesma chamada do EmptyStandbyList). Precisa de admin."""
    advapi, kernel, ntdll = ctypes.WinDLL("advapi32", use_last_error=True), ctypes.windll.kernel32, ctypes.windll.ntdll
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    token = wintypes.HANDLE()
    if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x28, ctypes.byref(token)):
        raise PermissionError("não foi possível abrir o token do processo")
    try:
        tp = _TOKEN_PRIVILEGES(1, _LUID(), 2)
        advapi.LookupPrivilegeValueW(None, "SeProfileSingleProcessPrivilege", ctypes.byref(tp.Luid))
        advapi.AdjustTokenPrivileges(token, False, ctypes.byref(tp), 0, None, None)
        if ctypes.get_last_error() == 1300:
            raise PermissionError("precisa de administrador")
    finally:
        kernel.CloseHandle(token)
    command = ctypes.c_int(4)  # MemoryPurgeStandbyList
    status = ntdll.NtSetSystemInformation(80, ctypes.byref(command), ctypes.sizeof(command))
    if status != 0:
        raise RuntimeError(f"o Windows recusou a limpeza (NTSTATUS 0x{status & 0xFFFFFFFF:08X})")


def _hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except OSError:
        return None


def scan_lan(adapter, progress=None):
    """Lista os aparelhos da rede local: ping em todos os IPs da sub-rede + tabela ARP do Windows.

    Mesmo aparelhos que bloqueiam ping aparecem, porque o Windows precisa descobrir o MAC
    (ARP) antes de mandar o ping — e isso fica registrado na tabela de vizinhos.
    """
    me = ipaddress.IPv4Interface(f"{adapter['LocalIP']}/{adapter.get('Prefix') or 24}")
    net = me.network if me.network.prefixlen >= 22 else ipaddress.IPv4Interface(f"{me.ip}/24").network
    hosts = [str(h) for h in net.hosts()]
    alive, done = {}, [0]

    def probe(ip, timeout):
        alive[ip] = ping_once(ip, timeout)
        done[0] += 1
        if progress and done[0] % 16 == 0:
            progress(min(done[0], len(hosts)), len(hosts))

    with concurrent.futures.ThreadPoolExecutor(96) as pool:
        list(pool.map(lambda ip: probe(ip, 500), hosts))
        # celulares em economia de energia demoram a acordar: segunda chance para quem não respondeu
        missing = [ip for ip in hosts if alive.get(ip) is None]
        list(pool.map(lambda ip: probe(ip, 1000), missing))

    _, out = run(["arp", "-a", "-N", str(me.ip)])
    macs = {}
    for line in out.splitlines():
        m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})", line)
        if m and m.group(2).lower() not in ("ff-ff-ff-ff-ff-ff", "00-00-00-00-00-00") \
                and not m.group(2).lower().startswith("01-00-5e"):
            macs[m.group(1)] = m.group(2)
    macs[str(me.ip)] = adapter.get("Mac") or ""
    ips = sorted({ip for ip in macs if ipaddress.IPv4Address(ip) in net and ip != str(net.broadcast_address)}
                 | {ip for ip, ms in alive.items() if ms is not None}, key=ipaddress.IPv4Address)

    with concurrent.futures.ThreadPoolExecutor(32) as pool:
        futures = {ip: pool.submit(_hostname, ip) for ip in ips}
        concurrent.futures.wait(futures.values(), timeout=4)
        names = {ip: f.result() if f.done() else None for ip, f in futures.items()}

    devices = []
    for ip in ips:
        mac = (macs.get(ip) or "").upper()
        devices.append({
            "ip": ip, "mac": mac, "ping": alive.get(ip), "name": names.get(ip),
            "me": ip == str(me.ip), "gateway": ip == adapter.get("Gateway"),
            # 2º dígito 2, 6, A ou E = endereço "aleatório" (privacidade de celulares e Windows 11)
            "random_mac": len(mac) > 1 and mac[1] in "26AE",
        })
    return {"network": str(net), "devices": devices}


def traceroute(ip, max_hops=20):
    """Saltos até o servidor (tracert do Windows): [{hop, ip, times: [ms|None x3], avg}]."""
    ip = str(ipaddress.IPv4Address(ip))  # só IPv4 literal chega ao tracert
    _, out = run(["tracert", "-d", "-h", str(max_hops), "-w", "800", ip], timeout=max_hops * 3 * 1 + 30)
    hops = []
    for line in out.splitlines():
        m = re.match(r"\s*(\d+)\s+(.+)$", line)
        if not m:
            continue
        rest = m.group(2)
        times = [None if t == "*" else int(t.lstrip("<")) for t in re.findall(r"(<?\d+)\s*ms|\*", rest)
                 for t in [t or "*"]][:3]
        addr = re.findall(r"\d+\.\d+\.\d+\.\d+", rest)
        ok = [t for t in times if t is not None]
        hops.append({"hop": int(m.group(1)), "ip": addr[-1] if addr else None, "times": times,
                     "avg": round(sum(ok) / len(ok)) if ok else None})
    return hops


def ping_once(host, timeout_ms=1000):
    code, out = run(["ping", "-4", "-n", "1", "-w", str(timeout_ms), host], timeout=timeout_ms / 1000 + 3)
    m = REPLY_RE.search(out)
    return int(m.group(1)) if m else None


def ping_stream(host, count, on_packet, stop=None):
    """Roda o ping do Windows (count=0 → contínuo) e chama on_packet(ms ou None)."""
    args = ["ping", "-4", "-w", "1000"] + (["-t"] if count == 0 else ["-n", str(count)]) + [host]
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                         encoding="oem", errors="replace", creationflags=NO_WINDOW)
    try:
        for line in p.stdout:
            if stop is not None and stop.is_set():
                break
            m = REPLY_RE.search(line)
            if m:
                on_packet(int(m.group(1)))
            elif PACKET_LINE_RE.search(line):
                on_packet(None)
    finally:
        if p.poll() is None:
            p.kill()
        p.wait()


def tcp_ping(host, port, timeout=1.5):
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, int(port)), timeout=timeout):
            return (time.perf_counter() - t0) * 1000
    except OSError:
        return None


def ping_stats(samples):
    ok = [s for s in samples if s is not None]
    sent = len(samples)
    if not ok:
        return {"avg": None, "min": None, "max": None, "jitter": None, "loss": 100.0 if sent else 0.0, "spikes": 0}
    avg = statistics.mean(ok)
    jitter = statistics.mean(abs(a - b) for a, b in zip(ok, ok[1:])) if len(ok) > 1 else 0.0
    spikes = sum(1 for s in ok if s > max(avg * 2, avg + 30))
    return {"avg": avg, "min": min(ok), "max": max(ok), "jitter": jitter,
            "loss": 100.0 * (sent - len(ok)) / sent, "spikes": spikes}


def quality(st, local=False):
    if st["avg"] is None:
        return "down"
    jit_lim, ping_lim = (5, 10) if local else (10, 80)
    if st["loss"] >= 2 or st["jitter"] > jit_lim * 2:
        return "bad"
    if st["loss"] > 0 or st["jitter"] > jit_lim or st["avg"] > ping_lim:
        return "fair"
    return "good"


def dns_query_ms(server, domain, timeout=1.5):
    tid = secrets.randbelow(0x10000)  # imprevisível: dificulta resposta DNS falsificada
    query = struct.pack(">HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    query += b"".join(bytes([len(p)]) + p.encode() for p in domain.split(".")) + b"\x00"
    query += struct.pack(">HH", 1, 1)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(timeout)
        t0 = time.perf_counter()
        try:
            s.sendto(query, (server, 53))
            while True:
                data, _ = s.recvfrom(1024)
                if len(data) >= 2 and struct.unpack(">H", data[:2])[0] == tid:
                    return (time.perf_counter() - t0) * 1000
        except OSError:
            return None


# ---------------------------------------------------------------- registro

HIVES = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}
REG_TYPES = {"DWord": winreg.REG_DWORD, "String": winreg.REG_SZ}


def windows_accent():
    """Cor de destaque do Windows (#rrggbb), usada pelo tema Material."""
    cur = reg_get("HKCU", r"Software\Microsoft\Windows\DWM", "AccentColor")
    if not cur:
        return "#3b82f6"
    abgr = cur["value"] & 0xFFFFFFFF
    return f"#{abgr & 0xFF:02x}{(abgr >> 8) & 0xFF:02x}{(abgr >> 16) & 0xFF:02x}"


def reg_get(hive, path, name):
    try:
        with winreg.OpenKey(HIVES[hive], path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            value, typ = winreg.QueryValueEx(k, name)
            return {"value": value, "type": typ}
    except OSError:
        return None


def reg_set(hive, path, name, value, typ):
    with winreg.CreateKeyEx(HIVES[hive], path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
        winreg.SetValueEx(k, name, 0, typ, value)


def reg_delete(hive, path, name):
    try:
        with winreg.OpenKey(HIVES[hive], path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.DeleteValue(k, name)
    except FileNotFoundError:
        pass


# ---------------------------------------------------------------- Wi-Fi (técnica do WLANOptimizer)

class _GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


class _WLAN_INTERFACE_INFO(ctypes.Structure):
    _fields_ = [("InterfaceGuid", _GUID), ("strInterfaceDescription", ctypes.c_wchar * 256),
                ("isState", ctypes.c_int)]


class _WLAN_INTERFACE_INFO_LIST(ctypes.Structure):
    _fields_ = [("dwNumberOfItems", wintypes.DWORD), ("dwIndex", wintypes.DWORD),
                ("InterfaceInfo", _WLAN_INTERFACE_INFO * 1)]


WLAN_CONNECTED = 1
OPCODE_BACKGROUND_SCAN = 2
OPCODE_MEDIA_STREAMING = 3


class WlanOptimizer:
    """Desliga a busca de redes em segundo plano e liga o modo streaming do Wi-Fi.

    Mesma técnica do WLANOptimizer (catid): o Windows só mantém a configuração
    enquanto o handle está aberto, então ela é reaplicada periodicamente.
    """

    def __init__(self):
        self.handle = None
        self.enabled = False
        self.last_result = "desligado"
        self._stop = threading.Event()
        self._thread = None
        try:
            self.api = ctypes.WinDLL("wlanapi.dll")
        except OSError:
            self.api = None

    def _open(self):
        if self.handle is None and self.api:
            version, handle = wintypes.DWORD(), wintypes.HANDLE()
            if self.api.WlanOpenHandle(2, None, ctypes.byref(version), ctypes.byref(handle)) == 0:
                self.handle = handle
        return self.handle

    def apply(self, enable=True):
        if not self.api:
            return "Wi-Fi indisponível neste PC"
        handle = self._open()
        if not handle:
            return "serviço de Wi-Fi (WLAN AutoConfig) não está ativo"
        lst = ctypes.POINTER(_WLAN_INTERFACE_INFO_LIST)()
        if self.api.WlanEnumInterfaces(handle, None, ctypes.byref(lst)) != 0:
            return "não foi possível listar as placas Wi-Fi"
        try:
            count = lst.contents.dwNumberOfItems
            infos = ctypes.cast(ctypes.byref(lst.contents.InterfaceInfo),
                                ctypes.POINTER(_WLAN_INTERFACE_INFO * count)).contents
            done = []
            for info in infos:
                if info.isState != WLAN_CONNECTED:
                    continue
                for opcode, value in ((OPCODE_MEDIA_STREAMING, enable), (OPCODE_BACKGROUND_SCAN, not enable)):
                    v = wintypes.BOOL(value)
                    self.api.WlanSetInterface(handle, ctypes.byref(info.InterfaceGuid), opcode,
                                              ctypes.sizeof(v), ctypes.byref(v), None)
                done.append(info.strInterfaceDescription)
            return ("ativo em " + ", ".join(done)) if done else "nenhuma rede Wi-Fi conectada"
        finally:
            self.api.WlanFreeMemory(lst)

    def start(self):
        self.enabled = True
        self._stop.clear()
        if not self._thread or not self._thread.is_alive():
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
        self.last_result = self.apply(True)
        return self.last_result

    def stop(self):
        self.enabled = False
        self._stop.set()
        self.last_result = self.apply(False) if self.handle else "desligado"
        if self.handle:
            self.api.WlanCloseHandle(self.handle, None)
            self.handle = None
        return "desligado"

    def _loop(self):
        while not self._stop.wait(5):
            if self.enabled:
                self.last_result = self.apply(True)
