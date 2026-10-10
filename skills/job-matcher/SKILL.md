---
name: job-matcher
description: >
  Perform a comprehensive job match analysis between a candidate's resume/LinkedIn profile and a
  target job. Trigger this skill whenever the user uploads a resume (PDF or DOCX), a LinkedIn
  profile PDF, or pastes/provides a job description URL, and wants to know how well they match,
  what gaps exist, what keywords to add, or how to tailor their application. Also trigger when
  the user says things like "how do I match this job", "am I a good fit", "analyze my resume vs
  this JD", "job match report", "keyword gap", "ATS score", or "tailor my resume".
  ALWAYS use this skill when both a resume and job description are present, even if the user
  doesn't explicitly say "job match" — the intent to compare them is sufficient to trigger it.
---

# Job Matcher Skill

## Purpose
Produce a rich, structured **Job Match Report** that tells the candidate exactly how well they
fit a target role, where the gaps are, and what actions to take — using their resume, LinkedIn
PDF work history, and the job description (URL or pasted text).

---

## Step 1 — Gather Inputs

### Required inputs (prompt user if missing):
| Input | How to receive |
|-------|---------------|
| Resume | Uploaded PDF or DOCX — extract text via `pdfplumber` or `pypdf` |
| LinkedIn profile PDF | Uploaded PDF — extract work history, skills, endorsements |
| Job description | Pasted text **or** a URL (use `web_fetch` to retrieve full JD) |

### Extracting text from uploaded files
```python
import pdfplumber

def extract_pdf_text(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

resume_text = extract_pdf_text("/mnt/user-data/uploads/resume.pdf")
linkedin_text = extract_pdf_text("/mnt/user-data/uploads/linkedin.pdf")
```

If the file is DOCX:
```python
from docx import Document
def extract_docx_text(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])
```

### Fetching JD from a URL
If the user provides a URL, use `web_fetch` to retrieve the page and extract the job description
section. Look for keywords like "responsibilities", "requirements", "qualifications".

---

## Step 2 — Send to Claude API for Analysis

Call the Anthropic API with the extracted texts. Ask for a JSON-structured match report.

```python
import json, requests

SYSTEM_PROMPT = """You are an expert ATS system and career coach. Analyze the candidate's 
resume and LinkedIn profile against the job description. Return ONLY valid JSON — no markdown, 
no preamble — with this exact structure:

{
  "match_score": <integer 0-100>,
  "match_tier": "<Excellent|Strong|Moderate|Weak>",
  "summary": "<2-3 sentence executive summary of fit>",
  "skills_present": ["skill1", "skill2", ...],
  "skills_missing": ["skill1", "skill2", ...],
  "keyword_gaps": ["keyword1", "keyword2", ...],
  "keyword_matches": ["keyword1", "keyword2", ...],
  "experience_alignment": {
    "years_required": "<from JD>",
    "years_candidate": "<from resume>",
    "role_alignment": "<High|Medium|Low>",
    "notes": "<brief note>"
  },
  "education_alignment": {
    "required": "<from JD>",
    "candidate": "<from resume>",
    "status": "<Met|Exceeds|Below>"
  },
  "strengths": ["strength1", "strength2", "strength3"],
  "gaps": ["gap1", "gap2", "gap3"],
  "tailoring_actions": [
    {"action": "<specific thing to add/change in resume>", "priority": "<High|Medium|Low>"},
    ...
  ],
  "ats_keywords_to_add": ["keyword1", "keyword2", ...],
  "linkedin_vs_resume_gaps": ["item present on LinkedIn but missing from resume", ...]
}"""

def analyze_match(resume_text, linkedin_text, jd_text):
    user_content = f"""
RESUME:
{resume_text}

LINKEDIN PROFILE:
{linkedin_text}

JOB DESCRIPTION:
{jd_text}
"""
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"Content-Type": "application/json"},
        json={
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_content}]
        }
    )
    data = response.json()
    raw = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    return json.loads(raw.replace("```json","").replace("```","").strip())
```

---

## Step 3 — Generate the Combined Rich Match Report PDF

Use `reportlab` to produce a **multi-section rich PDF** combining the match score dashboard
AND the full side-by-side skills table AND all supporting sections in one document.

### Color system:
| Color | Hex | Use |
|-------|-----|-----|
| Navy | #1E3A5F | Section headers, primary |
| Green | #2D6A4F | Present skills, strengths |
| Red | #C1121F | Missing skills, gaps |
| Amber | #E07B39 | Medium priority |
| Teal | #006D77 | Keywords, LinkedIn gaps |
| Light bg | #F8F9FA | Alternating row fill |

### Report sections (full combined layout):

