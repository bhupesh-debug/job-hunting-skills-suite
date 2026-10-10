#!/usr/bin/env python3
"""
HireMe PDF Report Generator
Generates a branded, print-ready, fully hyperlinked coaching report PDF from
session content: clickable index, PDF bookmark tabs (sidebar outline) per
job/question, per-question "REF" anchors, and an every-page navigation bar
that links Index <-> every job section.

Usage:
    python3 generate_pdf.py \
        --candidate "Bhupesh Chamoli" \
        --role "Credit Risk Analyst" \
        --company "BNY" \
        --content_file /tmp/hireme_session.txt \
        --output /mnt/user-data/outputs/hireme_coaching_report.pdf
"""

import argparse
import re
import sys
from datetime import datetime

# Install reportlab if needed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether, Flowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "--break-system-packages", "-q"])
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether, Flowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Brand Colors ──────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0A1628")
GOLD       = colors.HexColor("#C9A84C")
LIGHT_GREY = colors.HexColor("#F5F6F8")
MID_GREY   = colors.HexColor("#8A8F99")
WHITE      = colors.white
DARK_GREY  = colors.HexColor("#2D3142")
ACCENT     = colors.HexColor("#1A3A6B")
RED_FLAG   = colors.HexColor("#B3261E")
GREEN_OK   = colors.HexColor("#1E7B34")
IMPORTANT_BG = colors.HexColor("#FCF3D9")   # soft gold highlight — "#" important questions
ASKED_BG     = colors.HexColor("#FDE8E4")   # soft red highlight — "*" most-asked questions
BOTH_BG      = colors.HexColor("#0A1628")   # navy — questions that are both
MNEMONIC_BG  = colors.HexColor("#EAF1FB")   # soft blue highlight for mnemonics
LINK_BLUE    = colors.HexColor("#1A3A6B")

INDEX_KEY = "index_page"

# Known finance/ERP acronyms — hover tooltip prepends the expansion before
# the question preview, so a short tab word like "SIOP" explains itself.
ACRONYM_EXPANSIONS = {
    "ERP": "Enterprise Resource Planning",
    "SIOP": "Sales, Inventory & Operations Planning",
    "HFM": "Hyperion Financial Management",
    "AP": "Accounts Payable",
    "PO": "Purchase Order",
    "AOP": "Annual Operating Plan",
    "RVP": "Regional Vice President",
    "KPI": "Key Performance Indicator",
    "BI": "Business Intelligence",
    "CPA": "Certified Public Accountant",
}

# Plain-English, one-line meaning for the Glossary page (kept separate from
# the short "full form" expansion above, which is what shows in headers,
# footers, and hover tooltips).
ACRONYM_EXPLANATIONS = {
    "ERP": "A software platform that integrates core business processes — finance, HR, procurement, supply chain — into one system.",
    "SIOP": "A recurring planning cycle that aligns sales forecasts, inventory levels, and operations capacity into one integrated plan.",
    "HFM": "Oracle Hyperion's consolidation and financial-reporting engine, used for multi-entity close and reporting.",
    "AP": "The function responsible for reviewing, approving, and paying a company's outstanding vendor invoices.",
    "PO": "A buyer-issued document that formally authorizes a purchase before an invoice is created or paid.",
    "AOP": "The board-approved annual budget that actual performance is measured against throughout the year.",
    "RVP": "A regional executive who owns commercial (sales/revenue) performance across a defined geography.",
    "KPI": "A measurable value used to track how effectively a team or company is hitting its objectives.",
    "BI": "Tools and processes — dashboards, reporting, analytics — used to turn raw data into actionable insight.",
    "CPA": "A U.S. accounting license earned by passing the Uniform CPA Exam plus education/experience requirements.",
}

GLOSSARY_KEY = "glossary_page"


def esc(text):
    """Escape XML-sensitive characters for reportlab Paragraphs."""
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def short(text, n=70):
    text = text.strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


# ── Invisible anchor flowable: creates a named PDF destination + outline entry ─
class Anchor(Flowable):
    """
    Zero-size flowable. When drawn it:
      1) Registers a named destination (`key`) at this exact point in the doc,
         so any internal <a href="#key"> link (Index -> question, or vice versa)
         lands here.
      2) Optionally adds a PDF bookmark/outline entry (the sidebar "tabs" most
         PDF readers show), nested by `level` (0 = job section, 1 = question).
      3) Updates canvas-level tracking so the running header/footer always
         knows which job section the current page belongs to.
    """
    def __init__(self, key, outline_title=None, level=0):
        Flowable.__init__(self)
        self.key = key
        self.outline_title = outline_title
        self.level = level
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        self.canv.bookmarkPage(self.key)
        if self.outline_title:
            self.canv.addOutlineEntry(self.outline_title, self.key, level=self.level, closed=False)
        if self.level == 0:
            self.canv._hireme_job_title = self.outline_title
            self.canv._hireme_job_key = self.key


