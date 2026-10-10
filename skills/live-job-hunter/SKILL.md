---
name: live-job-hunter
description: >
  Live job search skill for senior finance professionals. Searches LinkedIn, Indeed, Wellfound,
  company career pages, and other boards for recently posted roles matched to the candidate's resume.
  Delivers a 20+ job table with direct links, hiring manager info, salary ranges, match rationale,
  and a keyword gap report. ALWAYS trigger when the user asks to "find jobs", "search for jobs",
  "job hunt", "show me open roles", "look for jobs matching my resume", "what jobs should I apply to",
  "find me FP&A jobs", "search LinkedIn for finance roles", "what's hiring right now", or any phrasing
  implying they want live job listings. Also trigger when a resume is present and the user asks what
  to apply for — even casual phrasing like "what's out there for me?" should trigger this. Analyzes
  the candidate's resume deeply before searching to match seniority, domain, and target location.
---

# Live Job Hunter

A real-time job search skill for senior finance professionals. It combines deep resume analysis
with live web search across multiple job platforms to surface relevant, recently posted opportunities
— and delivers a structured, actionable table the user can act on immediately.

---

## Step 0: Resolve candidate profile

Before searching, establish the candidate profile. Use the following sources in order of priority:

1. **Attached resume in conversation** — extract all relevant details (see Profile Schema below)
2. **userMemories** — supplement with known context (current role targets, location, skills)
3. **User-provided details in the current message** — any inline overrides (e.g., "focus on remote only")

If no resume is attached and no profile is available, ask the user to share their resume or paste
their background before proceeding.

### Profile Schema to extract:
- **Name and contact info**
- **Seniority level** (IC, senior IC, manager, director, VP)
- **Years of experience**
- **Core domain expertise** (e.g., FP&A, brokerage finance, commercial lending, strategic finance)
- **Technical skills** (tools, languages, platforms, ERPs)
- **Certifications and education**
- **Industries worked in**
- **Target roles** (from conversation or memories)
- **Target locations** (from conversation or memories)

---

## Step 1: Understand target roles and locations

If the user has not specified target roles or location in the current message, use what's in memories
or the resume context. For Bhupesh (the primary user of this skill), defaults are:

- **Target roles:** Finance & Strategy Manager, FP&A Manager, FP&A Director, Brokerage Finance Manager,
  Strategic Finance Manager, Revenue Operations Finance, Head of FP&A, Senior Finance Manager
- **Target location:** New York City Metro (NYC, Brooklyn, Manhattan, Jersey City, Hoboken) + Remote (US)
- **Preferred industries:** Fintech, brokerage/wealth management, banking, SaaS/tech with finance function,
  asset management, financial services

---

## Step 2: Live job search across platforms

Search the web for recently posted jobs (last 7–30 days). Use multiple targeted searches to maximize
coverage across platforms. Run searches with variations in role titles and locations.

### Search queries to run (adapt per session):

Use `web_search` with queries like:
- `"Finance & Strategy Manager" NYC site:linkedin.com/jobs`
- `"FP&A Manager" fintech New York 2025`
- `"Brokerage Finance" "FP&A" "Manager" New York jobs`
- `"Strategic Finance Manager" remote fintech 2025`
- `"Head of FP&A" NYC OR "New York" site:indeed.com`
- `"FP&A Director" brokerage "New York" jobs posted`
- `"Finance Manager" "brokerage" "variance analysis" NYC`
- `"Revenue Finance Manager" fintech NYC remote`
- `site:wellfound.com "finance" "FP&A" "New York" OR remote`
- `"Finance & Strategy" Manager fintech startup NYC jobs 2025`

Vary queries to hit different platforms. Use `web_fetch` on job listing URLs to retrieve full details
(salary, hiring manager, requirements, posting date) when snippets are insufficient.

### Platforms to cover:
- LinkedIn Jobs (linkedin.com/jobs)
- Indeed (indeed.com)
- Company career pages (for fintech/brokerage firms: Robinhood, Interactive Brokers, Fidelity, Charles
  Schwab, Goldman Sachs, Morgan Stanley, Jane Street, Citadel, Virtu, Two Sigma, Betterment, Wealthfront,
  SoFi, Chime, Brex, Ramp, Carta, and similar)
