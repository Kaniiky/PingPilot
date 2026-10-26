"""Atualização de drivers pelo catálogo oficial do Windows Update.

Programas como o Driver Booster usam um banco de drivers próprio. Aqui a fonte é
o próprio Windows Update (API Microsoft.Update.Session), que só entrega drivers
assinados e testados pela Microsoft para o hardware deste PC.
"""
import core

VENDOR_PAGES = {
    "nvidia": ("NVIDIA", "https://www.nvidia.com/pt-br/drivers/"),
    "amd": ("AMD", "https://www.amd.com/pt/support/download/drivers.html"),
    "advanced micro devices": ("AMD", "https://www.amd.com/pt/support/download/drivers.html"),
    "intel": ("Intel", "https://www.intel.com.br/content/www/br/pt/support/detect.html"),
}

CLASS_NAMES = {
    "DISPLAY": "Vídeo", "NET": "Rede", "MEDIA": "Áudio", "BLUETOOTH": "Bluetooth", "USB": "USB",
    "HIDCLASS": "Dispositivos de entrada", "MOUSE": "Mouse", "KEYBOARD": "Teclado", "SYSTEM": "Sistema",
    "PROCESSOR": "Processador", "DISKDRIVE": "Discos", "SCSIADAPTER": "Armazenamento", "HDC": "Armazenamento",
    "MONITOR": "Monitor", "AUDIOENDPOINT": "Áudio", "CAMERA": "Câmera", "PRINTER": "Impressora",
}

_SEARCH = (
    "$s = New-Object -ComObject Microsoft.Update.Session; $q = $s.CreateUpdateSearcher();"
    "$q.ServerSelection = 2; $q.Online = $true;"
    "$r = $q.Search(\"IsInstalled=0 and Type='Driver'\");"
    "foreach ($u in $r.Updates) { [pscustomobject]@{ Id=$u.Identity.UpdateID; Title=$u.Title;"
    " Class=$u.DriverClass; Maker=$u.DriverManufacturer; Model=$u.DriverModel;"
    " Date=$u.DriverVerDate.ToString('yyyy-MM-dd'); HardwareId=$u.DriverHardwareID;"
    " Size=[int64]$u.MaxDownloadSize } }"
)


def installed():
    rows = core.ps_json(
        "Get-CimInstance Win32_PnPSignedDriver | Where-Object { $_.DeviceName -and $_.DriverVersion } |"
        " ForEach-Object { [pscustomobject]@{ Name=$_.DeviceName; Version=$_.DriverVersion;"
        " Date=$(if ($_.DriverDate) { $_.DriverDate.ToString('yyyy-MM-dd') } else { '' });"
        " Maker=$_.Manufacturer; Class=[string]$_.DeviceClass; HardwareId=[string]$_.HardWareID } }",
        timeout=120)
    for r in rows:
        r["ClassName"] = CLASS_NAMES.get((r.get("Class") or "").upper(), r.get("Class") or "Outros")
        maker = (r.get("Maker") or "").lower()
        if (r.get("Class") or "").upper() == "DISPLAY":
            page = next((v for k, v in VENDOR_PAGES.items() if k in maker or k in r["Name"].lower()), None)
            r["Vendor"] = {"name": page[0], "url": page[1]} if page else None
    rows.sort(key=lambda r: (r["ClassName"], r["Name"]))
    return rows


def available():
    """Drivers mais novos oferecidos pelo Windows Update (leva de 20 s a 2 min)."""
    return core.ps_json(_SEARCH, timeout=300)


def match(installed_rows, updates):
    """Liga cada atualização ao dispositivo instalado pelo Hardware ID."""
    for u in updates:
        hw = (u.get("HardwareId") or "").lower()
        dev = next((d for d in installed_rows if hw and (d.get("HardwareId") or "").lower().startswith(hw)), None)
        u["Device"] = dev["Name"] if dev else (u.get("Model") or u["Title"])
        u["CurrentDate"] = dev["Date"] if dev else ""
        u["CurrentVersion"] = dev["Version"] if dev else ""
    return updates


def install(update_ids, log):
    ids = [i for i in update_ids if all(c in "0123456789abcdef-" for c in i.lower())]
    if not ids:
        raise ValueError("nenhum driver selecionado")
    criteria = " or ".join(f"UpdateID='{i}'" for i in ids)
    log(f"Baixando {len(ids)} driver(s) do Windows Update…")
    rows = core.ps_json(
        "$s = New-Object -ComObject Microsoft.Update.Session; $q = $s.CreateUpdateSearcher();"
        f"$q.ServerSelection = 2; $r = $q.Search(\"IsInstalled=0 and Type='Driver' and ({criteria})\");"
        "$c = New-Object -ComObject Microsoft.Update.UpdateColl;"
        "foreach ($u in $r.Updates) { if (-not $u.EulaAccepted) { $u.AcceptEula() }; [void]$c.Add($u) };"
        "if ($c.Count -eq 0) { return [pscustomobject]@{ Error='Nenhum dos drivers está mais disponível' } };"
        "$d = $s.CreateUpdateDownloader(); $d.Updates = $c; [void]$d.Download();"
        "$i = $s.CreateUpdateInstaller(); $i.Updates = $c; $res = $i.Install();"
        "for ($n = 0; $n -lt $c.Count; $n++) { [pscustomobject]@{ Title=$c.Item($n).Title;"
        " Code=$res.GetUpdateResult($n).ResultCode; Reboot=$res.RebootRequired } }",
        timeout=1800)
    if rows and rows[0].get("Error"):
        raise RuntimeError(rows[0]["Error"])
    # ResultCode: 2 = sucesso, 3 = sucesso com erros, 4 = falhou, 5 = cancelado
    results = [{"title": r["Title"], "ok": r["Code"] in (2, 3), "reboot": bool(r.get("Reboot"))} for r in rows]
    for r in results:
        log(("Driver instalado: " if r["ok"] else "Falha ao instalar: ") + r["title"])
    return results
