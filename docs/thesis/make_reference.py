#!/usr/bin/env python3
"""Builds reference.docx: patches pandoc's default Word styles into thesis styling."""

import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
BUILD = HERE / ".refbuild"
OUT = HERE / "reference.docx"

PANDOC_CANDIDATES = [
    "pandoc",
    r"C:\Program Files\Pandoc\pandoc.exe",
    str(Path.home() / "AppData/Local/Pandoc/pandoc.exe"),
]

# 11 pt body, 1.5 line spacing. Word measures font in half-points and spacing in twentieths of a point.
BODY_FONT = "Calibri"
HEAD_FONT = "Calibri"
MONO_FONT = "Consolas"


# Locate a usable pandoc executable, or exit with a message.
def find_pandoc() -> str:
    for candidate in PANDOC_CANDIDATES:
        if shutil.which(candidate) or Path(candidate).exists():
            return candidate
    sys.exit("pandoc not found; install it with: winget install --id JohnMacFarlane.Pandoc -e")


# Replace a complete <w:style> block identified by its styleId.
def replace_style(xml: str, style_id: str, replacement: str) -> str:
    pattern = re.compile(
        r'<w:style [^>]*w:styleId="' + re.escape(style_id) + r'"[^>]*>.*?</w:style>',
        re.S,
    )
    if not pattern.search(xml):
        raise KeyError(f"style {style_id!r} not found in reference styles.xml")
    return pattern.sub(replacement, xml, count=1)


# Paragraph style definition with explicit font, size, colour and spacing.
def para_style(style_id, name, based_on, size_half_pt, *, bold=False, italic=False,
               colour=None, before=0, after=0, line=None, page_break=False,
               keep_next=False, font=None, outline=None, justify=False):
    # OOXML requires w:pPr children in schema order (CT_PPrBase): keepNext, pageBreakBefore,
    # spacing, jc, outlineLvl. Word and pandoc silently drop elements that appear out of order.
    props = []
    if keep_next:
        props.append("<w:keepNext/>")
    if page_break:
        props.append("<w:pageBreakBefore/>")
    spacing = f'<w:spacing w:before="{before}" w:after="{after}"'
    if line:
        spacing += f' w:line="{line}" w:lineRule="auto"'
    spacing += "/>"
    props.append(spacing)
    if justify:
        props.append('<w:jc w:val="both"/>')
    if outline is not None:
        props.append(f'<w:outlineLvl w:val="{outline}"/>')

    run = [f'<w:rFonts w:ascii="{font or BODY_FONT}" w:hAnsi="{font or BODY_FONT}" '
           f'w:cs="{font or BODY_FONT}"/>']
    if bold:
        run.append("<w:b/>")
    if italic:
        run.append("<w:i/>")
    if colour:
        run.append(f'<w:color w:val="{colour}"/>')
    run.append(f'<w:sz w:val="{size_half_pt}"/><w:szCs w:val="{size_half_pt}"/>')

    return (
        f'<w:style w:type="paragraph" w:styleId="{style_id}">'
        f'<w:name w:val="{name}"/>'
        f'<w:basedOn w:val="{based_on}"/><w:qFormat/>'
        f'<w:pPr>{"".join(props)}</w:pPr>'
        f'<w:rPr>{"".join(run)}</w:rPr>'
        f"</w:style>"
    )


# Table style with a full grid and a shaded, bold header row.
def table_style() -> str:
    border = ('<w:{side} w:val="single" w:sz="4" w:space="0" w:color="A6A6A6"/>')
    borders = "".join(
        border.format(side=s) for s in ("top", "left", "bottom", "right", "insideH", "insideV")
    )
    return (
        '<w:style w:type="table" w:default="1" w:styleId="Table">'
        '<w:name w:val="Table"/><w:basedOn w:val="TableNormal"/><w:qFormat/>'
        "<w:tblPr>"
        '<w:tblInd w:type="dxa" w:w="0"/>'
        f"<w:tblBorders>{borders}</w:tblBorders>"
        '<w:tblCellMar>'
        '<w:top w:type="dxa" w:w="72"/><w:left w:type="dxa" w:w="108"/>'
        '<w:bottom w:type="dxa" w:w="72"/><w:right w:type="dxa" w:w="108"/>'
        "</w:tblCellMar>"
        "</w:tblPr>"
        # Header row: shaded, bold, thicker rule beneath, repeats across page breaks.
        '<w:tblStylePr w:type="firstRow">'
        "<w:pPr><w:keepNext/></w:pPr>"
        '<w:rPr><w:b/><w:color w:val="1F3864"/></w:rPr>'
        "<w:tcPr>"
        '<w:shd w:val="clear" w:color="auto" w:fill="DEE6F1"/>'
        '<w:tcBorders><w:bottom w:val="single" w:sz="12" w:space="0" w:color="1F3864"/></w:tcBorders>'
        '<w:vAlign w:val="center"/>'
        "</w:tcPr>"
        "</w:tblStylePr>"
        "</w:style>"
    )


