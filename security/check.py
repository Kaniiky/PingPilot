"""Bateria de segurança do PingPilot — rode antes de TODA versão:

    python security/check.py            (sai com código 1 se algo bloquear o lançamento)

O build (build/compilar.ps1) roda esta bateria primeiro e não compila se ela falhar.

Verificações:
  1. bandit       análise estática do Python (achados HIGH bloqueiam)
  2. pip-audit    vulnerabilidades conhecidas nas dependências fixadas em requirements*.txt
  3. dados        segredos, chaves e dados pessoais nos arquivos que vão para o Git
  4. powershell   todo valor variável montado em comando PowerShell passa por ps_quote()/int()
  5. xss          interpolações no HTML gerado pelo JS: ou passam por esc(), ou foram revisadas
  6. api          métodos expostos à interface (pywebview e HTTP) só mudam com revisão
  7. html         CSP presente, sem scripts inline, sem recursos externos
  8. servidor     modo navegador só escuta em 127.0.0.1 e exige token + Host local
  9. pacote       o .zip de lançamento não leva configuração, logs ou backup de ninguém

As listas revisadas ficam em security/allowlists/. Quando um item novo aparecer, revise o código
e, se for seguro, rode com --update para regravar a lista — e explique no commit por que é seguro.
"""
import ast
import fnmatch
import json
import os
import re
import subprocess
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "pingpilot")
ALLOW = os.path.join(ROOT, "security", "allowlists")
UPDATE = "--update" in sys.argv
results = []  # (nome, ok, detalhes)


def report(name, ok, details=()):
    results.append((name, ok, list(details)))


def allowlist(name, found):
    """Compara o que foi encontrado com a lista revisada; itens novos reprovam (ou entram, com --update)."""
    path = os.path.join(ALLOW, name)
    reviewed = set()
    if os.path.exists(path):
        reviewed = {l.rstrip("\n") for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")}
    found = set(found)
    if UPDATE:
        os.makedirs(ALLOW, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# Revisado manualmente. Gerado por security/check.py --update\n")
            f.writelines(x + "\n" for x in sorted(found))
        return [], sorted(reviewed - found)
    return sorted(found - reviewed), sorted(reviewed - found)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    return r.returncode, r.stdout, r.stderr


# ---------------------------------------------------------------- 1. bandit

def check_bandit():
    code, out, err = run([sys.executable, "-m", "bandit", "-r", SRC, "-f", "json", "-q",
                          "-c", os.path.join(ROOT, "security", "bandit.yaml")])
    try:
        data = json.loads(out)
    except ValueError:
        return report("bandit", False, [f"bandit não rodou: {err.strip()[:300]}"])
    issues = data.get("results", [])
    high = [i for i in issues if i["issue_severity"] == "HIGH"]
    lines = [f"{os.path.relpath(i['filename'], ROOT)}:{i['line_number']} [{i['issue_severity']}/{i['issue_confidence']}] "
             f"{i['test_id']} {i['issue_text']}" for i in sorted(issues, key=lambda i: i["issue_severity"])]
    report("bandit (análise estática)", not high,
           [f"{len(high)} HIGH, {len(issues) - len(high)} MEDIUM/LOW (não bloqueiam; revise)"] + lines[:25])


# ---------------------------------------------------------------- 2. pip-audit

def check_deps():
    details, ok = [], True
    for req in ("requirements.txt", "requirements-dev.txt"):
        code, out, err = run([sys.executable, "-m", "pip_audit", "-r", req, "--progress-spinner", "off", "-f", "json"])
        try:
            deps = json.loads(out).get("dependencies", [])
        except ValueError:
            ok = False
            details.append(f"{req}: pip-audit não rodou ({err.strip()[:200]})")
            continue
        vulns = [(d["name"], d["version"], v["id"]) for d in deps for v in d.get("vulns", [])]
        ok = ok and not vulns
        details.append(f"{req}: {len(deps)} pacotes, {len(vulns)} vulnerabilidade(s)")
        details += [f"   {n} {v}: {i}" for n, v, i in vulns]
    report("pip-audit (dependências)", ok, details)


# ---------------------------------------------------------------- 3. segredos e dados pessoais

def tracked_files():
    """Arquivos que vão para o Git (respeita o .gitignore)."""
    code, out, _ = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"])
    if code == 0 and out.strip():
        return [f for f in out.splitlines() if os.path.isfile(os.path.join(ROOT, f))]
    ignored = ["referencias/*", "compilado/*", "build/work/*", "build/teste/*", "*/logs/*", "*.pyc", ".git/*"]
    files = []
    for dp, dn, fn in os.walk(ROOT):
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), ROOT).replace("\\", "/")
            if not any(fnmatch.fnmatch(rel, p) for p in ignored):
                files.append(rel)
    return files


