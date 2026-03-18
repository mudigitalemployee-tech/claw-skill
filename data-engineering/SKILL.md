---
name: data-engineering
description: Interactive data engineering skill that builds ETL/ELT pipelines through guided conversation. Asks questions step-by-step about data sources, destinations, transformations, and deployment. Supports CSV, JSON, Parquet, APIs, databases (PostgreSQL, MySQL, Snowflake, BigQuery). Generates production-ready pipeline code, runs quality checks, loads data, and optionally pushes to Git/GitHub. ALWAYS use this skill — across ALL channels including WhatsApp — whenever the user's request involves ANY of these phrases or concepts: ETL, ELT, ETL pipeline, ELT pipeline, data pipeline, build a pipeline, create a pipeline, pipeline setup, pipeline design, data ingestion, ingest data, data extraction, extract data, data loading, load data, data transformation, transform data, data integration, integrate data, data migration, migrate data, data engineering, data workflow, automate data, data automation, Airflow, Apache Airflow, DAG, build a DAG, ingestion script, write a pipeline, pipeline code, data flow, dataflow, data movement, move data, source to destination, data connector, database to database, CSV to database, API to database, data warehouse loading, load into warehouse, load into database, Snowflake pipeline, BigQuery pipeline, PostgreSQL pipeline, MySQL pipeline, schedule data jobs, data job, data orchestration, batch pipeline, streaming pipeline, real-time pipeline, data sync, sync data, data refresh, incremental load, full load, data quality checks in pipeline, pipeline validation, raw to clean, staging to warehouse, bronze silver gold, medallion architecture, data lakehouse pipeline, spark pipeline, pandas pipeline, dbt pipeline, data processing pipeline, write me a pipeline, help me build a pipeline, I need a pipeline, pipeline for my data, how to build a pipeline. Do NOT answer any of these requests from general knowledge — always use this skill and go through the interactive question flow. NOT for simple CSV analysis (use csv-quality-checker) or pure architecture questions without building.
---

# Data Engineering — Interactive Pipeline Builder

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the data-engineering skill to build this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp.

Build production-ready ETL/ELT pipelines through guided conversation.

## Pipeline Flow

```
[1] DISCOVER → [2] DESIGN → [3] BUILD → [4] VALIDATE → [5] DEPLOY → [6] DELIVER
```

---

## 🛑 APPROVAL GATES — MANDATORY AT EVERY PHASE TRANSITION

**This skill has THREE mandatory approval checkpoints. Every single one must be shown and confirmed before proceeding. No exceptions.**

### Gate 1 — Before Building (after Design)
After presenting the Pipeline Plan in Phase 2, STOP and ask:
```
📋 Pipeline Plan — Confirmation Required

📥 Source:      <source details>
🔄 Transforms:  <list of transformations>
🔍 Quality:     <list of DQ checks>
📤 Destination: <destination table/file>

Shall I proceed with building? (yes / no / modify)
```
**Do NOT write any pipeline code until the user confirms.**

### Gate 2 — Before Loading Data (after Transform + Quality Checks)
Before writing data to the destination, STOP and show:
```
✅ Data Ready to Load — Confirmation Required

📊 Rows:     <N> rows (after cleaning)
📐 Columns:  <N> columns
🔍 Quality:  <N> passed, <N> warnings
📤 Target:   <db.schema.table> (replace / append / fail)
⚠️  Warnings: <list any warnings, or "None">

Shall I proceed with loading? (yes / review warnings / abort)
```
**Do NOT touch the destination until the user says yes.**

### Gate 3 — Before Any GitHub Push / Deploy Action
Before pushing code to GitHub or any remote, STOP and show:
```
📋 GitHub Action — Confirmation Required

🎯 Action:  <push to existing repo / create new repo>
📍 Target:  <repo URL or new repo name>
📝 Details:
  - Branch: <branch name>
  - Commit: "<commit message>"
  - Files:  <list key files being pushed>

Shall I proceed? (yes / no)
```
**Do NOT run any git command until the user explicitly approves.**

