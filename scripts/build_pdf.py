#!/usr/bin/env python3
"""Wrap the page sections in the template, print them to PDF, and report how well each page fits.

Usage:
    python build_pdf.py <body.html> --out <notes.pdf> [--title "Course - Short Notes"]
                        [--course "CS101 · Short notes"] [--paper a4|letter]
                        [--previews <dir>] [--browser <path>]

<body.html> holds only the <section class="page"> elements (see references/page-components.md).
The template's script shrinks each page's font until it fits one sheet; this script reads the
resulting size per page and prints OK / TIGHT / TOO DENSE so you know which pages to trim.

Printing uses a Chromium-based browser in headless mode (Chrome, Edge, Chromium or Brave;
override with --browser or the CHROME_PATH environment variable). If none is found it falls
back to Playwright (pip install playwright && playwright install chromium).
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template.html"
OK_PT, TIGHT_PT = 8.0, 7.4


def find_browser(explicit=None):
    if explicit:
        return explicit
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge", "microsoft-edge-stable", "msedge", "chrome", "brave-browser"):
        if shutil.which(name):
            return shutil.which(name)
    local = os.environ.get("LOCALAPPDATA", "")
    for c in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              os.path.join(local, r"Google\Chrome\Application\chrome.exe"),
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              "/Applications/Chromium.app/Contents/MacOS/Chromium",
              "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"):
        if c and os.path.exists(c):
            return c
    return None


def run_browser(browser, url, extra):
    with tempfile.TemporaryDirectory() as profile:
        cmd = [browser, "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               "--disable-extensions", f"--user-data-dir={profile}"]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")
        r = subprocess.run(cmd + extra + [url], capture_output=True, timeout=180)
    return r.stdout.decode("utf-8", "replace")


def build_with_browser(browser, html_path, pdf_path):
    url = html_path.resolve().as_uri()
    dom = run_browser(browser, url, ["--dump-dom"])
    run_browser(browser, url, ["--no-pdf-header-footer", "--print-to-pdf-no-header",
                               f"--print-to-pdf={pdf_path.resolve()}"])
    return re.findall(r'data-fit="([^"]*)"', dom)


def build_with_playwright(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page()
        page.goto(html_path.resolve().as_uri())
        fits = page.eval_on_selector_all(".page", "els => els.map(e => e.dataset.fit)")
        page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
        b.close()
    return fits


def count_pdf_pages(pdf_path):
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        pass
    try:
        import fitz
        with fitz.open(pdf_path) as d:
            return d.page_count
    except Exception:
        pass
    data = pdf_path.read_bytes()
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def make_previews(pdf_path, out_dir, dpi=100):
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        import fitz
        with fitz.open(pdf_path) as d:
            for i, pg in enumerate(d, 1):
                pg.get_pixmap(dpi=dpi).save(str(out_dir / f"page-{i:02d}.png"))
        return True
    except Exception:
        pass
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(str(pdf_path))
        for i in range(len(doc)):
            doc[i].render(scale=dpi / 72).to_pil().save(str(out_dir / f"page-{i + 1:02d}.png"))
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("body", help="HTML file containing the <section class=\"page\"> elements")
    ap.add_argument("--out", required=True, help="output PDF path")
    ap.add_argument("--title", default="Short Notes", help="PDF document title")
    ap.add_argument("--course", default="Short notes", help="label shown top-right on every page ({{COURSE}})")
    ap.add_argument("--paper", choices=["a4", "letter"], default="a4")
    ap.add_argument("--previews", help="folder for PNG previews of each page (needs PyMuPDF or pypdfium2)")
    ap.add_argument("--browser", help="path to Chrome/Edge/Chromium")
    args = ap.parse_args()

    body = Path(args.body).read_text(encoding="utf-8")
    if "<!--BODY-->" not in TEMPLATE.read_text(encoding="utf-8"):
        sys.exit(f"template is missing the <!--BODY--> marker: {TEMPLATE}")
    doc = (TEMPLATE.read_text(encoding="utf-8")
           .replace("<!--BODY-->", body)
           .replace("{{TITLE}}", html.escape(args.title))
           .replace("{{COURSE}}", html.escape(args.course)))
    if args.paper == "letter":
        doc = doc.replace("size: A4;", "size: letter;").replace("width: 210mm; height: 297mm;",
                                                              "width: 215.9mm; height: 279.4mm;")
    expected = len(re.findall(r'<section\s[^>]*class="[^"]*\bpage\b', body))

    pdf_path = Path(args.out)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    html_path = Path(args.body).with_name(Path(args.body).stem + ".full.html")
    html_path.write_text(doc, encoding="utf-8")

    browser = find_browser(args.browser)
    if browser:
        fits = build_with_browser(browser, html_path, pdf_path)
    else:
        try:
            fits = build_with_playwright(html_path, pdf_path)
        except Exception as e:
            print("No Chromium-based browser found and Playwright is unavailable "
                  f"({type(e).__name__}).\nInstall Chrome/Edge/Chromium, or: pip install playwright && "
                  "playwright install chromium.\nManual fallback: open this file in Chrome/Edge and Print -> "
                  f"Save as PDF (Margins: None, Background graphics: on):\n  {html_path.resolve()}")
            sys.exit(2)

    if not pdf_path.exists():
        sys.exit("PDF was not created - try passing --browser <path to chrome/msedge>")
    pages = count_pdf_pages(pdf_path)

    print(f"PDF: {pdf_path.resolve()}")
    print(f"Pages: {pages} (sections in body: {expected})" + ("" if pages == expected else "   <-- MISMATCH"))
    print(f"HTML: {html_path.resolve()}\n")
    print("Page  font   status")
    trim = []
    for i, fit in enumerate(fits, 1):
        size = float(fit.split()[0])
        if "OVERFLOW" in fit or size < TIGHT_PT:
            status = "TOO DENSE - trim this page" + (" (text is cut off)" if "OVERFLOW" in fit else "")
            trim.append(i)
        elif size < OK_PT:
            status = "TIGHT - prints fine, trim if easy"
        else:
            status = "OK"
        print(f"{i:>4}  {size:>4.1f}pt  {status}")
    if not fits:
        print("  (could not read page fit data)")
    if trim:
        print(f"\nACTION: pages {trim} are below {TIGHT_PT}pt - shorten them and rebuild.")

    if args.previews:
        if make_previews(pdf_path, Path(args.previews)):
            print(f"\nPreviews: {Path(args.previews).resolve()}")
        else:
            print("\nPreviews skipped (pip install pymupdf to enable)")


if __name__ == "__main__":
    main()
