#!/usr/bin/env python3
"""Stamp a code-and-protocol landing page into docs/ (GitHub Pages artifact).

Stdlib only. Does not copy figure binaries, table extracts, or paper_*.pdf.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from html import escape
from pathlib import Path

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
CONTENT = SITE / "content"
TEMPLATE = (SITE / "templates" / "page.html").read_text(encoding="utf-8")
OUT = REPO / "docs"

NAV = [
    ("Code", "index.html", "code"),
    ("Protocol", "protocol/index.html", "protocol"),
    ("Reproduce", "reproduce/index.html", "reproduce"),
    ("Record", "cite/index.html", "cite"),
]

PAGES = [
    (
        "index.html",
        "index.md",
        "code",
        "structured-data-fm-reliability-research",
        "Code and protocol leaf for keyed tabular reliability scripts.",
        "",
    ),
    (
        "protocol/index.html",
        "protocol.md",
        "protocol",
        "Protocol",
        "Keyed-split coverage test and uncertainty abstention fallback.",
        "../",
    ),
    (
        "tables/index.html",
        "tables.md",
        "tables",
        "Tables",
        "This path does not host figures or result numbers.",
        "../",
    ),
    (
        "figures/index.html",
        "figures.md",
        "figures",
        "Figures",
        "This path does not host figures or result numbers.",
        "../",
    ),
    (
        "key/index.html",
        "key.md",
        "key",
        "Key included vs key excluded",
        "This path does not host figures or result numbers.",
        "../",
    ),
    (
        "quarantine/index.html",
        "quarantine.md",
        "quarantine",
        "Scope notes",
        "This path does not host figures or result numbers.",
        "../",
    ),
    (
        "reproduce/index.html",
        "reproduce.md",
        "reproduce",
        "Reproduce",
        "Smoke test, data licenses, and archive links.",
        "../",
    ),
    (
        "cite/index.html",
        "cite.md",
        "cite",
        "Record",
        "Code archive and Zenodo DOI.",
        "../",
    ),
]

FORBIDDEN = (
    "/home/",
    "/root/",
    "checkpoint-",
    "F1_debt",
    "Matbench",
    "MVTec",
    "paper_rie",
    "inspect-gate",
    "asr-gate",
    "peaceiris",
    "manuscripts/",
    "paper_kbs.pdf",
    "@gmail.com",
    "fuzeyu09",
    "KBS",
    "DMKD",
    "Knowledge-Based",
    "this paper",
    "the paper",
    "manuscript",
    "submitted",
    "journal",
    "InfoSci",
    "Paper companion",
    "Print PDF",
    "Thesis",
    "unpublished",
    "SOTA",
    "REJECT",
    "CONFIRM",
    "KILL",
    "13/14",
    "H1 coverage",
    "Same frozen numbers",
    "verdict-reject",
    "verdict-kill",
    "Science Gateway",
    "Launch Explorer",
    "flagship",
    "AURC",
)


def md_inline(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def md_to_html(src: str) -> str:
    lines = src.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def flush_para(buf: list[str]) -> None:
        if buf:
            out.append("<p>" + md_inline(" ".join(buf)) + "</p>")
            buf.clear()

    while i < n:
        line = lines[i]
        if line.startswith("```"):
            fence = []
            i += 1
            while i < n and not lines[i].startswith("```"):
                fence.append(escape(lines[i]))
                i += 1
            i += 1
            out.append("<pre><code>" + "\n".join(fence) + "</code></pre>")
            continue
        stripped = line.lstrip()
        if stripped.startswith("<") or stripped.startswith("{{"):
            out.append(stripped)
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{md_inline(m.group(2))}</h{level}>")
            i += 1
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < n and re.match(r"^[-*]\s+", lines[i]):
                items.append("<li>" + md_inline(re.sub(r"^[-*]\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i]):
                items.append("<li>" + md_inline(re.sub(r"^\d+\.\s+", "", lines[i])) + "</li>")
                i += 1
            out.append("<ol>" + "".join(items) + "</ol>")
            continue
        para: list[str] = [line]
        i += 1
        while i < n and lines[i].strip() and not re.match(
            r"^(#|[-*] |\d+\. |<|```|{{)", lines[i].lstrip()
        ):
            para.append(lines[i])
            i += 1
        flush_para(para)
    return "\n".join(out)


def nav_html(current: str, root: str) -> str:
    bits = []
    for label, rel, key in NAV:
        href = root + rel
        cur = ' aria-current="page"' if key == current else ""
        bits.append(f'<a href="{href}"{cur}>{escape(label)}</a>')
    return "".join(bits)


def page(
    *,
    title: str,
    description: str,
    current: str,
    body: str,
    root: str,
    scripts: str = "",
) -> str:
    html = TEMPLATE
    html = html.replace("{{title}}", escape(title))
    html = html.replace("{{description}}", escape(description))
    html = html.replace("{{root}}", root)
    html = html.replace("{{nav}}", nav_html(current, root))
    html = html.replace("{{nav_mobile}}", nav_html(current, root))
    html = html.replace("{{main_class}}", "prose")
    html = html.replace("{{scripts}}", scripts)
    html = html.replace("{{body}}", body)
    return html


def write_page(rel: str, html: str) -> Path:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def leak_scan() -> None:
    problems: list[str] = []
    if list(OUT.glob("paper_*.pdf")):
        problems.append("paper_*.pdf in Pages artifact")
    fig_dir = OUT / "figures"
    if fig_dir.is_dir():
        binaries = [
            p for p in fig_dir.iterdir() if p.suffix.lower() in {".png", ".pdf", ".svg", ".jpg"}
        ]
        if binaries:
            problems.append("figure binaries in docs/figures")
    data_dir = OUT / "data"
    if data_dir.is_dir() and any(data_dir.iterdir()):
        problems.append("table extracts in docs/data")
    for path in OUT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".css", ".js", ".md", ".csv", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(OUT)).replace("\\", "/")
        for needle in FORBIDDEN:
            if needle in text:
                problems.append(f"{rel}: contains {needle}")
        if path.suffix == ".html":
            if re.search(r"""(?:href|src)=["']/(?:css|js|figures)/""", text):
                problems.append(f"{rel}: root-absolute asset path")
    if problems:
        raise SystemExit("leak scan failed:\n  " + "\n  ".join(problems))


