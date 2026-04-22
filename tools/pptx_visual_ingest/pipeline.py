#!/usr/bin/env python3
"""Vault-local PPTX/PDF visual ingest workflow.

This tool is intentionally stored under tools/ rather than wiki/.
It renders slide decks through a PDF-first path by default:

PPTX -> PDF -> per-page PNG screenshots -> Obsidian visual digest

If the source is already a PDF, it skips PPTX conversion and renders the PDF directly.
The older QuickLook HTML renderer is retained only as a fallback render method.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET


TODAY = date.today().isoformat()
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


@dataclass
class Deck:
    pptx: str
    slug: str
    summary_slug: str
    title: str
    tags: list[str]
    related: list[str]


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def vault_root(config: dict) -> Path:
    root = Path(config.get("vault_root", ".")).expanduser()
    return root.resolve()


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def slide_sort_key(name: str) -> int:
    match = re.search(r"slide(\d+)\.xml$", name)
    return int(match.group(1)) if match else 10**9


def deck_from_config(raw: dict, config: dict, source_root: Path) -> Deck:
    pptx = raw["pptx"]
    slug = raw.get("slug") or slugify(Path(pptx).stem)
    summary_slug = raw.get("summary_slug") or f"{config.get('summary_prefix', 'lecture')}-{slug}"
    title = raw.get("title") or Path(pptx).stem
    tags = raw.get("tags") or config.get("tags", [])
    related = raw.get("related") or [f"[[{config.get('course_hub', '').removesuffix('.md')}]]"]
    return Deck(pptx=pptx, slug=slug, summary_slug=summary_slug, title=title, tags=tags, related=related)


def discover_decks(config: dict) -> list[Deck]:
    source_root = Path(config["source_root"]).expanduser()
    if "decks" in config and config["decks"]:
        return [deck_from_config(item, config, source_root) for item in config["decks"]]
    decks = []
    pattern = config.get("pptx_glob", "**/*.pptx")
    for pptx in sorted(source_root.glob(pattern)):
        if pptx.name.startswith(".~"):
            continue
        rel = str(pptx.relative_to(source_root))
        slug = slugify(f"{pptx.parent.name}-{pptx.stem}")
        decks.append(Deck(
            pptx=rel,
            slug=slug,
            summary_slug=f"{config.get('summary_prefix', 'lecture')}-{slug}",
            title=pptx.stem,
            tags=config.get("tags", []),
            related=[f"[[{config.get('course_hub', '').removesuffix('.md')}]]"],
        ))
    return decks


def extract_pptx_text(pptx: Path, out_md: Path, deck: Deck, source_root: Path) -> int:
    if pptx.suffix.lower() != ".pptx":
        raise ValueError(f"Text extraction currently expects .pptx, got {pptx}")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pptx) as zf:
        slide_names = sorted(
            [n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)],
            key=slide_sort_key,
        )
        lines = [
            f"# {deck.title}",
            "",
            f"- Source: `{pptx}`",
            f"- Converted: {TODAY} by local PPTX XML text extraction",
            f"- Slides: {len(slide_names)}",
            "",
        ]
        for idx, name in enumerate(slide_names, start=1):
            lines.append(f"## Slide {idx}")
            lines.append("")
            slide_lines = text_from_xml(zf.read(name))
            if slide_lines:
                for line in slide_lines:
                    if line.startswith("#"):
                        line = "\\" + line
                    lines.append(f"- {line}")
            else:
                lines.append("- [No extractable text]")
            lines.append("")
    out_md.write_text("\n".join(lines), encoding="utf-8")
    return len(slide_names)


def text_from_xml(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    lines: list[str] = []
    for para in root.iter(A_NS + "p"):
        parts = [node.text for node in para.iter(A_NS + "t") if node.text]
        line = re.sub(r"\s+", " ", "".join(parts)).strip()
        if line and (not lines or lines[-1] != line):
            lines.append(line)
    return lines


def find_soffice(config: dict) -> str:
    candidates = [
        config.get("soffice_path"),
        shutil.which("soffice"),
        shutil.which("libreoffice"),
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise FileNotFoundError("LibreOffice/soffice not found. Install LibreOffice or set soffice_path in config.")


def export_pptx_to_pdf(config: dict, source: Path, out_pdf: Path, overwrite: bool = False) -> Path:
    if source.suffix.lower() == ".pdf":
        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        if overwrite or not out_pdf.exists() or source.resolve() != out_pdf.resolve():
            if source.resolve() != out_pdf.resolve():
                shutil.copy2(source, out_pdf)
        return out_pdf
    if source.suffix.lower() != ".pptx":
        raise ValueError(f"Unsupported source type for PDF-first render: {source}")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if out_pdf.exists() and not overwrite:
        return out_pdf
    soffice = find_soffice(config)
    with tempfile.TemporaryDirectory(prefix=f"pdf_export_{source.stem}_") as tmp_name:
        tmp = Path(tmp_name)
        convert_to = config.get("pdf_export_filter", "pdf:impress_pdf_Export")
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--norestore",
                "--nodefault",
                "--nofirststartwizard",
                "--convert-to",
                convert_to,
                "--outdir",
                str(tmp),
                str(source),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=int(config.get("pdf_export_timeout", 180)),
        )
        produced = tmp / f"{source.stem}.pdf"
        if result.returncode != 0 or not produced.exists():
            raise RuntimeError("LibreOffice PDF export failed\nSTDOUT:\n" + result.stdout + "\nSTDERR:\n" + result.stderr)
        shutil.move(str(produced), str(out_pdf))
    return out_pdf


def render_pdf_to_png(config: dict, pdf: Path, asset_dir: Path) -> list[dict]:
    try:
        import fitz  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "PDF rendering requires PyMuPDF (`fitz`). Use the Python interpreter that has PyMuPDF installed "
            "or install pymupdf for the active Python."
        ) from exc

    dpi = int(config.get("pdf_render_dpi", 180))
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    meta: list[dict] = []
    doc = fitz.open(str(pdf))
    for idx, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        out = asset_dir / f"slide-{idx:03d}.png"
        pix.save(str(out))
        text = page.get_text("text") or ""
        meta.append({
            "index": idx,
            "text": text,
            "imgCount": len(page.get_images(full=True)),
            "width": pix.width,
            "height": pix.height,
            "sourcePdf": str(pdf),
            "renderMethod": "pdf_first_pymupdf",
            "dpi": dpi,
        })
    doc.close()
    (asset_dir / "slides-meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def convert_pdf_attachments(preview_dir: Path) -> int:
    html = preview_dir / "Preview.html"
    if not html.exists():
        return 0
    html_text = html.read_text(encoding="utf-8", errors="ignore")
    count = 0
    for pdf in preview_dir.glob("Attachment*.pdf"):
        png = preview_dir / f"{pdf.name}.png"
        if not png.exists():
            result = subprocess.run(
                ["sips", "-s", "format", "png", str(pdf), "--out", str(png)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0 and png.exists():
                count += 1
        if png.exists():
            html_text = html_text.replace(f'src="{pdf.name}"', f'src="{png.name}"')
            html_text = html_text.replace(f"src='{pdf.name}'", f"src='{png.name}'")
    html.write_text(html_text, encoding="utf-8")
    return count


def render_deck_quicklook(config: dict, deck: Deck, overwrite: bool = False) -> dict:
    root = vault_root(config)
    source_root = Path(config["source_root"]).expanduser()
    pptx = source_root / deck.pptx
    asset_dir = root / config["asset_root"] / deck.slug
    if not pptx.exists():
        raise FileNotFoundError(pptx)
    if asset_dir.exists() and not overwrite and (asset_dir / "slides-meta.json").exists():
        slide_count = len(list(asset_dir.glob("slide-*.png")))
        return {"slug": deck.slug, "pptx": str(pptx), "slides": slide_count, "asset_dir": str(asset_dir.relative_to(root)), "skipped": True, "render_method": "quicklook_chrome"}

    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix=f"ql_{deck.slug}_") as tmp_name:
        tmp = Path(tmp_name)
        result = subprocess.run(["qlmanage", "-p", "-o", str(tmp), str(pptx)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(result.stdout + "\n" + result.stderr)
        previews = list(tmp.glob("*.qlpreview"))
        if not previews:
            raise RuntimeError(f"No QuickLook preview produced for {pptx}")
        preview = previews[0]
        converted = convert_pdf_attachments(preview)
        node_script = root / "tools/pptx_visual_ingest/cdp_screenshot_slides.mjs"
        result = subprocess.run(
            ["node", str(node_script), str(preview / "Preview.html"), str(asset_dir), "slide", config.get("chrome_path", "")],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout + "\n" + result.stderr)
        meta = json.loads((asset_dir / "slides-meta.json").read_text(encoding="utf-8"))
    return {"slug": deck.slug, "pptx": str(pptx), "slides": len(meta), "asset_dir": str(asset_dir.relative_to(root)), "pdf_attachments_converted": converted, "skipped": False, "render_method": "quicklook_chrome"}


def render_deck_pdf_first(config: dict, deck: Deck, overwrite: bool = False) -> dict:
    root = vault_root(config)
    source_root = Path(config["source_root"]).expanduser()
    source = source_root / deck.pptx
    asset_dir = root / config["asset_root"] / deck.slug
    raw_pdf_root = Path(config.get("raw_pdf_root", f"raw/pdfs/{config.get('course_id', 'slides')}"))
    pdf_path = root / raw_pdf_root / f"{deck.slug}.pdf"
    if not source.exists():
        raise FileNotFoundError(source)
    materialize_file(source)
    if asset_dir.exists() and not overwrite and (asset_dir / "slides-meta.json").exists():
        slide_count = len(list(asset_dir.glob("slide-*.png")))
        return {"slug": deck.slug, "source": str(source), "pdf": str(pdf_path), "slides": slide_count, "asset_dir": str(asset_dir.relative_to(root)), "skipped": True, "render_method": "pdf_first"}

    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    asset_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = export_pptx_to_pdf(config, source, pdf_path, overwrite=overwrite)
    meta = render_pdf_to_png(config, pdf_path, asset_dir)
    return {
        "slug": deck.slug,
        "source": str(source),
        "pdf": str(pdf_path.relative_to(root) if pdf_path.is_relative_to(root) else pdf_path),
        "slides": len(meta),
        "asset_dir": str(asset_dir.relative_to(root)),
        "skipped": False,
        "render_method": "pdf_first",
    }


def render_deck(config: dict, deck: Deck, overwrite: bool = False) -> dict:
    method = config.get("render_method", "pdf_first")
    if method in {"pdf_first", "pdf"}:
        return render_deck_pdf_first(config, deck, overwrite=overwrite)
    if method in {"quicklook_chrome", "quicklook"}:
        return render_deck_quicklook(config, deck, overwrite=overwrite)
    raise ValueError(f"Unknown render_method: {method}")


def clean_lines(text: str) -> list[str]:
    raw = []
    for line in text.replace("\xa0", " ").splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line or line in {"‹#›", "<#>", "#"}:
            continue
        if re.fullmatch(r"[•●⮚\-–]+", line):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = line.replace("[['", "\\[\\['")
        raw.append(line)
    lines = []
    for line in raw:
        if not lines or lines[-1] != line:
            lines.append(line)
    return lines


def visual_cue(lines: list[str], img_count: int, slug: str) -> str:
    joined = " ".join(lines).lower()

    def has(*keywords: str) -> bool:
        return any(keyword.lower() in joined for keyword in keywords)

    cues = []
    if has("map-reduce", "mapreduce", "map step", "reduce step", "shuffle", "distributed file"):
        cues.append("关注图中的数据流：input split → mapper → shuffle/group-by-key → reducer，以及节点/存储之间的容错关系。")
    if has("spark", "rdd", "transformation", "action", "partition", "lineage"):
        cues.append("关注 RDD/partition/lineage 的关系，以及哪些操作会触发 shuffle 或 action。")
    if has("apriori", "frequent itemset", "support", "association rule", "confidence"):
        cues.append("关注候选项集如何逐轮生成/剪枝，以及 support、confidence 在图表中的对应位置。")
    if has("pcy", "bitmap") or ("bucket" in joined and has("frequent", "pair")):
        cues.append("关注 hash bucket → bitmap → candidate pair 的剪枝路径。")
    if has("shingle", "jaccard", "minhash", "signature"):
        cues.append("关注从 document/set 到 shingles、signature matrix 的压缩过程。")
    if has("lsh", "band", "bands", "s-curve", "candidate pair"):
        cues.append("关注 signature matrix 按 b 个 bands、每 band r 行切分后如何产生 candidate pairs。")
    if has("recommend", "collaborative", "utility matrix", "pearson", "cosine", "item-based", "user-based"):
        cues.append("关注 utility matrix 中用户/物品相似度如何转成邻居加权预测。")
    if has("community", "girvan", "betweenness", "network") and "linkanalysis" not in slug:
        cues.append("关注图中桥边/高 betweenness edge 如何把 dense communities 分开。")
    if has("stream", "sampling", "bloom", "flajolet", "dgim", "window", "reservoir"):
        cues.append("关注数据流只能单遍扫描时，sample/sketch/window 状态如何随新元素更新。")
    if has("clustering", "cluster", "hierarchical", "k-means", "euclidean", "centroid"):
        cues.append("关注距离定义、簇合并规则或中心点更新如何决定 cluster shape。")
    if has("pagerank", "spider trap", "dead end", "teleport", "taxation", "random surfer", "stationary"):
        cues.append("关注 directed graph 上 rank flow 如何被 teleport/taxation 修正。")
    if has("hits", "hub", "authority"):
        cues.append("关注 hub 与 authority 的互相强化关系。")
    if not cues:
        if img_count >= 4:
            cues.append("本页包含较多视觉元素；优先看 slide image 中的流程、矩阵、图或例题布局，再用下方文字定位概念。")
        elif img_count >= 1:
            cues.append("本页有图示/嵌入对象；图片保留 PPT 视觉上下文，文字用于搜索和快速定位。")
        else:
            cues.append("本页主要是文字结构；用标题和 bullet 抓住定义、动机或步骤。")
    return " ".join(cues[:2])


def frontmatter(title: str, source: str, tags: list[str], related: list[str]) -> str:
    lines = [
        "---",
        "type: summary",
        f'title: "{title}"',
        f"created: {TODAY}",
        f"updated: {TODAY}",
        f"source: {source}",
        "tags: [" + ", ".join(tags) + "]",
        "status: draft",
        "related:",
    ]
    for rel in related:
        lines.append(f'  - "{rel}"')
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def is_macos_placeholder(path: Path) -> bool:
    """Return True for cloud-sync placeholder files that would block on read/write.

    Some older generated vault files can be offloaded by cloud-sync and show the
    `placeholder` flag in `ls -lO`. Opening those files from Python may hang while
    macOS tries to materialize them. For generated visual digests we can safely
    unlink and replace them; for human-facing summary pages we skip link updates
    rather than blocking the ingest run.
    """
    if not path.exists() or sys.platform != "darwin":
        return False
    try:
        result = subprocess.run(
            ["/bin/ls", "-lO", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
    except Exception:
        return False
    return "placeholder" in result.stdout


def write_generated_text(path: Path, text: str) -> None:
    """Write generated markdown without hanging on cloud-sync placeholder placeholders."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        # The visual digest is fully generated, so replacing the prior file is
        # safer than opening an cloud-sync placeholder in-place.
        path.unlink()
    path.write_text(text, encoding="utf-8")


