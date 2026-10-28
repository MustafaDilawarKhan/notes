---
name: lecture-short-notes
description: Turn lecture slides or notes (PPTX, PPT, PDF, DOCX, TXT, a whole folder of them) into a printable PDF of short revision notes with exactly one A4 page per lecture, built mostly from compact tables. Each page has a "big idea", every examinable topic in simple words, a "key people" table of famous names and what they are known for, formulas with worked examples, a 6-point exam must-know box and a memory hook. Use this whenever someone wants short notes, revision notes, exam notes, a cheat sheet, study notes, a summary sheet or "notes from my lectures/slides/chapters", especially as a PDF and especially one page per lecture, week or chapter. Use it even if they don't say "one page" or name a format, and for any number of lectures (1 to 30+).
license: MIT
compatibility: Needs Python 3.8+ and a Chromium-based browser (Chrome, Edge, Chromium or Brave) or Playwright. Optional extras are PyMuPDF or pypdf (PDF input and previews) and LibreOffice or MS Office (old .ppt/.doc files).
---

# Lecture Short Notes

The goal is a student who can revise a whole lecture from **one page** and not miss anything examinable. Two forces pull against each other here. **Completeness** means every named theory, model, person, formula, list and case the lecturer covered. **Brevity** means one page, in simple words. Tables resolve that tension: a 3-column table says in 4 lines what prose needs 12 for, and it lets the eye compare instead of re-read.

The result is a PDF where every page has the same anatomy, so students learn where to look:

```
┌ LECTURE n │ Title ··· sources ─────────────────────┐
│ BIG IDEA: the whole lecture in 1–2 sentences       │
│ ┌ block: table ┐  ┌ block: table ┐                 │
│ ┌ block: table ┐  ┌ block: bullets┐   2 columns of  │
│ ┌ block: formula + worked example ┐   6–10 blocks  │
│ ┌ block ...    ┐  ┌ KEY PEOPLE   ┐                 │
│ ★ EXAM MUST-KNOW (6 items)   ·   Memory hook        │
└─────────────────────────────────────────────────────┘
```

## Workflow

Paths below are relative to this skill's folder: `scripts/…`, `assets/…`, `references/…`. Use a scratch or temporary folder as the work folder, and save only the final PDF where the user's lectures are (or wherever they ask).

### 1. Extract the lectures

```bash
python scripts/extract_lectures.py "<lecture folder or files>" --out "<work>/extracted"
```

The script writes one `.txt` per lecture, covering slide text, tables, SmartArt and **speaker notes**. It prints the order it detected from the file names ("Week 3", "Lecture_03", "Session1", …), and it flags:
- **Slides with no text.** These are usually diagrams or pictures. Cover the topic from the surrounding slides, and tell the user which slides were images.
- **PDF pages with no text.** The file is probably scanned. Tell the user it needs OCR, or ask for a text-based copy.
- **Files with no lecture number, or duplicate numbers.** Infer the order from the content (an introduction is usually first). If it's still ambiguous, confirm it with the user.

Old `.ppt` and `.doc` files are converted with LibreOffice, or with PowerPoint/Word on Windows. If neither is available, ask the user to save the files as `.pptx` or `.pdf`.

### 2. Read every lecture fully, one at a time

Read each extracted file completely, **including the `Notes:` lines**. Lecturers often put the actual explanation, the worked numbers or "this is important" in the speaker notes. Skimming is exactly how important topics get lost, so don't skim.

For more than about 3 lectures, work in a loop: read lecture N, write its page, then move on to N+1. That way each lecture is fresh in mind while you condense it. When lectures overlap (recap slides, a topic split across weeks), give full detail where the topic is actually taught and a one-line pointer elsewhere ("see Lecture 1").

### 3. Decide what goes on the page

Capture everything in this inventory that the lecture contains:
- **Named theories, models, frameworks, laws and principles, with all their parts.** If a model has 5 levels, list all 5, because examiners ask for the parts.
- **People.** Everyone named alongside an idea goes into the Key people table.
- **Definitions.** Give one simple line each, and keep the technical term in **bold** so the student learns the exam's vocabulary.
- **Lists, steps and processes.** Number them.
- **Comparisons (A vs B).** Turn them into tables.
- **Formulas.** Add one worked example using **the slide's own numbers**.
- **Cases, stories and examples.** One line each: what happened → the lesson.
- **Emphasized numbers and dates,** such as statistics the lecturer repeated or results of studies.
- **The anchor book or reading,** if the course pairs lectures with one. Show how it links to the textbook ideas.