SECRET_PATTERNS = {
    "chave privada": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "token do GitHub": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "chave da AWS": r"\bAKIA[0-9A-Z]{16}\b",
    "chave de API genérica": r"(?i)\b(api[_-]?key|secret|password|senha)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]",
    "pasta de usuário do Windows": r"(?i)C:[\\/]+Users[\\/]+(?!Public|Default|<|%|\{|\$|USER|USERNAME|voce|you)[A-Za-z0-9._ -]+[\\/]",
    "e-mail": r"\b[A-Za-z0-9._%+-]+@(?!example\.|users\.noreply\.github\.com|anthropic\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "IP da rede local": r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
    "endereço MAC": r"\b[0-9A-Fa-f]{2}(?:[-:][0-9A-Fa-f]{2}){5}\b",
    "nome de PC": r"\bDESKTOP-[A-Z0-9]{5,}\b",
}


def check_secrets():
    personal = []
    extra = os.path.join(ROOT, "security", "personal.txt")  # opcional e fora do Git: nomes, e-mails seus etc.
    if os.path.exists(extra):
        personal = [l.strip() for l in open(extra, encoding="utf-8") if l.strip() and not l.startswith("#")]
    hits = []
    for rel in tracked_files():
        if rel.endswith((".png", ".ico", ".exe", ".zip", ".pyc")) or rel.startswith("security/allowlists/"):
            continue
        try:
            text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for label, rx in SECRET_PATTERNS.items():
                if re.search(rx, line):
                    hits.append(f"{rel}:{n} {label}")
            for term in personal:
                if term.lower() in line.lower():
                    hits.append(f"{rel}:{n} termo pessoal ({term[:3]}…)")
    new, _ = allowlist("secrets.txt", hits)
    report("segredos e dados pessoais", not new, [f"{len(hits)} ocorrência(s), {len(new)} não revisada(s)"] + new[:30])


# ---------------------------------------------------------------- 4. injeção em PowerShell

SAFE_PS = {"ps_quote", "int", "core.ps_quote"}


def check_powershell():
    found = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(SRC, f), encoding="utf-8").read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = ast.unparse(node.func)
            if fn.split(".")[-1] not in ("ps", "ps_json") or not node.args:
                continue
            for part in ast.walk(node.args[0]):
                if isinstance(part, ast.FormattedValue):
                    expr = ast.unparse(part.value)
                    call = part.value.func if isinstance(part.value, ast.Call) else None
                    if call is not None and ast.unparse(call) in SAFE_PS:
                        continue
                    found.append(f"{f}: {expr}")
    new, gone = allowlist("powershell.txt", found)
    report("injeção em comandos PowerShell", not new,
           [f"{len(found)} valor(es) sem ps_quote()/int(), {len(new)} não revisado(s)"] + [f"novo: {x}" for x in new])


# ---------------------------------------------------------------- 5. XSS no HTML montado pelo JavaScript

SAFE_JS = re.compile(r"^(esc|svg|ms|pct|fmtDate|fmtSize|duration|gameIcon|dnsRow|ago)\(")


def template_exprs(src):
    """${...} de nível mais alto dentro de template strings que contêm HTML."""
    out, i = [], 0
    while True:
        i = src.find("`", i)
        if i < 0:
            return out
        j, depth, exprs, start = i + 1, 0, [], None
        while j < len(src):
            c = src[j]
            if depth == 0 and c == "`":
                break
            if src.startswith("${", j):
                if depth == 0:
                    start = j + 2
                depth += 1
                j += 2
                continue
            if c == "}" and depth:
                depth -= 1
                if depth == 0:
                    exprs.append(src[start:j])
            j += 1
        body = src[i:j]
        if "<" in body:
            out += exprs
        i = j + 1


