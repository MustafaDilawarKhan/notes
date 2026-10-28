# Page components

`body.html` contains only `<section class="page">` elements, one per lecture. `scripts/build_pdf.py` wraps them in `assets/template.html`, which supplies all the CSS, a colour per page and the auto-fit script. You never write `<html>`, `<head>` or `<style>`.

## Contents
1. Page skeleton
2. Blocks (the building unit)
3. Table patterns: definitions, comparison, grouped rows, steps, timeline, winner row, matrix
4. Small parts: formula, case box, note, colours
5. Key people table
6. Footer: exam must-know and memory hook
7. Characters and escaping
8. Complete example page

---

## 1. Page skeleton

```html
<section class="page">
  <div class="hd">
    <div class="wk"><small>LECTURE</small><b>3</b></div>
    <div><h1>Lecture title in plain words</h1>
      <div class="src"><b>Textbook:</b> Author, Ch. 4 &nbsp;·&nbsp; <b>Anchor book:</b> <i>Title</i> — Author (Year)</div></div>
    <div class="pg">{{COURSE}}</div>
  </div>
  <div class="idea">One or two sentences: the whole lecture in a nutshell, with the key terms in <b>bold</b>.</div>

  <div class="cols">
    <!-- 6–10 blocks; the last one is Key people -->
  </div>

  <div class="ft">
    <div class="must"><b class="t">EXAM MUST-KNOW</b><ol> <!-- exactly 6 <li> --> </ol></div>
    <div class="hook">One line that makes the lecture stick.</div>
  </div>
</section>
```

- `.wk`: change `LECTURE` to `WEEK`, `CHAPTER`, `UNIT` or `TOPIC` to match the course's own word.
- `.src`: list only the sources that exist. If there is none, use `<div class="src">Main topics: A · B · C</div>`.
- `{{COURSE}}` is replaced by `--course`, for example "CS101 · Short notes".
- Colours are assigned automatically per page. To force one, use `<section class="page" style="--h:140">`, where the value is a hue from 0 to 360.

## 2. Blocks

```html
<div class="blk"><h2>Heading <span>(short qualifier)</span></h2>
  <table>…</table>
  <p class="note">Optional one-line takeaway.</p>
</div>
```

- Blocks flow down the left column and then the right one. A block never splits across columns.
- To span both columns with a very wide table, use `<div class="blk wide">`. Use it rarely, because it breaks the column flow.
- A bullet block holds at most 2–4 `<li>`, and each one starts with a bold label: `<li><b>Label:</b> plain-words point.</li>`.

## 3. Table patterns

The first column is bold automatically, because it is usually the label. Add `class="plain"` to the table when both sides should look equal, as in "X vs Y" tables.

**Definitions** (term, then a simple meaning):
```html
<table><tr><th>Term</th><th>Simple meaning</th></tr>
  <tr><td>Opportunity cost</td><td>What you give up by choosing one option over the next best</td></tr>
</table>
```

**Comparison** (A vs B, laid out as rows of aspects):
```html
<table><tr><th></th><th>Engineer</th><th>Manager</th></tr>
  <tr><td>Focus</td><td>Technical tasks</td><td>People &amp; projects</td></tr>
  <tr><td>Asks</td><td><b>HOW</b> — “Will it work?”</td><td><b>WHY</b> — “Will it add value?”</td></tr>
</table>
```

**Two lists side by side** (pros/cons, hygiene/motivators):
```html
<table class="plain"><tr><th>Pros</th><th>Cons</th></tr>
  <tr><td>Money · authority · growth</td><td>Long hours · stress</td></tr>
</table>
```

**Grouped rows** (theories grouped by school or type). The group row spans all columns:
```html
<table><tr><th>Who</th><th>Key idea</th></tr>
  <tr class="gp"><td colspan="2">Content theories — WHAT people need</td></tr>
  <tr><td>Maslow</td><td>5 levels: …</td></tr>
  <tr class="gp"><td colspan="2">Process theories — HOW people decide</td></tr>
  <tr><td>Vroom</td><td>M = E × I × V</td></tr>
</table>
```