def build_styles():
    styles = {
        "cover_name": ParagraphStyle(
            "cover_name", fontSize=28, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER, spaceAfter=6
        ),
        "cover_role": ParagraphStyle(
            "cover_role", fontSize=14, fontName="Helvetica",
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=4
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontSize=11, fontName="Helvetica",
            textColor=colors.HexColor("#CBD5E1"), alignment=TA_CENTER, spaceAfter=4
        ),
        "cover_badge": ParagraphStyle(
            "cover_badge", fontSize=10, fontName="Helvetica-Bold",
            textColor=NAVY, alignment=TA_CENTER
        ),
        "section_header": ParagraphStyle(
            "section_header", fontSize=13, fontName="Helvetica-Bold",
            textColor=WHITE, spaceAfter=4, spaceBefore=2, leftIndent=0
        ),
        "subsection": ParagraphStyle(
            "subsection", fontSize=11, fontName="Helvetica-Bold",
            textColor=GOLD, spaceAfter=4, spaceBefore=8
        ),
        "body": ParagraphStyle(
            "body", fontSize=10, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=4, leading=15
        ),
        "body_white": ParagraphStyle(
            "body_white", fontSize=10, fontName="Helvetica",
            textColor=WHITE, spaceAfter=4, leading=15
        ),
        "bullet": ParagraphStyle(
            "bullet", fontSize=10, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=3, leading=14,
            leftIndent=14, bulletIndent=4
        ),
        "label": ParagraphStyle(
            "label", fontSize=9, fontName="Helvetica-Bold",
            textColor=MID_GREY, spaceAfter=2, spaceBefore=6
        ),
        "footer": ParagraphStyle(
            "footer", fontSize=8, fontName="Helvetica",
            textColor=MID_GREY, alignment=TA_CENTER
        ),
        "toc_item": ParagraphStyle(
            "toc_item", fontSize=10, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=5, leading=14
        ),
        "toc_job": ParagraphStyle(
            "toc_job", fontSize=10.5, fontName="Helvetica-Bold",
            textColor=NAVY, spaceBefore=6, spaceAfter=2, leading=13
        ),
        "toc_q": ParagraphStyle(
            "toc_q", fontSize=7.8, fontName="Helvetica",
            textColor=ACCENT, spaceAfter=0.5, leading=10, leftIndent=14
        ),
        "qtext": ParagraphStyle(
            "qtext", fontSize=10.5, fontName="Helvetica-Bold",
            textColor=DARK_GREY, leading=14
        ),
        "qtext_white": ParagraphStyle(
            "qtext_white", fontSize=10.5, fontName="Helvetica-Bold",
            textColor=WHITE, leading=14
        ),
        "tag_label": ParagraphStyle(
            "tag_label", fontSize=7.5, fontName="Helvetica-Bold",
            textColor=WHITE, leading=10
        ),
        "answer": ParagraphStyle(
            "answer", fontSize=10, fontName="Helvetica",
            textColor=DARK_GREY, spaceAfter=6, leading=14.5, leftIndent=10
        ),
        "do_item": ParagraphStyle(
            "do_item", fontSize=9.5, fontName="Helvetica",
            textColor=GREEN_OK, spaceAfter=3, leading=13, leftIndent=14
        ),
        "dont_item": ParagraphStyle(
            "dont_item", fontSize=9.5, fontName="Helvetica",
            textColor=RED_FLAG, spaceAfter=3, leading=13, leftIndent=14
        ),
        "mnemonic": ParagraphStyle(
            "mnemonic", fontSize=9.5, fontName="Helvetica-Oblique",
            textColor=ACCENT, spaceAfter=3, leading=13.5, leftIndent=8
        ),
        "priority_rank": ParagraphStyle(
            "priority_rank", fontSize=8, fontName="Helvetica-Bold",
            textColor=MID_GREY, spaceBefore=6, spaceAfter=0
        ),
        "ref_link": ParagraphStyle(
            "ref_link", fontSize=8, fontName="Helvetica",
            textColor=LINK_BLUE, spaceBefore=2, spaceAfter=0
        ),
        "ref_link_white": ParagraphStyle(
            "ref_link_white", fontSize=8, fontName="Helvetica",
            textColor=colors.HexColor("#CBD5E1"), spaceBefore=2, spaceAfter=0
        ),
    }
    return styles


# ── Question-line parsing (shared by pre-scan and render pass, kept in sync) ──
Q_MARKERS = [
    (re.compile(r"^(?:#\*Q:|\*#Q:)\s*(.*)$"), True, True),
    (re.compile(r"^#Q:\s*(.*)$"), True, False),
    (re.compile(r"^\*Q:\s*(.*)$"), False, True),
    (re.compile(r"^Q:\s*(.*)$"), False, False),
]
KW_PATTERN = re.compile(r"^KW:\s*(.*)$", re.IGNORECASE)


def match_question_line(stripped_line):
    """Returns (question_text, important, asked) if the line is a Q-marker line, else None."""
    for pattern, important, asked in Q_MARKERS:
        m = pattern.match(stripped_line)
        if m:
            return m.group(1).strip(), important, asked
    return None


def highlight_keyword(escaped_text, keyword):
    """
    Wraps the first case-insensitive occurrence of `keyword` inside already-
    escaped question text with a gold bold-underline span, so the exact word
    a page-level chip links to is visibly marked inside the question itself.
    """
    if not keyword:
        return escaped_text
    kw_esc = esc(keyword)
    pattern = re.compile(re.escape(kw_esc), re.IGNORECASE)
    return pattern.sub(
        lambda m: f'<font color="#8A6A00"><b><u>{m.group(0)}</u></b></font>',
        escaped_text, count=1
    )


