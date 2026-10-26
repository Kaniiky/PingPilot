"""Lista os textos em português da interface e do backend, para montar os dicionários de tradução.

    python build/extract_strings.py            -> build/strings_pt.json (todas as chaves)
    python build/extract_strings.py --missing  -> mostra as chaves que faltam em i18n-en.js / i18n-es.js
"""
import ast
import html.parser
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pingpilot")
LETTER = re.compile(r"[A-Za-zÀ-ÿ]")
CODEISH = re.compile(r"^[a-z0-9_\-.#\[\]=:>\s\"'()]+$")  # seletores, classes, ids


def keep(s):
    s = re.sub(r"\s+", " ", s).strip()
    if not s or not LETTER.search(s) or len(s) < 2:
        return None
    if CODEISH.match(s) and " " not in s.strip() and not re.search(r"[À-ÿ]", s):
        return None  # palavra solta em minúsculas sem acento: provavelmente código
    if re.fullmatch(r"[\w\-]+\.(exe|png|json|js|css|py)", s):
        return None
    return s


class HTMLTexts(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.skip = set(), 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        for k, v in attrs:
            if k in ("title", "placeholder") and v and keep(v):
                self.out.add(keep(v))

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and keep(data):
            self.out.add(keep(data))


def template_to_key(s):
    """`Último teste: ${x}` -> 'Último teste: {0}' (expressões aninhadas são removidas)."""
    out, depth, n, i = "", 0, 0, 0
    while i < len(s):
        if s.startswith("${", i) and depth == 0:
            depth, i = 1, i + 2
            out += f"{{{n}}}"
            n += 1
            continue
        if depth:
            depth += {"{": 1, "}": -1}.get(s[i], 0)
            i += 1
            continue
        out += s[i]
        i += 1
    return out


def js_strings(src):
    found = set()
    for m in re.finditer(r'`((?:\\.|[^`\\])*)`|"((?:\\.|[^"\\\n])*)"', src):
        raw = m.group(1) if m.group(1) is not None else m.group(2)
        text = template_to_key(raw) if m.group(1) is not None else raw
        # partes de texto entre tags HTML; renumera os {n} de cada parte a partir de 0
        for seg in re.split(r"<[^>]+>", text):
            k = keep(seg.replace("&nbsp;", " "))
            if k and not re.fullmatch(r"[\s{}\d·|/–—-]*", k):
                idx = iter(range(99))
                k = re.sub(r"\{\d+\}", lambda _: f"{{{next(idx)}}}", k)
                found.add(k)
    return found


def py_strings(path):
    """Textos de UI no Python: títulos/descrições de ajustes, mensagens de erro e de retorno."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if re.search(r"[À-ÿ]", s) or (" " in s and s[:1].isupper()):
                k = keep(s)
                if k and "\\" not in s and "$" not in s and "|" not in s and not s.startswith(("Get-", "netsh", "SYSTEM", "SOFTWARE")):
                    found.add(k)
        elif isinstance(node, ast.JoinedStr):  # f-string -> modelo com {n}
            parts, n = [], 0
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                else:
                    parts.append(f"{{{n}}}")
                    n += 1
            k = keep("".join(parts))
            if k and re.search(r"[À-ÿ]|^[A-Z][a-z]+ ", k) and "$" not in k and "\\" not in k:
                found.add(k)
    return found


def main():
    p = HTMLTexts()
    p.feed(open(os.path.join(ROOT, "ui", "index.html"), encoding="utf-8").read())
    keys = set(p.out) | js_strings(open(os.path.join(ROOT, "ui", "app.js"), encoding="utf-8").read())
    for f in ("app.py", "tweaks.py", "drivers.py", "core.py"):
        keys |= py_strings(os.path.join(ROOT, f))
    keys = sorted(keys, key=str.casefold)
    if "--missing" in sys.argv:
        for lang in ("en", "es"):
            src = open(os.path.join(ROOT, "ui", f"i18n-{lang}.js"), encoding="utf-8").read()
            have = set(json.loads(src[src.index("{"):src.rindex("}") + 1]))
            miss = [k for k in keys if k not in have]
            print(f"{lang}: faltam {len(miss)}")
            for k in miss:
                print("   ", k)
        return
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "strings_pt.json")
    json.dump(keys, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(len(keys), "textos ->", out)


if __name__ == "__main__":
    main()