def check_xss():
    src = open(os.path.join(SRC, "ui", "app.js"), encoding="utf-8").read()
    found = set()
    for e in template_exprs(src):
        e = " ".join(e.split())
        if SAFE_JS.match(e) or re.fullmatch(r"[\"'][^\"']*[\"']", e):
            continue
        found.add(e)
    new, gone = allowlist("xss.txt", found)
    report("XSS na interface (innerHTML)", not new,
           [f"{len(found)} interpolação(ões) sem esc(), {len(new)} não revisada(s)"] + [f"novo: ${{{x}}}" for x in new])


# ---------------------------------------------------------------- 6. API exposta à interface

def check_api():
    sys.path.insert(0, SRC)
    tree = ast.parse(open(os.path.join(SRC, "app.py"), encoding="utf-8").read())
    api = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Api")
    methods = [n.name for n in api.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
    new, gone = allowlist("api.txt", methods)
    report("API exposta à interface", not new,
           [f"{len(methods)} método(s) públicos; qualquer script na página pode chamá-los"] +
           [f"novo (revise validação de argumentos): {x}" for x in new])


# ---------------------------------------------------------------- 7. HTML

def check_html():
    html = open(os.path.join(SRC, "ui", "index.html"), encoding="utf-8").read()
    problems = []
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)"', html)
    if not csp:
        problems.append("sem Content-Security-Policy")
    elif "script-src 'self'" not in csp.group(1) or "unsafe-inline" in csp.group(1).split("script-src")[1].split(";")[0]:
        problems.append("CSP permite script inline")
    if re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html):
        problems.append("script inline no index.html (bloqueado pela CSP)")
    if re.search(r'\son[a-z]+\s*=\s*"', html):
        problems.append("atributo de evento inline (onclick=…)")
    for m in re.finditer(r'(?:src|href)="(https?:)?//', html):
        problems.append(f"recurso externo: {html[m.start():m.start() + 60]}")
    js = open(os.path.join(SRC, "ui", "app.js"), encoding="utf-8").read()
    for bad in ("eval(", "new Function(", "document.write("):
        if bad in js:
            problems.append(f"app.js usa {bad}")
    report("HTML, CSP e JavaScript perigoso", not problems, problems)


# ---------------------------------------------------------------- 8. servidor do modo navegador

def check_server():
    src = open(os.path.join(SRC, "app.py"), encoding="utf-8").read()
    problems = []
    if 'ThreadingHTTPServer(("127.0.0.1"' not in src:
        problems.append("servidor não está preso a 127.0.0.1")
    if "X-PP-Token" not in src or "compare_digest" not in src:
        problems.append("API HTTP sem token (qualquer site aberto no navegador poderia chamá-la)")
    if "_host_ok" not in src:
        problems.append("API HTTP sem conferência do cabeçalho Host (DNS rebinding)")
    report("servidor do modo navegador", not problems, problems)


# ---------------------------------------------------------------- 9. pacote de lançamento

def check_package():
    out = os.path.join(ROOT, "compilado")
    zips = [f for f in os.listdir(out) if f.endswith(".zip")] if os.path.isdir(out) else []
    if not zips:
        return report("pacote de lançamento", True, ["nenhum .zip em compilado/ ainda (roda de novo depois do build)"])
    problems = []
    for z in zips:
        for n in zipfile.ZipFile(os.path.join(out, z)).namelist():
            low = n.lower()
            if any(k in low for k in ("config.json", "backup.json", "/logs/", ".log", "personal", ".webview")):
                problems.append(f"{z}: {n}")
    report("pacote de lançamento", not problems, [f"{len(zips)} pacote(s) conferidos"] + problems)


def main():
    checks = (check_bandit, check_deps, check_secrets, check_powershell, check_xss, check_api, check_html,
              check_server, check_package)
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None  # ex.: --only package
    for check in checks:
        if only and check.__name__ != f"check_{only}":
            continue
        try:
            check()
        except Exception as e:  # uma verificação quebrada também reprova
            report(check.__name__, False, [f"erro ao rodar: {e!r}"])
    print("\n=== Bateria de segurança do PingPilot ===\n")
    for name, ok, details in results:
        print(f"[{'OK ' if ok else 'FALHOU'}] {name}")
        for d in details:
            print(f"        {d}")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} verificações passaram." +
          ("" if not failed else "  NÃO LANCE esta versão."))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