def materialize_file(path: Path) -> None:
    """Force cloud-sync/FileProvider placeholder files to download before tooling uses them."""
    if not is_macos_placeholder(path):
        return
    print(f"materializing cloud-sync placeholder source: {path}")
    with path.open("rb") as handle:
        while handle.read(1024 * 1024):
            pass


def make_digest(config: dict, deck: Deck) -> Path:
    root = vault_root(config)
    source_root = Path(config["source_root"]).expanduser()
    asset_dir_rel = Path(config["asset_root"]) / deck.slug
    asset_dir = root / asset_dir_rel
    meta_path = asset_dir / "slides-meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(meta_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    visual_slug = f"{deck.summary_slug}-slides"
    out = root / config.get("summary_root", "wiki/summaries") / f"{visual_slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    source_abs = source_root / deck.pptx
    source_label = str(source_abs) if config.get("include_absolute_source") else deck.pptx
    pdf_rel = None
    if config.get("render_method", "pdf_first") in {"pdf_first", "pdf"}:
        raw_pdf_root = Path(config.get("raw_pdf_root", f"raw/pdfs/{config.get('course_id', 'slides')}"))
        pdf_rel = raw_pdf_root / f"{deck.slug}.pdf"
        source = str(pdf_rel)
    else:
        source = str(source_abs)
    course_hub = config.get("course_hub", "").removesuffix(".md")
    related = [f"[[{course_hub}]]", f"[[{config.get('summary_root', 'wiki/summaries')}/{deck.summary_slug}]]"]
    for rel in deck.related:
        if rel not in related:
            related.append(rel)

    body = frontmatter(f"{deck.title} — visual slide digest", source, deck.tags, related)
    body += f"# {deck.title} — visual slide digest\n\n"
    body += f"- Original source: `{source_label}`\n"
    if pdf_rel:
        body += f"- Rendered PDF: `[[{pdf_rel}]]`\n"
    body += f"- Rendered slide assets: `{asset_dir_rel}`\n"
    body += f"- Course summary: [[{config.get('summary_root', 'wiki/summaries')}/{deck.summary_slug}]]\n"
    if config.get("render_method", "pdf_first") in {"pdf_first", "pdf"}:
        body += "- Render method: PPTX/PDF → PDF-first fixed layout → PyMuPDF per-page PNG screenshots.\n"
    else:
        body += "- Render method: macOS QuickLook HTML preview → Chrome headless screenshots.\n"
    body += "- Caption note: “Visual cue” 是基于 slide text + 图像对象数量生成的复习提示，不是人工精修 caption。\n\n"
    body += "## Slides\n\n"

    for slide in meta:
        idx = int(slide["index"])
        lines = clean_lines(slide.get("text", ""))
        title_line = lines[0] if lines else f"Slide {idx}"
        img = asset_dir_rel / f"slide-{idx:03d}.png"
        body += f"### Slide {idx:03d} — {title_line}\n\n"
        body += f"![[{img}]]\n\n"
        body += f"**Visual cue:** {visual_cue(lines, int(slide.get('imgCount', 0)), deck.slug)}\n\n"
        if lines:
            body += "**Extracted text:**\n\n"
            for line in lines[:60]:
                body += f"- {line}\n"
            if len(lines) > 60:
                body += f"- … ({len(lines) - 60} more text lines omitted)\n"
            body += "\n"
        else:
            body += "**Extracted text:** _No text extracted from rendered preview._\n\n"
    write_generated_text(out, body)
    return out


