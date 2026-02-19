#!/opt/homebrew/bin/python3
"""Convert markdown files to styled PDFs.

Usage:
    md2pdf [input.md] [output.pdf] [--style resume|doc|notes]

Styles:
    resume  — LaTeX Sourabh Bajaj template (via tectonic)
    doc     — Clean document style for guides/writeups (via weasyprint)
    notes   — Relaxed study notes with larger font (via weasyprint)
"""

import argparse
import re
import subprocess
from pathlib import Path
import markdown
import weasyprint

# ── LaTeX resume template (Sourabh Bajaj style) ─────────────────────────────

LATEX_PREAMBLE = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{fancyhdr}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.375in}
\addtolength{\evensidemargin}{-0.375in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\newcommand{\resumeSubheading}[4]{
  \vspace{-1pt}\item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-5pt}
}

\renewcommand{\labelitemii}{$\circ$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=*]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

\setlength{\footskip}{4.08003pt}
\begin{document}
"""


def escape_tex(t):
    """Escape LaTeX special chars, preserving markdown formatting markers."""
    t = t.replace('&', r'\&')
    t = t.replace('%', r'\%')
    t = t.replace('#', r'\#')
    t = t.replace('_', r'\_')
    return t


def fmt(t):
    """Convert markdown inline to LaTeX: bold, italic, links, symbols."""
    t = escape_tex(t)
    t = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', t)
    t = re.sub(r'\*(.+?)\*', r'\\textit{\1}', t)
    t = re.sub(r'\[(.+?)\]\((.+?)\)', r'\\href{\2}{\1}', t)
    t = t.replace('→', r'$\rightarrow$')
    t = t.replace('–', '--')
    t = t.replace('\u201c', '``').replace('\u201d', "''")
    return t


def parse_heading3(line):
    """Parse ### line into (name_or_company, role_or_empty)."""
    text = line.lstrip('#').strip()
    for sep in [' — ', ' -- ', ' \\textemdash ', u'\u2014']:
        if sep in text:
            a, b = text.split(sep, 1)
            return a.strip(), b.strip()
    return text, ''


def parse_meta(line):
    """Parse **Location | Dates** line. Returns (location, dates, extra)."""
    raw = line.strip()
    # Extract bold portion and any trailing | *italic*
    extra = ''
    m = re.match(r'\*\*(.+?)\*\*(?:\s*\|\s*\*(.+?)\*)?', raw)
    if not m:
        return '', '', ''
    bold_part = m.group(1).strip()
    if m.group(2):
        extra = m.group(2).strip()
    if '|' in bold_part:
        loc, dates = bold_part.split('|', 1)
        return loc.strip(), dates.strip(), extra
    return '', bold_part.strip(), extra


