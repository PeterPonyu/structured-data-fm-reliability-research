#!/usr/bin/env python3
"""Stamp the Structure tabular reliability audit into docs/ (GitHub Pages artifact).

Stdlib only. Reads frozen extracts in site/data/ and copies figure binaries
(does not restyle them). Does not copy paper_*.pdf into docs/.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from html import escape
from pathlib import Path

SITE = Path(__file__).resolve().parent
REPO = SITE.parent
DATA = SITE / "data"
CONTENT = SITE / "content"
TEMPLATE = (SITE / "templates" / "page.html").read_text(encoding="utf-8")
OUT = REPO / "docs"

NAV = [
    ("Thesis", "index.html", "thesis"),
    ("Protocol", "protocol/index.html", "protocol"),
    ("Tables", "tables/index.html", "tables"),
    ("Figures", "figures/index.html", "figures"),
    ("Key in/out", "key/index.html", "key"),
    ("Quarantine", "quarantine/index.html", "quarantine"),
    ("Reproduce", "reproduce/index.html", "reproduce"),
    ("Record", "cite/index.html", "cite"),
]

FIGURES = [
    {
        "id": "overview",
        "stem": "overview",
        "source": "fig0_overview",
        "title": "Overview",
        "supporting": False,
        "caption": (
            "Keyed tabular data is split randomly or by group/time; a frozen "
            "predictor is wrapped in split-conformal prediction; a remedy ladder "
            "is scored by worst-group coverage (Restore or Fail). The exploratory "
            "remedy ladder is quarantined from the held-out TableShift arm."
        ),
    },
    {
        "id": "aurc-random-vs-grouped",
        "stem": "aurc-random-vs-grouped",
        "source": "F1_aurc_random_vs_grouped",
        "title": "AURC, random vs grouped/time",
        "supporting": False,
        "caption": (
            "Per-dataset risk-coverage AURC under random vs grouped/time split, "
            "on a log-scaled AURC axis. Grouped points to the right are worse. "
            "A linear axis is a known failure mode across classification and regression."
        ),
    },
    {
        "id": "repair-ratio",
        "stem": "repair-ratio",
        "source": "F2_repair_ratio",
        "title": "Repair ratio",
        "supporting": False,
        "caption": (
            "Uncertainty-ranked abstention vs random deferral under the grouped "
            "split. The zero line is the claim boundary: points to the right beat "
            "random deferral. Moneyball’s near-zero/negative points are retained."
        ),
    },
    {
        "id": "model-agnostic",
        "stem": "model-agnostic",
        "source": "F3_model_agnostic",
        "title": "Model-agnostic coverage",
        "supporting": False,
        "caption": (
            "Four configurations spanning three architecture families. Grouped "
            "coverage vs the 0.90 target is the coverage-failure evidence. "
            "Tuning a GBM does not restore grouped coverage. TabDPT is omitted "
            "from the key-out coverage panel; that panel is not imputed."
        ),
    },
    {
        "id": "split-repeats-fragility",
        "stem": "split-repeats-fragility",
        "source": "F6_split_repeats_fragility",
        "title": "Split-realization fragility",
        "supporting": False,
        "caption": (
            "Headline counts across repeated grouped-split draws. The dashed "
            "majority threshold is 8/14. Only “repair beats random” never drops "
            "below 8 (100% of draws). Degradation counts are a split-realization "
            "distribution, not a confirmed majority."
        ),
    },
    {
        "id": "calsize-vs-mondrian",
        "stem": "calsize-vs-mondrian",
        "source": "F4_calsize_vs_mondrian",
        "title": "Mondrian vs calibration size",
        "supporting": False,
        "caption": (
            "Key-dependent flip. Key included: calibration-fold size predicts "
            "Mondrian improvement (Spearman rho = 0.50, threshold balanced "
            "accuracy 0.854). Key excluded: rho = −0.12, balanced accuracy 0.548 "
            "(KILL). Equal-size panels; do not lead with SUCCESS alone."
        ),
    },
    {
        "id": "tableshift",
        "stem": "tableshift",
        "source": "F5_tableshift",
        "title": "TableShift-class ACS generalization",
        "supporting": False,
        "caption": (
            "Folktables ACS leave-states-out spatial OOD. Repair on four tasks "
            "with 400-bootstrap intervals, then RAC1P worst−best coverage gap. "
            "Narrow viewports can use the ACS repair and RAC1P coverage-gap "
            "crops below."
        ),
        "crops": [
            {
                "stem": "tableshift-repair",
                "source": "F5a_tableshift_repair",
                "title": "ACS repair",
            },
            {
                "stem": "tableshift-subgroup-gap",
                "source": "F5b_tableshift_subgroup_gap",
                "title": "RAC1P coverage gap",
            },
        ],
    },
    {
        "id": "power-mde",
        "stem": "power-mde",
        "source": "F7_power_mde",
        "title": "Post-hoc power / MDE",
        "supporting": True,
        "caption": (
            "Supporting. Post-hoc power on observed flip frequencies, not a "
            "priori design. Independence idealization overstates power "
            "(Poisson-binomial 0.909 vs empirical 0.833; overdispersion 1.45×). "
            "Leave-one-out: dropping Electricity or Adult drops power below 0.8."
        ),
    },
    {
        "id": "calsize-planning",
        "stem": "calsize-planning",
        "source": "F8_calsize_planning",
        "title": "Within-dataset calibration-size sweep (negative result)",
        "supporting": True,
        "caption": (
            "Negative result: the within-dataset calibration-size "
            "sweep does not reproduce the cross-sectional dose-response. No trend "
            "line on the “helps” side (sign disagreement)."
        ),
    },
]


def load_json(name: str) -> object:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def pretty_dataset(name: str, mapping: dict[str, str]) -> str:
    return mapping.get(name, name.replace("_", " "))


def fmt_num(value: object, digits: int = 3) -> str:
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def fmt_cov(value: object) -> str:
    """Four decimals so a fail below 0.90 is not shown as 0.900."""
    if value is None:
        return "—"
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return fmt_num(value)
    return f"{float(value):.4f}"


def fmt_ci(pair: object) -> str:
    if not isinstance(pair, (list, tuple)) or len(pair) != 2:
        return "—"
    return f"[{fmt_num(pair[0])}, {fmt_num(pair[1])}]"


def cov_class(value: object, target: float = 0.90) -> str:
    if not isinstance(value, (int, float)):
        return ""
    return "cov-ok" if float(value) >= target else "cov-fail"


def verdict_class(text: str) -> str:
    t = text.strip().upper()
    if t in {"REJECT", "KILL"}:
        return "verdict-reject" if t == "REJECT" else "verdict-kill"
    if t in {"CONFIRM", "SUCCESS"}:
        return "verdict-confirm"
    return ""


def table_html(
    headers: list[str],
    rows: list[list[str]],
    *,
    classes: list[list[str]] | None = None,
    numeric: set[int] | None = None,
) -> str:
    numeric = numeric or set()
    thead = "".join(
        f'<th class="num">' + escape(h) + "</th>" if i in numeric else f"<th>{escape(h)}</th>"
        for i, h in enumerate(headers)
    )
    body = []
    for r_i, row in enumerate(rows):
        tds = []
        for c_i, cell in enumerate(row):
            cls = []
            if numeric and c_i in numeric:
                cls.append("num")
            extra = ""
            if classes and r_i < len(classes) and c_i < len(classes[r_i]):
                extra = classes[r_i][c_i]
                if extra:
                    cls.append(extra)
            attr = f' class="{" ".join(cls)}"' if cls else ""
            tds.append(f"<td{attr}>{cell}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return (
        '<div class="table-scroll"><table>'
        f"<thead><tr>{thead}</tr></thead><tbody>{''.join(body)}</tbody>"
        "</table></div>"
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
    wide: bool,
    scripts: str = "",
) -> str:
    html = TEMPLATE
    html = html.replace("{{title}}", escape(title))
    html = html.replace("{{description}}", escape(description))
    html = html.replace("{{root}}", root)
    html = html.replace("{{nav}}", nav_html(current, root))
    html = html.replace("{{nav_mobile}}", nav_html(current, root))
    html = html.replace("{{main_class}}", "wide" if wide else "prose")
    html = html.replace("{{scripts}}", scripts)
    html = html.replace("{{body}}", body)
    return html


def write_page(rel: str, html: str) -> Path:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path


def render_content(name: str, mapping: dict[str, str]) -> str:
    text = (CONTENT / name).read_text(encoding="utf-8")
    for key, value in mapping.items():
        text = text.replace("{{" + key + "}}", value)
    return md_to_html(text)


def gbm_coverage_table(
    rows: list[dict],
    *,
    pretty: dict[str, str],
    models: tuple[str, ...],
    order: list[str],
) -> str:
    by: dict[tuple[str, str], dict] = {(r["name"], r["model"]): r for r in rows}
    headers = [
        "Dataset",
        "Key",
        "Kind",
        "Model",
        "AURC random",
        "AURC grouped",
        "Coverage grouped",
        "Repair grouped",
        "Repair CI",
    ]
    numeric = {4, 5, 6, 7}
    body: list[list[str]] = []
    classes: list[list[str]] = []
    for name in order:
        for model in models:
            r = by.get((name, model))
            if not r:
                continue
            cov = r.get("conformal_cov_grouped_split")
            body.append(
                [
                    escape(pretty_dataset(name, pretty)),
                    escape(str(r.get("key") or "")),
                    escape(str(r.get("kind") or "")),
                    escape(model.replace("xgboost", "XGBoost").replace("lightgbm", "LightGBM")),
                    escape(fmt_num(r.get("aurc_random"), 4 if (r.get("aurc_random") or 0) > 1 else 3)),
                    escape(fmt_num(r.get("aurc_grouped"), 4 if (r.get("aurc_grouped") or 0) > 1 else 3)),
                    escape(fmt_cov(cov)),
                    escape(fmt_num(r.get("repair_ratio_grouped"))),
                    f'<span class="mute">{escape(fmt_ci(r.get("repair_grouped_ci")))}</span>',
                ]
            )
            cls = [""] * 9
            cls[6] = cov_class(cov)
            classes.append(cls)
    return table_html(headers, body, classes=classes, numeric=numeric)


def fm_table(fm: dict, pretty: dict[str, str], order: list[str]) -> str:
    by = {r["name"]: r for r in fm["rows"]}
    headers = ["Dataset", "Key", "Kind", "Coverage random", "Coverage grouped", "Gap", "Repair (grouped)", "Repair CI"]
    body = []
    classes = []
    for name in order:
        r = by.get(name)
        if not r:
            continue
        cov_g = r.get("conformal_cov_grouped")
        body.append(
            [
                escape(pretty_dataset(name, pretty)),
                escape(str(r.get("key") or "")),
                escape(str(r.get("kind") or "")),
                escape(fmt_cov(r.get("conformal_cov_random"))),
                escape(fmt_cov(cov_g)),
                escape(fmt_num(r.get("coverage_gap"))),
                escape(fmt_num(r.get("repair_ratio_grouped"))),
                f'<span class="mute">{escape(fmt_ci(r.get("repair_grouped_ci")))}</span>',
            ]
        )
        cls = [""] * 8
        cls[3] = cov_class(r.get("conformal_cov_random"))
        cls[4] = cov_class(cov_g)
        classes.append(cls)
    return table_html(headers, body, classes=classes, numeric={3, 4, 5, 6})


def two_col_table(rows: list[list[str]], headers: list[str] | None = None) -> str:
    headers = headers or ["Comparison / statistic", "Value"]
    body = []
    classes = []
    for row in rows:
        label, value = row[0], row[1]
        vclass = verdict_class(value)
        body.append([escape(label), escape(value)])
        classes.append(["", vclass])
    return table_html(headers, body, classes=classes)


def key_count_table(counts: dict) -> str:
    headers = ["Condition", "Model", "Grouped-gap", "Repair beats random", "Stage-2"]
    body = []
    classes = []
    for cond_key, cond_label in (("key_included", "Key included"), ("key_excluded", "Key excluded")):
        block = counts[cond_key]
        for model in ("xgboost", "lightgbm"):
            m = block["models"][model]
            body.append(
                [
                    escape(cond_label),
                    escape("XGBoost" if model == "xgboost" else "LightGBM"),
                    escape(f"{m['grouped_gap']}/14"),
                    escape(f"{m['repair']}/14"),
                    escape(block["verdict"]),
                ]
            )
            classes.append(["", "", "", "", verdict_class(block["verdict"])])
    return table_html(headers, body, classes=classes)


def acs_table(acs: dict, pretty_acs: dict[str, str], pretty_rac: dict[str, str]) -> str:
    headers = [
        "Task",
        "Model",
        "Coverage in-domain",
        "Coverage OOD",
        "Repair OOD",
        "Repair CI",
        "RAC1P worst−best",
    ]
    body = []
    classes = []
    for r in acs["rows"]:
        body.append(
            [
                escape(pretty_acs.get(r["task"], r["task"])),
                escape("XGBoost" if r["model"] == "xgboost" else "LightGBM"),
                escape(fmt_cov(r.get("conformal_cov_random"))),
                escape(fmt_cov(r.get("conformal_cov_ood"))),
                escape(fmt_num(r.get("repair_ratio_ood"))),
                f'<span class="mute">{escape(fmt_ci(r.get("repair_ood_ci")))}</span>',
                escape(fmt_num(r.get("grouped_coverage_gap_worst_minus_best"))),
            ]
        )
        cls = [""] * 7
        cls[2] = cov_class(r.get("conformal_cov_random"))
        cls[3] = cov_class(r.get("conformal_cov_ood"))
        classes.append(cls)
    html = table_html(headers, body, classes=classes, numeric={2, 3, 4, 6})
    # RAC1P breakdown (first model pair is enough as a values table)
    rac_headers = ["Task", "Model"] + [pretty_rac.get(k, k) for k in ("1", "2", "6", "8", "9")]
    rac_body = []
    rac_cls = []
    for r in acs["rows"]:
        per = r.get("grouped_coverage_per_RAC1P") or {}
        row = [
            escape(pretty_acs.get(r["task"], r["task"])),
            escape("XGBoost" if r["model"] == "xgboost" else "LightGBM"),
        ]
        cls = ["", ""]
        for code in ("1", "2", "6", "8", "9"):
            val = per.get(code)
            row.append(escape(fmt_cov(val)))
            cls.append(cov_class(val))
        rac_body.append(row)
        rac_cls.append(cls)
    html += "<h3>RAC1P group coverage</h3>"
    html += table_html(rac_headers, rac_body, classes=rac_cls, numeric=set(range(2, 7)))
    return html


def f6_table(f6: dict) -> str:
    headers = ["Condition", "Model", "Count", "Median", "Min", "Max", "Share of draws ≥ 8/14"]
    body = []
    for cond, clabel in (("key_included", "Key included"), ("key_excluded", "Key excluded")):
        block = f6["stage2"][cond]
        for model in ("xgboost", "lightgbm"):
            mlabel = "XGBoost" if model == "xgboost" else "LightGBM"
            arm = block[model]
            for key, label in (
                ("grouped_gap", "Grouped-gap"),
                ("aurc_degrade", "AURC-degrade"),
                ("undercover", "Undercover"),
                ("repair", "Repair beats random"),
            ):
                c = arm[key]
                body.append(
                    [
                        escape(clabel),
                        escape(mlabel),
                        escape(label),
                        escape(fmt_num(c["median"], 1)),
                        escape(str(c["min"])),
                        escape(str(c["max"])),
                        escape(fmt_num(c["frac_k_ge_majority"])),
                    ]
                )
    return table_html(headers, body, numeric={3, 4, 5, 6})


def figure_block(fig: dict, root: str, extra_table: str = "") -> str:
    stem = fig["stem"]
    png = f"figures/{stem}.png"
    pdf = f"figures/{stem}.pdf"
    tag = '<p class="note">Supporting figure.</p>' if fig.get("supporting") else ""
    html = [
        f'<section id="{escape(fig["id"])}">',
        f'<h2>{escape(fig["title"])}</h2>',
        tag,
        '<figure class="panel">',
        f'<img src="{root}{png}" alt="{escape(fig["title"])}">',
        f"<figcaption>{escape(fig['caption'])}</figcaption>",
        "</figure>",
        f'<p class="fig-link"><a href="{root}{pdf}">Download figure</a></p>',
    ]
    for crop in fig.get("crops") or []:
        crop_stem = crop["stem"] if isinstance(crop, dict) else crop[0]
        crop_title = crop["title"] if isinstance(crop, dict) else crop[1]
        html.append(
            f'<figure class="panel" id="{escape(crop_stem)}">'
            f'<img src="{root}figures/{crop_stem}.png" alt="{escape(crop_title)}">'
            f"<figcaption>{escape(crop_title)}. Crop of the TableShift figure for narrow viewports.</figcaption>"
            f"</figure>"
            f'<p class="fig-link"><a href="{root}figures/{crop_stem}.pdf">Download figure</a></p>'
        )
    if extra_table:
        html.append("<h3>Values</h3>")
        html.append(extra_table)
    html.append("</section>")
    return "\n".join(html)


def rasterize_pdf(pdf: Path, dest_png: Path) -> None:
    dest_png.parent.mkdir(parents=True, exist_ok=True)
    prefix = dest_png.with_suffix("")
    subprocess.run(
        ["pdftocairo", "-png", "-singlefile", "-scale-to", "1600", str(pdf), str(prefix)],
        check=True,
    )


def figure_copy_pairs(fig: dict) -> list[tuple[str, str]]:
    """(public_stem, source_stem) pairs for the main panel and any crops."""
    pairs = [(fig["stem"], fig.get("source", fig["stem"]))]
    for crop in fig.get("crops") or []:
        if isinstance(crop, dict):
            pairs.append((crop["stem"], crop.get("source", crop["stem"])))
        else:
            pairs.append((crop[0], crop[0]))
    return pairs


def copy_figures() -> list[str]:
    src_dirs = [SITE / "figures", REPO / "manuscripts" / "figures"]
    dest = OUT / "figures"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    pairs: list[tuple[str, str]] = []
    for fig in FIGURES:
        pairs.extend(figure_copy_pairs(fig))
    cairo = shutil.which("pdftocairo")
    for public, source in pairs:
        for ext in (".png", ".pdf"):
            for src_dir in src_dirs:
                src = src_dir / f"{source}{ext}"
                if not src.exists() and source != public:
                    src = src_dir / f"{public}{ext}"
                if src.exists():
                    shutil.copy2(src, dest / f"{public}{ext}")
                    copied.append(f"{public}{ext}")
                    break
        png = dest / f"{public}.png"
        if png.exists():
            continue
        pdf = None
        for d in src_dirs:
            for name in (source, public):
                candidate = d / f"{name}.pdf"
                if candidate.exists():
                    pdf = candidate
                    break
            if pdf is not None:
                break
        if pdf is not None and cairo:
            rasterize_pdf(pdf, png)
            copied.append(png.name)
    return copied


def copy_csv() -> None:
    (OUT / "data").mkdir(parents=True, exist_ok=True)
    shutil.copy2(DATA / "p4_table.csv", OUT / "data" / "p4_table.csv")
    # CORE14 export already is p4_table; also dump ACS as csv
    acs = load_json("p5_acs.json")
    with (OUT / "data" / "p5_tableshift_table.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "task",
                "model",
                "conformal_cov_random",
                "conformal_cov_ood",
                "repair_ratio_ood",
                "grouped_coverage_gap_worst_minus_best",
            ]
        )
        for r in acs["rows"]:
            w.writerow(
                [
                    r["task"],
                    r["model"],
                    r["conformal_cov_random"],
                    r["conformal_cov_ood"],
                    r["repair_ratio_ood"],
                    r["grouped_coverage_gap_worst_minus_best"],
                ]
            )


def leak_scan(reproduce_rel: str) -> None:
    forbidden_all = (
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
    )
    json_ok_prefix = reproduce_rel
    problems: list[str] = []
    if list(OUT.glob("paper_*.pdf")):
        problems.append("paper_*.pdf in Pages artifact (off this stretch)")
    for path in OUT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".html", ".css", ".js", ".md", ".csv", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = str(path.relative_to(OUT)).replace("\\", "/")
        for needle in forbidden_all:
            if needle in text:
                problems.append(f"{rel}: contains {needle}")
        if path.suffix == ".html" and rel != json_ok_prefix:
            if re.search(r"[\w.-]+\.json", text):
                problems.append(f"{rel}: JSON filename outside reproduce")
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
        "css/portal.css",
        "fonts/ibm-plex.css",
        "fonts/IBMPlexSans-normal-400.woff2",
        ".nojekyll",
        "data/p4_table.csv",
        "figures/overview.png",
        "figures/aurc-random-vs-grouped.png",
        "figures/split-repeats-fragility.png",
    ]
    missing = [r for r in required if not (OUT / r).exists()]
    if missing:
        raise SystemExit("verify missing: " + ", ".join(missing))
    if list(OUT.glob("paper_*.pdf")):
        raise SystemExit("verify: paper_*.pdf must not be in docs/ this stretch")
    home = (OUT / "index.html").read_text(encoding="utf-8")
    for token in (
        "H1 coverage restoration",
        "REJECT",
        "H2 uncertainty",
        "CONFIRM",
        "KILL",
        "13/14",
        "Random-split validation overstates reliability",
        "The contribution is a reusable protocol",
    ):
        if token not in home:
            raise SystemExit(f"verify: index missing {token!r}")
    if "&lt;li" in home or "&lt;a " in home or "&lt;strong" in home:
        raise SystemExit("verify: index still has escaped HTML (document fallback)")
    tables = (OUT / "tables/index.html").read_text(encoding="utf-8")
    if "cov-fail" not in tables or "cov-ok" not in tables:
        raise SystemExit("verify: coverage coloring missing")
    if "Electricity" not in tables or "151" in tables:
        raise SystemExit("verify: expected human-readable names, no OpenML id 151")
    key = (OUT / "key/index.html").read_text(encoding="utf-8")
    if "data-key-panel" not in key or "Key excluded" not in key:
        raise SystemExit("verify: key page incomplete")
    repro = (OUT / "reproduce/index.html").read_text(encoding="utf-8")
    if "10.5281/zenodo.21130297" not in repro:
        raise SystemExit("verify: reproduce missing reserved DOI")
    if "github.com/PeterPonyu/structured-data-fm-reliability-research" not in repro:
        raise SystemExit("verify: reproduce missing public code archive")
    cite_page = (OUT / "cite/index.html").read_text(encoding="utf-8")
    if "<pre><code>@misc{fu2026conformal," not in cite_page:
        raise SystemExit("verify: cite missing rendered BibTeX block")
    if "&lt;/code&gt;" in cite_page or "&lt;/pre&gt;" in cite_page:
        raise SystemExit("verify: cite still has escaped code-block tags (document fallback)")
    for rel in (
        "index.html",
        "protocol/index.html",
        "tables/index.html",
        "figures/index.html",
        "key/index.html",
        "quarantine/index.html",
        "reproduce/index.html",
        "cite/index.html",
    ):
        text = (OUT / rel).read_text(encoding="utf-8")
        for banned in (
            "KBS",
            "DMKD",
            "Knowledge-Based",
            "this paper",
            "the paper",
            "manuscript",
            "submitted",
            "journal",
            "paper_kbs",
            "InfoSci",
            "Paper companion",
            "Print PDF",
            "fonts.googleapis.com",
            "fonts.gstatic.com",
        ):
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
        fonts_dest = OUT / "fonts"
        if fonts_dest.exists():
            shutil.rmtree(fonts_dest)
        shutil.copytree(fonts_src, fonts_dest)
    js_dest = OUT / "js"
    js_dest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SITE / "js" / "keytoggle.js", js_dest / "keytoggle.js")

    pretty = load_json("pretty.json")
    dmap: dict[str, str] = pretty["dataset"]
    order: list[str] = pretty["core14_order"]
    core = load_json("core14_rows.json")
    counts = load_json("key_counts.json")
    fm = load_json("tab_fm.json")
    learned = load_json("tab_learned.json")
    roster = load_json("p5_roster.json")
    p5v = load_json("p5_verdict.json")
    acs = load_json("p5_acs.json")
    f6 = load_json("f6_fragility.json")
    cite = load_json("cite.json")
    quarantine = load_json("quarantine.json")

    copy_figures()
    copy_csv()

    verdict_table = table_html(
        ["Gate", "Result"],
        [
            ["H1 coverage restoration (held-out TableShift)", "REJECT"],
            ["H2 uncertainty vs tuned selector (held-out TableShift)", "CONFIRM"],
            ["Stage-2 conjunctive gate (exploratory 14)", "KILL"],
            ["Repair vs random deferral (exploratory 14, all arms)", "13/14 (load-bearing)"],
        ],
        classes=[["", "verdict-reject"], ["", "verdict-confirm"], ["", "verdict-kill"], ["", ""]],
    )

    core14_html = gbm_coverage_table(
        core["key_included"], pretty=dmap, models=("xgboost", "lightgbm"), order=order
    )
    fm_html = fm_table(fm, dmap, order)
    learned_html = two_col_table(learned["rows"])
    roster_html = table_html(
        ["Task", "Endpoint", "n groups", "In H1/H2 tally"],
        [
            [
                escape(pretty["tableshift_task"].get(r["task"], r["task"])),
                escape(r["endpoint"]),
                escape(str(r["n_groups"])),
                "yes" if r["in_tally"] else "excluded-by-rule",
            ]
            for r in roster["rows"]
        ],
        numeric={2},
    )
    p5_html = two_col_table(p5v["rows"])
    acs_html = acs_table(acs, pretty["acs"], pretty["rac1p"])
    key_html = key_count_table(counts)
    q_html = table_html(
        ["Item", "Status", "May a reader cite it as a result?"],
        [[escape(a), escape(b), escape(c)] for a, b, c in quarantine["rows"]],
    )

    fig_tables = {
        "aurc-random-vs-grouped": gbm_coverage_table(
            core["key_included"], pretty=dmap, models=("xgboost", "lightgbm"), order=order
        ),
        "repair-ratio": table_html(
            ["Dataset", "Model", "Repair grouped", "Repair CI", "Beats random"],
            [
                [
                    escape(pretty_dataset(r["name"], dmap)),
                    escape("XGBoost" if r["model"] == "xgboost" else "LightGBM"),
                    escape(fmt_num(r.get("repair_ratio_grouped"))),
                    f'<span class="mute">{escape(fmt_ci(r.get("repair_grouped_ci")))}</span>',
                    "yes" if r.get("repair_excludes0_pos") else "no",
                ]
                for r in core["key_included"]
            ],
            numeric={2},
        ),
        "model-agnostic": fm_html,
        "split-repeats-fragility": f6_table(f6),
        "calsize-vs-mondrian": two_col_table(
            [
                ["Key included Spearman rho", "0.50"],
                ["Key included threshold balanced accuracy", "0.854"],
                ["Key included gate", "SUCCESS"],
                ["Key excluded Spearman rho", "−0.12"],
                ["Key excluded threshold balanced accuracy", "0.548"],
                ["Key excluded gate", "KILL"],
            ]
        ),
        "tableshift": acs_html,
        "overview": "",
        "power-mde": "",
        "calsize-planning": "",
    }
    gallery = "\n".join(figure_block(fig, "../", fig_tables.get(fig["id"], "")) for fig in FIGURES)

    fig0 = figure_block(FIGURES[0], "../", "")

    key_cov = (
        '<div data-key-panel="included">'
        "<h2>Coverage, key included</h2>"
        + gbm_coverage_table(
            core["key_included"], pretty=dmap, models=("xgboost", "lightgbm"), order=order
        )
        + "</div>"
        '<div data-key-panel="excluded">'
        "<h2>Coverage, key excluded</h2>"
        + gbm_coverage_table(
            core["key_excluded"], pretty=dmap, models=("xgboost", "lightgbm"), order=order
        )
        + "</div>"
    )
    key_toggle = """
