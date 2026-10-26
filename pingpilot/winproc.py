"""Processos, ícones e tabelas de conexão direto pela API do Windows (ctypes, sem PowerShell).

Funciona também com processos protegidos por anti-cheat (Vanguard, EAC...), que escondem
o caminho do .exe de Get-Process mas não de QueryFullProcessImageNameW.
"""
import base64
import ctypes
import csv
import io
import os
import socket
import struct
import subprocess
import zlib
from ctypes import wintypes

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
version = ctypes.WinDLL("version", use_last_error=True)
iphlp = ctypes.WinDLL("iphlpapi", use_last_error=True)

k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.CloseHandle.argtypes = [wintypes.HANDLE]
k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                           ctypes.POINTER(wintypes.DWORD)]
k32.GetPriorityClass.argtypes = [wintypes.HANDLE]
k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]

QUERY_LIMITED, SET_INFO = 0x1000, 0x0200
PRIORITY = {"High": 0x80, "AboveNormal": 0x8000, "Normal": 0x20}


# ---------------------------------------------------------------- processos

def pids_by_name():
    """{nome do exe em minúsculas: [pids]} de todos os processos em execução."""
    r = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, encoding="oem",
                       errors="replace", creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
    out = {}
    for row in csv.reader(io.StringIO(r.stdout)):
        if len(row) > 1 and row[1].isdigit():
            out.setdefault(row[0].lower(), []).append(int(row[1]))
    return out


def exe_path(pid):
    h = k32.OpenProcess(QUERY_LIMITED, False, pid)
    if not h:
        return None
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        return buf.value if k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else None
    finally:
        k32.CloseHandle(h)


def file_info(path):
    """ProductName, FileDescription e CompanyName do recurso de versão do .exe."""
    info = {}
    try:
        size = version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return info
        data = ctypes.create_string_buffer(size)
        if not version.GetFileVersionInfoW(path, 0, size, data):
            return info
        ptr, length = ctypes.c_void_p(), wintypes.UINT()
        langs = []
        if version.VerQueryValueW(data, "\\VarFileInfo\\Translation", ctypes.byref(ptr), ctypes.byref(length)):
            raw = ctypes.string_at(ptr, length.value)
            langs = [struct.unpack_from("<HH", raw, i) for i in range(0, len(raw) - 3, 4)]
        langs += [(0x0409, 0x04B0), (0x0409, 0x04E4), (0x0416, 0x04B0)]
        for key in ("ProductName", "FileDescription", "CompanyName"):
            for lang, cp in langs:
                q = f"\\StringFileInfo\\{lang:04x}{cp:04x}\\{key}"
                if version.VerQueryValueW(data, q, ctypes.byref(ptr), ctypes.byref(length)) and length.value:
                    info[key] = ctypes.wstring_at(ptr, length.value - 1).strip()
                    break
    except OSError:
        pass
    return info


# pastas que guardam vários programas: o app é a subpasta logo abaixo delas
CONTAINERS = {"program files", "program files (x86)", "riot games", "common", "epic games", "games",
              "local", "roaming", "programs", "xboxgames", "windowsapps", "steamapps", "battle.net",
              "ubisoft game launcher", "ea games", "gog galaxy", "programdata", "common files",
              "users", "documents", "desktop", "downloads", "onedrive"}
# nomes de produto que não dizem qual é o jogo (engine/inicializador)
GENERIC = {"bootstrappackagedgame", "unreal engine", "unity", "electron", "cef", "chromium embedded framework"}
SKIP_WORDS = ("crash", "uninstall", "unins", "setup", "update", "installer", "reporter")


def install_root(path):
    """Pasta de instalação do app: a subpasta logo abaixo de Program Files, Riot Games, steamapps\\common…"""
    folder = os.path.dirname(path)
    while True:
        parent = os.path.dirname(folder)
        if parent == folder or os.path.basename(parent).casefold() in CONTAINERS or parent == os.path.dirname(parent):
            return folder
        folder = parent


