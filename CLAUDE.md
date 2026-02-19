# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A shared tools folder for the sideprojects workspace. Contains utilities used across multiple projects.

## Tools

### md2pdf.py — Markdown to PDF converter

Converts markdown files to styled PDFs with multiple style presets.

**Dependencies**: `pandoc`, `tectonic` (for resume), `markdown` + `weasyprint` (for doc/notes)

```bash
# Resume (auto-detected from filename, uses LaTeX via pandoc+tectonic)
python3 tools/md2pdf.py personal/resume.md

# Any markdown with explicit style
python3 tools/md2pdf.py path/to/file.md -s doc
python3 tools/md2pdf.py path/to/file.md -s notes
python3 tools/md2pdf.py path/to/file.md output.pdf -s resume

# No args = builds personal/resume.md -> personal/resume.pdf
python3 tools/md2pdf.py
```

**Styles**:
- `resume` — LaTeX-rendered via pandoc + tectonic. Serif font (Computer Modern), small caps section headers, centered name, thin rules. Classic academic look.
- `doc` — HTML/CSS via weasyprint. Clean sans-serif, blue section headers. Good for guides, writeups, deep dives.
- `notes` — HTML/CSS via weasyprint. Larger font, wider margins. For study/learning material.

**Auto-detection**: filenames containing "resume"/"cv" → resume style, "note"/"study"/"learn" → notes, everything else → doc.

**LaTeX header customization**: The resume style uses a custom LaTeX header embedded in the script. To modify section formatting, list spacing, or title style, edit the `LATEX_HEADER` string in `md2pdf.py`.
