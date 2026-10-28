#!/usr/bin/env python3
"""Extract the text of every lecture file into one .txt per lecture, in lecture order.

Usage:
    python extract_lectures.py <folder-or-files...> --out <dir> [--recursive]

Reads .pptx (slide text, tables, SmartArt, speaker notes), .docx, .pdf, .txt/.md,
and legacy .ppt/.doc (converted first with LibreOffice, or PowerPoint/Word on Windows).

Writes <out>/NN-<name>.txt plus <out>/index.json, and prints a summary with the
detected lecture order and any slides/pages that had no text (usually pictures or
diagrams, or a scanned PDF that needs OCR).

Only the Python standard library is required. For PDFs it uses the first of
PyMuPDF, pypdf, pdfplumber or the `pdftotext` command that is available.
"""
import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SUPPORTED = {".pptx", ".ppt", ".pdf", ".docx", ".doc", ".txt", ".md"}

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"

# "Week 3", "Lecture-03", "Session1", "Chapter_2" ... (max 3 digits so dates are ignored)
LONG_KEY = re.compile(r"(week|lecture|lect|session|chapter|module|unit|topic|class|lesson)[\s_\-.#]*0*(\d{1,3})(?!\d)")
SHORT_KEY = re.compile(r"(?<![a-z])(wk|lec|ch|chap|w|l)[\s_\-.#]*0*(\d{1,3})(?!\d)")
LEADING = re.compile(r"^\s*0*(\d{1,3})(?!\d)")


def lecture_number(name):
    s = name.lower()
    for rx in (LONG_KEY, SHORT_KEY, LEADING):
        m = rx.search(s)
        if m:
            return int(m.group(m.lastindex))
    return None


def clean(text):
    return " ".join((text or "").split())


# ---------------------------------------------------------------- OOXML helpers
def rels_of(z, part):
    """Map rId -> (type, absolute target path) for an OOXML part."""
    p = PurePosixPath(part)
    rels_path = str(p.parent / "_rels" / (p.name + ".rels"))
    if rels_path not in z.namelist():
        return {}
    out = {}
    for rel in ET.fromstring(z.read(rels_path)).iter(REL + "Relationship"):
        target = rel.get("Target", "")
        if rel.get("TargetMode") == "External":
            continue
        full = os.path.normpath(str(p.parent / target)).replace("\\", "/")
        out[rel.get("Id")] = (rel.get("Type", ""), full)
    return out


def para_text(p):
    # <a:br/> is a line break inside a paragraph; keep it as a space so words don't run together
    return clean("".join((el.text or "") if el.tag == A + "t" else " "
                         for el in p.iter() if el.tag in (A + "t", A + "br")))


def table_rows(root):
    rows = []
    for tbl in root.iter(A + "tbl"):
        for tr in tbl.iter(A + "tr"):
            cells = [clean(" ".join(para_text(p) for p in tc.iter(A + "p"))) for tc in tr.findall(A + "tc")]
            if any(cells):
                rows.append("| " + " | ".join(cells) + " |")
        rows.append("")
    return rows