def update_summary_link(config: dict, deck: Deck) -> None:
    root = vault_root(config)
    summary_path = root / config.get("summary_root", "wiki/summaries") / f"{deck.summary_slug}.md"
    if not summary_path.exists():
        return
    if is_macos_placeholder(summary_path):
        print(f"skipped summary link update for cloud-sync placeholder file: {summary_path.relative_to(root)}")
        return
    source_abs = str(Path(config["source_root"]).expanduser() / deck.pptx)
    source_label = source_abs if config.get("include_absolute_source") else deck.pptx
    asset_dir = Path(config["asset_root"]) / deck.slug
    visual_slug = f"{deck.summary_slug}-slides"
    text = summary_path.read_text(encoding="utf-8")
    text = re.sub(r"updated: \d{4}-\d{2}-\d{2}", f"updated: {TODAY}", text, count=1)
    marker = f"Visual slide digest: [[{config.get('summary_root', 'wiki/summaries')}/{visual_slug}]]"
    pdf_line = ""
    if config.get("render_method", "pdf_first") in {"pdf_first", "pdf"}:
        raw_pdf_root = Path(config.get("raw_pdf_root", f"raw/pdfs/{config.get('course_id', 'slides')}"))
        pdf_line = f"Rendered PDF: [[{raw_pdf_root / (deck.slug + '.pdf')}]]\n"
    if marker not in text:
        insertion = f"\n{marker}\n\nOriginal source: `{source_label}`\n{pdf_line}Rendered assets: `{asset_dir}`\n"
        if "\nSource text:" in text:
            text = text.replace("\nSource text:", insertion + "\nSource text:", 1)
        else:
            text = text.replace("\n## ", insertion + "\n## ", 1)
    elif pdf_line and "Rendered PDF:" not in text:
        text = text.replace("Rendered assets:", pdf_line + "Rendered assets:", 1)
    summary_path.write_text(text, encoding="utf-8")