def prescan_sections(sections):
    """
    Walks parsed (title, body) sections and builds a navigation map WITHOUT
    rendering anything, so the Index page, PDF bookmark tree, and the
    every-page keyword nav strip can be built before (and independent of)
    the main render pass. Order of questions here MUST match the order
    text_to_paragraphs() encounters them — both use match_question_line()
    and KW_PATTERN for that reason.
    """
    nav = []
    for idx, (title, body) in enumerate(sections):
        sec_key = f"sec{idx}"
        questions = []
        pending_kw = None
        for line in body.splitlines():
            stripped = line.strip()
            kwm = KW_PATTERN.match(stripped)
            if kwm:
                pending_kw = kwm.group(1).strip()
                continue
            hit = match_question_line(stripped)
            if hit:
                qtext, important, asked = hit
                qidx = len(questions)
                questions.append({
                    "key": f"{sec_key}_q{qidx}",
                    "text": qtext,
                    "important": important,
                    "asked": asked,
                    "ref": f"{idx + 1}.{qidx + 1}",
                    "keyword": pending_kw,
                })
                pending_kw = None
        nav.append({"key": sec_key, "title": title, "questions": questions})
    return nav


def make_tag_question(question_text, rank_label, styles, anchor_key, ref_label,
                       important=False, asked=False, keyword=None):
    """
    Renders a Q&A header row with a colored tag badge, a REF code, an anchor
    (so the Index, the every-page keyword strip, and every other page can
    jump straight here), and a "back to Index" link. The `keyword` (a word
    literally found in the question) is highlighted gold/underlined inside
    the question text — that's the exact word the page-footer chip points to.
    Returns a LIST of flowables (anchor + table).
    """
    q = esc(question_text)
    q = highlight_keyword(q, keyword)
    if important and asked:
        bg, tag, txt_style = BOTH_BG, "#*  CRITICAL — IMPORTANT & MOST ASKED", "qtext_white"
        badge_bg = GOLD
        link_style = "ref_link_white"
    elif important:
        bg, tag, txt_style = IMPORTANT_BG, "#  IMPORTANT", "qtext"
        badge_bg = GOLD
        link_style = "ref_link"
    elif asked:
        bg, tag, txt_style = ASKED_BG, "*  MOST ASKED", "qtext"
        badge_bg = RED_FLAG
        link_style = "ref_link"
    else:
        bg, tag, txt_style = LIGHT_GREY, None, "qtext"
        badge_bg = GOLD
        link_style = "ref_link"

    rows = []
    top_line_bits = [f"REF {esc(ref_label)}"]
    if rank_label:
        top_line_bits.append(esc(rank_label))
    if keyword:
        top_line_bits.append(f'KEY: <b>{esc(keyword).upper()}</b>')
    top_line_bits.append(f'<a href="#{INDEX_KEY}" color="{"#CBD5E1" if (important and asked) else "#1A3A6B"}"><u>↩ Back to Index</u></a>')
    rows.append([Paragraph("   ·   ".join(top_line_bits), styles[link_style])])

    if tag:
        tag_color = WHITE if txt_style == "qtext_white" else (NAVY if important and not asked else RED_FLAG)
        badge_data = [[Paragraph(tag, ParagraphStyle("tagd", parent=styles["tag_label"], textColor=tag_color))]]
        badge = Table(badge_data, colWidths=[2.6 * inch])
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), badge_bg),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        rows.append([badge])
    rows.append([Paragraph(f'<a name="{anchor_key}"/>{q}', styles[txt_style])])

    box = Table([[r[0]] for r in rows], colWidths=[6.2 * inch])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return [box]


def make_mnemonic_box(text, styles):
    body = Paragraph(f"🧠 <b>MNEMONIC:</b> {esc(text)}", styles["mnemonic"])
    box = Table([[body]], colWidths=[6.2 * inch])
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), MNEMONIC_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return box


def section_block(title, story, styles, content_paragraphs, anchor_key, sec_number, label_prefix="JOB"):
    """Renders a navy header bar (with its own anchor for deep-linking) + content block."""
    header_data = [[Paragraph(esc(title), styles["section_header"])]]
    header_table = Table(header_data, colWidths=[6.2 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [NAVY]),
    ]))

    top_link = Paragraph(
        f'<a href="#{INDEX_KEY}" color="#8A8F99"><u>↩ Back to Index</u></a>',
        styles["ref_link"]
    )

    # Outline (bookmark sidebar) label — "JOB N:" for job sections, or a
    # custom prefix (e.g. "ROLE MASTERY N:") for other section types.
    outline_label = f"{label_prefix} {sec_number}: {title}"
    block = [Anchor(anchor_key, outline_title=outline_label, level=0), header_table, top_link, Spacer(1, 6)]
    block.extend(content_paragraphs)
    block.append(Spacer(1, 10))

    story.append(KeepTogether(block[:5]))  # keep header + back-link + first content together
    if len(block) > 5:
        story.extend(block[5:])