def build_resume_tex(md_text):
    """Convert resume markdown to LaTeX string using Sourabh Bajaj template."""
    lines = md_text.strip().split('\n')
    out = [LATEX_PREAMBLE]
    item_list_open = False
    sub_list_open = False
    current_section = ''

    def close_items():
        nonlocal item_list_open
        if item_list_open:
            out.append(r'    \resumeItemListEnd')
            item_list_open = False

    def close_sublist():
        nonlocal sub_list_open
        close_items()
        if sub_list_open:
            out.append(r'  \resumeSubHeadingListEnd')
            sub_list_open = False

    i = 0
    while i < len(lines):
        L = lines[i].strip()

        # Skip blanks and ---
        if not L or L.startswith('---'):
            i += 1
            continue

        # ── H1: Name ──
        if re.match(r'^# [^#]', L):
            name = escape_tex(L[2:].strip())
            i += 1
            # Find contact line
            while i < len(lines) and not lines[i].strip():
                i += 1
            contact = fmt(lines[i].strip()) if i < len(lines) else ''
            out.append(r'\begin{tabular*}{\textwidth}{l@{\extracolsep{\fill}}r}')
            out.append(f'  \\textbf{{\\Large {name}}} & \\\\')
            out.append(f'  {contact}')
            out.append(r'\end{tabular*}')
            out.append(r'\vspace{2mm}')
            i += 1
            continue

        # ── H2: Section ──
        if re.match(r'^## [^#]', L):
            close_sublist()
            current_section = L[3:].strip().lower()
            out.append(f'\\section{{{escape_tex(L[3:].strip())}}}')
            out.append(r'  \resumeSubHeadingListStart')
            sub_list_open = True
            i += 1
            continue

        # ── H3: Subheading ──
        if re.match(r'^### [^#]', L):
            close_items()
            company, role = parse_heading3(L)
            company = escape_tex(company)
            role = escape_tex(role)
            # Peek for meta line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            loc = dates = extra = ''
            if j < len(lines) and lines[j].strip().startswith('**'):
                loc, dates, extra = parse_meta(lines[j])
                loc = loc.replace('–', '--')
                dates = dates.replace('–', '--')
                if extra:
                    role = (role + ' | ' + extra) if role else extra
                i = j + 1
            else:
                i += 1
            # Peek: if next content is ####, need extra space after subheading
            peek = i
            while peek < len(lines) and not lines[peek].strip():
                peek += 1
            has_h4 = peek < len(lines) and lines[peek].strip().startswith('####')

            if 'education' in current_section:
                uni = dates or loc
                out.append(f'    \\resumeSubheading{{{company}}}{{}}')
                out.append(f'      {{{escape_tex(uni)}}}{{}}')
            elif has_h4:
                # Inline subheading without -5pt so #### header doesn't collide
                out.append(r'    \vspace{-1pt}\item')
                out.append(r'      \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}')
                out.append(f'        \\textbf{{{company}}} & {escape_tex(loc)} \\\\')
                out.append(f'        \\textit{{\\small {role}}} & \\textit{{\\small {escape_tex(dates)}}} \\\\')
                out.append(r'      \end{tabular*}\vspace{2pt}')
            else:
                out.append(f'    \\resumeSubheading{{{company}}}{{{escape_tex(loc)}}}')
                out.append(f'      {{{role}}}{{{escape_tex(dates)}}}')
            continue

        # ── H4: Sub-section italic header ──
        if re.match(r'^#### [^#]', L):
            close_items()
            header = escape_tex(L[5:].strip())
            out.append(f'    {{\\small {header}}}')
            out.append(r'    \vspace{-8pt}')
            i += 1
            continue

        # ── Bullet ──
        if L.startswith('- '):
            text = fmt(L[2:].strip())
            is_flat = 'skill' in current_section or 'co-curricular' in current_section

            if is_flat:
                # Flat sections: items go directly in SubHeadingList, no ItemList
                m = re.match(r'\\textbf\{(.+?):\}?\s*(.*)', text)
                if m:
                    out.append(f'    \\item[$\\circ$]\\small{{\\textbf{{{m.group(1)}}}{{: {m.group(2)}}}}}\\vspace{{-5pt}}')
                else:
                    out.append(f'    \\item[$\\circ$]\\small{{{text}}}\\vspace{{-5pt}}')
            else:
                if not item_list_open:
                    out.append(r'    \resumeItemListStart')
                    item_list_open = True
                out.append(f'      \\item\\small{{{text}}}')
            i += 1
            continue

        # Fallback: skip
        i += 1

    close_sublist()
    out.append(r'\end{document}')
    return '\n'.join(out)


def build_resume_pdf(md_path, out_path):
    """Convert resume markdown to Sourabh Bajaj LaTeX template and compile."""
    tex = build_resume_tex(md_path.read_text())
    tex_path = out_path.with_suffix('.tex')
    tex_path.write_text(tex)

    r = subprocess.run(["tectonic", str(tex_path)], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"LaTeX error:\n{r.stderr}")
        # Show the .tex for debugging
        print(f"Generated .tex at: {tex_path}")
        raise SystemExit(1)
    print(f"OK {tex_path}")


# ── CSS for doc/notes ────────────────────────────────────────────────────────

