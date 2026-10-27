# Security

PingPilot runs as administrator and changes Windows settings, so a bug in it can do real damage.
This file explains how the app is protected and how releases are checked.

## Reporting a vulnerability

Please open a [GitHub security advisory](../../security/advisories/new) (private) instead of a public issue.
Include the version (Settings → About), what you did, and the exported logs if relevant
(Settings → *Export logs to send*).

## How the app is protected

- **The UI is local-only.** `index.html` has a strict Content-Security-Policy (`script-src 'self'`, no inline
  scripts, no external resources). Even if some text from outside (a device name on your network, a process name,
  data from GitHub) slipped past escaping, injected HTML could not run script.
- **Everything shown from outside is escaped** with `esc()` before it reaches `innerHTML`.
- **The page can only call the methods it needs.** Internal helpers are private; every public API method
  validates its arguments (IP addresses, hostnames, MAC addresses, executable paths, enum values).
- **No shell.** Windows tools are started with argument lists. Values that go into PowerShell commands pass
  through `ps_quote()` or are integers / validated constants.
- **Dev server (`--browser`)** listens on `127.0.0.1` only, rejects foreign `Host` headers (DNS rebinding) and
  requires a per-run token on every API call (so a website open in your browser cannot drive it).
- **Network access** is limited to: ping/DNS/TCP probes you start, Windows Update (drivers), HTTPS calls to
  `api.github.com` / `raw.githubusercontent.com` to check the source projects, the speed test (only when
  you click "Start test": M-Lab's locator at `locate.measurementlab.net` and the M-Lab server it returns, or the
  public LibreSpeed server list at `librespeed.org` and the server you pick). M-Lab publishes test results, including
  the IP address, as open data; the app says so next to the server choice, and
  Multi Internet's TCP probes to 1.1.1.1 / 8.8.8.8 / 9.9.9.9 on port 443 (no data is sent).
- **Cleaner** only deletes inside a fixed list of cache folders; it never follows symbolic links or junctions,
  never touches its own files, and browser cleanup is limited to cache folders (no cookies, history or passwords).
- **Everything reversible.** Every registry change is backed up before it is made.

## The security battery

```powershell
python -m pip install -r requirements-dev.txt
python security/check.py
```

| Check | Fails the release when |
|---|---|
| bandit | any HIGH-severity finding in `pingpilot/` |
| pip-audit | any known vulnerability in `requirements*.txt` |
| secrets & personal data | a key, token, e-mail, user folder path, LAN IP, MAC address or PC name appears in a tracked file |
| PowerShell injection | a variable reaches a PowerShell command without `ps_quote()`/`int()` and wasn't reviewed |
| XSS | an HTML template interpolates a value without `esc()` and it wasn't reviewed |
| API surface | a new public method appears on the API without review |
| HTML / CSP | the CSP is missing or weakened, or there is inline script, `eval`, or an external resource |
| dev server | it stops binding to `127.0.0.1` or loses the token / Host checks |
| release package | the zip contains a config, backup, log or browser cache |

Items that were reviewed and judged safe live in `security/allowlists/`. When a new one shows up, review the code;
if it is safe, run `python security/check.py --update` and explain why in the commit message.

Local, never-committed extras: put your own name, e-mail or PC name in `security/personal.txt` (git-ignored) and
the battery will also look for them.