- Wellfound / AngelList (wellfound.com) — for fintech startups
- Glassdoor (glassdoor.com/Jobs)
- Builtin NYC (builtinnyc.com)
- Levels.fyi (for comp data cross-reference)

### Recency filter:
Only include jobs posted within the **last 30 days**. Prefer jobs posted within the last 7 days.
Note the posting date in the output. If a date cannot be confirmed, note "Date unverified."

---

## Step 3: Match filtering

For each job found, evaluate fit against the candidate profile. **Only include jobs that meet ALL of:**

1. Role title is a reasonable match (Finance Manager, FP&A Manager/Director, Brokerage Finance,
   Strategic Finance, Revenue Finance, or close adjacent)
2. Seniority is appropriate (Manager, Senior Manager, Director, or Head-of level — not analyst/associate)
3. Required experience overlaps meaningfully with the candidate's background
4. Location is NYC/Metro OR explicitly Remote (US)
5. Posted within the last 30 days

Exclude roles that are clearly junior (e.g., "Financial Analyst," "Associate") or wildly off-domain
(e.g., "Finance Manager – Real Estate Development" with no fintech/banking overlap).

---

## Step 4: Output — Structured Job Table

Present results in a clean markdown table with these exact columns:

| # | Job Title | Company | Location | Posted | Exp Required | Key Skills | Salary | Source | Link |
|---|-----------|---------|----------|--------|--------------|------------|--------|--------|------|

After the table, for each job add a brief **match rationale** block (2–3 sentences) explaining why
this role fits the candidate's resume. Group these after the table, numbered to match.

### Minimum output: 20 jobs. Target 25+.

If fewer than 20 are found in the first search pass, run additional targeted searches to fill gaps.

---

## Step 5: Hiring manager intelligence (best effort)

For each job, attempt to identify:
- **Hiring Manager or Recruiter name** (check LinkedIn, company website, job post)
- **Hiring Manager LinkedIn profile URL**
- **Company LinkedIn page URL**

Mark as "Not found" if unavailable after a reasonable search. Do not fabricate names.

---

## Step 6: Keyword gap analysis

After the table, produce a **Keyword & Skills Gap Report** section:

1. List the top 10–15 keywords/skills appearing frequently across the job listings that are NOT
   prominently featured on the candidate's resume
2. For each gap keyword, briefly note which jobs require it and why it matters
3. Suggest specific ways to incorporate each keyword into the resume (which section, what phrasing)

### Known strong keywords for Bhupesh's target roles (reference for gap analysis):
Already strong: FP&A, variance analysis, budget vs. actuals, KPI reporting, Oracle ERP, Power BI,
Python, SQL, Tableau, Bloomberg, UiPath RPA, SOX compliance, GAAP, revenue modeling, Advanced Excel

Likely gaps to check for: Anaplan, Adaptive Insights, Workday Adaptive, NetSuite Planning, Pigment,
EBITDA modeling, LBO modeling, three-statement modeling, board/investor reporting, headcount planning,
burn rate, runway analysis, ARR/MRR forecasting, go-to-market finance, unit economics, brokerage P&L,
securities lending, net interest income, margin lending, regulatory capital, FINRA, equity research.

---

## Step 7: Weekly search cadence tip

End every session with a one-line reminder:

> 💡 *Run this search again next week — most platforms refresh listings every 7 days, and the
> freshest applications get the fastest responses.*

---

## Output format notes

- Use markdown tables for the job listings
- Use numbered lists for match rationales and keyword gaps
- Keep match rationales concise — 2–3 sentences max per job
- Hyperlink job titles or "Link" column cells to direct application URLs wherever possible
- If a direct link is unavailable, provide the company careers page URL
- Flag any links that may require login (LinkedIn, Glassdoor) with a 🔒 icon

---

## Edge cases

**"Just find me jobs fast"** — Skip deep analysis preamble, go straight to search and table output.
Resume profile is assumed from memories. Deliver table first, then gap analysis.

**User provides new target role not in defaults** — incorporate it into search queries for this session.

**User specifies a specific company** — add a targeted search for that company's career page in addition
to the general searches.

**No jobs found on first search pass** — broaden title variants (e.g., include "Senior Finance Manager",
"VP Finance", "Controller") and re-run before reporting low results.

**User asks for remote only** — filter table to remote roles only and re-run searches with "remote" added.