**Steps** (7 steps fit in 4 rows when you use two step-columns):
```html
<table><tr><th>#</th><th>Step</th><th>#</th><th>Step</th></tr>
  <tr><td>1</td><td>Recognize</td><td>5</td><td>Evaluate</td></tr>
  …
</table>
```

**Timeline** (`class="n"` stops a short cell from wrapping):
```html
<table><tr><th class="n">When</th><th>What</th><th>Why it matters</th></tr>
  <tr><td class="n">1911</td><td>Taylor’s principles</td><td>Efficiency through measurement</td></tr>
</table>
```

**Winner row** (best option or correct answer, shown in green): `<tr class="win">…</tr>`. For a single winning cell, use `<td class="win">`.

**Matrix** (SWOT, 2×2 grids):
```html
<table><tr><th></th><th>Positive</th><th>Negative</th></tr>
  <tr><td>Internal</td><td><span class="good">Strengths</span> → Build on</td><td><span class="bad">Weaknesses</span> → Fix</td></tr>
  <tr><td>External</td><td><span class="good">Opportunities</span> → Exploit</td><td><span class="bad">Threats</span> → Avoid</td></tr>
</table>
```

Keep tables to 2–4 columns. Each column is only about 45 characters wide, so a 5-column table squeezes the cells to one word per line. When a table gets too wide, split it in two or make it `.blk wide`.

## 4. Small parts

- **Formula:** `<span class="f">EV = Σ (p × outcome)</span>`. Follow it with a worked example that uses the slide's own numbers: `<p><b>Example:</b> 0.3×110 + 0.7×100 = <b>103</b></p>`.
- **Case or story box:** `<p class="case"><b>Case name (year):</b> what happened → the lesson.</p>`. Inside a list, use `<li class="case">`.
- **Muted note:** `<p class="note">…</p>`, for a one-line takeaway, a caveat or a "used for" line.
- **Colour words:** `<span class="good">`, `<span class="bad">` and `<span class="warn">` (green, red, amber).

## 5. Key people table

Every page ends its body with this table. It lists each person named in the lecture together with the idea they are known for, with one line per person or pair.

```html
<div class="blk"><h2>Key people</h2>
  <table class="people"><tr><th>Name</th><th>Known for</th></tr>
    <tr><td>Abraham Maslow</td><td>Hierarchy of Needs</td></tr>
    <tr><td>Blake &amp; Mouton</td><td>Leadership Grid</td></tr>
  </table>
</div>
```

If the lecture names nobody, replace this block with **Key terms**, a definitions table of the 5–8 most examinable terms.

## 6. Footer

```html
<div class="ft">
  <div class="must"><b class="t">EXAM MUST-KNOW</b>
    <ol>
      <li>Short, testable fact.</li>   <!-- exactly 6, each under ~60 characters -->
    </ol></div>
  <div class="hook">Theories in order: <b>Born</b> → <b>Behave</b> → <b>Adapt</b>.</div>
</div>
```

The six must-know items are the things most likely to be examined: definitions, the parts of a model, formulas with an answer, and "X vs Y". The memory hook is a mnemonic, a 3–4 word chain, or an analogy.

## 7. Characters and escaping

- Escape `&` as `&amp;` and `<` as `&lt;` in text.
- For subscripts and superscripts, use `<sub>` and `<sup>`, as in `F<sub>new</sub>` and `x<sup>2</sup>`. Unicode subscript digits are missing from many fonts.
- Avoid emoji, because they render as empty boxes on systems without an emoji font. These symbols are safe: ★ ✔ ✗ → ← ↑ ↓ ≈ ≠ ≤ ≥ × ÷ − ± Σ α β σ · …

---

## 8. Complete example page

This shows what a finished page looks like. It is about generic economics content, so copy the structure, not the content. It is deliberately short: a real lecture usually has 6–10 fuller blocks that fill the sheet, and the footer stays pinned to the bottom either way.

