# md2pdf

Convert markdown files to styled PDFs with multiple presets.

## Styles

| Style | Engine | Use case |
|-------|--------|----------|
| `resume` | LaTeX (tectonic) | Sourabh Bajaj resume template |
| `doc` | weasyprint | Clean document style for guides/writeups |
| `notes` | weasyprint | Relaxed study notes with larger font |

## Usage

```bash
# Auto-detect style from filename
md2pdf resume.md

# Explicit style
md2pdf guide.md -s doc
md2pdf study-notes.md -s notes

# Custom output path
md2pdf input.md output.pdf -s resume
```

Style is auto-detected from the filename: `resume`/`cv` → resume, `note`/`study`/`learn` → notes, everything else → doc.

## Dependencies

```bash
brew install pango tectonic
pip install markdown weasyprint
```

## Install

```bash
# Add alias to your shell
echo 'alias md2pdf="/opt/homebrew/bin/python3 /path/to/md2pdf.py"' >> ~/.zshrc
```
