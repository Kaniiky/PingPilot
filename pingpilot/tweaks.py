"""Catálogo de ajustes do Windows, com backup e restauração.

Origem de cada ajuste (campo "source"):
  WinUtil  – Chris Titus Tech, licença MIT (config/tweaks.json)
  KOALA    – KOALA Gaming Optimizer, licença MIT (koalaoptimizerps1.ps1)
  HoneCTRL – Auraside / Hone, licença GNU AGPLv3 (HoneCtrl.bat 2.7)
  PingPilot – próprio
Os valores foram reimplementados aqui; nenhum script dos projetos é executado.
"""
import json
import os
import threading

import core

DW, SZ = "DWord", "String"
MM = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
GAMES = MM + r"\Tasks\Games"
TCPIP_IF = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\{guid}"
QOS_KEY = r"SYSTEM\CurrentControlSet\Services\Tcpip\QoS"
DNSCACHE = r"SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"
# opções de economia de energia da placa de rede; só as que o driver já expõe são alteradas
NIC_POWER = ["*EEE", "EEE", "AdvancedEEE", "EnableGreenEthernet", "GigaLite", "PowerSavingMode",
             "*NicAutoPowerSaver", "ULPMode", "EnableSavePowerNow", "EnableDynamicPowerGating",
             "EnableConnectedPowerGating", "AutoPowerSaveModeEnabled", "*SelectiveSuspend"]


def _qos_apply(engine):
    if not engine.exes:
        raise RuntimeError("Adicione seus jogos em Conexões antes de ativar este ajuste.")
    lines = ["Get-NetQosPolicy -EA SilentlyContinue | Where-Object Name -like 'PingPilot-*' |"
             " Remove-NetQosPolicy -Confirm:$false"]
    for exe in engine.exes:
        name = core.ps_quote("PingPilot-" + exe)
        lines.append(f"New-NetQosPolicy -Name {name} -AppPathNameMatchCondition {core.ps_quote(exe)}"
                     " -DSCPAction 46 -NetworkProfile All | Out-Null")
    qos = core.ps_quote("HKLM:" + "\\" + QOS_KEY)
    lines.append(f"New-Item -Force {qos} | Out-Null; Set-ItemProperty {qos} 'Do not use NLA' '1'")
    return "; ".join(lines)

HIGH_PERF = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"

