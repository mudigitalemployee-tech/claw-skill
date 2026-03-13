# Digital Employee Skill Repository

A curated collection of OpenClaw skills for the Digital Employee platform. Each skill is a self-contained module that extends the agent's capabilities.

---

## Skills

| # | Skill | Directory | Description |
|---|-------|-----------|-------------|
| 1 | **MuSigma HTML Report Generator** | `report_generatror/` | Generate structured, interactive HTML analytics reports using the MuSigma canonical template. Supports EDA summaries, business analytics, decision science reports, and dataset-based insights. |
| 2 | **Connected Insights** | `connected-insights/` | CXO-grade insight engine that analyses dashboards, reports, and datasets to produce prescriptive, business-standard findings using the framework: *What Happened → Why It Happened → What Should We Do → What We'll Achieve*. |

---

## Supported Input Formats

### Report Generator
- CSV, Excel, JSON, or any tabular data source
- Outputs self-contained HTML reports with Plotly charts and DataTables

### Connected Insights
- CSV, XLSX, PDF, images (PNG/JPG), HTML reports, Markdown, PPTX
- Tableau (.twb/.twbx), Power BI (.pbix)
- Outputs structured executive-grade insight reports

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