def verify() -> None:
    required = [
        "index.html",
        "protocol/index.html",
        "tables/index.html",
        "figures/index.html",
        "key/index.html",
        "quarantine/index.html",
        "reproduce/index.html",
        "cite/index.html",
        "404.html",
        "css/portal.css",
        "fonts/ibm-plex.css",
        "fonts/IBMPlexSans-normal-400.woff2",
        ".nojekyll",
    ]
    missing = [r for r in required if not (OUT / r).exists()]
    if missing:
        raise SystemExit("verify missing: " + ", ".join(missing))
    home = (OUT / "index.html").read_text(encoding="utf-8")
    for token in (
        "structure-code-protocol",
        "Code and protocol",
        "does not host figures or result numbers",
        "github.com/PeterPonyu/structured-data-fm-reliability-research",
        "10.5281/zenodo.21130297",
        "./smoke_test.sh",
    ):
        if token not in home and token not in (OUT / "reproduce/index.html").read_text(
            encoding="utf-8"
        ):
            if token == "./smoke_test.sh":
                repro = (OUT / "reproduce/index.html").read_text(encoding="utf-8")
                if token not in repro:
                    raise SystemExit(f"verify: reproduce missing {token!r}")
                continue
            raise SystemExit(f"verify: missing {token!r}")
    if "structure-code-protocol" not in home:
        raise SystemExit("verify: index missing site binding")
    if "does not host figures or result numbers" not in home:
        raise SystemExit("verify: index missing no-results scope")
    for rel in (
        "index.html",
        "protocol/index.html",
        "tables/index.html",
        "figures/index.html",
        "key/index.html",
        "quarantine/index.html",
        "reproduce/index.html",
        "cite/index.html",
        "404.html",
    ):
        text = (OUT / rel).read_text(encoding="utf-8")
        for banned in FORBIDDEN:
            if banned in text:
                raise SystemExit(f"verify: {rel} contains {banned!r}")
    print("verify: ok")


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    css_dest = OUT / "css"
    css_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SITE / "css" / "portal.css", css_dest / "portal.css")
    favicon = SITE / "favicon.svg"
    if favicon.is_file():
        shutil.copy2(favicon, OUT / "favicon.svg")
    fonts_src = SITE / "fonts"
    if fonts_src.is_dir():
        shutil.copytree(fonts_src, OUT / "fonts")

    for rel, md_name, current, title, desc, root in PAGES:
        body = md_to_html((CONTENT / md_name).read_text(encoding="utf-8"))
        html = page(
            title=title,
            description=desc,
            current=current,
            body=body,
            root=root,
        )
        write_page(rel, html)

    write_page(
        "404.html",
        page(
            title="Path not found",
            description="This path is not on the code leaf.",
            current="",
            body=(
                "<h1>Path not found</h1>"
                "<p>This is a code and protocol leaf. "
                "The requested path does not host figures or result numbers.</p>"
                '<p><a href="index.html">Back to the code leaf</a></p>'
            ),
            root="",
        ),
    )

    leak_scan()
    verify()
    print(f"built {OUT}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    build()


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)