BASE_CSS = """
body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1a1a1a; }
strong { color: #111; }
a { color: #2563eb; text-decoration: none; }
hr { border: none; border-top: 0.5pt solid #e2e8f0; }
table { width: 100%; border-collapse: collapse; }
th, td { border: 0.5pt solid #e2e8f0; text-align: left; }
th { background: #f8fafc; font-weight: 600; }
code { background: #f1f5f9; padding: 1pt 3pt; border-radius: 2pt; font-size: 0.9em; }
pre { background: #f8fafc; border: 0.5pt solid #e2e8f0; border-radius: 3pt; padding: 8pt; }
pre code { background: none; padding: 0; }
"""

STYLES = {
    "doc": BASE_CSS + """
@page { size: A4; margin: 2cm 2.2cm; }
body { font-size: 10.5pt; line-height: 1.5; }
h1 { font-size: 22pt; margin: 0 0 6pt 0; color: #111; border-bottom: 2pt solid #2563eb; padding-bottom: 6pt; }
h2 { font-size: 14pt; color: #2563eb; border-bottom: 0.75pt solid #cbd5e1; padding-bottom: 3pt; margin-top: 18pt; margin-bottom: 8pt; }
h3 { font-size: 12pt; margin: 14pt 0 4pt 0; color: #111; }
h4 { font-size: 11pt; margin: 10pt 0 3pt 0; color: #374151; font-style: italic; }
p { margin: 4pt 0; } li { margin: 2pt 0; }
ul, ol { margin: 4pt 0; padding-left: 20pt; }
hr { margin: 12pt 0; }
table { font-size: 10pt; margin: 8pt 0; } th, td { padding: 4pt 8pt; }
""",
    "notes": BASE_CSS + """
@page { size: A4; margin: 2.2cm 2.5cm; }
body { font-size: 11.5pt; line-height: 1.6; }
h1 { font-size: 24pt; margin: 0 0 8pt 0; color: #111; border-bottom: 2.5pt solid #2563eb; padding-bottom: 8pt; }
h2 { font-size: 16pt; color: #2563eb; border-bottom: 1pt solid #cbd5e1; padding-bottom: 4pt; margin-top: 22pt; margin-bottom: 10pt; }
h3 { font-size: 13pt; margin: 16pt 0 6pt 0; color: #111; }
h4 { font-size: 12pt; margin: 12pt 0 4pt 0; color: #374151; font-style: italic; }
p { margin: 6pt 0; } li { margin: 3pt 0; }
ul, ol { margin: 6pt 0; padding-left: 22pt; }
hr { margin: 14pt 0; }
table { font-size: 10.5pt; margin: 10pt 0; } th, td { padding: 5pt 10pt; }
""",
}


def guess_style(f):
    n = f.lower()
    return "resume" if ("resume" in n or "cv" in n) else "notes" if ("note" in n or "study" in n or "learn" in n) else "doc"


def build_html_pdf(md_path, out_path, style):
    md_text = md_path.read_text()
    html_body = markdown.markdown(md_text, extensions=["tables", "smarty", "fenced_code"])
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    weasyprint.HTML(string=html).write_pdf(str(out_path), stylesheets=[weasyprint.CSS(string=STYLES[style])])


def main():
    parser = argparse.ArgumentParser(description="Convert markdown to styled PDF")
    parser.add_argument("input", nargs="?", help="Input markdown file")
    parser.add_argument("output", nargs="?", help="Output PDF file")
    parser.add_argument("--style", "-s", choices=["resume", "doc", "notes"],
                        help="Style preset (default: auto-detect from filename)")
    args = parser.parse_args()

    personal = Path(__file__).parent.parent / "personal"
    md_path = Path(args.input) if args.input else personal / "resume.md"
    out_path = Path(args.output) if args.output else md_path.with_suffix(".pdf")
    style = args.style or guess_style(md_path.name)

    if style == "resume":
        build_resume_pdf(md_path, out_path)
    else:
        build_html_pdf(md_path, out_path, style)

    print(f"OK {out_path} ({out_path.stat().st_size // 1024}KB) [{style}]")


if __name__ == "__main__":
    main()
