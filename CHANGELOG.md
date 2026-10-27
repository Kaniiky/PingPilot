# Changelog

## 1.1.0

- **Speed test** (Network analyzer): download, upload, idle ping/jitter and ping under load (bufferbloat grade A+–F),
  on [M-Lab](https://www.measurementlab.net/) (NDT7, the same servers as Google's speed test, with servers in Brazil),
  public [LibreSpeed](https://github.com/librespeed/speedtest) servers, or your own LibreSpeed server; history of the
  last 30 tests.
  Warns before testing during a match or with a VPN on.
- **RAM cleanup** redesigned: memory bar (in use / standby cache / free), "Needs cleanup" status, last cleanup,
  and a routine that cleans automatically when a game opens or when memory needs it (at most once per interval).
- **Cleaner** (new page): CCleaner/BleachBit-style disk cleanup — Windows temp, Windows Update and Delivery
  Optimization caches, thumbnails, error reports and dumps, Recycle Bin, browser caches (never cookies, history or
  passwords), Steam, Discord and shader caches. Analyze first, pick what to delete, see what was freed. Never
  follows links/junctions, keeps files from the last 24 h in Temp, skips items whose program is open.
- **Multi Internet** (new page): use two connections (cable + Wi-Fi, cable + USB-tethered phone). Priority mode
  keeps the main one first; automatic failover tests the main connection every 5 s and switches to the backup when
  its internet goes down (even with the cable still plugged in), switching back after 30 s stable. Original
  Windows metrics are backed up and restored.
- **Traffic limiter** (PC Boost): cap the upload of programs like OneDrive or torrent clients with Windows QoS
  policies, the most common cause of high ping at home.
- New notification options for automatic RAM cleanup and Multi Internet switches.

## 1.0.0 — first public release

- Connections: games grouped by install folder (all executables together), HD icons, CPU priority on launch,
  game-server ping, route trace, per-match summary.
- Network analyzer: real-time monitor (router / internet / AWS), ping test with diagnosis, LAN device list.
- PC Boost: 19 reversible Windows tweaks from WinUtil, KOALA and HoneCTRL, with backup and one-click undo.
- DNS Optimizer: 10 providers + custom, optional automatic switch (never during a match).
- Drivers from Windows Update; Wi-Fi optimizer; RAM standby cleanup; network reset.
- Notification center, tray icon, English / Português / Español, 7 themes, exportable crash logs.
- Security battery (`security/check.py`) run by the build; CSP, validated API, hardened dev server.