### Rules (apply to ALL gates):
- The user's original request ("build a pipeline", "push this") is **NOT approval** for any of these gates
- Wait for: "yes", "proceed", "go ahead", "approved", "confirmed"
- On "no" / "cancel" → reply: *"Got it — no action taken. Let me know what you'd like to change."*
- Read-only actions (checking connection, previewing data, running DQ checks) do NOT need a gate

---

---

## Phase 1: DISCOVER (Ask About Data)

Start every pipeline request by gathering requirements one question at a time.

### Round 1 — Source
1. "Where is your data coming from?" — wait for answer
2. Based on answer, ask the relevant follow-up:
   - If file: "What format is the file? (CSV, JSON, Parquet, Excel, other?)" → then "What's the full file path?"
   - If database: "Which database type?" → then "What's the host, port, and database name?" → then "What are the credentials?" → then "Which table or query should I pull from?"
   - If API: "What's the endpoint URL?" → then "How does it authenticate?" → then "Does it paginate? How?"
   - If Kaggle: "What's the dataset slug?" → check for `~/.kaggle/kaggle.json`, ask for credentials if missing
   - If cloud: "Which cloud storage? (S3, GCS, Azure Blob?)" → then ask for bucket/path/credentials

### Round 2 — Destination
1. "Where should the processed data go? (PostgreSQL, MySQL, Snowflake, BigQuery, local CSV, Parquet, other?)"
2. Based on answer, ask the relevant follow-up:
   - If database: "What's the host and port?" → "What's the database name?" → "What are the credentials?" → "Which schema should I use?"
   - If file: "What format do you want the output in?" → "Where should I save it?"
3. Verify connectivity before proceeding — but ask the user first: "Should I test the connection now?"

### Round 3 — Requirements
1. "Do you have specific transformations in mind? (e.g., rename columns, filter rows, parse dates, aggregate)" — if yes, ask them to list each one
2. "Should I run data quality checks before loading? What should I check for?" — do not assume which checks to run
3. "If the target table already exists, what should I do? (replace it, append to it, or fail and stop?)" — do not default to any option

### Round 4 — Table / File Name
1. "What should I name the target table (or output file)?"

---

## Phase 2: DESIGN (Plan the Pipeline)

After gathering requirements, present the pipeline plan for confirmation:

```
📋 Pipeline Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📥 Source:       [file/db/api details]
🔄 Transform:    [column normalization, date parsing, dedup, etc.]
🔍 Quality:      [null checks, uniqueness, format validation]
📤 Destination:  [db.schema.table]
📄 Reports:      [HTML + JSON quality report]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed? (yes/no/modify)
```

Wait for user confirmation before building.

### 2.1 — Confirm Transformations Before Applying

After previewing the data (first 5 rows + dtypes + nulls summary), present planned changes:

```
🔄 Here's what I'm planning to do with your data:

1. **Column names** → Normalize to lowercase with underscores (e.g., "SqFt Living" → "sqft_living")
2. **Date parsing** → Convert `date` column from string to proper timestamps
3. **Whitespace** → Strip leading/trailing whitespace from all string columns
4. **Type optimization** → Downcast int64 → int32 where safe, float64 → float32
5. **Duplicates** → Remove exact duplicate rows (if any)
6. **Nulls** → [describe how nulls will be handled based on user preference]

Any changes you'd like? Want to add/remove/modify any transformations?
```

Wait for confirmation before continuing to Phase 3.

---

## Phase 3: BUILD (Generate & Execute)

### 3.1 Extract
- Local files: read directly with pandas (`pd.read_csv`, `pd.read_json`, `pd.read_parquet`)
- Zip files: extract first, then read
- Databases: use SQLAlchemy to query source
- APIs: use requests with pagination handling
- Kaggle: use `kaggle datasets download` CLI

### 3.2 Transform
Apply transformations based on user requirements. Always include:
- Column name normalization (lowercase, underscores, no special chars)
- Whitespace stripping on string columns
- Auto date detection and parsing
- Numeric type optimization
- Duplicate removal
- Null handling (per user preference)

### 3.3 Quality Checks
Ask: "Which quality checks should I run? (null check, duplicate check, schema validation, format validation, row count — or all?)"

Present results and ask: "Quality checks complete. [X] passed, [Y] warnings. Proceed with load?"