def text_to_paragraphs(text, styles, sec_idx, sec_key):
    """
    Convert raw text lines to reportlab flowables.

    Markup conventions (checked in priority order, before generic bullets):
      RANK: <label>          -> small grey priority-rank tag above the next question
      KW: <word>             -> a word FROM the next question to highlight + link
                                 from the every-page keyword nav strip
      #Q: <question>         -> IMPORTANT question (gold highlight, '#' badge)
      *Q: <question>         -> MOST-ASKED question (red highlight, '*' badge)
      #*Q: / *#Q: <question> -> both flags (navy highlight, critical badge)
      Q: <question>          -> plain question, no badge
      A: <answer text>       -> indented answer paragraph
      DO: <text>             -> green checklist item ("Do" list)
      DONT: <text>           -> red checklist item ("Don't" list)
      MNEMONIC: <text>       -> highlighted recall-mnemonic box

    Every Q-marker line gets its own anchor (`{sec_key}_q{n}`) and a REF code,
    generated in the SAME order as prescan_sections() so links always resolve
    to the correct question.
    """
    paras = []
    pending_rank = None
    pending_kw = None
    qcounter = 0
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            paras.append(Spacer(1, 4))
            continue

        if stripped.upper().startswith("RANK:"):
            pending_rank = esc(stripped.split(":", 1)[1].strip())
            continue

        kwm = KW_PATTERN.match(stripped)
        if kwm:
            pending_kw = kwm.group(1).strip()
            continue

        upper = stripped.upper()
        hit = match_question_line(stripped)
        if hit:
            qtext, important, asked = hit
            anchor_key = f"{sec_key}_q{qcounter}"
            ref_label = f"{sec_idx + 1}.{qcounter + 1}"

            # Outline (bookmark sidebar) label: tag marker + keyword label +
            # question preview, e.g. "[#*] MANAGER — Walk me through how..."
            if important and asked:
                tag_marker = "[#*]"
            elif important:
                tag_marker = "[#]"
            elif asked:
                tag_marker = "[*]"
            else:
                tag_marker = "[ ]"
            kw_label = f" {pending_kw.upper()} —" if pending_kw else ""
            outline_label = f"{tag_marker}{kw_label} {short(qtext, 46)}"

            paras.append(Anchor(anchor_key, outline_title=outline_label, level=1))
            paras.extend(make_tag_question(
                qtext, pending_rank, styles, anchor_key, ref_label,
                important=important, asked=asked, keyword=pending_kw
            ))
            pending_rank = None
            pending_kw = None
            qcounter += 1
        elif stripped.startswith("A:"):
            paras.append(Paragraph(f"<b>Answer —</b> {esc(stripped[2:].strip())}", styles["answer"]))
        elif upper.startswith("DO:"):
            paras.append(Paragraph(f"✔ {esc(stripped[3:].strip())}", styles["do_item"]))
        elif upper.startswith("DONT:") or upper.startswith("DON'T:"):
            rest = stripped.split(":", 1)[1].strip()
            paras.append(Paragraph(f"✘ {esc(rest)}", styles["dont_item"]))
        elif upper.startswith("MNEMONIC:"):
            paras.append(make_mnemonic_box(stripped.split(":", 1)[1].strip(), styles))
        # Bullets
        elif stripped.startswith(("- ", "• ", "✅ ", "❌ ", "👉 ")):
            clean = esc(stripped.lstrip("-•✅❌👉 "))
            paras.append(Paragraph(f"• {clean}", styles["bullet"]))
        # Sub-headers (lines ending in : or starting with **)
        elif stripped.startswith("**") and stripped.endswith("**"):
            clean = esc(stripped.strip("*"))
            paras.append(Paragraph(clean, styles["subsection"]))
        elif stripped.startswith("##"):
            clean = esc(stripped.lstrip("# "))
            paras.append(Paragraph(clean, styles["subsection"]))
        else:
            clean = esc(stripped)
            paras.append(Paragraph(clean, styles["body"]))
    return paras


def add_cover_page(story, styles, candidate, role, company, date_str):
    """Full Navy cover page."""
    story.append(Spacer(1, 0.6 * inch))

    badge_data = [[Paragraph("HIREME  ·  ELITE COACHING REPORT", styles["cover_badge"])]]
    badge = Table(badge_data, colWidths=[2.4 * inch])
    badge.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GOLD),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    badge_wrapper = Table([[badge]], colWidths=[6.2 * inch])
    badge_wrapper.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(badge_wrapper)
    story.append(Spacer(1, 0.35 * inch))

    card_content = [
        [Paragraph(esc(candidate), styles["cover_name"])],
        [Paragraph(esc(role), styles["cover_role"])],
        [Paragraph(esc(company), styles["cover_meta"])],
        [Spacer(1, 0.1 * inch)],
        [HRFlowable(width="60%", thickness=1, color=GOLD, spaceAfter=10)],
        [Paragraph(f"Session Date: {date_str}", styles["cover_meta"])],
        [Paragraph(
            f'<a href="#{INDEX_KEY}" color="#C9A84C"><u>↩ Jump to Clickable Index</u></a>',
            styles["cover_meta"]
        )],
    ]
    card = Table(card_content, colWidths=[6.2 * inch])
    card.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("LEFTPADDING",   (0, 0), (-1, -1), 30),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 30),
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(card)
    story.append(Spacer(1, 0.4 * inch))

    tagline = Paragraph(
        "Top 1% Interview Preparation · Recruiter-Side Analysis · Offer-Ready",
        styles["cover_meta"]
    )
    story.append(tagline)
    story.append(PageBreak())