CATALOG = [
    # ---- sistema
    {"id": "game_mode", "group": "sistema", "icon": "gamepad", "source": "WinUtil", "recommended": True,
     "title": "Modo de Jogo do Windows",
     "desc": "Faz o Windows priorizar recursos para o jogo aberto e adiar atualizações durante a partida.",
     "warn": "Raramente causa problema; desligue se notar travadas em algum jogo específico.",
     "reg": [("HKCU", r"Software\Microsoft\GameBar", "AllowAutoGameMode", 1, DW),
             ("HKCU", r"Software\Microsoft\GameBar", "AutoGameModeEnabled", 1, DW)]},
    {"id": "game_dvr", "group": "sistema", "icon": "record", "source": "KOALA", "recommended": True,
     "title": "Desligar gravação em segundo plano",
     "desc": "Desativa o Game DVR do Xbox Game Bar, que grava os últimos minutos do jogo o tempo todo.",
     "warn": "Você usa o Win+Alt+G para gravar clipes.",
     "reg": [("HKCU", r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0, DW),
             ("HKCU", r"System\GameConfigStore", "GameDVR_Enabled", 0, DW)]},
    {"id": "mmcss", "group": "sistema", "icon": "cpu", "source": "KOALA", "recommended": True, "admin": True,
     "title": "Prioridade multimídia para jogos",
     "desc": "Sobe a prioridade de CPU e GPU que o agendador multimídia (MMCSS) dá às threads de jogos.",
     "warn": "Não há contraindicação conhecida; o efeito depende do jogo usar MMCSS.",
     "reg": [("HKLM", GAMES, "GPU Priority", 8, DW), ("HKLM", GAMES, "Priority", 6, DW),
             ("HKLM", GAMES, "Scheduling Category", "High", SZ), ("HKLM", GAMES, "SFIO Priority", "High", SZ)],
     "defaults": {"GPU Priority": 8, "Priority": 2, "Scheduling Category": "Medium", "SFIO Priority": "Normal"}},
    {"id": "responsiveness", "group": "sistema", "icon": "gauge", "source": "KOALA", "recommended": True, "admin": True,
     "title": "Menos CPU reservada a tarefas de fundo",
     "desc": "Reduz de 20% para 10% a fatia de CPU que o Windows guarda para tarefas de baixa prioridade.",
     "warn": "Você grava ou transmite áudio profissional enquanto joga.",
     "reg": [("HKLM", MM, "SystemResponsiveness", 10, DW)],
     "defaults": {"SystemResponsiveness": 20}},
    {"id": "foreground", "group": "sistema", "icon": "target", "source": "KOALA", "recommended": True, "admin": True,
     "title": "Priorizar a janela em primeiro plano",
     "desc": "Dá fatias de tempo de CPU maiores e mais curtas ao programa ativo (Win32PrioritySeparation = 38).",
     "warn": "Você roda tarefas pesadas (render, compilação) em segundo plano enquanto joga.",
     "reg": [("HKLM", r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 38, DW)],
     "defaults": {"Win32PrioritySeparation": 2}},
    {"id": "power_plan", "group": "sistema", "icon": "bolt", "source": "KOALA", "recommended": True, "admin": True,
     "title": "Plano de energia Alto desempenho",
     "desc": "Mantém o processador em frequência alta, evitando atrasos ao sair do modo de economia.",
     "warn": "Você usa notebook na bateria — gasta mais energia e esquenta mais.",
     "power": True},
    {"id": "hags", "group": "sistema", "icon": "gpu", "source": "KOALA", "admin": True, "reboot": True,
     "title": "Agendamento de GPU por hardware",
     "desc": "Deixa a própria placa de vídeo gerenciar sua fila de trabalho, o que pode reduzir a latência.",
     "warn": "Sua GPU é antiga ou você notar engasgos depois de ativar.",
     "reg": [("HKLM", r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2, DW)]},
    {"id": "mouse_accel", "group": "sistema", "icon": "mouse", "source": "WinUtil", "recommended": True,
     "title": "Desligar aceleração do mouse",
     "desc": "O cursor passa a andar sempre a mesma distância para o mesmo movimento — mira mais consistente.",
     "warn": "Você está acostumado com a aceleração (vale ao sair e entrar no Windows).",
     "reg": [("HKCU", r"Control Panel\Mouse", "MouseSpeed", "0", SZ),
             ("HKCU", r"Control Panel\Mouse", "MouseThreshold1", "0", SZ),
             ("HKCU", r"Control Panel\Mouse", "MouseThreshold2", "0", SZ)],
     "defaults": {"MouseSpeed": "1", "MouseThreshold1": "6", "MouseThreshold2": "10"}},
    {"id": "bg_apps", "group": "sistema", "icon": "apps", "source": "WinUtil",
     "title": "Bloquear apps da Store em segundo plano",
     "desc": "Impede que apps da Microsoft Store fiquem rodando escondidos.",
     "warn": "Você depende de notificações de apps da Store (ex.: WhatsApp da Store).",
     "reg": [("HKCU", r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications",
              "GlobalUserDisabled", 1, DW)]},
    # ---- rede
    {"id": "nagle", "group": "rede", "icon": "network", "source": "KOALA", "recommended": True, "admin": True,
     "reboot": True, "iface": True,
     "title": "Desligar algoritmo de Nagle",
     "desc": "Envia pacotes TCP pequenos na hora, sem esperar juntar mais dados (TcpAckFrequency e TCPNoDelay "
             "no adaptador ativo).",
     "warn": "Só ajuda jogos que usam TCP; a maioria usa UDP e não muda nada.",
     "reg": [("HKLM", TCPIP_IF, "TcpAckFrequency", 1, DW), ("HKLM", TCPIP_IF, "TCPNoDelay", 1, DW)]},
    {"id": "throttling", "group": "rede", "icon": "speed", "source": "KOALA", "recommended": True, "admin": True,
     "reboot": True,
     "title": "Desligar limitação de rede multimídia",
     "desc": "Remove o limite de pacotes por segundo que o Windows aplica enquanto toca áudio ou vídeo.",
     "warn": "Não há contraindicação conhecida.",
     "reg": [("HKLM", MM, "NetworkThrottlingIndex", 0xFFFFFFFF, DW)],
     "defaults": {"NetworkThrottlingIndex": 10}},
    {"id": "delivery_opt", "group": "rede", "icon": "upload", "source": "WinUtil", "recommended": True,
     "admin": True,
     "title": "Não enviar atualizações para outros PCs",
     "desc": "Desliga a Otimização de Entrega, que usa sua internet para mandar atualizações do Windows a outros PCs.",
     "warn": "Você tem vários PCs em casa e quer que compartilhem atualizações.",
     "reg": [("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", "DODownloadMode", 0, DW)]},
    {"id": "ipv4_pref", "group": "rede", "icon": "route", "source": "WinUtil", "admin": True, "reboot": True,
     "title": "Preferir IPv4 em vez de IPv6",
     "desc": "Quando um servidor tem os dois endereços, usa o IPv4 — às vezes a rota IPv6 da operadora é pior.",
     "warn": "Sua operadora só funciona bem em IPv6 (raro no Brasil).",
     "reg": [("HKLM", r"SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters", "DisabledComponents", 32, DW)],
     "defaults": {"DisabledComponents": 0}},
    {"id": "teredo", "group": "rede", "icon": "tunnel", "source": "WinUtil", "admin": True,
     "title": "Desligar túnel Teredo",
     "desc": "Desativa um túnel IPv6 antigo do Windows que pode adicionar latência.",
     "warn": "Você joga pelo app Xbox / Game Pass com party chat — o Xbox usa o Teredo.",
     "cmd": {"check": "(Get-NetTeredoConfiguration).Type -eq 'Disabled'",
             "apply": "netsh interface teredo set state disabled",
             "undo": "netsh interface teredo set state default"}},
    {"id": "nic_power", "group": "rede", "icon": "plug", "source": "HoneCTRL", "recommended": True, "admin": True,
     "reboot": True, "nic": True, "cable_only": True,
     "title": "Desligar economia de energia da placa de rede",
     "desc": "Desativa Energy Efficient Ethernet, Green Ethernet e similares no adaptador ativo — eles "
             "colocam a placa em repouso entre pacotes e podem somar atraso.",
     "warn": "Você usa Wi-Fi (só vale para cabo) ou precisa economizar bateria no notebook.",
     "reg": [("HKLM", "{nic}", n, "0", "Same") for n in NIC_POWER]},
    {"id": "dns_negcache", "group": "rede", "icon": "refresh", "source": "HoneCTRL", "recommended": True,
     "admin": True,
     "title": "Não guardar falhas de DNS",
     "desc": "Quando um site ou servidor falha ao resolver, o Windows tenta de novo na hora em vez de "
             "lembrar da falha por até 15 minutos.",
     "warn": "Não há contraindicação conhecida.",
     "reg": [("HKLM", DNSCACHE, "NegativeCacheTime", 0, DW), ("HKLM", DNSCACHE, "NetFailureCacheTime", 0, DW),
             ("HKLM", DNSCACHE, "NegativeSOACacheTime", 0, DW)]},
    {"id": "qos_dscp", "group": "rede", "icon": "flag", "source": "HoneCTRL", "admin": True,
     "title": "Marcar pacotes dos jogos como prioritários",
     "desc": "Cria regras de QoS (DSCP 46) para os jogos da sua lista. Roteadores com QoS por DSCP passam "
             "esses pacotes na frente de downloads e vídeos.",
     "warn": "Seu roteador não tem QoS — aí não muda nada (também não atrapalha).",
     "cmd": {"check": "@(Get-NetQosPolicy -EA SilentlyContinue | Where-Object Name -like 'PingPilot-*').Count -gt 0",
             "apply": _qos_apply,
             "undo": "Get-NetQosPolicy -EA SilentlyContinue | Where-Object Name -like 'PingPilot-*' |"
                     " Remove-NetQosPolicy -Confirm:$false"}},
    # ---- privacidade
    {"id": "activity", "group": "windows", "icon": "eye", "source": "WinUtil", "recommended": True, "admin": True,
     "title": "Desligar histórico de atividades",
     "desc": "Impede o Windows de registrar e enviar o que você faz no PC (mantém o histórico da área de transferência).",
     "warn": "Você usa a Linha do Tempo para retomar atividades em outro PC.",
     "reg": [("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "EnableActivityFeed", 0, DW),
             ("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities", 0, DW),
             ("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "UploadUserActivities", 0, DW)]},
    {"id": "consumer", "group": "windows", "icon": "store", "source": "WinUtil", "recommended": True, "admin": True,
     "title": "Bloquear apps promovidos",
     "desc": "Para de instalar sozinho jogos e apps patrocinados (Candy Crush etc.) no menu Iniciar.",
     "warn": "Não há contraindicação conhecida.",
     "reg": [("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures", 1, DW)]},
]

# Ajustes encontrados nos projetos e deixados de fora de propósito.
EXCLUDED = [
    ("Desligar mitigações Spectre/Meltdown (FeatureSettingsOverride)", "KOALA",
     "Abre uma falha de segurança séria em troca de ganho mínimo."),
    ("Desligar recuperação de driver de vídeo (TdrLevel = 0)", "KOALA",
     "Se o driver travar, o PC congela em vez de se recuperar."),
    ("Desligar C-States e estacionamento de núcleos da CPU", "KOALA",
     "Aumenta consumo e temperatura; ganho só mensurável em casos raros."),
    ("Mudar tamanho do arquivo de paginação e páginas grandes", "KOALA",
     "Pode causar falta de memória ou falhas de boot; o padrão do Windows é melhor."),
    ("Desligar compressão de memória e Prefetch", "KOALA",
     "Costuma piorar o desempenho em PCs com pouca RAM."),
    ("Desativar IPv6 por completo", "WinUtil",
     "Quebra alguns apps e serviços; preferir IPv4 resolve o mesmo problema."),
    ("Desligar autotuning de TCP e offload de tarefas", "HoneCTRL",
     "Limita a velocidade de download e joga para a CPU trabalho que a placa de rede faz melhor."),
    ("Trocar o controle de congestionamento para NewReno", "HoneCTRL",
     "O padrão do Windows (CUBIC) se recupera melhor de perda de pacotes."),
    ("NonBestEffortLimit, Psched TimerResolution e prioridade do csrss.exe", "HoneCTRL",
     "Não têm efeito comprovado nas versões atuais do Windows."),
    ("Forçar modo MSI na GPU e na placa de rede", "HoneCTRL",
     "Os drivers atuais já usam MSI quando suportam; forçar em hardware que não suporta trava o PC."),
    ("Bloquear drivers do Windows Update e remover driver de vídeo com DDU", "HoneCTRL",
     "Conflita com a busca de drivers do PingPilot e pode deixar o PC sem vídeo até reinstalar."),
    ("Apagar Prefetch e esvaziar a Lixeira na limpeza", "HoneCTRL",
     "O Prefetch acelera a abertura de programas; a Lixeira pode ter arquivos que você quer recuperar."),
    ("Remover Microsoft Edge / OneDrive", "WinUtil",
     "Não afeta jogos e pode quebrar componentes que dependem do WebView2 — inclusive este app."),
]


class TweakEngine:
    def __init__(self, backup_file, log):
        self.backup_file = backup_file
        self.log = log
        self.guid = None
        self.nic = None
        self.wireless = False
        self.exes = []
        self.lock = threading.Lock()

    # ---- backup

    def _load(self):
        try:
            with open(self.backup_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {"reg": {}, "power": None}

    def _save(self, data):
        with open(self.backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---- helpers

    def _regs(self, t):
        out = []
        for hive, path, name, value, typ in t.get("reg", []):
            if "{guid}" in path:
                if not self.guid:
                    continue
                path = path.replace("{guid}", self.guid)
            if "{nic}" in path:
                if not self.nic:
                    continue
                path = path.replace("{nic}", self.nic)
            if typ == "Same":
                cur = core.reg_get(hive, path, name)
                if cur is None:
                    continue
                typ = cur["type"]
                value = str(value) if typ == core.winreg.REG_SZ else int(value)
            out.append((hive, path, name, value, typ))
        return out

    def available(self, t):
        if t.get("iface") and not self.guid:
            return False
        if t.get("cable_only") and self.wireless:
            return False
        if t.get("nic") and not self._regs(t):
            return False
        return True

    def state(self, t):
        if t.get("power"):
            _, out = core.run(["powercfg", "/getactivescheme"])
            return HIGH_PERF in out.lower()
        if "cmd" in t:
            _, out = core.ps(self._cmd(t, "check"))
            return out.strip().endswith("True")
        regs = self._regs(t)
        if not regs:
            return False
        for hive, path, name, value, _ in regs:
            cur = core.reg_get(hive, path, name)
            if cur is None or str(cur["value"]) != str(value):
                return False
        return True

    def _cmd(self, t, which):
        c = t["cmd"][which]
        return c(self) if callable(c) else c

    def listing(self, admin):
        items = []
        for t in CATALOG:
            available = self.available(t)
            items.append({k: t.get(k) for k in ("id", "group", "icon", "source", "title", "desc", "warn")}
                         | {"recommended": bool(t.get("recommended")), "admin": bool(t.get("admin")),
                            "reboot": bool(t.get("reboot")), "available": available,
                            "locked": bool(t.get("admin")) and not admin,
                            "on": self.state(t) if available else False})
        return items

    # ---- aplicar / desfazer

    def set(self, tid, on):
        t = next((x for x in CATALOG if x["id"] == tid), None)
        if not t:
            raise ValueError("ajuste desconhecido")
        with self.lock:
            data = self._load()
            if t.get("power"):
                self._power(data, on)
            elif "cmd" in t:
                code, out = core.ps(self._cmd(t, "apply" if on else "undo"))
                if code != 0:
                    raise RuntimeError(out.strip() or "falha no comando")
            for hive, path, name, value, typ in self._regs(t):
                key = f"{hive}|{path}|{name}"
                if on:
                    if key not in data["reg"]:
                        data["reg"][key] = core.reg_get(hive, path, name)
                        self._save(data)
                    core.reg_set(hive, path, name, value, typ if isinstance(typ, int) else core.REG_TYPES[typ])
                else:
                    # sem backup (já estava assim antes do app): volta ao padrão do Windows
                    default = t.get("defaults", {}).get(name)
                    original = data["reg"].pop(key, None if default is None else
                                               {"value": default, "type": typ if isinstance(typ, int) else core.REG_TYPES[typ]})
                    if original is None:
                        core.reg_delete(hive, path, name)
                    else:
                        core.reg_set(hive, path, name, original["value"], original["type"])
            self._save(data)
        self.log(("Ativado: " if on else "Desativado: ") + t["title"])
        return self.state(t)

    def _power(self, data, on):
        if on:
            _, out = core.run(["powercfg", "/getactivescheme"])
            current = next((w for w in out.split() if w.count("-") == 4), None)
            if current and current.lower() != HIGH_PERF and not data.get("power"):
                data["power"] = current
            code, _ = core.run(["powercfg", "/setactive", HIGH_PERF])
            if code != 0:
                core.run(["powercfg", "-duplicatescheme", HIGH_PERF, HIGH_PERF])
                code, out = core.run(["powercfg", "/setactive", HIGH_PERF])
                if code != 0:
                    raise RuntimeError("plano Alto desempenho indisponível neste PC")
        else:
            previous = data.pop("power", None) or "381b4222-f694-41f0-9685-ff5bb260df2e"
            core.run(["powercfg", "/setactive", previous])

    def restore_all(self):
        restored = 0
        for t in CATALOG:
            try:
                if self.state(t):
                    self.set(t["id"], False)
                    restored += 1
            except Exception as e:
                self.log(f"Falha ao restaurar {t['title']}: {e}")
        with self.lock:
            data = self._load()
            for key, original in list(data["reg"].items()):
                hive, path, name = key.split("|", 2)
                if original is None:
                    core.reg_delete(hive, path, name)
                else:
                    core.reg_set(hive, path, name, original["value"], original["type"])
                data["reg"].pop(key)
            self._save(data)
        return restored
