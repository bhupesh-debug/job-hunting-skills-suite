# 🚀 Job Hunting & Career Acceleration Skills Suite

> A battle-tested suite of 6 agentic skills for senior professionals, international candidates (F-1 STEM OPT), and high-impact job seekers. Engineered for use with **Antigravity**, **Claude Code**, **Gemini**, **Cursor**, **ChatGPT**, and agentic coding workflows.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Skills: 8](https://img.shields.io/badge/Skills-8%20Specialized%20Agents-indigo.svg)](#the-skills-suite)
[![Platform: Antigravity%20%7C%20Claude%20Code](https://img.shields.io/badge/Platform-Antigravity%20%7C%20Claude%20Code-emerald.svg)](#installation--agent-setup)
[![Interactive App: Included](https://img.shields.io/badge/Web%20App-Multi--Tab%20Executive%20Suite-cyan.svg)](#interactive-web-application)

---

## 🎯 The Skills Suite

This repository consolidates 8 high-leverage career and job-hunting agent skills into a single unified workspace:

| Skill | Folder | Package | Core Capability |
|---|---|---|---|
| **Mastery** | [`skills/mastery`](skills/mastery) | [`packages/mastery.skill`](packages/mastery.skill) | Elite job-mastery coach, operations trainer, process engineer & performance mentor: complete 8-phase training program, reverse-engineered workflows, practical job simulator & 30/60/90-day plan. |
| **HireMe** | [`skills/hireme`](skills/hireme) | [`packages/hireme.skill`](packages/hireme.skill) | Elite interview coaching, 6-step system, word-for-word salary negotiation, STAR story bank & automated branded PDF report generator. |
| **Injobman** | [`skills/injobman`](skills/injobman) | [`packages/injobman.skill`](packages/injobman.skill) | End-to-end application package builder: JD breakdown, ATS-tailored resume (.docx), cover letter (.docx), and 80/20 interview cards. |
| **Job Matcher** | [`skills/job-matcher`](skills/job-matcher) | [`packages/job-matcher.skill`](packages/job-matcher.skill) | Deep resume-to-JD match analysis, keyword gap forensics, ATS scoring rubric, and executive PDF reporting with color-coded alerts. |
| **JD → ML Project** | [`skills/jd-to-ml-project`](skills/jd-to-ml-project) | [`packages/jd-to-ml-project.skill`](packages/jd-to-ml-project.skill) | 10-step ML project architect that deconstructs any JD into an execution-ready production ML repo and 10-slide interview presentation. |
| **Live Job Hunter** | [`skills/live-job-hunter`](skills/live-job-hunter) | [`packages/live-job-hunter.skill`](packages/live-job-hunter.skill) | Real-time multi-platform job hunter (LinkedIn, Indeed, Wellfound, ATS), candidate keyword forensics, 20+ curated pipeline, and hiring manager outreach. |
| **STEM OPT NYC Hunter** | [`skills/stem-opt-nyc-employer-hunter`](skills/stem-opt-nyc-employer-hunter) | [`packages/stem-opt-nyc-employer-hunter.skill`](packages/stem-opt-nyc-employer-hunter.skill) | U.S. immigration + career strategist for F-1 STEM OPT: 25+ NYC E-Verify database, compliance auditor (Form I-983), and 30-day conversion action plan. |
| **RecruitXray** | [`skills/recruitxray`](skills/recruitxray) | [`packages/recruitxray.skill`](packages/recruitxray.skill) | Forensic recruiter due diligence investigator: 9-phase audit (digital footprint, scam signal detection, contradiction analysis, Riskometer 0–100 score). |

---

## 🏗️ Repository Architecture

```text
job-hunting-skills-suite/
├── index.html                               # Rich multi-tab interactive web portal & execution engine
├── README.md                                # Comprehensive documentation & operational guide
├── packages/                                # Pre-packaged .skill zip bundles for 1-click import
│   ├── mastery.skill
│   ├── hireme.skill
│   ├── injobman.skill
│   ├── jd-to-ml-project.skill
│   ├── job-matcher.skill
│   ├── live-job-hunter.skill
│   ├── stem-opt-nyc-employer-hunter.skill
│   └── recruitxray.skill
└── skills/                                  # Unpacked skill source code, scripts & references
    ├── mastery/
    │   └── SKILL.md                         # 8-phase job-mastery curriculum, workflows & simulation engine
    ├── hireme/
    │   ├── SKILL.md                         # 6-step coaching protocol & prompt engine
    │   ├── scripts/
    │   │   └── generate_pdf.py              # ReportLab hyperlinked PDF coaching report builder
    │   └── references/
    │       ├── email-wrapper.md             # Delivery email templates
    │       ├── negotiation-scripts.md       # Word-for-word salary counter scripts
    │       ├── question-bank.md             # 80+ categorized high-probability questions
    │       └── star-bank.md                 # STAR narrative repository (Leadership, Conflict, Analytics)
    ├── injobman/
    │   ├── SKILL.md                         # Application handbook generator engine
    │   └── references/
    │       ├── full_handbook_spec.md        # Comprehensive multi-page career handbook schema
    │       ├── interview_prep_framework.md  # 80/20 priority rating system (Must Master cards)
    │       └── resume_and_cover_letter.md   # ATS resume & targeted cover letter rules
    ├── jd-to-ml-project/
    │   └── SKILL.md                         # 10-step ML problem framing & repo scaffold
    ├── job-matcher/
    │   └── SKILL.md                         # Resume vs JD gap analysis & scoring rubric
    ├── live-job-hunter/
    │   └── SKILL.md                         # Boolean query engine, search cadence & pipeline schema
    ├── stem-opt-nyc-employer-hunter/
        ├── SKILL.md                         # NYC STEM OPT placement workflow & rules
        └── references/
            ├── 30-day-action-plan.md        # Daily 10 apps + 3 networking conversion plan
            ├── employer-profiles.md         # 25 curated NYC E-Verify employer profiles
            ├── red-flags-and-compliance.md  # Third-party staffing traps & Form I-983 audit
            └── targeting-strategy.md        # LinkedIn Boolean strings & outreach scripts
    └── recruitxray/
        └── SKILL.md                         # Forensic recruiter vetting & 9-phase due diligence
```

---

## ⚡ Interactive Web Application (`index.html`)

An executive-level, zero-dependency interactive dashboard is included right in the repository root:

- **Unified Multi-Tab Interface**: Navigate smoothly between all 6 skills and an executive Suite Overview.
- **One-Click Demo Preload**: Instantly loads Bhupesh's senior finance & analytics profile along with a live sample Job Description to test all engines simultaneously.
- **Interactive Simulators**:
  - **Match Scorer**: Computes ATS compatibility, hard skills match, and missing keywords in real time.
  - **Mock Interview Engine**: Randomized question selector across 4 categories with answer evaluator and STAR rubric.
  - **Salary Negotiation Terminal**: Copyable scripts for deflection, counter-offers, and competing offer leverage.
  - **ML Project Architect**: Visualizes the 10-step pipeline and generates a 10-slide deck outline.
  - **Job Pipeline Tracker**: Filterable table of 20+ senior roles across NYC and remote with salary bands and direct apply links.
  - **NYC E-Verify Employer Database**: Searchable table of 25 confirmed NYC employers with OPT friendliness rankings.
  - **30-Day Conversion Checklist**: Interactive day-by-day roadmap with progress tracking.
- **Instant Prompt Exporters**: One-click copy buttons for prompt markdown tailored for Antigravity, Claude Code, or ChatGPT.

To run the web app, simply open `index.html` in any web browser, or serve it locally:

```bash
# Python local server
python -m http.server 8080
# Open http://localhost:8080 in your browser
```

---

## 💻 Installation & Agent Setup

### 1. Using in Google Antigravity IDE
To install these skills in your Antigravity agent configuration:
```bash
# Copy all skills into your local Antigravity skills directory
cp -r skills/* ~/.gemini/config/skills/
# Or copy to your workspace .agents/skills/ directory
cp -r skills/* .agents/skills/
```

### 2. Using in Claude Code
```bash
# Copy into Claude Code's skills folder
cp -r skills/* ~/.claude/skills/
```

### 3. Using as Standalone Prompts
Open any `SKILL.md` file in `skills/<skill-name>/SKILL.md` and paste its contents directly into your AI prompt window or system prompt.

---

## 🔄 End-to-End Workflow Pipeline

```text
[1. Job Discovery & Recruiter Forensics]
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
  live-job-hunter                            recruitxray
  (20+ Active Senior Roles)                 (Recruiter Due Diligence & Riskometer)
       │                                         │
       ├─────────────────────────────────────────┘
       ▼
[2. Employer Verification]              [3. Match Forensics]
       │                                         │
stem-opt-nyc-employer-hunter                 job-matcher
  - E-Verify Confirmation                   - ATS Score (0-100%)
  - Form I-983 Compliance                   - Keyword Gap Analysis
  - 30-Day Action Cadence                   - Disqualifier Audit
       │                                         │
       └────────────────────┬────────────────────┘
                            │
                            ▼
               [4. Tailored Application]
                            │
                         injobman
                 - Tailored ATS Resume (.docx)
                 - Targeted Cover Letter (.docx)
                 - 80/20 High-ROI Interview Cards
                            │
       ┌────────────────────┴────────────────────┐
       ▼                                         ▼
[5. Portfolio Project]                  [6. Interview Mastery]
       │                                         │
jd-to-ml-project                              hireme
  - 10-Step ML Blueprint                    - 6-Step Interview Coaching
  - 10-Slide Interview Deck                 - STAR Story Bank
  - Production GitHub Repo                  - Word-for-Word Salary Negotiation
                                            - Branded PDF Coaching Report
```

---

## 📄 License & Credits
Curated and architected by [Bhupesh Chandra](https://github.com/bhupesh-debug). Licensed under the MIT License.