def add_index(story, styles, nav):
    """
    Clickable Index page: every job title links to its section header;
    every question underneath links straight to that question's anchor.
    Badges preview which questions are IMPORTANT / MOST ASKED / CRITICAL.
    Deliberately compact — sized to fit on a single page regardless of how
    many jobs/questions the report covers.
    """
    story.append(Anchor(INDEX_KEY, outline_title="Index", level=0))

    header_data = [[Paragraph("INDEX  ·  TAP ANY ROW TO JUMP", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[6.2 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 5))

    note = Paragraph(
        '<font color="#C9A84C"><b>#</b></font> Important&nbsp;&nbsp;'
        '<font color="#B3261E"><b>*</b></font> Most Asked&nbsp;&nbsp;'
        '<b>#*</b> Critical&nbsp;&nbsp;&nbsp;·&nbsp;&nbsp;&nbsp;'
        '<i>Every page also has clickable keyword tabs in the margins (hover for a tooltip, tap to jump).</i>'
        f'&nbsp;&nbsp;·&nbsp;&nbsp;<a href="#{GLOSSARY_KEY}" color="#8A6A00"><u>Jump to Glossary →</u></a>',
        ParagraphStyle("note", parent=styles["toc_item"], fontSize=7.6, textColor=MID_GREY,
                        spaceAfter=6, leading=10)
    )
    story.append(note)

    # Estimate whether the index needs extra shrinking to guarantee a single
    # page (very large reports) — shrink question-row font/preview length
    # proportionally to total question count.
    total_q = sum(len(sec["questions"]) for sec in nav)
    preview_len = 78 if total_q <= 26 else max(40, int(78 * 26 / total_q))
    q_style = styles["toc_q"]
    if total_q > 26:
        q_style = ParagraphStyle("toc_q_tight", parent=styles["toc_q"],
                                  fontSize=6.8, leading=8.6, spaceAfter=0.3)

    for i, sec in enumerate(nav, 1):
        job_link = Paragraph(
            f'<a href="#{sec["key"]}" color="#0A1628"><b>{i}. {esc(sec["title"])}</b></a>',
            styles["toc_job"]
        )
        story.append(job_link)

        for q in sec["questions"]:
            if q["important"] and q["asked"]:
                mark = '<font color="#B3261E"><b>#*</b></font>'
            elif q["important"]:
                mark = '<font color="#C9A84C"><b>#</b></font>'
            elif q["asked"]:
                mark = '<font color="#B3261E"><b>*</b></font>'
            else:
                mark = "&nbsp;&nbsp;"
            q_link = Paragraph(
                f'{mark}&nbsp; <a href="#{q["key"]}" color="#1A3A6B">'
                f'{esc(q["ref"])} — {esc(short(q["text"], preview_len))}</a>'
                + (f' <font color="#8A6A00"><b>[{esc(q["keyword"]).upper()}]</b></font>' if q.get("keyword") else ""),
                q_style
            )
            story.append(q_link)

    story.append(PageBreak())


def add_glossary(story, styles, nav):
    """
    Glossary & Explanation — always the LAST page. Two parts:
      1) ACRONYM GLOSSARY: every real acronym used anywhere as a keyword tab,
         with its full form AND a plain-English one-line meaning (the header/
         footer only ever show the full form — this is where the actual
         explanation lives).
      2) KEYWORD REFERENCE: every keyword tab in the document, cross-linked
         back to its exact question, so the glossary doubles as a second,
         explanation-oriented index.
    """
    story.append(Anchor(GLOSSARY_KEY, outline_title="Glossary & Explanation", level=0))

    header_data = [[Paragraph("GLOSSARY & EXPLANATION", styles["section_header"])]]
    header_table = Table(header_data, colWidths=[6.2 * inch])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",   (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
    ]))
    story.append(header_table)
    top_link = Paragraph(
        f'<a href="#{INDEX_KEY}" color="#8A8F99"><u>↩ Back to Index</u></a>',
        styles["ref_link"]
    )
    story.append(top_link)
    story.append(Spacer(1, 8))

    # Part 1 — Acronym glossary
    used_acronyms = []
    for sec in nav:
        for q in sec["questions"]:
            kw = (q.get("keyword") or "").upper()
            if kw in ACRONYM_EXPANSIONS and kw not in used_acronyms:
                used_acronyms.append(kw)

    if used_acronyms:
        story.append(Paragraph("Acronym Glossary", styles["subsection"]))
        for kw in used_acronyms:
            full = ACRONYM_EXPANSIONS[kw]
            meaning = ACRONYM_EXPLANATIONS.get(kw, "")
            story.append(Paragraph(
                f'<font color="#8A6A00"><b>{esc(kw)}</b></font> — <b>{esc(full)}</b><br/>'
                f'<font color="#2D3142">{esc(meaning)}</font>',
                ParagraphStyle("gloss_item", parent=styles["body"], spaceAfter=7, leading=13.5)
            ))
        story.append(Spacer(1, 8))

    # Part 2 — Full keyword reference, cross-linked back to every question
    story.append(Paragraph("Keyword Reference — Every Question, A–Z", styles["subsection"]))
    all_q = []
    for sec in nav:
        for q in sec["questions"]:
            if q.get("keyword"):
                all_q.append((sec, q))
    all_q.sort(key=lambda pair: pair[1]["keyword"].upper())

    total = len(all_q)
    ref_style = styles["toc_q"] if total <= 26 else ParagraphStyle(
        "gloss_ref_tight", parent=styles["toc_q"], fontSize=6.8, leading=8.6, spaceAfter=0.3
    )
    for sec, q in all_q:
        story.append(Paragraph(
            f'<font color="#8A6A00"><b>{esc(q["keyword"]).upper()}</b></font> — '
            f'<a href="#{q["key"]}" color="#1A3A6B">REF {esc(q["ref"])}, {esc(short(sec["title"], 40))} — '
            f'{esc(short(q["text"], 68))}</a>',
            ref_style
        ))

    story.append(Spacer(1, 10))