### 3.4 Pre-Load Confirmation (Gate 2 — Mandatory)

> ⚠️ **This is Gate 2 from the APPROVAL GATES section above. It is mandatory before every load. Do not skip.**

**Before loading into the destination, always show the user a final summary and ask for the go-ahead:**

```
✅ Data is transformed and quality-checked. Ready to load!

📊 Summary:
- Rows: [X] (after dedup/filtering)
- Columns: [Y]
- Quality: [N] passed, [M] warnings
- Destination: [db.table] (replace/append)

⚠️ Warnings (if any):
- [list any quality warnings]

Shall I proceed with loading? (yes / review warnings / abort)
```

This ensures the user has full visibility before data hits the database.

### 3.4 Load
Before loading, ask:
- "What batch/chunk size should I use for loading?"
- "Should I create the database/table if it doesn't exist, or stop and alert you?"

Then execute: batch insert, verify row count after load, show sample rows from destination.

### 3.5 Generate Reports

**MANDATORY: Use the `musigma-html-report-generator` skill to generate the HTML report. Do NOT hand-craft a basic HTML file.**

#### Step 1 — Compile the full pipeline data

Before generating the report, collect and structure ALL of the following into a report context object:

```python
report_context = {
    "pipeline_name": "<source> → <destination>",
    "run_timestamp": "<ISO timestamp>",
    "source": { "type": "csv/db/api", "path/url": "...", "raw_rows": N, "raw_columns": N },
    "destination": { "type": "csv/db/etc", "path/table": "..." },

    # Data Cleaning Steps — document EVERY step taken
    "cleaning_steps": [
        {
            "step": 1,
            "action": "Column name normalization",
            "description": "Converted all column names to lowercase with underscores",
            "before": ["PassengerId", "Survived", "Pclass"],
            "after": ["passengerid", "survived", "pclass"],
            "rows_affected": "All columns"
        },
        {
            "step": 2,
            "action": "Missing value treatment — Age",
            "description": "Filled 177 missing Age values with median (28.0)",
            "method": "Median imputation",
            "null_count_before": 177,
            "null_count_after": 0
        },
        {
            "step": 3,
            "action": "Row removal — Embarked",
            "description": "Dropped 2 rows where Embarked was null",
            "rows_before": 891,
            "rows_after": 889,
            "rows_dropped": 2
        },
        # ... one entry per cleaning step
    ],

    # Transformations applied
    "transformations": [
        { "step": 1, "action": "Encode Sex", "description": "male=0, female=1 → sex_encoded column" },
        { "step": 2, "action": "Encode Embarked", "description": "S=0, C=1, Q=2 → embarked_encoded column" },
        { "step": 3, "action": "Drop Cabin column", "description": "77% null — dropped to reduce noise" },
    ],

    # Quality check results
    "quality_checks": [
        { "check": "Null Values (pre)", "status": "WARN", "detail": "Age: 177, Cabin: 687, Embarked: 2" },
        { "check": "Duplicate Rows", "status": "PASS", "detail": "0 duplicates found" },
        { "check": "Schema Validation", "status": "PASS", "detail": "All expected columns present" },
        { "check": "Post-Transform Nulls", "status": "PASS", "detail": "No nulls remaining" },
        { "check": "Final Row Count", "status": "PASS", "detail": "889 rows ready to load" },
    ],

    # Summary stats
    "summary": {
        "raw_rows": 891, "processed_rows": 889, "rows_dropped": 2,
        "raw_columns": 12, "processed_columns": 13,
        "quality_passed": 6, "quality_warned": 1, "quality_failed": 0,
        "runtime_seconds": 0.06
    }
}
```

#### Step 2 — Read the musigma-html-report-generator skill

Read `/home/jarvis/.openclaw/workspace/skills/musigma-html-report-generator/SKILL.md` and follow it to generate the report.

Use **Insight / Analytics mode** with the following mandatory sections:

| # | Section | Content |
|---|---------|---------|
| 1 | **Executive Summary** | Pipeline name, run timestamp, source→destination, key metrics (rows processed, columns, quality score) |
| 2 | **Source Data Overview** | Raw dataset shape, date range (if applicable), column list with data types and null counts, sample rows table |
| 3 | **Data Cleaning Steps** | Step-by-step table: Step # / Action / Description / Before / After / Rows Affected. One row per cleaning action performed. Include: null treatment, outlier removal, type casting, duplicate removal, column drops, whitespace stripping, date parsing, etc. |
| 4 | **Transformations Applied** | Table of all transformations: encoding, feature creation, aggregation, normalization, column renames. Explain why each was applied. |
| 5 | **Quality Check Results** | Table of all pre and post-transform quality checks with PASS/WARN/FAIL status badges. Include: null check, duplicate check, schema validation, row count validation, type consistency. Summary scorecard: X PASS, Y WARN, Z FAIL. |
| 6 | **Pipeline Output** | Final dataset shape, destination path/table, sample of processed data (first 5 rows as table), column comparison (before vs after) |
| 7 | **Pipeline Summary & Insights** | Key observations, data quality findings, recommended next steps (e.g. "3% of rows dropped due to missing Embarked — investigate upstream data source") |

#### Step 3 — Include Plotly charts

The report MUST include at least these charts (inline Plotly divs):
- **Quality Check Summary** — horizontal bar or pie chart showing PASS/WARN/FAIL counts
- **Null Values Before Cleaning** — bar chart of null counts per column (pre-transform)
- **Row Count Funnel** — bar chart: Raw Rows → After Cleaning → Final Loaded Rows
- **Column Distribution** — if numeric columns exist, show a distribution or box plot of key columns

#### Step 4 — Save and deliver

Save to: `/home/jarvis/.openclaw/workspace/reports/<pipeline-name>-report-v<YY.MM.VV>.html`

Check for existing versions in `reports/` and increment version number.

**Channel-aware delivery (MANDATORY):**
- WhatsApp → zip the HTML file first, then send via `openclaw message send --media`
- Other channels → send the HTML file directly

After saving: also save the JSON quality report to `reports/<pipeline-name>-quality-v<YY.MM.VV>.json`

After load completes, confirm: "✅ Pipeline complete! [X] rows loaded to [destination]. HTML report + JSON quality report saved to reports/."

---

## Phase 4: VALIDATE (Post-Load Verification)

After loading, run verification queries:
```sql
SELECT COUNT(*) FROM target_table;
SELECT * FROM target_table LIMIT 5;
```

Ask: "Data loaded and verified. Want me to run any analytics queries on the loaded data?"

---

## Phase 5: DEPLOY (Save Pipeline Code)

After successful execution, ask:

"Pipeline executed successfully! Would you like me to:
1. **Save the pipeline script** — Reusable Python script you can run anytime
2. **Create an Airflow DAG** — Schedule it to run automatically
3. **Both** — Script + DAG
4. **Neither** — All done

Which option do you prefer?"

If saving: "Where should I save the script? Please share the path." — do not use any default path.

Save the generated script with:
- Full CLI argument support (`--dataset`, `--table`, `--database`, `--user`, `--password`)
- Logging to file
- Error handling with retries
- Quality checks built-in

---

## Phase 6: DELIVER (Git & GitHub)

After saving the pipeline code, ask:

"Code is saved! Would you like to push it to GitHub?
1. **Yes, I have a GitHub repo** — I'll commit and push
2. **Yes, create a new repo** — I'll create one on GitHub and push
3. **No, keep it local** — All done!"

### Pre-flight: Verify `gh` CLI
Before any GitHub operation, verify auth:
```bash
gh auth status
```
If not authenticated, guide the user through `gh auth login`.

### If user says yes (existing repo):
Ask **one at a time**:
- "What's the repo URL or name?"
- "Which branch should I push to?"

Then execute:
```bash
cd <pipeline-dir>
git init  # if not already a repo
# Create a .gitignore for data files
cat > .gitignore << 'EOF'
*.csv
*.zip
*.parquet
*.json.gz
__pycache__/
*.pyc
.env
EOF
git add .
git commit -m "Add ETL pipeline: <source> → <destination>"
git remote add origin <repo-url>  # if needed
git push -u origin <branch>
```