Drop agenda and learning-objective slides, "any questions?" slides, repeated slides, decorative quotes and filler. Keep assessment or marks information as a single line on the first page only.

**Simple words, exact terms.** Write as if explaining to a smart friend who missed class. Use short phrases and arrows (→) instead of full sentences. Keep the real term and gloss it, for example: "**Bounded rationality** — limited time & info, so we pick 'good enough'". Don't replace the term with the gloss, because the exam will use the term.

**Accuracy.** Never invent facts, numbers, dates or attributions. The notes will be trusted for an exam. Memory hooks, mnemonics and plain-language rewording are your own and that's expected. If you add anything that isn't in the slides (a well-known first name, an obvious label), keep it uncontroversial and list it in your final message so the student knows.

### 4. Write the pages

Read `references/page-components.md` before writing the first page. It has the page skeleton, every component, the table patterns and a complete example page. Then write **only** the `<section class="page">` elements, one per lecture, into `<work>/body.html`. The template supplies the CSS, a colour per page and the auto-fit script.

Each page follows the same layout:
1. **Header.** LECTURE/WEEK/CHAPTER + number, a plain-words title, and the sources (textbook chapter, anchor book) when they're known.
2. **Big idea.** 1–2 sentences with the key words in bold. If the student read only this, what should they know?
3. **6–10 blocks in two columns.** Each block is a small heading plus a table (preferred) or 2–4 bullets, ordered as the lecture teaches them. Pick the table pattern that fits the content: definitions, comparison, grouped rows, steps, timeline or matrix.
4. **Key people.** This is the last block, with one line per person (Name → known for). If nobody is named, use **Key terms** instead.
5. **Footer.** Exactly 6 exam must-know items (short and testable) plus one memory hook.

### 5. Build and check

```bash
python scripts/build_pdf.py "<work>/body.html" --out "<destination>/<Course>-Short-Notes.pdf" \
  --title "<Course> — Short Notes" --course "<Course code> · Short notes" --previews "<work>/previews"
```

Each page's font shrinks automatically until it fits one sheet. The script reports the final size per page:

| Report | Meaning | What to do |
|---|---|---|
| **OK** (≥ 8.0pt) | Comfortable to read when printed | Nothing |
| **TIGHT** (7.4–7.9pt) | Prints fine, a bit dense | Trim if it's easy |
| **TOO DENSE** (< 7.4pt or overflow) | Hard to read, or text is cut off | Trim and rebuild |

To trim a page, do these in order: shorten the wording (phrases, not sentences), merge small tables, cut cases to one line, and drop minor detail. Keep every named concept, because those are what the student can't afford to lose. Splitting a lecture across two pages breaks the "one page per lecture" promise, so only do it if the user agrees.

If previews were created, look at them before delivering, and check that:
- the page count equals the lecture count;
- no table column is squeezed to one or two words per line (fix with fewer columns, a `class="n"` cell, or a `wide` block);
- no orphan word sits alone on a line in a heading;
- there is no large empty area. A short page is fine, but a half-empty page means you may have left something out.

### 6. Deliver

Give the user:
- the PDF path;
- a short table mapping page → lecture → main topics;
- what you checked (page count, font sizes);
- any caveats: image-only slides, a guessed lecture order, and anything you added that wasn't in the slides.

Keep the message short. The PDF is the deliverable.

## Variations

- **US Letter paper.** Pass `--paper letter`.
- **Language.** Write in the lectures' language unless the user asks otherwise.
- **Textbook chapters instead of slides.** Use the same workflow, with one page per chapter. A single big PDF is fine: use the `=== Page N ===` markers to find the chapter boundaries.
- **Overview or cover page.** Only add one if the user asks. It's an extra `<section class="page">` with a table mapping lecture → main ideas → how the lectures connect.
- **No browser available.** `build_pdf.py` falls back to Playwright. If that's also missing, it prints the path of the full HTML, which the user can open in any Chromium browser and save with Print → Save as PDF (Margins: None, Background graphics: on).