def build_tooltip(q):
    """Best-effort hover text for a keyword tab: acronym expansion (if the
    word is a known acronym) + the full question it links to. PDF hover-
    tooltip support for Link annotations varies by reader (Acrobat and most
    desktop readers show it; some lightweight/browser viewers don't) — the
    tab is still always clickable regardless of tooltip support."""
    kw = (q.get("keyword") or "").upper()
    expansion = ACRONYM_EXPANSIONS.get(kw)
    prefix = f"{kw} = {expansion}.  " if expansion else ""
    return f"{prefix}REF {q['ref']}: {q['text']}"[:300]


def tab_color_for(q):
    if q["important"] and q["asked"]:
        return NAVY
    if q["important"]:
        return GOLD
    if q["asked"]:
        return RED_FLAG
    return ACCENT


def draw_cover_keyword_summary(canvas_obj, nav, page_width, top_y, bottom_y):
    """
    Compact, shrink-to-fit keyword tag summary drawn near the bottom of the
    cover page: one labeled row per job, with every question's keyword as a
    small clickable+tooltipped chip (wraps as needed). Font auto-shrinks so
    the whole thing always fits inside [bottom_y, top_y].
    """
    left = 1.05 * inch
    max_x = page_width - 1.05 * inch
    avail_h = top_y - bottom_y

    def measure(font_size, row_h):
        y = top_y
        for sec in nav:
            y -= 12
            x = left
            for q in sec["questions"]:
                if not q.get("keyword"):
                    continue
                w = canvas_obj.stringWidth(q["keyword"].upper(), "Helvetica-Bold", font_size) + 10
                if x + w > max_x:
                    x = left
                    y -= row_h
                x += w + 4
            y -= row_h + 7
        return top_y - y

    font_size, row_h = 6.6, 12.5
    while font_size > 4.6 and measure(font_size, row_h) > avail_h:
        font_size -= 0.35
        row_h = max(9.5, row_h - 0.4)

    canvas_obj.setFont("Helvetica", 7.5)
    canvas_obj.setFillColor(colors.HexColor("#CBD5E1"))
    canvas_obj.drawCentredString(page_width / 2.0, top_y + 12,
                                  "Tap any keyword below to jump straight to that question")

    y = top_y
    for i, sec in enumerate(nav, 1):
        canvas_obj.setFont("Helvetica-Bold", font_size + 1.4)
        canvas_obj.setFillColor(NAVY)
        canvas_obj.drawString(left, y - 9, f"{i}. {short(sec['title'], 60).upper()}")
        canvas_obj.linkRect(f"Jump to {sec['title']}", sec["key"],
                             (left, y - 11, max_x, y + 2), thickness=0)
        y -= 13

        x = left
        canvas_obj.setFont("Helvetica-Bold", font_size)
        for q in sec["questions"]:
            if not q.get("keyword"):
                continue
            label = q["keyword"].upper()
            w = canvas_obj.stringWidth(label, "Helvetica-Bold", font_size) + 10
            if x + w > max_x:
                x = left
                y -= row_h
            canvas_obj.saveState()
            canvas_obj.setFillAlpha(0.42)
            canvas_obj.setFillColor(tab_color_for(q))
            canvas_obj.roundRect(x, y - row_h + 2, w, row_h - 2.5, 3, fill=1, stroke=0)
            canvas_obj.restoreState()
            canvas_obj.setFillColor(WHITE)
            canvas_obj.drawString(x + 5, y - row_h + 5.5, label)
            canvas_obj.linkRect(build_tooltip(q), q["key"], (x, y - row_h + 2, x + w, y), thickness=0)
            x += w + 4
        y -= row_h + 7


def draw_margin_tabs(canvas_obj, nav, zone_top, zone_bottom, page_width):
    """
    Draws one faded, rotated, clickable tab per question down the LEFT and
    RIGHT page margins (split roughly in half between the two sides, in REF
    order). Each tab:
      - has a translucent fill (setFillAlpha) so it never fully hides
        anything drawn beneath it,
      - is colored by tag: gold = IMPORTANT, red = MOST ASKED, navy = both,
      - is a live link straight to that question's anchor,
      - carries a hover tooltip (Link /Contents) with the acronym
        expansion (if any) and the full question text.
    """
    flat = []
    for sec in nav:
        for q in sec["questions"]:
            if q.get("keyword"):
                flat.append(q)
    if not flat:
        return

    half = (len(flat) + 1) // 2
    left_items, right_items = flat[:half], flat[half:]

    tab_w = 0.62 * inch
    left_x0 = 0.06 * inch
    right_x0 = page_width - 0.06 * inch - tab_w
    zone_h = zone_top - zone_bottom
    gap = 2.5

    def draw_column(items, x0):
        if not items:
            return
        tab_h = (zone_h - gap * (len(items) - 1)) / len(items)
        tab_h = max(tab_h, 26)  # floor so short columns don't get illegibly thin
        y = zone_top
        for q in items:
            y_bottom = y - tab_h
            fill = tab_color_for(q)

            canvas_obj.saveState()
            canvas_obj.setFillAlpha(0.38)
            canvas_obj.setFillColor(fill)
            canvas_obj.roundRect(x0, y_bottom, tab_w, tab_h, 4, fill=1, stroke=0)
            canvas_obj.restoreState()

            # Rotated label — INVERTED (white) text so it stays readable
            # against every tab color, faded or not.
            canvas_obj.saveState()
            canvas_obj.setFillColor(WHITE)
            label = q["keyword"].upper()
            font_size = 6.6
            avail = tab_h - 8
            while font_size > 4.3 and canvas_obj.stringWidth(label, "Helvetica-Bold", font_size) > avail:
                font_size -= 0.3
            if canvas_obj.stringWidth(label, "Helvetica-Bold", font_size) > avail:
                while len(label) > 3 and canvas_obj.stringWidth(label + "…", "Helvetica-Bold", font_size) > avail:
                    label = label[:-1]
                label = label + "…"
            canvas_obj.setFont("Helvetica-Bold", font_size)
            canvas_obj.translate(x0 + tab_w / 2.0 + 2.3, y_bottom + 4)
            canvas_obj.rotate(90)
            canvas_obj.drawString(0, 0, label)
            canvas_obj.restoreState()

            # Clickable + hover tooltip (best-effort — reader-dependent)
            canvas_obj.linkRect(
                build_tooltip(q), q["key"],
                (x0, y_bottom, x0 + tab_w, y),
                thickness=0
            )
            y = y_bottom - gap

    draw_column(left_items, left_x0)
    draw_column(right_items, right_x0)