# Apply every thesis style override to the reference styles.xml.
def patch_styles(xml: str) -> str:
    # Document-wide defaults: font, size, 1.5 spacing.
    xml = re.sub(
        r"<w:docDefaults>.*?</w:docDefaults>",
        "<w:docDefaults>"
        "<w:rPrDefault><w:rPr>"
        f'<w:rFonts w:ascii="{BODY_FONT}" w:hAnsi="{BODY_FONT}" w:cs="{BODY_FONT}"/>'
        '<w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-GB"/>'
        "</w:rPr></w:rPrDefault>"
        "<w:pPrDefault><w:pPr>"
        '<w:spacing w:before="0" w:after="160" w:line="360" w:lineRule="auto"/>'
        "</w:pPr></w:pPrDefault>"
        "</w:docDefaults>",
        xml,
        flags=re.S,
    )

    xml = replace_style(xml, "Normal", para_style(
        "Normal", "Normal", "Normal", 22, after=160, line=360))
    # Base body text: justified, 1.5 spacing.
    xml = replace_style(xml, "BodyText", para_style(
        "BodyText", "Body Text", "Normal", 22, after=160, line=360, justify=True))
    xml = replace_style(xml, "FirstParagraph", para_style(
        "FirstParagraph", "First Paragraph", "BodyText", 22, after=160, line=360, justify=True))
    # Compact is what pandoc puts inside table cells and tight lists: single-spaced and smaller.
    xml = replace_style(xml, "Compact", para_style(
        "Compact", "Compact", "Normal", 20, before=40, after=40, line=240))

    # Heading hierarchy: each level visibly distinct in size, weight and colour.
    # Chapter heading: 22 pt, and every chapter starts on a fresh page.
    xml = replace_style(xml, "Heading1", para_style(
        "Heading1", "heading 1", "Normal", 44, bold=True, colour="1F3864",
        before=0, after=400, line=240, page_break=True, keep_next=True,
        font=HEAD_FONT, outline=0))
    xml = replace_style(xml, "Heading2", para_style(
        "Heading2", "heading 2", "Normal", 28, bold=True, colour="2E5496",
        before=360, after=140, line=240, keep_next=True, font=HEAD_FONT, outline=1))
    xml = replace_style(xml, "Heading3", para_style(
        "Heading3", "heading 3", "Normal", 24, bold=True, colour="2E5496",
        before=280, after=120, line=240, keep_next=True, font=HEAD_FONT, outline=2))
    xml = replace_style(xml, "Heading4", para_style(
        "Heading4", "heading 4", "Normal", 22, bold=True, italic=True, colour="404040",
        before=240, after=100, line=240, keep_next=True, font=HEAD_FONT, outline=3))
    xml = replace_style(xml, "Heading5", para_style(
        "Heading5", "heading 5", "Normal", 22, italic=True, colour="404040",
        before=200, after=80, line=240, keep_next=True, font=HEAD_FONT, outline=4))

    xml = replace_style(xml, "Title", para_style(
        "Title", "Title", "Normal", 56, bold=True, colour="1F3864",
        before=0, after=200, line=240, font=HEAD_FONT))
    xml = replace_style(xml, "Subtitle", para_style(
        "Subtitle", "Subtitle", "Normal", 28, italic=True, colour="404040",
        before=0, after=400, line=240, font=HEAD_FONT))

    # Captions: centred, small, grey — figure captions are italic in the source.
    for cap in ("Caption", "TableCaption", "ImageCaption"):
        xml = replace_style(xml, cap, (
            f'<w:style w:type="paragraph" w:styleId="{cap}">'
            f'<w:name w:val="{cap}"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:keepNext/><w:spacing w:before="80" w:after="240" w:line="240" '
            'w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii="{BODY_FONT}" w:hAnsi="{BODY_FONT}"/>'
            '<w:i/><w:color w:val="595959"/><w:sz w:val="19"/><w:szCs w:val="19"/></w:rPr>'
            "</w:style>"
        ))

    # Images centred on their own line.
    xml = replace_style(xml, "Figure", (
        '<w:style w:type="paragraph" w:styleId="Figure">'
        '<w:name w:val="Figure"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80" w:line="240" '
        'w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>'
        "</w:style>"
    ))
    xml = replace_style(xml, "CaptionedFigure", (
        '<w:style w:type="paragraph" w:styleId="CaptionedFigure">'
        '<w:name w:val="Captioned Figure"/><w:basedOn w:val="Figure"/><w:qFormat/>'
        '<w:pPr><w:keepNext/><w:jc w:val="center"/></w:pPr>'
        "</w:style>"
    ))

    # Block quotes: indented, left rule, grey.
    xml = replace_style(xml, "BlockText", (
        '<w:style w:type="paragraph" w:styleId="BlockText">'
        '<w:name w:val="Block Text"/><w:basedOn w:val="Normal"/><w:qFormat/>'
        '<w:pPr><w:pBdr><w:left w:val="single" w:sz="18" w:space="10" w:color="B4C6E7"/></w:pBdr>'
        '<w:spacing w:before="200" w:after="200" w:line="300" w:lineRule="auto"/>'
        '<w:ind w:left="360"/></w:pPr>'
        '<w:rPr><w:color w:val="333333"/><w:i/></w:rPr>'
        "</w:style>"
    ))

    # Code: monospace, single-spaced, lightly shaded.
    xml = replace_style(xml, "VerbatimChar", (
        '<w:style w:type="character" w:styleId="VerbatimChar">'
        '<w:name w:val="Verbatim Char"/><w:basedOn w:val="DefaultParagraphFont"/><w:qFormat/>'
        f'<w:rPr><w:rFonts w:ascii="{MONO_FONT}" w:hAnsi="{MONO_FONT}"/>'
        '<w:sz w:val="19"/><w:szCs w:val="19"/>'
        '<w:shd w:val="clear" w:color="auto" w:fill="F2F2F2"/></w:rPr>'
        "</w:style>"
    ))

    xml = replace_style(xml, "Table", table_style())

    # SourceCode paragraph style is emitted by pandoc for fenced blocks; add if absent.
    if 'w:styleId="SourceCode"' not in xml:
        xml = xml.replace("</w:styles>", (
            '<w:style w:type="paragraph" w:styleId="SourceCode">'
            '<w:name w:val="Source Code"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:pBdr>'
            '<w:top w:val="single" w:sz="4" w:space="4" w:color="D9D9D9"/>'
            '<w:left w:val="single" w:sz="4" w:space="4" w:color="D9D9D9"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="4" w:color="D9D9D9"/>'
            '<w:right w:val="single" w:sz="4" w:space="4" w:color="D9D9D9"/>'
            "</w:pBdr>"
            '<w:shd w:val="clear" w:color="auto" w:fill="F7F7F7"/>'
            '<w:spacing w:before="120" w:after="120" w:line="240" w:lineRule="auto"/>'
            "</w:pPr>"
            f'<w:rPr><w:rFonts w:ascii="{MONO_FONT}" w:hAnsi="{MONO_FONT}"/>'
            '<w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
            "</w:style></w:styles>"
        ))

    return xml


