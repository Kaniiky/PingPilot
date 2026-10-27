"""Limpeza de arquivos (estilo CCleaner), com a mesma filosofia do BleachBit — reimplementada aqui.

Regras de segurança:
  - cada item só apaga DENTRO das pastas dele; o caminho real de cada arquivo é conferido antes de apagar;
  - atalhos, links simbólicos e junções nunca são seguidos (um link dentro do Temp não leva a limpeza para fora);
  - navegadores: só cache — nunca cookies, histórico, senhas ou sessões;
  - se o programa dono do cache estiver aberto, o item é pulado (os arquivos estão em uso);
  - arquivos em uso são simplesmente ignorados;
  - nada é apagado sem uma análise antes mostrando o tamanho.
"""
import ctypes
import glob
import os
import stat
import sys
import time
from ctypes import wintypes

import winproc

L = os.environ.get
CHROMIUM_CACHE = ["Cache\\Cache_Data", "Code Cache", "GPUCache", "Service Worker\\CacheStorage"]


def _chromium(base, profiles="*"):
    return [os.path.join(base, profiles, sub) for sub in CHROMIUM_CACHE]


# id, grupo, ícone, título, descrição, pastas (glob; o CONTEÚDO de cada uma é limpo), marcado por padrão,
# "não recomendado se", precisa de admin, programas que precisam estar fechados
CATALOG = [
    {"id": "user_temp", "group": "Windows", "icon": "trash", "title": "Arquivos temporários do usuário",
     "desc": "A pasta Temp da sua conta: sobras de instaladores e programas. Arquivos das últimas 24 h ficam.",
     "default": True, "min_age": 86400, "paths": ["%TEMP%"]},
    {"id": "win_temp", "group": "Windows", "icon": "trash", "title": "Arquivos temporários do Windows",
     "desc": "A pasta Temp do sistema. Arquivos das últimas 24 h ficam.", "default": True, "admin": True, "min_age": 86400, "paths": ["%SystemRoot%\\Temp"]},
    {"id": "wu_cache", "group": "Windows", "icon": "download", "title": "Downloads do Windows Update",
     "desc": "Atualizações já instaladas que ficaram guardadas.", "default": True, "admin": True,
     "warn": "Há uma atualização do Windows sendo instalada agora.",
     "paths": ["%SystemRoot%\\SoftwareDistribution\\Download"]},
    {"id": "do_cache", "group": "Windows", "icon": "upload", "title": "Cache da Otimização de Entrega",
     "desc": "Pedaços de atualizações que o Windows guarda para compartilhar com outros PCs.", "default": True,
     "admin": True,
     "paths": ["%SystemRoot%\\ServiceProfiles\\NetworkService\\AppData\\Local\\Microsoft\\Windows\\DeliveryOptimization\\Cache"]},
    {"id": "thumbs", "group": "Windows", "icon": "apps", "title": "Cache de miniaturas",
     "desc": "Prévias de imagens e vídeos do Explorador; são recriadas quando você abre as pastas.", "default": False,
     "warn": "Você abre pastas com muitas fotos e não quer esperar as miniaturas recarregarem.",
     "files": ["%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db",
               "%LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\iconcache_*.db"]},
    {"id": "crash", "group": "Windows", "icon": "shield", "title": "Relatórios de erro e despejos de memória",
     "desc": "Relatórios do Windows Error Reporting e arquivos .dmp de travamentos antigos.", "default": True,
     "admin": True, "warn": "Você está investigando uma tela azul recente (os .dmp ajudam no diagnóstico).",
     "paths": ["%ProgramData%\\Microsoft\\Windows\\WER\\ReportArchive", "%ProgramData%\\Microsoft\\Windows\\WER\\ReportQueue",
               "%LOCALAPPDATA%\\Microsoft\\Windows\\WER\\ReportArchive", "%LOCALAPPDATA%\\CrashDumps",
               "%SystemRoot%\\Minidump"], "files": ["%SystemRoot%\\MEMORY.DMP"]},
    {"id": "recycle", "group": "Windows", "icon": "trash", "title": "Lixeira",
     "desc": "Esvazia a Lixeira de todos os discos.", "default": False, "recycle": True,
     "warn": "Pode haver algo lá que você ainda quer recuperar — isto é permanente."},
    # ---- navegadores (só cache)
    {"id": "chrome", "group": "Navegadores", "icon": "globe", "title": "Google Chrome (cache)",
     "desc": "Imagens e scripts guardados. Cookies, histórico e senhas não são tocados.", "default": True,
     "running": ["chrome.exe"], "paths": _chromium("%LOCALAPPDATA%\\Google\\Chrome\\User Data")},
    {"id": "edge", "group": "Navegadores", "icon": "globe", "title": "Microsoft Edge (cache)",
     "desc": "Imagens e scripts guardados. Cookies, histórico e senhas não são tocados.", "default": True,
     "running": ["msedge.exe"], "paths": _chromium("%LOCALAPPDATA%\\Microsoft\\Edge\\User Data")},
    {"id": "brave", "group": "Navegadores", "icon": "globe", "title": "Brave (cache)",
     "desc": "Imagens e scripts guardados. Cookies, histórico e senhas não são tocados.", "default": True,
     "running": ["brave.exe"], "paths": _chromium("%LOCALAPPDATA%\\BraveSoftware\\Brave-Browser\\User Data")},
    {"id": "opera", "group": "Navegadores", "icon": "globe", "title": "Opera / Opera GX (cache)",
     "desc": "Imagens e scripts guardados. Cookies, histórico e senhas não são tocados.", "default": True,
     "running": ["opera.exe"],
     "paths": ["%LOCALAPPDATA%\\Opera Software\\*\\Cache\\Cache_Data", "%LOCALAPPDATA%\\Opera Software\\*\\Code Cache",
               "%APPDATA%\\Opera Software\\*\\GPUCache"]},
    {"id": "firefox", "group": "Navegadores", "icon": "globe", "title": "Firefox (cache)",
     "desc": "Imagens e scripts guardados. Cookies, histórico e senhas não são tocados.", "default": True,
     "running": ["firefox.exe"], "paths": ["%LOCALAPPDATA%\\Mozilla\\Firefox\\Profiles\\*\\cache2"]},
    # ---- jogos e apps
    {"id": "steam", "group": "Jogos e apps", "icon": "gamepad", "title": "Steam (cache da loja e logs)",
     "desc": "Imagens da loja e da biblioteca e registros antigos. Seus jogos e saves não são tocados.",
     "default": True, "running": ["steam.exe"],
     "paths": ["%ProgramFiles(x86)%\\Steam\\appcache\\httpcache", "%ProgramFiles(x86)%\\Steam\\logs",
               "%LOCALAPPDATA%\\Steam\\htmlcache\\Cache"]},
    {"id": "discord", "group": "Jogos e apps", "icon": "network", "title": "Discord (cache)",
     "desc": "Imagens, GIFs e vídeos já vistos. Suas conversas ficam no servidor e não são afetadas.",
     "default": True, "running": ["discord.exe"],
     "paths": ["%APPDATA%\\discord\\Cache\\Cache_Data", "%APPDATA%\\discord\\Code Cache", "%APPDATA%\\discord\\GPUCache"]},
    {"id": "shaders", "group": "Jogos e apps", "icon": "gpu", "title": "Caches de shader (DirectX, NVIDIA, AMD)",
     "desc": "Shaders compilados dos jogos. Limpar resolve gráficos corrompidos ou travadas depois de trocar o driver de vídeo.",
     "default": False,
     "warn": "Seus jogos estão rodando bem — depois de limpar, as primeiras partidas recompilam os shaders e podem engasgar.",
     "paths": ["%LOCALAPPDATA%\\D3DSCache", "%LOCALAPPDATA%\\NVIDIA\\DXCache", "%LOCALAPPDATA%\\NVIDIA\\GLCache",
               "%LOCALAPPDATA%\\AMD\\DxCache", "%LOCALAPPDATA%\\AMD\\DxcCache", "%LOCALAPPDATA%\\AMD\\GLCache"]},
]