def make_on_page(nav, candidate):
    """
    Builds the onPage callback. Draws, on EVERY page (after the cover):
      - a navy top accent bar + running header (current job section) +
        a compact ACRONYM GLOSSARY line whenever any real acronym (ERP,
        SIOP, etc.) is in play as a keyword tab, so the full term is
        visible in plain text — not just on hover,
      - faded, clickable, hover-tooltipped keyword TABS running down the
        LEFT and RIGHT margins — one per question, every page, so any
        question is reachable from anywhere without leaving the page edge,
      - a slim footer with the same acronym glossary line, candidate name,
        page number, and a compact [INDEX] [JOB 1] [JOB 2] ... strip.
    """
    # Build the glossary line once — every acronym actually used as a
    # keyword tab, in first-seen order, expanded to its full term.
    seen = []
    for sec in nav:
        for q in sec["questions"]:
            kw = (q.get("keyword") or "").upper()
            if kw in ACRONYM_EXPANSIONS and kw not in seen:
                seen.append(kw)
    glossary_line = "   ·   ".join(f"{kw} = {ACRONYM_EXPANSIONS[kw]}" for kw in seen)

    def on_page(canvas_obj, doc):
        if doc.page == 1:
            canvas_obj.saveState()
            draw_cover_keyword_summary(
                canvas_obj, nav, letter[0],
                top_y=3.85 * inch, bottom_y=0.65 * inch
            )
            canvas_obj.restoreState()
            return
        canvas_obj.saveState()

        # Top accent bar
        canvas_obj.setFillColor(NAVY)
        canvas_obj.rect(0, letter[1] - 0.18 * inch, letter[0], 0.18 * inch, fill=1, stroke=0)

        # Running header: current job section (tracked by Anchor.draw())
        current_title = getattr(canvas_obj, "_hireme_job_title", None)
        canvas_obj.setFont("Helvetica-Bold", 8.5)
        canvas_obj.setFillColor(MID_GREY)
        header_text = short(current_title, 70) if current_title else "HireMe Coaching Report"
        canvas_obj.drawCentredString(letter[0] / 2.0, letter[1] - 0.40 * inch, header_text.upper())
        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.drawRightString(letter[0] - 0.85 * inch, letter[1] - 0.40 * inch, esc(candidate))

        if glossary_line:
            canvas_obj.setFont("Helvetica-Oblique", 6.3)
            canvas_obj.setFillColor(MID_GREY)
            canvas_obj.drawCentredString(letter[0] / 2.0, letter[1] - 0.53 * inch, glossary_line)

        # Margin tabs — the every-page, every-question keyword nav
        draw_margin_tabs(
            canvas_obj, nav,
            zone_top=letter[1] - 0.68 * inch,
            zone_bottom=0.68 * inch,
            page_width=letter[0],
        )

        # Slim footer: acronym glossary (repeated — visible wherever the
        # acronyms are used, not just on hover), page number, Index/Job chips
        if glossary_line:
            canvas_obj.setFont("Helvetica-Oblique", 6.3)
            canvas_obj.setFillColor(MID_GREY)
            canvas_obj.drawCentredString(letter[0] / 2.0, 0.52 * inch, glossary_line)

        canvas_obj.setFont("Helvetica", 7.5)
        canvas_obj.setFillColor(MID_GREY)
        canvas_obj.drawCentredString(letter[0] / 2.0, 0.38 * inch,
                                      f"HireMe Coaching Report · Confidential · Page {doc.page}")

        x = letter[0] / 2.0 - 0.9 * inch
        y = 0.20 * inch
        canvas_obj.setFont("Helvetica-Bold", 7)

        def chip(label, key, fill):
            nonlocal x
            w = canvas_obj.stringWidth(label, "Helvetica-Bold", 7) + 8
            canvas_obj.setFillColor(fill)
            canvas_obj.roundRect(x, y - 2, w, 11, 3, fill=1, stroke=0)
            canvas_obj.setFillColor(WHITE)
            canvas_obj.drawString(x + 4, y + 1, label)
            canvas_obj.linkRect("Jump to " + label, key, (x, y - 2, x + w, y + 9), thickness=0)
            x += w + 5

        chip("INDEX", INDEX_KEY, NAVY)
        for i, sec in enumerate(nav, 1):
            chip(f"J{i}", sec["key"], ACCENT)
        chip("GLOSSARY", GLOSSARY_KEY, colors.HexColor("#8A6A00"))

        canvas_obj.restoreState()
    return on_page