**PAGE 1 — EXECUTIVE DASHBOARD**
1. Branded header bar (navy) — Candidate name, role, company, date
2. Score banner — Large % score (color-coded), tier badge, 2-sentence summary
3. Side-by-side skills table — ✅ Have (green) | ❌ Need (red), up to 10 rows each
4. Experience & Education alignment — 2-col quick-reference table

**PAGE 2 — DEEP ANALYSIS**
5. Keyword heatmap — Matched keywords (green pill style) + Missing keywords (red pill style)
6. Strengths section — Numbered green bullets
7. Gaps section — Numbered red bullets
8. LinkedIn → Resume gap — Items on LinkedIn not reflected in resume (teal)

**PAGE 3 — ACTION PLAN**
9. Tailoring Actions — Priority-ranked table (High/Medium/Low color-coded rows)
10. ATS Keyword block — Gray small text, all keywords to add
11. Quick-win checklist — Top 5 immediate changes to make

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import date

NAVY  = colors.HexColor("#1E3A5F")
GREEN = colors.HexColor("#2D6A4F")
RED   = colors.HexColor("#C1121F")
AMBER = colors.HexColor("#E07B39")
TEAL  = colors.HexColor("#006D77")
LGRAY = colors.HexColor("#F8F9FA")
WHITE = colors.white

def section_header(text, color=NAVY):
    return Paragraph(text, ParagraphStyle(
        'SH', fontSize=13, fontName='Helvetica-Bold',
        textColor=WHITE, backColor=color,
        spaceAfter=6, spaceBefore=10,
        leftIndent=-6, rightIndent=-6,
        borderPad=6))

