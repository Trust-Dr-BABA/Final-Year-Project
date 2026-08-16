#!/usr/bin/env bash
# Assembles the thesis chapters into a single Word document.
set -euo pipefail

cd "$(dirname "$0")"

PANDOC="${PANDOC:-pandoc}"
command -v "$PANDOC" >/dev/null 2>&1 || PANDOC="/c/Program Files/Pandoc/pandoc.exe"
command -v "$PANDOC" >/dev/null 2>&1 || PANDOC="/c/Users/AJ/AppData/Local/Pandoc/pandoc.exe"

JAVA_HOME_GUESS="/c/Program Files/Microsoft/jdk-21.0.12.8-hotspot"
JAVA="java"
command -v "$JAVA" >/dev/null 2>&1 || JAVA="$JAVA_HOME_GUESS/bin/java"

mkdir -p out

# Render diagrams if the jar is present and any source is newer than its PNG.
if [ -f diagrams/plantuml.jar ] && command -v "$JAVA" >/dev/null 2>&1; then
  echo "Rendering diagrams…"
  (cd diagrams && "$JAVA" -jar plantuml.jar -tpng -o out ./*.puml)
else
  echo "Skipping diagram render (plantuml.jar or java unavailable); using existing PNGs."
fi

# Regenerate the Word style definitions (page breaks, table borders, 1.5 spacing).
if [ ! -f reference.docx ] || [ make_reference.py -nt reference.docx ]; then
  echo "Building reference.docx…"
  python make_reference.py
fi

echo "Building thesis.docx…"
"$PANDOC" \
  00-front-matter.md \
  01-introduction.md \
  02-system-analysis.md \
  03-system-design.md \
  04-implementation.md \
  05-testing.md \
  06-conclusion.md \
  07-references.md \
  --from markdown \
  --reference-doc=reference.docx \
  --resource-path=. \
  -o out/thesis.docx

# Reinstate the properties pandoc's writer cannot represent (page breaks, keep-with-next).
python finalise_docx.py out/thesis.docx

echo "Wrote out/thesis.docx"