def generate_pdf(candidate, role, company, content_text, output_path, mastery_text=None):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=1.05 * inch,
        rightMargin=1.05 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.75 * inch,
        title=f"HireMe Coaching Report — {candidate}",
        author="HireMe Coaching System",
        subject=f"{role} at {company}",
    )

    styles = build_styles()
    story = []
    date_str = datetime.now().strftime("%B %d, %Y")

    # Cover
    add_cover_page(story, styles, candidate, role, company, date_str)

    # Parse sections + pre-scan the question map (drives Index + bookmarks)
    sections = parse_content_into_sections(content_text)
    nav = prescan_sections(sections)

    # Clickable Index page (also registers the PDF bookmark root)
    add_index(story, styles, nav)

    # Content sections — each gets its own anchor/bookmark, each question inside
    # gets its own anchor/bookmark + REF code + "back to Index" link.
    for idx, (title, body) in enumerate(sections):
        sec_key = f"sec{idx}"
        content_paras = text_to_paragraphs(body, styles, idx, sec_key)
        if content_paras:
            section_block(title, story, styles, content_paras, sec_key, idx + 1)
            story.append(Spacer(1, 6))

    # Glossary & Explanation — acronym expansions with plain-English meaning,
    # plus a full explanation reference for every keyword tab in the document.
    add_glossary(story, styles, nav)

    # /graphify Role Mastery — one condensed "1% Topper" knowledge pack per
    # job (Knowledge Map, Terminology Decoder, KPI Vault, Tool Map, 30-60-90,
    # Top-1% Behavior, recall mnemonic), always AFTER the Glossary.
    if mastery_text:
        story.append(Spacer(1, 4))
        mastery_sections = parse_content_into_sections(mastery_text)
        for idx, (title, body) in enumerate(mastery_sections):
            m_key = f"mastery{idx}"
            m_paras = text_to_paragraphs(body, styles, 500 + idx, m_key)
            if m_paras:
                section_block(title, story, styles, m_paras, m_key, idx + 1,
                               label_prefix="ROLE MASTERY")
                story.append(Spacer(1, 6))

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "— End of Report —",
        ParagraphStyle("end", parent=styles["toc_item"], alignment=TA_CENTER,
                        textColor=MID_GREY, fontSize=8.5)
    ))

    # Build
    on_page = make_on_page(nav, candidate)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"✅ PDF generated: {output_path}")


def parse_content_into_sections(raw_text):
    """
    Splits raw session text into labeled sections.
    Detects 'JOB N' headers (multi-role reports) and 'STEP N' headers
    (single coaching-session reports). Falls back to one section.
    """
    sections = []
    current_title = "Coaching Output"
    current_lines = []

    step_pattern = re.compile(
        r"^(?:#{1,3}\s*)?(?:STEP\s+(\d+)|Step\s+(\d+))\s*[—\-–:]?\s*(.*)",
        re.IGNORECASE
    )
    job_pattern = re.compile(
        r"^(?:#{1,3}\s*)?(?:JOB\s+(\d+))\s*[—\-–:]?\s*(.*)",
        re.IGNORECASE
    )
    step_names = {
        "1": "Deep Analysis", "2": "Positioning Strategy", "3": "Interview Simulation",
        "4": "Interpersonal Mastery", "5": "Closing Strategy", "6": "Offer Maximization",
    }

    for line in raw_text.splitlines():
        jm = job_pattern.match(line.strip())
        m = step_pattern.match(line.strip())
        if jm:
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            extra = jm.group(2).strip()
            current_title = extra if extra else f"Job {jm.group(1)}"
            current_lines = []
        elif m:
            if current_lines:
                sections.append((current_title, "\n".join(current_lines)))
            num = m.group(1) or m.group(2)
            extra = m.group(3).strip() or step_names.get(num, "")
            current_title = f"Step {num} — {extra}" if extra else f"Step {num}"
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines)))

    return sections if sections else [("Full Coaching Session", raw_text)]


def main():
    parser = argparse.ArgumentParser(description="Generate HireMe coaching PDF")
    parser.add_argument("--candidate", default="Bhupesh Chamoli")
    parser.add_argument("--role", default="Target Role")
    parser.add_argument("--company", default="Target Company")
    parser.add_argument("--content_file", required=True, help="Path to session text file")
    parser.add_argument("--mastery_file", default=None,
                         help="Optional path to /graphify Role Mastery content "
                              "(same JOB N — Title section format), rendered after the Glossary")
    parser.add_argument("--output", default="/mnt/user-data/outputs/hireme_coaching_report.pdf")
    args = parser.parse_args()

    with open(args.content_file, "r", encoding="utf-8") as f:
        content = f.read()

    mastery_content = None
    if args.mastery_file:
        with open(args.mastery_file, "r", encoding="utf-8") as f:
            mastery_content = f.read()

    generate_pdf(args.candidate, args.role, args.company, content, args.output,
                 mastery_text=mastery_content)


if __name__ == "__main__":
    main()