```html
<section class="page">
  <div class="hd">
    <div class="wk"><small>LECTURE</small><b>3</b></div>
    <div><h1>Supply, Demand &amp; Market Equilibrium</h1>
      <div class="src"><b>Textbook:</b> Principles of Economics, Ch. 4</div></div>
    <div class="pg">{{COURSE}}</div>
  </div>
  <div class="idea">Prices are set where <b>what buyers want</b> (demand) meets <b>what sellers offer</b> (supply). A change in price <b>moves along</b> a curve; a change in anything else <b>shifts</b> the curve. Price controls away from equilibrium cause <b>shortages</b> or <b>surpluses</b>.</div>

  <div class="cols">
    <div class="blk"><h2>The two laws</h2>
      <table><tr><th></th><th>Law of demand</th><th>Law of supply</th></tr>
        <tr><td>Rule</td><td>Price ↑ → quantity demanded ↓</td><td>Price ↑ → quantity supplied ↑</td></tr>
        <tr><td>Curve</td><td>Slopes down</td><td>Slopes up</td></tr>
        <tr><td>Why</td><td>Substitutes, less buying power</td><td>More profit per unit</td></tr>
      </table>
    </div>

    <div class="blk"><h2>Movement vs shift</h2>
      <table><tr><th>Change in…</th><th>Effect</th></tr>
        <tr><td>The good’s own price</td><td><b>Movement along</b> the curve</td></tr>
        <tr><td>Income, tastes, related prices, expectations, no. of buyers</td><td><b>Demand curve shifts</b></td></tr>
        <tr><td>Input costs, technology, taxes, no. of sellers</td><td><b>Supply curve shifts</b></td></tr>
      </table>
    </div>

    <div class="blk"><h2>Equilibrium <span>(worked example)</span></h2>
      <p><span class="f">Qd = 100 − 2P</span> &nbsp; <span class="f">Qs = 20 + 2P</span></p>
      <p>Set Qd = Qs → 100 − 2P = 20 + 2P → 4P = 80 → <b>P = 20, Q = 60</b>.</p>
    </div>

    <div class="blk"><h2>Price elasticity of demand</h2>
      <p><span class="f">PED = %ΔQd ÷ %ΔP</span></p>
      <table><tr><th>|PED|</th><th>Name</th><th>Example</th></tr>
        <tr><td>&gt; 1</td><td>Elastic</td><td>Restaurant meals</td></tr>
        <tr><td>&lt; 1</td><td>Inelastic</td><td>Petrol, medicine</td></tr>
      </table>
    </div>

    <div class="blk"><h2>Price controls</h2>
      <table><tr><th>Control</th><th>Set…</th><th>Result</th></tr>
        <tr><td>Ceiling (rent control)</td><td>Below equilibrium</td><td><span class="bad">Shortage</span></td></tr>
        <tr><td>Floor (minimum wage)</td><td>Above equilibrium</td><td><span class="bad">Surplus</span></td></tr>
      </table>
    </div>

    <div class="blk"><h2>Key people</h2>
      <table class="people"><tr><th>Name</th><th>Known for</th></tr>
        <tr><td>Adam Smith</td><td>“Invisible hand” of markets (1776)</td></tr>
        <tr><td>Alfred Marshall</td><td>Supply–demand diagram; “scissors” analogy</td></tr>
      </table>
    </div>
  </div>

  <div class="ft">
    <div class="must"><b class="t">EXAM MUST-KNOW</b>
      <ol>
        <li>Demand slopes down, supply slopes up.</li>
        <li>Own price → movement; other factors → shift.</li>
        <li>Equilibrium: Qd = Qs (example P = 20, Q = 60).</li>
        <li>|PED| &gt; 1 elastic, &lt; 1 inelastic.</li>
        <li>Ceiling below equilibrium → shortage.</li>
        <li>Floor above equilibrium → surplus.</li>
      </ol></div>
    <div class="hook">Marshall’s <b>scissors</b>: price is cut by two blades, supply <b>and</b> demand.</div>
  </div>
</section>
```