def app_title(root, paths):
    """Nome para mostrar: o nome da pasta, se ela fica numa pasta de jogos; senão o nome do produto."""
    parent = os.path.basename(os.path.dirname(root)).casefold()
    if parent in ("riot games", "common", "epic games", "games", "xboxgames", "ea games"):
        return os.path.basename(root)
    names = [file_info(p).get("ProductName") or "" for p in paths]
    names = [n for n in names if n and n.casefold() not in GENERIC and "microsoft" not in n.casefold()]
    return min(names, key=len) if names else os.path.basename(root)


def running_apps():
    """Processos do usuário agrupados por pasta de instalação (ex.: os 3 .exe do Riot Client viram um só)."""
    windows = os.environ.get("SystemRoot", r"C:\Windows").lower()
    me = os.getpid()
    groups = {}
    for name, pids in pids_by_name().items():
        if not name.endswith(".exe") or any(w in name for w in SKIP_WORDS) or name.startswith("pingpilot"):
            continue
        path = next((p for p in (exe_path(pid) for pid in pids if pid != me) if p), None)
        if not path or path.lower().startswith(windows) or "\\python" in path.lower():
            continue
        root = install_root(path)
        g = groups.setdefault(root.casefold(), {"root": root, "exes": [], "paths": []})
        g["exes"].append(os.path.basename(path))
        g["paths"].append(path)
    apps = []
    for g in groups.values():
        g["name"] = app_title(g["root"], g["paths"])
        g["exes"] = sorted(set(g["exes"]), key=str.casefold)
        # ícone/caminho principal: o .exe mais perto da raiz (o inicializador costuma ter o ícone do jogo)
        g["path"] = min(g["paths"], key=lambda p: (p.count("\\"), len(p)))
        g["company"] = file_info(g["path"]).get("CompanyName", "")
        apps.append(g)
    return sorted(apps, key=lambda g: g["name"].casefold())


def sibling_exes(root, limit=500):
    """Todos os .exe da pasta de instalação — inclusive os que só abrem durante a partida
    (ex.: League of Legends\\Game\\League of Legends.exe)."""
    found = set()
    for dirpath, dirnames, files in os.walk(root):
        if dirpath.count("\\") - root.count("\\") >= 6:
            dirnames[:] = []
        for f in files:
            if f.lower().endswith(".exe") and not any(w in f.lower() for w in SKIP_WORDS):
                found.add(f)
                if len(found) >= limit:
                    return sorted(found, key=str.casefold)
    return sorted(found, key=str.casefold)


def ensure_priority(pids, priority):
    """Ajusta a prioridade; devolve (alterados, erros) — vazio quando já estava certo."""
    target = PRIORITY.get(priority)
    changed, errors = [], []
    for pid in pids:
        h = k32.OpenProcess(QUERY_LIMITED | SET_INFO, False, pid)
        if not h:
            errors.append((pid, ctypes.get_last_error()))
            continue
        try:
            if k32.GetPriorityClass(h) != target:
                if k32.SetPriorityClass(h, target):
                    changed.append(pid)
                else:
                    errors.append((pid, ctypes.get_last_error()))
        finally:
            k32.CloseHandle(h)
    return changed, errors


# ---------------------------------------------------------------- ícone em alta resolução

class _ICONINFO(ctypes.Structure):
    _fields_ = [("fIcon", wintypes.BOOL), ("xHotspot", wintypes.DWORD), ("yHotspot", wintypes.DWORD),
                ("hbmMask", wintypes.HBITMAP), ("hbmColor", wintypes.HBITMAP)]


class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD)]


user32.PrivateExtractIconsW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                        ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.UINT),
                                        wintypes.UINT, wintypes.UINT]
user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(_ICONINFO)]
user32.DestroyIcon.argtypes = [wintypes.HICON]
gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                            ctypes.c_void_p, wintypes.UINT]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


