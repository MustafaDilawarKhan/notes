# Lecture Short Notes: a Claude skill

This skill turns a folder of lecture slides into a **printable PDF of short revision notes, one page per lecture**. It works for any number of lectures.

Every page follows the same layout, so you always know where to look:

| Part | What it gives you |
|---|---|
| **Big idea** | The whole lecture in 1–2 sentences |
| **Topic tables** | Every examinable topic in simple words: definitions, comparisons, steps, timelines |
| **Formulas** | Each one with a worked example that uses the lecture's own numbers |
| **Key people** | Every famous name in the lecture, with the idea they're known for |
| **★ Exam must-know** | The 6 facts to revise the night before |
| **Memory hook** | One line to make the lecture stick |

It reads `.pptx`, `.ppt`, `.pdf`, `.docx`, `.doc`, `.txt` and `.md`, including **speaker notes**, tables and SmartArt diagrams.

## Install

**Claude Code:** clone this repo into your skills folder:

```bash
git clone https://github.com/MustafaDilawarKhan/notes.git ~/.claude/skills/lecture-short-notes
```

On Windows, the skills folder is `C:\Users\<you>\.claude\skills\`. You can also download the ZIP from GitHub (Code → Download ZIP), unzip it and rename the folder to `lecture-short-notes`.

**Claude apps:** download the ZIP from GitHub and upload it in the Skills section of Claude's settings.

## Use

Ask Claude in your own words. For example:

- *"Make short notes from my lectures in this folder, one page per lecture, as a PDF."*
- *"I have 12 weeks of slides in ~/Downloads/Biology. Give me a revision PDF for the exam."*
- *"Turn chapters 1–5 of this textbook PDF into one-page summaries with tables."*

## What you need

**Usually nothing.** If your lectures are PowerPoint (`.pptx`) or Word (`.docx`) files and you use a normal Windows, Mac or Linux computer, just ask Claude for notes and it does everything for you.

Behind the scenes the skill uses **Python** and a **web browser** (Chrome, Edge, Chromium or Brave). Claude's apps and most computers already have both: Windows always has Edge.

You only need something extra in two cases:

| Your situation | What to add |
|---|---|
| Your lectures are **PDF** files | `pip install pymupdf` (Claude can do this for you) |
| You have **old** `.ppt` or `.doc` files | LibreOffice or Microsoft Office. You can also re-save the files as `.pptx` or PDF. |

If no browser can be used, you still get your notes as a web page, which you can save as a PDF with **Print → Save as PDF**.

## How it works

1. `scripts/extract_lectures.py` pulls the text out of every lecture file, sorts the files by lecture number and flags slides that are only images.
2. Claude reads each lecture in full and condenses it into one page, using the components in `references/page-components.md`.
3. `scripts/build_pdf.py` puts the pages into `assets/template.html`, shrinks each page's font just enough to fit one sheet, and prints the PDF with your browser in headless mode. It then reports any page that is too dense, so Claude can trim it.

Everything runs on your own computer. Your lecture files are not uploaded anywhere by the scripts.

## Limitations

- Text inside pictures (screenshots, scanned slides, image-only diagrams) can't be read. The skill tells you which slides those were.
- Scanned PDFs need OCR before they can be used.
- The notes come from your slides. Always check them against your course material before an exam.

## License

MIT. See [LICENSE](LICENSE).