FILE_ATTRIBUTE_REPARSE_POINT = 0x400
# os arquivos do próprio PingPilot (o .exe se descompacta dentro do Temp) nunca entram na limpeza
PROTECTED = [os.path.normcase(os.path.realpath(p)) for p in (getattr(sys, "_MEIPASS", None), os.path.dirname(os.path.abspath(__file__))) if p]


def _expand(patterns):
    out = []
    for p in patterns or []:
        p = os.path.expandvars(p)
        if "%" in p:  # variável que não existe nesta máquina
            continue
        out += [os.path.abspath(x) for x in glob.glob(p) if not (os.path.islink(x) or os.path.isjunction(x))]
    return sorted(set(out))


def _is_link(entry):
    """Link simbólico, junção ou outro ponto de nova análise: nunca seguir."""
    try:
        st = entry.stat(follow_symlinks=False)
    except OSError:
        return True
    return entry.is_symlink() or bool(getattr(st, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT)


def _protected(path):
    """Links nunca são seguidos, então comparar o caminho como texto basta (e é rápido)."""
    p = os.path.normcase(path)
    return any(p == x or p.startswith(x + os.sep) for x in PROTECTED)


def _walk(root, min_age=0, dirs=None):
    """(arquivo, tamanho) dentro de root, sem atravessar links/junções. min_age pula arquivos recentes;
    dirs, se for uma lista, recebe as subpastas visitadas (para apagar as que ficarem vazias)."""
    limit = time.time() - min_age
    stack = [root]
    while stack:
        d = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            continue
        for e in entries:
            if _is_link(e):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if _protected(e.path):
                        continue
                    stack.append(e.path)
                    if dirs is not None:
                        dirs.append(e.path)
                elif e.is_file(follow_symlinks=False):
                    st = e.stat(follow_symlinks=False)
                    if st.st_mtime <= limit:
                        yield e.path, st.st_size
            except OSError:
                continue


def _inside(path, root):
    """path está dentro de root? (comparação de texto: _walk nunca atravessa links, então não há como escapar)"""
    return os.path.normcase(path).startswith(os.path.normcase(root).rstrip(os.sep) + os.sep)


class _SHQUERYRBINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("i64Size", ctypes.c_int64), ("i64NumItems", ctypes.c_int64)]


