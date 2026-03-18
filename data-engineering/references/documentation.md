# Data Engineering Skill — Complete Documentation

**Version:** 1.0.0  
**Date:** 2026-03-16  
**Author:** OpenClaw  
**Skill Type:** Interactive Pipeline Builder  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Use Case](#2-use-case)
3. [Requirements](#3-requirements)
4. [Architecture](#4-architecture)
5. [Pipeline Stages](#5-pipeline-stages)
6. [Checkpoint System](#6-checkpoint-system)
7. [Input Specifications](#7-input-specifications)
8. [Output Artifacts](#8-output-artifacts)
9. [Git Tracking](#9-git-tracking)
10. [Error Handling](#10-error-handling)
11. [Technology Stack](#11-technology-stack)
12. [Configuration](#12-configuration)
13. [Example Walkthrough](#13-example-walkthrough)
14. [Comparison with senior-data-engineer](#14-comparison)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. Overview

The `data-engineering` skill is an **interactive pipeline builder** that creates production-ready ETL/ELT pipelines through guided conversation. Unlike the `senior-data-engineer` skill (which provides reference material and code snippets), this skill **actively asks questions, validates inputs, builds code, executes pipelines, and delivers results** — all within a conversational flow.

### Key Differentiators

- **Interactive**: Asks questions instead of assuming
- **End-to-end**: From raw data to loaded database to Git push
- **Checkpoint-driven**: 8 user confirmation points prevent mistakes
- **Self-validating**: Quality checks before every load
- **Git-integrated**: Optional commit and push to GitHub

---

## 2. Use Case

### Primary Use Case

> A data engineer (or anyone with data) wants to build a production-ready ETL pipeline without writing boilerplate code. They provide raw data → OpenClaw asks smart questions → builds, validates, loads, and optionally deploys to Git.

### Target Users

| User | Scenario |
|------|----------|
| **Data Engineer** | Quick pipeline scaffolding for new datasets |
| **Data Analyst** | Load CSV/Excel data into a queryable database |
| **ML Engineer** | Ingest training data from Kaggle into PostgreSQL |
| **Developer** | Set up data infrastructure for a new project |

### Trigger Phrases

The skill activates when the user says:
- "Build a pipeline"
- "Create ETL"
- "Load data into database"
- "Ingest data from..."
- "Set up data pipeline"
- "Extract and load"
- "Move data from X to Y"

### NOT For

- Simple CSV analysis → use `csv-quality-checker`
- Architecture questions without building → use `senior-data-engineer`
- One-off SQL queries → use direct database tools

---

## 3. Requirements

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.8+ | 3.10+ |
| PostgreSQL | 12+ | 14+ |
| Disk Space | 1 GB | 10 GB |
| RAM | 2 GB | 8 GB |

### Python Dependencies

```
pandas>=1.5.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
kaggle>=1.5.0 (optional, for Kaggle datasets)
```

### Optional Components

| Component | Purpose |
|-----------|---------|
| `gh` CLI | GitHub repo creation and push |
| `docker` | Containerization |
| `airflow` | Pipeline scheduling |
| `kaggle` CLI | Kaggle dataset downloads |

---

## 4. Architecture

### High-Level Flow

```
USER INPUT
    │
    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   DISCOVER   │───▶│    DESIGN    │───▶│    BUILD     │
│ Source, Dest, │    │ Present plan │    │ Extract,     │
│ Requirements  │    │ for approval │    │ Transform,   │
└──────────────┘    └──────────────┘    │ Quality,Load │
                                        └──────┬───────┘
                                               │
    ┌──────────────┐    ┌──────────────┐       │
    │   DELIVER    │◀───│    DEPLOY    │◀──────┘
    │ Git commit,  │    │ Save script, │
    │ GitHub push  │    │ Airflow DAG  │
    └──────────────┘    └──────────────┘
```

### Component Interaction

```
┌─────────────────────────────────────────────────────┐
│                    OpenClaw Agent                     │
│  ┌─────────┐  ┌──────────┐  ┌─────────────────┐    │
│  │  SKILL  │  │  Scripts  │  │   References    │    │
│  │ SKILL.md│  │ *.py     │  │ architecture.md │    │
│  └────┬────┘  └────┬─────┘  └────────┬────────┘    │
│       │             │                  │             │
│       ▼             ▼                  ▼             │
│  ┌──────────────────────────────────────────┐       │
│  │         Pipeline Execution Engine         │       │
│  │  Extract → Transform → Quality → Load    │       │
│  └──────────────────────┬───────────────────┘       │
│                          │                           │
└──────────────────────────┼───────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │  Data  │  │  Post- │  │  Git/  │
         │  Source│  │ greSQL │  │ GitHub │
         └────────┘  └────────┘  └────────┘
```

---

## 5. Pipeline Stages

### Stage 1: DISCOVER SOURCE

**Purpose:** Identify and validate the data source

**Actions:**
1. Ask user where data is located
2. Verify file/connection exists
3. Preview first 5 rows
4. Analyze schema (columns, types, nulls)
5. Report findings to user

**Supported Sources:**

| Source | Detection | Validation |
|--------|-----------|------------|
| Local CSV | `ls -la <path>` | `head -5`, row count, schema analysis |
| Local JSON | `ls -la <path>` | Parse structure, detect nesting |
| Local Parquet | `ls -la <path>` | Read with pandas, check schema |
| ZIP archive | `unzip -l <path>` | Extract, find data files inside |
| PostgreSQL | `SELECT 1` | Test connection, list tables |
| MySQL | `SELECT 1` | Test connection, list tables |
| Kaggle | `kaggle datasets list` | Verify API key, download dataset |
| REST API | `curl <endpoint>` | Test endpoint, check response format |

---

### Stage 2: DISCOVER DESTINATION

**Purpose:** Identify target and verify connectivity

**Actions:**
1. Ask where clean data should land
2. Test database connection
3. Ask for database name (create if needed)
4. Ask for table name
5. Ask for conflict strategy (replace/append/fail)

---

### Stage 3: DISCOVER REQUIREMENTS

**Purpose:** Gather transformation and quality preferences

**Actions:**
1. Ask about transformations (rename, filter, derive)
2. Ask about quality checks
3. Ask about date parsing strategy
4. Ask about null handling
5. Ask about columns to exclude

---

### Stage 4: DESIGN

**Purpose:** Present complete plan for approval

**Output Format:**
```
📋 Pipeline Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Source:       [details]
🔄 Transform:    [operations]
🔍 Quality:      [checks]
📤 Destination:  [db.table]
📄 Reports:      [paths]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed? (yes / no / modify)
```

---

### Stage 5: BUILD & EXECUTE

**Sub-phases:**

| Phase | Action | Output |
|-------|--------|--------|
| **5a. Extract** | Read source into pandas DataFrame | Log: row/column count, file size |
| **5b. Transform** | Normalize columns, parse dates, dedup | Log: transformations applied |
| **5c. Quality** | Run validation checks | Log: pass/fail/warn per check |
| **5d. Load** | Batch insert to database | Log: rows loaded, time elapsed |
| **5e. Report** | Generate HTML + JSON reports | Log: report file paths |

**Transform Operations (always applied):**
1. Column name normalization (lowercase, underscores)
2. Whitespace stripping on string columns
3. Auto date detection and parsing
4. Numeric type optimization (float64 → Int64 where possible)
5. Empty row removal
6. Duplicate removal

**Quality Checks:**
1. Schema validation (expected columns present)
2. Row count (non-zero)
3. Null analysis per column
4. Uniqueness on key columns
5. Format validation (emails, dates, URLs, phones)
6. Data freshness check

---

### Stage 6: POST-LOAD VALIDATION

**Purpose:** Verify data in destination

**Actions:**
1. `SELECT COUNT(*)` — verify row count matches
2. `SELECT * LIMIT 5` — show sample rows
3. Offer analytics queries

---

### Stage 7: DEPLOY

**Purpose:** Save reusable pipeline code

**Options:**
1. **Python script** — CLI tool with argparse
2. **Airflow DAG** — Scheduled execution
3. **Dockerfile** — Containerized pipeline
4. **All of the above**
5. **Skip**

**Generated Script Features:**
- Full CLI argument support (`--dataset`, `--table`, `--database`, etc.)
- Logging to file
- Error handling with retries
- Built-in quality checks
- Configurable batch size

---

### Stage 8: DELIVER

**Purpose:** Version control and remote backup

**Options:**
1. **Existing GitHub repo** — commit + push to specified repo/branch
2. **New GitHub repo** — create repo via `gh` CLI + push
3. **Keep local** — no Git operations

**Commit Message Format:**
```
feat: ETL pipeline <source> → <destination>

- Source: <file> (<rows> rows × <cols> columns)
- Target: <host>:<port>/<database>.<table>
- Transforms: <list>
- Quality: <X>/<Y> checks passed
- Execution time: <N>s
```

---

## 6. Checkpoint System

The skill uses **8 checkpoints** to ensure user control at every critical point.

| # | Stage | Type | Question | Blocks |
|---|-------|------|----------|--------|
| 1 | Source | **Required** | "Found X rows. Correct?" | Execution |
| 2 | Destination | **Required** | "Load into db.table?" | Execution |
| 3 | Requirements | **Required** | "These transforms OK?" | Execution |
| 4 | Design | **Required** | "Plan looks good?" | Execution |
| 5 | Pre-Load | **Required** | "Quality passed. Load?" | DB write |
| 6 | Post-Load | **Optional** | "Run analytics?" | Nothing |
| 7 | Deploy | **Required** | "Save script?" | File write |
| 8 | Deliver | **Required** | "Push to Git?" | Git operations |

**Rules:**
- Never skip required checkpoints
- Present one question group at a time (don't overwhelm)
- Always offer "modify" or "go back" as options
- Confirm before any destructive action (replace table, force push)

---

## 7. Input Specifications

### Supported File Formats

| Format | Extensions | Read Method |
|--------|-----------|-------------|
| CSV | `.csv` | `pd.read_csv()` |
| JSON | `.json` | `pd.read_json()` |
| Parquet | `.parquet` | `pd.read_parquet()` |
| Excel | `.xlsx`, `.xls` | `pd.read_excel()` |
| ZIP | `.zip` | `unzip` → detect format inside |

### Supported Databases

| Database | Driver | Connection String |
|----------|--------|-------------------|
| PostgreSQL | `psycopg2` | `postgresql://user:pass@host:port/db` |
| MySQL | `pymysql` | `mysql+pymysql://user:pass@host:port/db` |
| SQLite | `sqlite3` | `sqlite:///path/to/db.sqlite` |
| Snowflake | `snowflake-connector` | `snowflake://user:pass@account/db` |

---

## 8. Output Artifacts

### Directory Structure

```
workspace/
├── etl-pipeline/
│   ├── scripts/
│   │   ├── etl_<source>_to_<dest>.py    # Reusable pipeline script
│   │   ├── quality_checks.py             # Quality checker
│   │   ├── data_quality_validator.py      # Advanced validator
│   │   ├── etl_performance_optimizer.py   # Performance analyzer
│   │   └── pipeline_orchestrator.py       # DAG generator
│   ├── dags/
│   │   └── dag_<name>.py                 # Airflow DAG (optional)
│   ├── data/
│   │   └── <extracted_files>             # Raw data cache
│   ├── logs/
│   │   └── pipeline.log                  # Execution log
│   └── config/
│       └── pipeline_config.yaml          # Pipeline config
│
├── reports/
│   ├── <name>_quality_report_*.html      # Quality report (HTML)
│   ├── <name>_quality_report_*.json      # Quality report (JSON)
│   └── etl_pipeline_report_*.html        # Execution report (HTML)
│
└── .git/                                 # Git tracking (optional)
```

### Report Types

| Report | Format | Contains |
|--------|--------|----------|
| Quality Report | HTML | Styled cards, check results, recommendations |
| Quality Report | JSON | Machine-readable check results |
| Pipeline Report | HTML | Execution summary, phase details, timing |
| Execution Log | Text | Timestamped log of all pipeline operations |

---

## 9. Git Tracking

### Workflow

```
1. git init (if not already a repo)
2. git add .
3. git commit -m "feat: ETL pipeline <source> → <dest>"
4. git remote add origin <url> (if new)
5. git push -u origin <branch>
```

### Commit Convention

Uses conventional commits:
- `feat:` — New pipeline or feature
- `fix:` — Bug fix in existing pipeline
- `docs:` — Documentation updates
- `refactor:` — Code restructuring

### GitHub Integration

| Action | Command |
|--------|---------|
| Check auth | `gh auth status` |
| Create repo | `gh repo create <name> --<visibility> --source=. --push` |
| Push existing | `git push -u origin <branch>` |
| Create PR | `gh pr create --title "..." --body "..."` |

---

## 10. Error Handling

### Error Response Protocol

1. Show exact error message
2. Explain in plain language
3. Suggest fix
4. Ask: "Fix and retry, or handle manually?"

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `fe_sendauth: no password supplied` | Missing DB password | Provide password via `--password` or `PGPASSWORD` |
| `role "X" does not exist` | User not created in PostgreSQL | `CREATE USER X WITH PASSWORD 'Y'` |
| `database "X" does not exist` | DB not created | `CREATE DATABASE X` |
| `FileNotFoundError` | Wrong file path | Verify path with `ls` |
| `kaggle: command not found` | Kaggle CLI not installed | `pip install kaggle` |
| `No CSV files found` | ZIP contains non-CSV data | Check ZIP contents, specify format |

---

## 11. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.10+ | Core pipeline code |
| **Data** | Pandas | Data manipulation & transformation |
| **Database** | SQLAlchemy + psycopg2 | Database abstraction & connection |
| **Quality** | Custom validators | Pre-load data validation |
| **Orchestration** | Apache Airflow | Scheduled pipeline execution |
| **Containers** | Docker | Pipeline containerization |
| **Version Control** | Git + GitHub CLI | Code versioning & collaboration |
| **Reports** | HTML/CSS | Styled execution reports |

---

## 12. Configuration

### Pipeline Config (YAML)

```yaml
source:
  type: kaggle|local|database|api
  path: /path/to/data
  format: csv|json|parquet

destination:
  type: postgresql|mysql|snowflake
  host: localhost
  port: 5432
  database: my_db
  table: my_table
  if_exists: replace|append|fail

transform:
  lowercase_columns: true
  strip_whitespace: true
  handle_nulls: keep|drop|fill_default
  date_columns: [] # auto-detected if empty

quality:
  enabled: true
  checks: [not_null, uniqueness, format, freshness]
  fail_on_warning: false

pipeline:
  batch_size: 5000
  log_file: logs/pipeline.log
```

---

## 13. Example Walkthrough

See `references/architecture.html` for a visual interactive walkthrough.

### Quick Example

```
User: "Build a pipeline for my house data"
Bot:  "Where is your data?"
User: "/home/user/Downloads/houses.csv"
Bot:  "Found 21,613 rows × 21 cols. Preview: [table]. Correct?"
User: "Yes"
Bot:  "Where should it land?"
User: "PostgreSQL localhost, user postgres, password password"
Bot:  "Connected ✅. Table name?"
User: "houses"
Bot:  "Plan: Extract → Transform → Quality → Load. Proceed?"
User: "Go"
Bot:  "📥→🔄→🔍→📤 Done! 21,613 rows in 6.7s. Save script?"
User: "Yes"
Bot:  "💾 Saved. Push to GitHub?"
User: "Yes, create new repo, private"
Bot:  "🚀 Created github.com/user/etl-pipelines. All done!"
```

---

## 14. Comparison

| Feature | `senior-data-engineer` | `data-engineering` |
|---------|----------------------|-------------------|
| **Mode** | Reference / Q&A | Interactive builder |
| **Interaction** | User drives | Skill drives (asks questions) |
| **Output** | Code snippets | Complete working pipeline |
| **Execution** | Manual | Automated (with checkpoints) |
| **Quality** | Templates provided | Built-in, runs automatically |
| **Git** | Not included | Full Git/GitHub integration |
| **Reports** | Not included | HTML + JSON auto-generated |
| **Checkpoints** | None | 8 confirmation points |
| **Scope** | Architecture + patterns | Build + deploy + deliver |

---

## 15. Troubleshooting

### Pipeline won't start
- Check Python version: `python3 --version` (need 3.8+)
- Check dependencies: `pip3 install pandas sqlalchemy psycopg2-binary`

### Can't connect to PostgreSQL
- Is PostgreSQL running? `systemctl status postgresql`
- Test manually: `PGPASSWORD=pass psql -U user -h localhost -d postgres -c "SELECT 1"`
- Check pg_hba.conf auth method

### Kaggle download fails
- Check API key: `ls ~/.kaggle/kaggle.json`
- Verify permissions: `chmod 600 ~/.kaggle/kaggle.json`
- Test CLI: `kaggle datasets list`

### Git push fails
- Check auth: `gh auth status`
- Check remote: `git remote -v`
- Try SSH: `ssh -T git@github.com`

### Reports not generating
- Check reports directory exists: `mkdir -p workspace/reports`
- Check write permissions: `ls -la workspace/reports/`
- Check disk space: `df -h`
