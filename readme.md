# Digital Employee Skill Repository

A curated collection of OpenClaw skills for the Digital Employee platform. Each skill is a self-contained module that extends the agent's capabilities.

---

## Skills

| # | Skill | Directory | Description |
|---|-------|-----------|-------------|
| 1 | **AutoTest Engineer** | `autotest-engineer/` | Automated testing skill that analyzes projects, generates tests, runs them, and produces structured QA reports. |
| 2 | **Connected Insights** | `connected-insights/` | CXO-grade insight engine for dashboards, reports, and datasets with prescriptive business recommendations. |
| 3 | **Data Engineering** | `data-engineering/` | Interactive ETL/ELT pipeline builder for ingestion, transformation, validation, and deployment workflows. |
| 4 | **Data Science (Master)** | `data-science/` | End-to-end tabular analytics pipeline orchestrator for EDA, modeling, forecasting, and report generation. |
| 5 | **Data Science Phase 1 - EDA** | `data-science/phase1-eda/` | Phase module focused on exploratory data analysis, profiling, and insight extraction. |
| 6 | **Data Science Phase 2 - Modeling** | `data-science/phase2-modeling/` | Phase module for feature engineering, model training, evaluation, and selection. |
| 7 | **Data Science Phase 3 - Execution** | `data-science/phase3-execution/` | Phase module for final execution outputs, business interpretation, and report-ready packaging. |
| 8 | **Enterprise Arch HTML** | `enterprise-arch-html/` | Generates polished, self-contained enterprise architecture HTML pages and decision artifacts. |
| 9 | **FullStack App Builder** | `fullstack-app-builder/` | Scaffolds full-stack web apps (frontend + backend) from requirements or datasets. |
| 10 | **GitHub Manager** | `github-manager/` | Handles Git/GitHub workflows including commits, branches, PRs, repo updates, and issue-driven work. |
| 11 | **Problem Definition** | `problem-definition/` | Produces muAoPS-style structured problem definitions with retrieval-backed synthesis workflows. |
| 12 | **MuSigma HTML Report Generator** | `report_generatror/` | Builds structured, interactive HTML analytics reports using the MuSigma canonical template. |
| 13 | **SDLC Planning** | `sdlc-planning/` | Creates milestone-driven SDLC plans and implementation roadmaps before build execution. |
| 14 | **Tavily Search** | `tavily-search/` | Performs web search and URL content extraction with recency and domain controls. |
| 15 | **Transcript Skill** | `transcript-skill/` | Transcribes and summarizes video/audio from URLs, embedded players, and local media files. |

---

## Supported Input Formats

### Report Generator
- CSV, Excel, JSON, or any tabular data source
- Outputs self-contained HTML reports with Plotly charts and DataTables

### Connected Insights
- CSV, XLSX, PDF, images (PNG/JPG), HTML reports, Markdown, PPTX
- Tableau (.twb/.twbx), Power BI (.pbix)
- Outputs structured executive-grade insight reports

### AutoTest Engineer
- Any project in Python, JavaScript/TypeScript, Java, Go, Ruby, C#, Rust, PHP
- Auto-detects language, framework, and appropriate test framework
- Generates tests, runs them, and produces HTML reports with optional SonarQube integration

---

## Prerequisites

- **Git** installed ([verify](https://git-scm.com/): `git --version`)
- Access to this repository
- **OpenClaw** installed with the skills directory at:

```bash
~/.openclaw/workspace/skills/
```

---

## Quick Start

### 1. Clone the repository

```bash
git clone git@github.com:mudigitalemployee-tech/claw-skill.git
cd claw-skill
```

### 2. Copy skill(s) into OpenClaw

Copy individual skills:

```bash
cp -r report_generatror ~/.openclaw/workspace/skills/
cp -r connected-insights ~/.openclaw/workspace/skills/
```

Or copy all skills at once:

```bash
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.openclaw/workspace/skills/; done
```

### 3. Verify installation

```bash
ls ~/.openclaw/workspace/skills/
```

You should see `report_generatror/` and `connected-insights/` listed.

---

## Skill Structure

Each skill follows the OpenClaw skill convention:

```
<skill-name>/
├── SKILL.md              # Skill definition and metadata
├── assets/               # Templates, static files
├── references/           # Guides, examples
├── scripts/              # Executable pipelines (if any)
└── README.md             # Skill-specific documentation
```

---

## Updating Skills

After pulling new changes from the repo, re-copy the updated skill(s):

```bash
cd claw-skill
git pull
cp -r report_generatror ~/.openclaw/workspace/skills/
cp -r connected-insights ~/.openclaw/workspace/skills/
```

---

## Integration

Each skill's `README.md` contains integration instructions for `SOUL.md` and `AGENTS.md`. Refer to:

- [`report_generatror/SKILL.md`](report_generatror/SKILL.md)
- [`connected-insights/README.md`](connected-insights/README.md)
- [`autotest-engineer/SKILL.md`](autotest-engineer/SKILL.md)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `No such file or directory` for skills path | `mkdir -p ~/.openclaw/workspace/skills` |
| Permission denied | Check ownership of `~/.openclaw/workspace/` |
| Clone fails | Verify repo URL and SSH key / access permissions |

---

## Repository

- **GitHub:** [mudigitalemployee-tech/claw-skill](https://github.com/mudigitalemployee-tech/claw-skill)