def _bitmap_bits(hdc, hbm, size):
    bmi = _BITMAPINFOHEADER(ctypes.sizeof(_BITMAPINFOHEADER), size, -size, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(size * size * 4)
    gdi32.GetDIBits(hdc, hbm, 0, size, buf, ctypes.byref(bmi), 0)
    return buf.raw


def _png(width, height, rgba):
    rows = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b""))


def icon_png(path, size=128):
    """Ícone do .exe em PNG (base64), no maior tamanho disponível até `size`."""
    if not path or not os.path.exists(path):
        return None
    hicon = wintypes.HICON()
    if user32.PrivateExtractIconsW(path, 0, size, size, ctypes.byref(hicon), None, 1, 0) != 1 or not hicon:
        return None
    info = _ICONINFO()
    hdc = gdi32.CreateCompatibleDC(None)
    try:
        if not user32.GetIconInfo(hicon, ctypes.byref(info)) or not info.hbmColor:
            return None
        bgra = bytearray(_bitmap_bits(hdc, info.hbmColor, size))
        if not any(bgra[3::4]):  # ícone antigo sem canal alfa: usa a máscara
            mask = _bitmap_bits(hdc, info.hbmMask, size)
            bgra[3::4] = bytes(0 if mask[i] else 255 for i in range(0, len(mask), 4))
        bgra[0::4], bgra[2::4] = bgra[2::4], bgra[0::4]  # BGRA -> RGBA
        return base64.b64encode(_png(size, size, bytes(bgra))).decode()
    finally:
        for h in (info.hbmColor, info.hbmMask):
            if h:
                gdi32.DeleteObject(h)
        gdi32.DeleteDC(hdc)
        user32.DestroyIcon(hicon)


# ---------------------------------------------------------------- tabelas TCP/UDP por processo

iphlp.GetExtendedTcpTable.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), wintypes.BOOL,
                                      wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
iphlp.GetExtendedUdpTable.argtypes = iphlp.GetExtendedTcpTable.argtypes


def _table(fn, kind, row_size):
    size = wintypes.DWORD(0)
    fn(None, ctypes.byref(size), False, socket.AF_INET, kind, 0)
    for _ in range(3):
        buf = ctypes.create_string_buffer(size.value + 4096)
        size = wintypes.DWORD(len(buf))
        if fn(buf, ctypes.byref(size), False, socket.AF_INET, kind, 0) == 0:
            count = struct.unpack_from("<I", buf.raw, 0)[0]
            return [buf.raw[4 + i * row_size:4 + (i + 1) * row_size] for i in range(count)]
    return []


def _port(raw):
    return socket.ntohs(raw & 0xFFFF)


def tcp_connections():
    """Conexões TCP IPv4 estabelecidas: [{pid, local_port, remote, port}]."""
    out = []
    for row in _table(iphlp.GetExtendedTcpTable, 5, 24):  # TCP_TABLE_OWNER_PID_ALL
        state, laddr, lport, raddr, rport, pid = struct.unpack("<IIIIII", row)
        if state != 5:  # ESTABLISHED
            continue
        remote = socket.inet_ntoa(struct.pack("<I", raddr))
        if remote.startswith(("127.", "0.")):
            continue
        out.append({"pid": pid, "local_port": _port(lport), "remote": remote, "port": _port(rport)})
    return out


def udp_endpoints():
    """Portas UDP IPv4 abertas: [{pid, local_port}] (o Windows não guarda o destino de UDP)."""
    out = []
    for row in _table(iphlp.GetExtendedUdpTable, 1, 12):  # UDP_TABLE_OWNER_PID
        laddr, lport, pid = struct.unpack("<III", row)
        if not socket.inet_ntoa(struct.pack("<I", laddr)).startswith("127."):
            out.append({"pid": pid, "local_port": _port(lport)})
    return out