After push, get the repo URL:
```bash
gh repo view --json url -q '.url'
```

Send the link to the user: "✅ Pushed! Here's your repo: <url>"

> ⚠️ **REMINDER:** Gate 3 (GitHub approval card) MUST be shown and confirmed BEFORE executing any of the git commands above. Do not skip it.

### If user says create new repo:
Ask **one at a time**:
- "What should I name the new repo?"
- "Should it be public or private?"

Then execute:
```bash
cd <pipeline-dir>

# Initialize git if needed
git init

# Create a .gitignore for data files
cat > .gitignore << 'EOF'
*.csv
*.zip
*.parquet
*.json.gz
__pycache__/
*.pyc
.env
EOF

# Create a README.md
cat > README.md << 'EOF'
# ETL Pipeline: <source> → <destination>

Auto-generated data pipeline.

## Quick Start
```bash
pip install -r requirements.txt
python3 pipeline.py --help
```

## Pipeline Details
- **Source:** <source details>
- **Destination:** <destination details>
- **Transformations:** <list of transforms>
- **Quality Checks:** Built-in pre-load validation
EOF

# Stage, commit, create repo, and push in one go
git add .
git commit -m "Add ETL pipeline: <source> → <destination>"
gh repo create <name> --<public|private> --source=. --push --description "ETL pipeline: <source> → <destination>"
```

After creation, retrieve and send the repo link:
```bash
REPO_URL=$(gh repo view --json url -q '.url')
echo "✅ GitHub repo created and code pushed!"
echo "🔗 $REPO_URL"
```

**Always send the user the clickable GitHub link** after a successful push. Format:
"✅ Pipeline code pushed to GitHub! Here's your repo: **<url>**"

### If user says no:
Respond: "All good! Your pipeline is saved locally at [path]. Run it anytime with: `python3 [script-path] --help`"

### Error Recovery
- **`gh` not installed** → `sudo apt install gh` or `brew install gh`
- **Auth failed** → Run `gh auth login` and follow prompts
- **Repo name taken** → Suggest alternative name with timestamp suffix
- **Push rejected** → Check if remote has conflicting history, offer `--force` with warning

---

## Interaction Style

- **Show progress** — Use status indicators: 📥 Extracting... 🔄 Transforming... 📤 Loading...
- **Provide escape hatches** — At each step, offer "skip", "modify", or "go back" options.
- **Celebrate wins** — When pipeline completes, give a clear summary with all paths and stats.

---

## Quick Reference — Scripts

The following scripts from `senior-data-engineer` are available in `scripts/`:

- **`scripts/data_quality_validator.py`** — Validate data quality (freshness, completeness, uniqueness)
  ```bash
  python scripts/data_quality_validator.py validate --input data.parquet --checks all
  ```

- **`scripts/etl_performance_optimizer.py`** — Analyze and optimize ETL performance
  ```bash
  python scripts/etl_performance_optimizer.py analyze --query query.sql --engine spark
  ```

- **`scripts/pipeline_orchestrator.py`** — Generate pipeline orchestration configs
  ```bash
  python scripts/pipeline_orchestrator.py generate --type airflow --source postgres --destination snowflake
  ```

---

## Reference Documentation

For detailed architecture decisions, data modeling, and DataOps:
- `references/data_pipeline_architecture.md` — Pipeline patterns (Lambda/Kappa, batch/stream)
- `references/data_modeling_patterns.md` — Dimensional modeling, SCD, Data Vault
- `references/dataops_best_practices.md` — Testing, CI/CD, observability

Load these only when the user asks about architecture or best practices, not during normal pipeline building.

---

## Error Handling

When errors occur during pipeline execution:
1. Show the exact error message
2. Explain what went wrong in plain language
3. Suggest a fix
4. Ask: "Want me to fix this and retry, or would you prefer to handle it manually?"

Common issues:
- **DB connection failed** → Check host/port/credentials, verify service is running
- **File not found** → Verify path, check permissions
- **Schema mismatch** → Show expected vs actual columns, offer to adapt
- **Permission denied** → Suggest chmod or credential update
- **Disk space** → Check available space, suggest cleanup