# Set A4 page size with 2.5 cm margins in the reference document body.
def patch_document(xml: str) -> str:
    return re.sub(
        r"<w:sectPr[^>]*>.*?</w:sectPr>",
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1418" w:right="1418" w:bottom="1418" w:left="1701" '
        'w:header="709" w:footer="709" w:gutter="0"/>'
        '<w:cols w:space="708"/><w:docGrid w:linePitch="360"/>'
        "</w:sectPr>",
        xml,
        flags=re.S,
    )


# Generate the patched reference document.
def main() -> None:
    pandoc = find_pandoc()
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)

    default_ref = BUILD / "default.docx"
    with open(default_ref, "wb") as handle:
        subprocess.run(
            [pandoc, "--print-default-data-file", "reference.docx"],
            stdout=handle, check=True,
        )

    extracted = BUILD / "x"
    with zipfile.ZipFile(default_ref) as archive:
        archive.extractall(extracted)

    styles_path = extracted / "word" / "styles.xml"
    styles_path.write_text(
        patch_styles(styles_path.read_text(encoding="utf-8")), encoding="utf-8"
    )

    doc_path = extracted / "word" / "document.xml"
    doc_path.write_text(
        patch_document(doc_path.read_text(encoding="utf-8")), encoding="utf-8"
    )

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(extracted.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(extracted).as_posix())

    shutil.rmtree(BUILD)
    print(f"wrote {OUT.relative_to(HERE)}")


if __name__ == "__main__":
    main()