<div class="key-controls" role="radiogroup" aria-label="Key condition">
  <label><input type="radio" name="key-condition" value="included" checked> Key included (headline)</label>
  <label><input type="radio" name="key-condition" value="excluded"> Key excluded (conservative bound)</label>
</div>
"""
    key_script = '<script src="../js/keytoggle.js"></script>'

    bib = (
        "```bibtex\n"
        "@misc{fu2026conformal,\n"
        f'  title   = {{{cite["title"]}}},\n'
        f'  author  = {{{cite["author"]}}},\n'
        f'  year    = {{{cite["year"]}}},\n'
        f'  howpublished = {{Zenodo reserved draft {cite["doi"]}}},\n'
        f'  url     = {{{cite["github"]}}}\n'
        "}\n"
        "```"
    )

    pages = [
        (
            "index.html",
            "index.md",
            "thesis",
            "Thesis",
            "Preregistered tabular reliability audit.",
            "",
            False,
            {"verdict_table": verdict_table, "root": ""},
        ),
        (
            "protocol/index.html",
            "protocol.md",
            "protocol",
            "Decision rule",
            "Keyed split comparison, coverage test, uncertainty abstention fallback.",
            "",
            False,
            {"fig0": fig0, "root": "../"},
        ),
        (
            "tables/index.html",
            "tables.md",
            "tables",
            "Tables",
            "CORE14, TabICLv2, learned selector, TableShift, ACS, key-in vs key-out.",
            "",
            True,
            {
                "core14_table": core14_html,
                "fm_table": fm_html,
                "learned_table": learned_html,
                "p5_roster_table": roster_html,
                "p5_verdict_table": p5_html,
                "acs_table": acs_html,
                "key_count_table": key_html,
                "root": "../",
            },
        ),
        (
            "figures/index.html",
            "figures.md",
            "figures",
            "Figures",
            "Audit figures in argument order, with values tables.",
            "",
            True,
            {"figure_gallery": gallery, "root": "../"},
        ),
        (
            "key/index.html",
            "key.md",
            "key",
            "Key included vs key excluded",
            "Headline key-in counts versus the conservative key-out bound.",
            key_script,
            True,
            {
                "key_toggle": key_toggle,
                "key_count_table": key_html,
                "key_coverage_tables": key_cov,
                "root": "../",
            },
        ),
        (
            "quarantine/index.html",
            "quarantine.md",
            "quarantine",
            "Honesty ledger",
            "Quarantine, KILL, and blocked items.",
            "",
            True,
            {"quarantine_table": q_html, "root": "../"},
        ),
        (
            "reproduce/index.html",
            "reproduce.md",
            "reproduce",
            "Reproduce",
            "Smoke test, data licenses, figure regeneration, archive filenames.",
            "",
            False,
            {"root": "../"},
        ),
        (
            "cite/index.html",
            "cite.md",
            "cite",
            "Record",
            "Code archive and reserved Zenodo DOI.",
            "",
            False,
            {"bibtex": bib, "root": "../"},
        ),
    ]

    for rel, md_name, current, title, desc, scripts, wide, mapping in pages:
        body = render_content(md_name, mapping)
        html = page(
            title=title,
            description=desc,
            current=current,
            body=body,
            root=mapping.get("root", ""),
            wide=wide,
            scripts=scripts,
        )
        write_page(rel, html)

    leak_scan("reproduce/index.html")
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