def build_rich_report(match_data, candidate_name, target_role, company, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            leftMargin=0.65*inch, rightMargin=0.65*inch,
                            topMargin=0.65*inch, bottomMargin=0.65*inch)
    story = []
    score = match_data["match_score"]
    score_color = GREEN if score >= 70 else (AMBER if score >= 50 else RED)

    # ── PAGE 1: EXECUTIVE DASHBOARD ──────────────────────────────────────────

    # Branded header bar
    header_data = [[
        Paragraph(f"<b>JOB MATCH REPORT</b>", ParagraphStyle('HT', fontSize=16, textColor=WHITE, fontName='Helvetica-Bold')),
        Paragraph(f"<b>{candidate_name}</b><br/>{target_role} @ {company}<br/>{date.today().strftime('%B %d, %Y')}",
                  ParagraphStyle('HS', fontSize=9, textColor=WHITE, alignment=2))
    ]]
    header_table = Table(header_data, colWidths=[4*inch, 3*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), NAVY),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Score banner
    score_data = [[
        Paragraph(f"<b>{score}%</b>",
                  ParagraphStyle('SC', fontSize=48, textColor=score_color,
                                  fontName='Helvetica-Bold', alignment=1)),
        Paragraph(
            f"<b>{match_data['match_tier'].upper()}</b><br/><br/>"
            f"<font size=10>{match_data['summary']}</font>",
            ParagraphStyle('SU', fontSize=14, textColor=score_color,
                            fontName='Helvetica-Bold', leading=16))
    ]]
    score_table = Table(score_data, colWidths=[1.8*inch, 5.2*inch])
    score_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,0), (-1,-1), LGRAY),
        ('BOX', (0,0), (-1,-1), 2, score_color),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 12))

    # Side-by-side skills table
    story.append(section_header("✅  SKILLS YOU BRING  |  ❌  SKILLS TO DEVELOP", NAVY))
    have = match_data["skills_present"][:10]
    need = match_data["skills_missing"][:10]
    skills_rows = [
        [Paragraph("<b>✅ You Have</b>", ParagraphStyle('SH2', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold')),
         Paragraph("<b>❌ To Develop</b>", ParagraphStyle('SH3', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold'))]
    ]
    for i in range(max(len(have), len(need))):
        h_text = have[i] if i < len(have) else "—"
        n_text = need[i] if i < len(need) else "—"
        skills_rows.append([
            Paragraph(h_text, ParagraphStyle('HI', fontSize=9, textColor=colors.HexColor("#1B4332"))),
            Paragraph(n_text, ParagraphStyle('NI', fontSize=9, textColor=colors.HexColor("#7B1919")))
        ])
    skills_t = Table(skills_rows, colWidths=[3.5*inch, 3.5*inch])
    skills_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), GREEN),
        ('BACKGROUND', (1,0), (1,0), RED),
        ('ROWBACKGROUNDS', (0,1), (0,-1), [WHITE, colors.HexColor("#D8F3DC")]),
        ('ROWBACKGROUNDS', (1,1), (1,-1), [WHITE, colors.HexColor("#FFE8E8")]),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('LINEAFTER', (0,0), (0,-1), 1.5, colors.lightgrey),
    ]))
    story.append(skills_t)
    story.append(Spacer(1, 10))

    # Experience & Education alignment table
    story.append(section_header("📊  EXPERIENCE & EDUCATION ALIGNMENT", NAVY))
    exp = match_data.get("experience_alignment", {})
    edu = match_data.get("education_alignment", {})
    align_rows = [
        [Paragraph("<b>Dimension</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
         Paragraph("<b>Required</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
         Paragraph("<b>You Bring</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
         Paragraph("<b>Status</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold'))],
        ["Experience", exp.get("years_required","—"), exp.get("years_candidate","—"), exp.get("role_alignment","—")],
        ["Education", edu.get("required","—"), edu.get("candidate","—"), edu.get("status","—")],
    ]
    align_t = Table(align_rows, colWidths=[1.5*inch, 1.8*inch, 2.2*inch, 1.5*inch])
    align_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(align_t)

    # ── PAGE 2: DEEP ANALYSIS ────────────────────────────────────────────────
    story.append(PageBreak())

    # Keyword heatmap — pill-style via table
    story.append(section_header("🔑  KEYWORD ALIGNMENT HEATMAP", TEAL))
    matched_kw = match_data.get("keyword_matches", [])
    missing_kw = match_data.get("keyword_gaps", [])

    def kw_row(label, kws, pill_color, text_color):
        pills = "   ".join(kws[:15])
        return [
            Paragraph(f"<b>{label}</b>", ParagraphStyle('KL', fontSize=9, textColor=WHITE,
                                                          fontName='Helvetica-Bold')),
            Paragraph(pills, ParagraphStyle('KP', fontSize=8, textColor=text_color))
        ]

    kw_rows = [
        [Paragraph("<b>Status</b>", ParagraphStyle('KH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
         Paragraph("<b>Keywords</b>", ParagraphStyle('KH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold'))],
        *[[Paragraph("✅ Matched", ParagraphStyle('KL', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
           Paragraph("  |  ".join(matched_kw[:15]), ParagraphStyle('KP', fontSize=8, textColor=colors.HexColor("#1B4332")))]],
        *[[Paragraph("❌ Missing", ParagraphStyle('KL2', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
           Paragraph("  |  ".join(missing_kw[:15]), ParagraphStyle('KP2', fontSize=8, textColor=colors.HexColor("#7B1919")))]],
    ]
    kw_t = Table(kw_rows, colWidths=[1.2*inch, 5.8*inch])
    kw_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), TEAL),
        ('BACKGROUND', (0,1), (0,1), GREEN),
        ('BACKGROUND', (0,2), (0,2), RED),
        ('BACKGROUND', (1,1), (1,1), colors.HexColor("#D8F3DC")),
        ('BACKGROUND', (1,2), (1,2), colors.HexColor("#FFE8E8")),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(kw_t)
    story.append(Spacer(1, 10))

    # Strengths & Gaps side-by-side
    story.append(section_header("💪  STRENGTHS  |  ⚠️  GAPS", NAVY))
    strengths = match_data.get("strengths", [])
    gaps = match_data.get("gaps", [])
    sg_rows = [[
        Paragraph("<b>💪 Strengths</b>", ParagraphStyle('SGH', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold')),
        Paragraph("<b>⚠️ Gaps</b>", ParagraphStyle('SGH2', fontSize=10, textColor=WHITE, fontName='Helvetica-Bold'))
    ]]
    for i in range(max(len(strengths), len(gaps))):
        s = f"• {strengths[i]}" if i < len(strengths) else ""
        g = f"• {gaps[i]}" if i < len(gaps) else ""
        sg_rows.append([
            Paragraph(s, ParagraphStyle('SI', fontSize=9, textColor=colors.HexColor("#1B4332"))),
            Paragraph(g, ParagraphStyle('GI', fontSize=9, textColor=colors.HexColor("#7B1919")))
        ])
    sg_t = Table(sg_rows, colWidths=[3.5*inch, 3.5*inch])
    sg_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), GREEN),
        ('BACKGROUND', (1,0), (1,0), AMBER),
        ('ROWBACKGROUNDS', (0,1), (0,-1), [WHITE, colors.HexColor("#D8F3DC")]),
        ('ROWBACKGROUNDS', (1,1), (1,-1), [WHITE, colors.HexColor("#FFF3CD")]),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('LINEAFTER', (0,0), (0,-1), 1.5, colors.lightgrey),
    ]))
    story.append(sg_t)
    story.append(Spacer(1, 10))

    # LinkedIn → Resume gaps
    li_gaps = match_data.get("linkedin_vs_resume_gaps", [])
    if li_gaps:
        story.append(section_header("🔗  LINKEDIN → RESUME TRANSFER OPPORTUNITIES", TEAL))
        li_rows = [[Paragraph("<b>Item on LinkedIn Missing from Resume</b>",
                               ParagraphStyle('LH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold'))]]
        for item in li_gaps[:8]:
            li_rows.append([Paragraph(f"→ {item}", ParagraphStyle('LI', fontSize=9,
                                                                    textColor=colors.HexColor("#004D5F")))])
        li_t = Table(li_rows, colWidths=[7*inch])
        li_t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), TEAL),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, colors.HexColor("#E0F7FA")]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(li_t)

    # ── PAGE 3: ACTION PLAN ──────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(section_header("🎯  TAILORING ACTION PLAN", NAVY))

    actions = match_data.get("tailoring_actions", [])
    action_rows = [[
        Paragraph("<b>#</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
        Paragraph("<b>Action</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
        Paragraph("<b>Priority</b>", ParagraphStyle('AH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold')),
    ]]
    priority_colors = {"High": colors.HexColor("#FFE8E8"), "Medium": colors.HexColor("#FFF3CD"),
                       "Low": colors.HexColor("#D8F3DC")}
    for i, act in enumerate(actions[:10], 1):
        action_rows.append([
            Paragraph(str(i), ParagraphStyle('AN', fontSize=9, alignment=1)),
            Paragraph(act["action"], ParagraphStyle('AT', fontSize=9)),
            Paragraph(f"<b>{act['priority']}</b>", ParagraphStyle('AP', fontSize=9,
                       textColor=RED if act['priority']=="High" else (AMBER if act['priority']=="Medium" else GREEN)))
        ])
    act_t = Table(action_rows, colWidths=[0.4*inch, 5.8*inch, 0.8*inch])
    act_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [WHITE, LGRAY]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(act_t)
    story.append(Spacer(1, 12))

    # Quick-win checklist
    story.append(section_header("⚡  QUICK WINS — DO THESE FIRST", GREEN))
    quick_wins = [a["action"] for a in actions if a.get("priority") == "High"][:5]
    qw_rows = [[Paragraph("<b>Immediate Action</b>",
                           ParagraphStyle('QH', fontSize=9, textColor=WHITE, fontName='Helvetica-Bold'))]]
    for i, qw in enumerate(quick_wins, 1):
        qw_rows.append([Paragraph(f"☐  {i}. {qw}",
                                   ParagraphStyle('QI', fontSize=9, textColor=colors.HexColor("#1B4332")))])
    qw_t = Table(qw_rows, colWidths=[7*inch])
    qw_t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), GREEN),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#D8F3DC")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 1, GREEN),
    ]))
    story.append(qw_t)
    story.append(Spacer(1, 12))

    # ATS keyword footer block
    story.append(section_header("🔤  ATS KEYWORDS TO ADD TO YOUR RESUME", TEAL))
    kw_block = " | ".join(match_data.get("ats_keywords_to_add", []))
    story.append(Paragraph(kw_block,
                           ParagraphStyle('KW', fontSize=8, textColor=colors.HexColor("#004D5F"),
                                           backColor=colors.HexColor("#E0F7FA"),
                                           borderPad=6, leading=14)))
    story.append(Spacer(1, 8))

    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Job Match Report | {candidate_name} | {target_role} @ {company} | {date.today()}",
        ParagraphStyle('FT', fontSize=7, textColor=colors.gray, alignment=1)))

    doc.build(story)
```

---

## Step 4 — Present Results

1. Show a **text summary** in the chat (match score, top 3 strengths, top 3 gaps, top 3 actions)
2. Save the PDF report to `/mnt/user-data/outputs/job_match_report.pdf`
3. Call `present_files` to deliver the PDF

### Chat summary format:
```
🎯 Match Score: 78% (Strong)

✅ You bring: [skill1], [skill2], [skill3]
❌ Key gaps: [gap1], [gap2], [gap3]

📋 Top 3 actions:
1. [action]
2. [action]  
3. [action]

📄 Full report with keyword map and tailoring guide → [PDF link]
```

---

## Edge Cases

- **No LinkedIn PDF**: Proceed with resume only; note in report that LinkedIn analysis is unavailable
- **URL job description fails**: Ask user to paste the JD text directly
- **DOCX resume**: Use python-docx extraction (see Step 1)
- **Very long JD**: Truncate to 3000 tokens, prioritizing Requirements and Responsibilities sections
- **Scanned/image PDF**: Use pdfplumber first; if text is empty, warn user and ask for a text-based PDF

---

## Dependencies
```bash
pip install pdfplumber python-docx reportlab --break-system-packages
```
