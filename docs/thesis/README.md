# Thesis source

The report is written as one Markdown file per chapter and built into a single Word document.
Diagrams are PlantUML sources rendered to PNG.

## Files

| File | Contents |
|---|---|
| `00-front-matter.md` | Title page fields, declaration, abstract, lists of figures and tables, abbreviations |
| `01-introduction.md` | Chapter 1 |
| `02-system-analysis.md` | Chapter 2 — use cases, contracts, domain model, activity and interaction diagrams |
| `03-system-design.md` | Chapter 3 — architecture, decisions, class diagram, ERDs, components |
| `04-implementation.md` | Chapter 4 — technology, deployment, algorithms, defect narrative |
| `05-testing.md` | Chapter 5 — strategy, test cases, model evaluation |
| `06-conclusion.md` | Chapter 6 |
| `07-references.md` | IEEE reference list |
| `08-appendices.md` | Traceability matrix, provenance, weights, build instructions, repository layout |
| `diagrams/*.puml` | Diagram sources |
| `diagrams/out/*.png` | Rendered diagrams (regenerate rather than edit) |
| `build.sh` | Renders diagrams, assembles the Word document, applies final styling |
| `make_reference.py` | Generates `reference.docx`, the Word style definitions |
| `finalise_docx.py` | Reinstates properties pandoc's writer cannot represent |

## Building

```bash
cd docs/thesis
./build.sh
```

Produces `out/thesis.docx`. Requires `pandoc` and a JDK, both installed during development with:

```bash
winget install --id JohnMacFarlane.Pandoc -e
winget install --id Microsoft.OpenJDK.21 -e
```

## How the Word styling works

Pandoc's default Word output is unsuitable for a thesis: single spacing, no page breaks between
chapters, and a table style with no borders, which makes tables read as loosely aligned text. Two
steps fix this.

**`make_reference.py`** patches pandoc's built-in reference document to give A4 pages with 2.5 cm
margins, 11 pt Calibri justified body text at 1.5 line spacing, a visible heading hierarchy
(22 / 14 / 12 pt), full-grid tables with a shaded header row, and single-spaced 10 pt text inside
table cells.

**`finalise_docx.py`** then patches the built file directly. Pandoc reads the reference document's
styles into an internal model that has no representation for `keepNext` or `pageBreakBefore`, so
both are silently dropped even when present in the reference. They are reinstated afterwards, which
is what makes each chapter start on a new page and stops headings being orphaned at a page foot.

One further detail worth knowing if you edit `make_reference.py`: OOXML requires the children of
`w:pPr` in a fixed schema order (`keepNext`, `pageBreakBefore`, `spacing`, `jc`, `outlineLvl`).
Elements written out of order are discarded without any error.

The table of contents is a native Word field rather than static text, so it stays accurate as you
edit. Right-click it and choose **Update Field** after any change.

## Rebuilding diagrams only

```bash
cd diagrams
java -jar plantuml.jar -tpng -o out *.puml
java -jar plantuml.jar -checkonly *.puml   # syntax check without rendering
```

Diagrams can also be edited with the PlantUML VS Code extension, which previews as you type.

## Before submitting

1. **Fill every ⟨M-nn⟩ marker.** Table 5.1 in Chapter 5 enumerates them. Each requires a run of the
   offline pipeline. A marker left in the submitted document reads as an unfinished result.
2. **Complete the bracketed fields** in `00-front-matter.md` (name, number, institution, supervisor,
   date) and in Appendices B, C and D.
3. **Verify every reference.** Report statistics change between editions; check the year and the
   quoted figure against the edition you cite, and add access dates to online sources.
4. **Rewrite the prose in your own voice.** You have to defend every sentence in the viva, and the
   passages carrying the most marks — the dataset audit narrative in §4.7.1, the fusion argument in
   §3.2.3, the reflection in §6.6 — are the ones an examiner will press hardest on.
5. **Apply your department's template** — font, margins, line spacing, heading numbering, page
   numbering, caption style.
6. **Update the table of contents** — right-click it in Word and choose *Update Field*. Do this last,
   after the template is applied and the page numbering is final.
7. **Check figure and table numbering** against the lists in the front matter after any
   reordering.
