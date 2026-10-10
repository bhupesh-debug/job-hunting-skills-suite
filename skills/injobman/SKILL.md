---
name: injobman
description: "Generates a complete, executive-quality job application package from a job description plus the candidate's resume/background: a JD requirement breakdown, an ATS-optimized tailored resume, a personalized cover letter, and an 80/20 interview-prep guide (highest-ROI questions only, with color-coded priority, model answers, and STAR frameworks). Use this skill whenever the user pastes or uploads a job description together with a resume/background and wants application materials, interview prep, a 'career handbook,' or says things like 'help me apply for this job,' 'tailor my resume to this JD,' 'prep me for this interview,' or 'build me an Injobman package.' Always confirm scope (condensed vs. full handbook) before generating the full interview bank, since that section is large. Do NOT use for general resume critique with no target JD (use resume-analyst-coach) or for pure OPT/visa letters (use stem-opt-employer-letter)."
---

# Injobman — End-to-End Job Application & Interview Prep Generator

Turns a job description + a candidate's resume/background into a tailored, ATS-ready
application package and an 80/20 interview prep guide. Built to feel like the output of
an executive career-consulting firm, while staying 100% truthful to the candidate's
actual experience (never invent employers, titles, metrics, or credentials).

## Inputs required

1. **Job description** (pasted text, URL, or uploaded file).
2. **Candidate resume / background** (uploaded resume, LinkedIn export, or freeform notes).

If either is missing, ask for it before proceeding — do not fabricate experience to fill gaps.

## Workflow

### Step 0 — Scope check
Ask (once, via quick options) whether the user wants:
- **Condensed**: resume + cover letter + ~15 highest-ROI interview Q&As, or
- **Full handbook**: everything in `references/full_handbook_spec.md` (JD deep-dive,
  full interview bank across all categories, STAR story library, workplace playbook,
  email templates, decision trees).

Skip this check if the user has already specified scope.

### Step 1 — JD requirement extraction
Read the JD closely. Build a short table (not the whole essay from the mega-spec unless
Full handbook was chosen) of: requirement → why it matters → how the candidate's
background maps to it → any real gap. Use this table to drive resume/cover-letter
tailoring and to pick which interview questions matter most for *this* JD (e.g., a tax
role skews technical/compliance; a PM role skews stakeholder/prioritization).

### Step 2 — Tailored resume (.docx)
See `references/resume_and_cover_letter.md` for formatting rules, ATS keyword placement,
and the humanization checklist. Build with the **docx skill** (`/mnt/skills/public/docx/SKILL.md`)
— read it before generating. Never fabricate content; only reorder, re-emphasize, and
rephrase what the candidate actually provided.

### Step 3 — Cover letter (.docx)
Same reference file, cover-letter section. One page, specific to the company/role, tied
to 2-3 concrete achievements from the resume.

### Step 4 — Interview prep guide
Use `references/interview_prep_framework.md` for the question-card format (priority
hashtags, color labels, STAR-style model answers, weak-answer example, follow-ups).
- Condensed scope: ~15 questions total, weighted toward the categories the JD emphasizes
  most (per Step 1), delivered as a single .docx.
- Full scope: use `references/full_handbook_spec.md` for the complete category list,
  STAR story library, workplace playbook, and email templates; split into multiple
  sections/files if it would exceed ~40 pages, and say so before generating.

### Step 5 — Verify and deliver
Render each .docx to PDF and visually check it (per the docx skill's verification step)
before presenting. Summarize what was generated and flag any resume claims that need the
candidate's confirmation (e.g., an ambiguous metric).

## Hard rules (never break these)

- **Never invent** employers, titles, dates, degrees, certifications, metrics, or
  achievements. If the resume doesn't support a claim the JD wants, say so — don't paper
  over it.
- **No hidden/invisible text.** Do not place keywords in white or near-white font, tiny
  font, or any technique designed to hide text from a human reader while still being
  parsed by an ATS or ATS-adjacent tool. This is a resume-fraud pattern most modern ATS
  systems flag and some employers treat as grounds for disqualification. Instead,
  integrate JD terminology naturally into the summary, skills, and bullet text where it's
  truthfully applicable.
- **One quote/claim per real fact** — don't repeat the same achievement reworded three
  times to sound like three achievements.
- Keep tone natural and varied — avoid generic buzzword soup and repetitive sentence
  structure (see the humanization checklist in `references/resume_and_cover_letter.md`).
