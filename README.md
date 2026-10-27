<p align="center"><img src="build/pingpilot.png" width="96" alt="PingPilot logo"></p>

<h1 align="center">PingPilot</h1>

<p align="center">
  A free, open-source network and PC optimizer for gamers on Windows.<br>
  Think of ExitLag's interface, but everything runs locally on your PC — no accounts, no servers, no subscription.
</p>

---

## Why

Paid "anti-lag" apps bundle two things: a global relay network (which genuinely needs servers and money) and
a lot of **local** diagnostics and Windows tweaks (which don't). PingPilot is the second half, free and
open: it shows you *where* your lag comes from and fixes what can be fixed on your own machine.

It is a non-profit hobby project. Take it, fork it, change it — that's the point.

## Features

- **Connections** — add your games (all of a game's executables are grouped automatically). PingPilot raises
  their CPU priority when they open, measures the ping to the game server, traces the route hop by hop and
  records a summary of each match.
- **Network analyzer** — real-time ping/jitter/loss to your router, Cloudflare/Google and AWS; a diagnosis that
  tells you whether the problem is your Wi-Fi, your ISP or the route; a speed test with bufferbloat grade; and a
  list of every device on your network.
- **PC Boost** — 19 Windows tweaks curated from WinUtil, KOALA and HoneCTRL, each one explained, reversible and
  backed up. Tweaks that are risky (e.g. disabling Spectre mitigations) are deliberately left out.
- **DNS Optimizer** — benchmarks 10 public DNS providers plus your own, and can switch to the fastest one
  automatically (never during a match).
- **Cleaner** — frees disk space from temp files, update caches, browser caches (never cookies or passwords),
  shader caches and more. Analyze first, choose what goes. Plus RAM standby cleanup with an automatic routine.
- **Multi Internet** — two connections at once (cable + Wi-Fi or phone): keeps your main one first and fails over to
  the backup when its internet drops, then switches back.
- **Traffic limiter** — caps the upload of cloud-sync and torrent apps so they don't flood your connection.
- **Drivers** — finds newer drivers on the official Windows Update catalog and installs them.
- **Wi-Fi optimizer** — stops Windows from scanning for networks mid-match (the cause of 100 ms+ spikes on laptops).
- **Quality of life** — tray icon, notification center, English / Português / Español, 7 themes,
  crash logs you can export with one click.

## What it does *not* do

PingPilot does not change the route your traffic takes across the internet — that requires relay servers,
which is exactly what paid services sell. For the same reason Multi Internet does not add up the speed of two
connections or duplicate packets, and the traffic limiter only limits upload (download limiting needs a network
driver). A free "smart route" (using Cloudflare WARP) is being explored for 2.0.

## Download

Get the latest release from [Releases](../../releases): download **`PingPilot-x.y.z-windows.exe`** and run it
(or the `.zip`, which has the same `.exe` plus README, LICENSE and CREDITS).

- Windows 10 or 11, 64-bit, with [Microsoft Edge WebView2](https://go.microsoft.com/fwlink/p/?LinkId=2124703)
  (already included in Windows 11).
- It asks for administrator rights — Windows tweaks, DNS changes and process priority need them.
- The executable is not code-signed, so SmartScreen will warn you ("More info" → "Run anyway").
  Each release ships a `SHA256SUMS.txt` so you can check your download.
- Nothing changes until you turn it on, and *Settings → Undo all* restores every original value.

## Run from source

```powershell
git clone https://github.com/<your-user>/PingPilot.git
cd PingPilot
python -m pip install -r requirements.txt
python pingpilot/app.py              # opens the app (asks for admin)
python pingpilot/app.py --browser    # dev mode: UI at http://127.0.0.1:8765, no admin
```

Python 3.12 on Windows. The dev mode is handy for UI work; it only listens on `127.0.0.1` and protects its API
with a per-run token.

## Build a release

```powershell
python -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File build\compilar.ps1
```

The script runs the **security battery** first and refuses to build if anything fails, opens the app once to
check that the UI and the Python bridge work, builds a single `PingPilot.exe` with PyInstaller, and writes the
release assets to `compilado/`: the standalone `.exe`, the `.zip` and `SHA256SUMS.txt`.

## Security

Run `python security/check.py` before every release (the build does it for you). It checks static analysis
(bandit), known vulnerabilities in dependencies (pip-audit), secrets and personal data in tracked files,
PowerShell command injection, unescaped HTML in the UI, the API surface exposed to the page, the
Content-Security-Policy, the dev server and the release package. See [SECURITY.md](SECURITY.md).

## Project layout

```
pingpilot/      the app — app.py (API + window), core.py, winproc.py, tweaks.py, drivers.py, speedtest.py,
                cleaner.py, multinet.py, limiter.py, ui/
build/          build script, icon, translations generator (make_i18n.py), real-window test
security/       security battery and its reviewed allowlists
```

Translations: the UI is written in Portuguese and translated at runtime. Add or fix strings in
`build/make_i18n.py`, run it, and use `python build/extract_strings.py --missing` to find untranslated text.

## Credits

Built on ideas from [WinUtil](https://github.com/ChrisTitusTech/winutil), [KOALA Gaming Optimizer](https://github.com/koalaaufpillen/koalaoptimizer),
[WLANOptimizer](https://github.com/catid/WLANOptimizer) and HoneCTRL — see [CREDITS.md](CREDITS.md).

## License

[MIT](LICENSE) — do whatever you want with it; just keep the license notice.