def extract_pptx(path):
    z = zipfile.ZipFile(path)
    names = set(z.namelist())
    # True slide order comes from presentation.xml, not from the file numbers.
    order = []
    if "ppt/presentation.xml" in names:
        prels = rels_of(z, "ppt/presentation.xml")
        pres = ET.fromstring(z.read("ppt/presentation.xml"))
        for sid in pres.iter(P + "sldId"):
            rid = sid.get(R + "id")
            if rid in prels:
                order.append(prels[rid][1])
    if not order:
        order = sorted((n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                       key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))

    lines, empty = [], []
    for i, part in enumerate(order, 1):
        if part not in names:
            continue
        root = ET.fromstring(z.read(part))
        title, body = [], []
        for sp in root.iter(P + "sp"):
            ph = sp.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
            ph_type = ph.get("type") if ph is not None else None
            if ph_type in ("sldNum", "dt", "ftr"):
                continue
            for p in sp.iter(A + "p"):
                t = para_text(p)
                if not t:
                    continue
                if ph_type in ("title", "ctrTitle"):
                    title.append(t)
                else:
                    ppr = p.find(A + "pPr")
                    lvl = int(ppr.get("lvl", "0")) if ppr is not None else 0
                    body.append("  " * lvl + "- " + t)
        body += [r for r in table_rows(root)]
        pics = sum(1 for _ in root.iter(P + "pic"))
        srels = rels_of(z, part)
        notes = []
        for rtype, target in srels.values():
            if target not in names:
                continue
            if rtype.endswith("/diagramData"):  # SmartArt text lives in a separate part
                d = ET.fromstring(z.read(target))
                smart = [para_text(p) for p in d.iter(A + "p")]
                body += ["- [diagram] " + s for s in smart if s]
            elif rtype.endswith("/chart"):
                body.append("- [chart]")
            elif rtype.endswith("/notesSlide"):
                n = ET.fromstring(z.read(target))
                for sp in n.iter(P + "sp"):
                    ph = sp.find(f"{P}nvSpPr/{P}nvPr/{P}ph")
                    if ph is not None and ph.get("type") in ("sldNum", "sldImg", "hdr", "ftr", "dt"):
                        continue
                    notes += [para_text(p) for p in sp.iter(A + "p") if para_text(p)]
        body = [b for b in body if b.strip()]
        lines.append(f"=== Slide {i}: {' / '.join(title) if title else '(no title)'} ===")
        lines += body
        if pics and len(body) < 2:
            lines.append(f"[{pics} picture(s) on this slide - content may be in an image]")
        if notes:
            lines.append("Notes: " + " ".join(notes))
        lines.append("")
        if not body and not notes:
            empty.append(i)
    return "\n".join(lines), len(order), empty, "slide"


def extract_docx(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    lines = []

    def ptext(p):
        return clean("".join((el.text or "") if el.tag == W + "t" else " "
                             for el in p.iter() if el.tag in (W + "t", W + "br", W + "tab")))

    for el in list(body) if body is not None else []:
        if el.tag == W + "p":
            t = ptext(el)
            if not t:
                continue
            style = el.find(f"{W}pPr/{W}pStyle")
            sval = (style.get(W + "val") or "") if style is not None else ""
            if sval.lower().startswith(("heading", "title")):
                lines.append("\n## " + t)
            elif el.find(f"{W}pPr/{W}numPr") is not None:
                lines.append("- " + t)
            else:
                lines.append(t)
        elif el.tag == W + "tbl":
            for tr in el.iter(W + "tr"):
                cells = [clean(" ".join(ptext(p) for p in tc.iter(W + "p"))) for tc in tr.findall(W + "tc")]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
    return "\n".join(lines), None, [], "page"


def extract_pdf(path):
    pages = None
    try:
        import fitz  # PyMuPDF
        with fitz.open(path) as d:
            pages = [pg.get_text() for pg in d]
    except Exception:
        pass
    if pages is None:
        try:
            from pypdf import PdfReader
            pages = [pg.extract_text() or "" for pg in PdfReader(str(path)).pages]
        except Exception:
            pass
    if pages is None:
        try:
            import pdfplumber
            with pdfplumber.open(path) as d:
                pages = [pg.extract_text() or "" for pg in d.pages]
        except Exception:
            pass
    if pages is None and shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True)
        pages = out.stdout.decode("utf-8", "replace").split("\f")
    if pages is None:
        raise RuntimeError("no PDF reader found - install one: pip install pymupdf  (or pypdf)")
    lines, empty = [], []
    for i, t in enumerate(pages, 1):
        lines.append(f"=== Page {i} ===")
        lines.append(t.strip())
        lines.append("")
        if len(t.strip()) < 20:
            empty.append(i)
    return "\n".join(lines), len(pages), empty, "page"


# ---------------------------------------------------------------- legacy formats
def find_soffice():
    for name in ("soffice", "libreoffice"):
        if shutil.which(name):
            return shutil.which(name)
    for c in (r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if os.path.exists(c):
            return c
    return None


def convert_legacy(path, tmp):
    """Convert .ppt -> .pptx or .doc -> .docx. Returns the new path."""
    target_ext = ".pptx" if path.suffix.lower() == ".ppt" else ".docx"
    out = Path(tmp) / (path.stem + target_ext)
    soffice = find_soffice()
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", target_ext[1:], "--outdir", str(tmp), str(path)],
                       capture_output=True, timeout=300)
        if out.exists():
            return out
    if sys.platform == "win32":  # Microsoft Office via COM automation
        q = lambda s: "'" + str(s).replace("'", "''") + "'"
        if target_ext == ".pptx":
            ps = (f"$a = New-Object -ComObject PowerPoint.Application; "
                  f"$p = $a.Presentations.Open({q(path.resolve())}, $true, $false, $false); "
                  f"$p.SaveAs({q(out)}, 24); $p.Close(); $a.Quit()")
        else:
            ps = (f"$a = New-Object -ComObject Word.Application; $a.Visible = $false; "
                  f"$d = $a.Documents.Open({q(path.resolve())}, $false, $true); "
                  f"$d.SaveAs2({q(out)}, 16); $d.Close(); $a.Quit()")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       capture_output=True, timeout=300)
        if out.exists():
            return out
    raise RuntimeError(f"could not convert {path.name}: install LibreOffice, or re-save it as {target_ext} / PDF")