def _recycle_size():
    info = _SHQUERYRBINFO(ctypes.sizeof(_SHQUERYRBINFO))
    if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) == 0:
        return info.i64Size, info.i64NumItems
    return 0, 0


def _blocked(item, running):
    return [exe for exe in item.get("running", []) if exe in running]


def scan(admin):
    """Quanto cada item ocupa agora (só leitura)."""
    running = winproc.pids_by_name()
    out = []
    for item in CATALOG:
        size = count = 0
        if item.get("recycle"):
            size, count = _recycle_size()
        else:
            for root in _expand(item.get("paths")):
                for _, sz in _walk(root, item.get("min_age", 0)):
                    size += sz
                    count += 1
            for f in _expand(item.get("files")):
                if os.path.isfile(f) and not os.path.islink(f):
                    size += os.path.getsize(f)
                    count += 1
        out.append({k: item.get(k) for k in ("id", "group", "icon", "title", "desc", "warn")}
                   | {"default": bool(item.get("default")), "size": size, "files": count,
                      "locked": bool(item.get("admin")) and not admin, "blocked": _blocked(item, running)})
    return out


def _remove(path):
    try:
        os.chmod(path, stat.S_IWRITE)  # arquivo somente leitura
    except OSError:
        pass
    os.remove(path)


def clean(ids, admin):
    """Apaga os itens escolhidos. Devolve o que foi liberado e o que foi pulado."""
    running = winproc.pids_by_name()
    freed = removed = 0
    skipped = []
    for item in CATALOG:
        if item["id"] not in ids:
            continue
        if item.get("admin") and not admin:
            skipped.append({"id": item["id"], "reason": "admin"})
            continue
        if _blocked(item, running):
            skipped.append({"id": item["id"], "reason": "running", "apps": _blocked(item, running)})
            continue
        if item.get("recycle"):
            size, count = _recycle_size()
            # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
            if size and ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x7) == 0:
                freed += size
                removed += count
            continue
        roots = _expand(item.get("paths"))
        for root in roots:
            dirs = []
            for path, size in list(_walk(root, item.get("min_age", 0), dirs)):
                if not _inside(path, root):  # nunca sai da pasta do item
                    continue
                try:
                    _remove(path)
                    freed += size
                    removed += 1
                except OSError:
                    pass  # em uso: fica para a próxima
            # pastas que ficaram vazias, das mais fundas para cima (a pasta raiz do item fica)
            for d in sorted(dirs, key=len, reverse=True):
                if _inside(d, root):
                    try:
                        os.rmdir(d)  # só remove se estiver vazia
                    except OSError:
                        pass
        for f in _expand(item.get("files")):
            if os.path.islink(f) or not os.path.isfile(f):
                continue
            try:
                size = os.path.getsize(f)
                _remove(f)
                freed += size
                removed += 1
            except OSError:
                pass
    return {"freed": freed, "files": removed, "skipped": skipped, "time": time.time()}