def write_manifest(config: dict, items: list[dict]) -> None:
    root = vault_root(config)
    manifest_path = root / config["asset_root"] / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"created": TODAY, "render_method": config.get("render_method", "pdf_first"), "items": items}
    if config.get("include_absolute_source"):
        manifest["source_root"] = config["source_root"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(root: Path, message: str) -> None:
    log_path = root / "log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"## [{TODAY}] tools | {message}\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PPTX/PDF visual ingest workflow")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--extract-text", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--digest", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--deck-slug", action="append", help="Only process matching deck slug; may be passed multiple times")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    root = vault_root(config)
    decks = discover_decks(config)
    if args.deck_slug:
        wanted = set(args.deck_slug)
        decks = [deck for deck in decks if deck.slug in wanted]
    print(f"Vault root: {root}")
    print(f"Source root: {config['source_root']}")
    print(f"Render method: {config.get('render_method', 'pdf_first')}")
    print(f"Decks: {len(decks)}")
    for deck in decks:
        print(f"- {deck.slug}: {deck.title} ({deck.pptx})")
    if args.dry_run:
        return 0

    do_extract = args.all or args.extract_text
    do_render = args.all or args.render
    do_digest = args.all or args.digest
    if not (do_extract or do_render or do_digest):
        print("Nothing to do. Pass --all, --extract-text, --render, or --digest.", file=sys.stderr)
        return 2

    manifest_items: list[dict] = []
    source_root = Path(config["source_root"]).expanduser()
    for deck in decks:
        source = source_root / deck.pptx
        if do_extract:
            if source.suffix.lower() == ".pptx":
                out_md = root / config["raw_text_root"] / f"{deck.slug}.md"
                count = extract_pptx_text(source, out_md, deck, source_root)
                print(f"extracted {count} slides -> {out_md.relative_to(root)}")
            else:
                print(f"skipped XML text extraction for non-PPTX source: {source}")
        if do_render:
            item = render_deck(config, deck, overwrite=args.overwrite)
            manifest_items.append(item)
            print(f"rendered {deck.slug}: {item['slides']} slides skipped={item.get('skipped')} method={item.get('render_method')}")
        if do_digest:
            out = make_digest(config, deck)
            update_summary_link(config, deck)
            print(f"digest -> {out.relative_to(root)}")
    if manifest_items:
        write_manifest(config, manifest_items)
    append_log(root, f"Ran pptx_visual_ingest for {config.get('course_id', 'unknown')} ({len(decks)} decks); modes: extract={do_extract}, render={do_render}, digest={do_digest}, render_method={config.get('render_method', 'pdf_first')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
