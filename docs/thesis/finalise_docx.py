#!/usr/bin/env python3
"""Adds the paragraph properties pandoc's docx writer drops when it re-emits reference styles.

Pandoc reads the reference document's styles into its own model and writes them back out. That
model has no representation for keepNext or pageBreakBefore, so both are lost even though they are
present in reference.docx. They are reinstated here, directly in the built file, which is what Word
actually reads.
"""

import re
import shutil
import sys
import zipfile
from pathlib import Path

DOCX = Path(sys.argv[1] if len(sys.argv) > 1 else "out/thesis.docx")

# style id -> properties to reinstate, in OOXML schema order (keepNext then pageBreakBefore).
WANTED = {
    "Heading1": ["<w:keepNext/>", "<w:pageBreakBefore/>"],
    "Heading2": ["<w:keepNext/>"],
    "Heading3": ["<w:keepNext/>"],
    "Heading4": ["<w:keepNext/>"],
    "Heading5": ["<w:keepNext/>"],
    "Caption": ["<w:keepNext/>"],
    "TableCaption": ["<w:keepNext/>"],
    "ImageCaption": ["<w:keepNext/>"],
    "Figure": ["<w:keepNext/>"],
    "CaptionedFigure": ["<w:keepNext/>"],
}


# Insert the requested properties at the head of a style's w:pPr, creating it if absent.
def reinstate(xml: str, style_id: str, props: list[str]) -> tuple[str, bool]:
    pattern = re.compile(
        r'(<w:style [^>]*w:styleId="' + re.escape(style_id) + r'"[^>]*>)(.*?)(</w:style>)',
        re.S,
    )
    match = pattern.search(xml)
    if not match:
        return xml, False

    head, body, tail = match.groups()
    missing = [p for p in props if p not in body]
    if not missing:
        return xml, False

    if "<w:pPr>" in body:
        body = body.replace("<w:pPr>", "<w:pPr>" + "".join(missing), 1)
    else:
        # w:pPr must precede w:rPr inside w:style.
        block = "<w:pPr>" + "".join(missing) + "</w:pPr>"
        body = block + body if "<w:rPr>" not in body else body.replace("<w:rPr>", block + "<w:rPr>", 1)

    return xml[: match.start()] + head + body + tail + xml[match.end() :], True


# Rewrite word/styles.xml inside the docx with the reinstated properties.
def main() -> None:
    if not DOCX.exists():
        sys.exit(f"{DOCX} not found; run build.sh first")

    with zipfile.ZipFile(DOCX) as archive:
        names = archive.namelist()
        contents = {name: archive.read(name) for name in names}

    styles = contents["word/styles.xml"].decode("utf-8")
    changed = []
    for style_id, props in WANTED.items():
        styles, did = reinstate(styles, style_id, props)
        if did:
            changed.append(style_id)
    contents["word/styles.xml"] = styles.encode("utf-8")

    temp = DOCX.with_suffix(".tmp.docx")
    with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in names:
            archive.writestr(name, contents[name])
    shutil.move(str(temp), str(DOCX))

    print(f"finalised {DOCX.name}: reinstated properties on {', '.join(changed) or 'nothing'}")


if __name__ == "__main__":
    main()
