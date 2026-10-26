"""Cria (ou atualiza) a Release do GitHub para a versão atual e anexa os arquivos de compilado/.

    python build/publish_release.py

Usa o login do GitHub que o Git já tem salvo (Git Credential Manager) — o mesmo do `git push`.
A credencial nunca é impressa nem gravada em arquivo.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "compilado")


def git(*args, input_text=None):
    r = subprocess.run(["git", *args], cwd=ROOT, input=input_text, capture_output=True, text=True)
    return r.stdout.strip()


def credential():
    out = git("credential", "fill", input_text="protocol=https\nhost=github.com\n\n")
    fields = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
    if not fields.get("password"):
        sys.exit("Sem login do GitHub salvo no Git. Faça um `git push` primeiro.")
    return fields["password"]


def api(method, url, token, body=None, data=None, content_type="application/json"):
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "PingPilot-release"}
    if body is not None:
        data = json.dumps(body).encode()
    if data is not None:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:  # nosec B310 - só https da API do GitHub
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"GitHub respondeu {e.code} em {method} {url.split('?')[0]}: {e.read().decode()[:300]}")


def main():
    version = re.search(r'^VERSION = "(.+)"', open(os.path.join(ROOT, "pingpilot", "app.py"), encoding="utf-8").read(), re.M)[1]
    tag = f"v{version}"
    remote = git("remote", "get-url", "origin")
    repo = re.search(r"github\.com[/:](.+?)(?:\.git)?$", remote)[1]
    assets = [f"PingPilot-{version}-windows.exe", f"PingPilot-{version}-windows.zip", "SHA256SUMS.txt"]
    for a in assets:
        if not os.path.isfile(os.path.join(OUT, a)):
            sys.exit(f"Falta {a} em compilado/ — rode build/compilar.ps1 antes.")
    notes = open(os.path.join(OUT, "RELEASE_NOTES.md"), encoding="utf-8").read()
    token = credential()
    base = f"https://api.github.com/repos/{repo}"

    existing = [r for r in api("GET", f"{base}/releases?per_page=100", token) if r["tag_name"] == tag]
    if existing:
        release = api("PATCH", f"{base}/releases/{existing[0]['id']}", token,
                      {"name": f"PingPilot {version}", "body": notes, "draft": False})
        print(f"Release {tag} atualizada")
    else:
        release = api("POST", f"{base}/releases", token, {"tag_name": tag, "name": f"PingPilot {version}",
                                                          "body": notes, "draft": False, "prerelease": False})
        print(f"Release {tag} criada")

    current = {a["name"]: a["id"] for a in release.get("assets", [])}
    upload = release["upload_url"].split("{")[0]
    for name in assets:
        if name in current:  # substitui arquivo antigo de mesmo nome
            api("DELETE", f"{base}/releases/assets/{current[name]}", token)
        path = os.path.join(OUT, name)
        ctype = "text/plain" if name.endswith(".txt") else "application/octet-stream"
        with open(path, "rb") as f:
            asset = api("POST", f"{upload}?name={name}", token, data=f.read(), content_type=ctype)
        print(f"  enviado {name} ({asset['size'] / 1e6:.1f} MB)")
    print(release["html_url"])


if __name__ == "__main__":
    main()