def extract(path, tmp):
    ext = path.suffix.lower()
    if ext in (".ppt", ".doc"):
        path = convert_legacy(path, tmp)
        ext = path.suffix.lower()
    if ext == ".pptx":
        return extract_pptx(path)
    if ext == ".docx":
        return extract_docx(path)
    if ext == ".pdf":
        return extract_pdf(path)
    return path.read_text(encoding="utf-8", errors="replace"), None, [], "page"


# ---------------------------------------------------------------- main
def collect(inputs, recursive, exclude):
    files = []
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            it = p.rglob("*") if recursive else p.iterdir()
            for f in it:
                if not f.is_file() or f.suffix.lower() not in SUPPORTED or f.name.startswith("~$"):
                    continue
                if any(fnmatch.fnmatch(f.name.lower(), pat.lower()) for pat in exclude):
                    print(f"  skipped (matches --exclude): {f.name}")
                    continue
                files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            print(f"! not found: {item}")
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="lecture folder(s) and/or files")
    ap.add_argument("--out", required=True, help="folder for the extracted .txt files")
    ap.add_argument("--recursive", action="store_true", help="also look in sub-folders")
    ap.add_argument("--exclude", action="append", default=["*short-notes*"],
                    help="file-name pattern to skip (repeatable); notes made earlier by this skill are skipped by default")
    args = ap.parse_args()

    files = collect(args.inputs, args.recursive, args.exclude)
    if not files:
        sys.exit("No lecture files found (looked for: " + ", ".join(sorted(SUPPORTED)) + ")")
    files.sort(key=lambda f: (lecture_number(f.name) is None, lecture_number(f.name) or 0, f.name.lower()))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    index, seen = [], {}
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(files, 1):
            num = lecture_number(f.name)
            entry = {"order": i, "number": num, "source": str(f.resolve())}
            try:
                text, units, empty, unit = extract(f, tmp)
            except Exception as e:  # keep going; report at the end
                entry["error"] = str(e)
                index.append(entry)
                continue
            slug = re.sub(r"[^A-Za-z0-9]+", "-", f.stem).strip("-")[:60]
            dest = out_dir / f"{i:02d}-{slug}.txt"
            dest.write_text(f"SOURCE: {f.name}\n\n{text}", encoding="utf-8")
            entry.update(output=str(dest.resolve()), units=units, unit=unit, chars=len(text), empty_units=empty)
            index.append(entry)
            if num is not None:
                seen.setdefault(num, []).append(f.name)
    (out_dir / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    print(f"Extracted {sum('output' in e for e in index)} of {len(index)} file(s) -> {out_dir.resolve()}\n")
    print(f"{'#':>2}  {'lect':>4}  {'size':>7}  {'count':>9}  file")
    for e in index:
        name = Path(e["source"]).name
        if "error" in e:
            print(f"{e['order']:>2}  {'?':>4}  {'-':>7}  {'-':>9}  {name}   ERROR: {e['error']}")
            continue
        count = f"{e['units']} {e['unit']}s" if e["units"] else "-"
        print(f"{e['order']:>2}  {str(e['number'] or '?'):>4}  {e['chars']:>7}  {count:>9}  {name}")
    print()
    for e in index:
        if e.get("empty_units"):
            what = "slides" if e["unit"] == "slide" else "pages"
            hint = "pictures/diagrams only" if e["unit"] == "slide" else "no text - scanned? may need OCR"
            print(f"! {Path(e['source']).name}: {what} {e['empty_units']} have {hint}")
    for num, names in seen.items():
        if len(names) > 1:
            print(f"! lecture number {num} appears in more than one file: {names} - check for duplicates")
    if any(e.get("number") is None for e in index if "error" not in e):
        print("! some files have no lecture number in their name - they are sorted last by name; confirm the order")


if __name__ == "__main__":
    main()
