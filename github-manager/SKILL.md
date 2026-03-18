---
name: github-manager
description: >
  The go-to skill for ANYTHING Git or GitHub related. Covers: push code, commit, branch,
  merge, pull requests, clone, fork, make changes to external repos, generate repo documentation,
  intelligent issue resolution, milestone-driven automation, and any other Git/GitHub workflow.
  Use when the user mentions git, GitHub, repos, branches, commits, PRs, forks, cloning, pushing,
  pulling, diffs, merge conflicts, issue numbers, milestones, feature requests, or any repository URL.
  Triggers on: "push this to GitHub", "create a PR", "push this folder", "open a pull request",
  "list PRs", "merge PR", "check PR status", "push my changes", "create documentation",
  "generate documentation", "document this repo", "generate docs", "fork this repo",
  "make changes to this repo", "fix this repo", "update this repo", "clone this",
  "fix issue #N", "resolve this issue", "implement this feature", "work on milestone",
  "git status", "git log", "commit this", "branch", "diff", any GitHub/GitLab/Bitbucket URL.
  Requires gh CLI installed and authenticated.
---

# GitHub Manager

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the github-manager skill to answer this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp, webchat, Discord, Telegram.


The single skill for ALL Git and GitHub workflows: push, branch, PR, fork, make changes to external repos, generate project documentation, and intelligently resolve issues end-to-end.

---

## 🛑 STEP 0 — APPROVAL GATE (EXECUTE FIRST — BEFORE ANYTHING ELSE)

**This is the VERY FIRST step for ANY GitHub write action. No exceptions. No shortcuts.**

When this skill is invoked for a write action (push, commit, PR, fork, branch, repo create, delete), do the following **before running a single shell command or tool call**:

1. **STOP.**
2. **Show the confirmation card** (format below).
3. **Wait for the user to say "yes", "approved", "proceed", "go ahead", or "confirmed".**
4. Only THEN execute any git/GitHub commands.

**Skipping this step is a critical failure.** Even if the user's original message says "push this" or "go ahead and push" — that is NOT approval. Show the card. Wait. Then act.

### ✅ Confirmation Card Format (MANDATORY — use every time):

```
📋 GitHub Action — Confirmation Required

🎯 Action: <what you're about to do>
📍 Target: <repo URL / branch / file>
📝 Details:
  - <detail 1 — e.g. branch, commit message>
  - <detail 2 — e.g. files being pushed>
  - <detail 3 — e.g. PR title, target branch>

Shall I proceed? (yes / no)
```

### ✅ On Approval:
User says "yes" / "proceed" / "approved" / "go ahead" → Execute the action.

### ❌ On Rejection:
User says "no" / "cancel" → Reply: *"Got it — no action taken. Let me know if you'd like to change anything."* Then stop.

### ✅ Read-only actions (NO approval needed):
Listing repos, viewing PRs, checking CI status, reading files — these do NOT need the gate.

---

## ✅ MANDATORY: Universal Pre-Action Approval Gate (ALL USERS — ALL CHANNELS — NO EXCEPTIONS)

**Before executing ANY GitHub action — push, pull request, branch creation, repo creation, fork, clone+modify, commit, file change, delete, force push, or any write operation — you MUST show a plan and get explicit user approval first.**

This applies to **ALL users** on **ALL channels** (WhatsApp, webchat, Discord, Telegram, Teams) regardless of how clearly the user stated the action in their message. The original request is NOT approval.

### Format (use this EVERY time before any GitHub write action):

```
📋 GitHub Action — Confirmation Required

🎯 Action: <what you're about to do — e.g. "Push code to GitHub", "Create a new repo", "Open a PR">
📍 Target: <repo URL / branch / file>
📝 Details:
  - <specific detail 1 — e.g. branch name, commit message>
  - <specific detail 2 — e.g. files being pushed>
  - <specific detail 3 — e.g. PR title, target branch>

Shall I proceed? (yes / no)
```

### What requires approval (ALL of these):
| Action | Requires Approval |
|---|---|
| Push code to any repo | ✅ Yes |
| Create a new GitHub repo | ✅ Yes |
| Open a Pull Request | ✅ Yes |
| Create or delete a branch | ✅ Yes |
| Fork a repo | ✅ Yes |
| Clone + make changes + push | ✅ Yes |
| Add/remove collaborators | ✅ Yes |
| Change repo visibility | ✅ Yes |
| Commit and push changes | ✅ Yes |
| Force push | ✅ Yes (also mark as irreversible) |
| Delete anything | ✅ Yes (use Deletion Approval Gate format below) |

### Rules:
- **Do NOT execute any GitHub write action until the user says "yes", "proceed", "go ahead", "do it", or "confirmed"**
- Even if the user said "push this to GitHub" — still show the plan and ask
- If the user says "no" or "cancel" → abort and say "Got it — no action taken. Let me know if you'd like to change anything."
- For multi-step tasks (e.g. clone → modify → push) — show the FULL plan in ONE approval request, not one per step
- Read-only actions (viewing PRs, listing repos, checking status) do NOT need approval

### Example:

User says: *"Push the ETL pipeline to GitHub"*

❌ Wrong — immediately runs git push
✅ Right — shows this first:
```
📋 GitHub Action — Confirmation Required

🎯 Action: Push code to GitHub (new public repo)
📍 Target: github.com/mudigitalemployee-tech/titanic-etl-pipeline
📝 Details:
  - Branch: main
  - Commit: "feat: Add Titanic ETL pipeline"
  - Files: pipeline.py, data/, reports/, README.md, requirements.txt

Shall I proceed? (yes / no)
```

---

## 🧠 MANDATORY: Repo-First Skill Routing (ALWAYS RUN BEFORE ANY ACTION)

**When a GitHub repo URL is shared, NEVER assume the task is a pure Git operation.**

### Step 0 — Scan the Repo and Reason About the Task

Every time a repo URL is received:

#### 0a. Clone and scan for instruction files
```bash
git clone --depth 1 https://github.com/<owner>/<repo>.git /tmp/<repo>
```

Look for instruction/task files in this priority order — read ALL that exist:
```bash
find /tmp/<repo> -maxdepth 2 -type f | grep -iE \
  "readme|task|instruction|problem|objective|assignment|brief|spec|requirements|challenge|prompt|description|notes" \
  | head -20
```

Also check for:
- Jupyter notebooks (`.ipynb`) — often contain the task description in markdown cells
- `docs/` folder — may contain specs or problem statements
- Any `.md`, `.txt`, `.pdf`, `.docx` file at root or in `docs/`

Read each file found. Extract the **actual instructions and objectives**.

#### 0b. Understand the task from content — NOT file names

Do NOT look for the word "data science" or "ETL" in the files.
Instead, **read the instructions and reason about what needs to be done**:

Ask yourself:
- What is the end goal? (build a model? clean data? create an app? fix a bug?)
- What data is involved? (CSV, database, API, images, text?)
- What output is expected? (prediction, report, dashboard, processed file, deployed app?)
- Is this exploratory or prescriptive? (analyze and find patterns vs. follow step-by-step instructions)
- Does it require building something new or modifying existing code?

#### 0c. Map the task to skill(s) through reasoning

Based on what you understood from reading the instructions:

| If the task says / implies... | Use this skill |
|---|---|
| Analyze data, find patterns, build a model, forecast, segment, classify | **data-science** |
| Move data from A to B, clean and load, build pipeline, ETL/ELT, ingest | **data-engineering** |
| Build a web app, create a UI, REST API, full-stack application | **fullstack-app-builder** |
| Generate insights, summarize findings, CXO report from data/dashboards | **connected-insights** |
| Explore and profile a dataset, EDA, data quality | **data-analyst** |
| Create HTML report, analytics report, structured output | **musigma-html-report-generator** |
| Fix a bug, implement a feature, resolve an issue in the repo | **github-manager Part C** |
| Document the codebase, generate repo documentation | **github-manager Part B** |
| Push code, create PR, branch management | **github-manager Part A** |

**If multiple skills are needed** — sequence them logically:
- Example: instructions say "analyze the dataset and push results to GitHub" → **data-science** first, then **github-manager** to push
- Example: instructions say "build a pipeline and deploy it" → **data-engineering** first, then **github-manager** to push

#### 0d. Never collapse multi-skill work into one operation

If the task requires multiple skills:
1. Identify the **primary skill** (the one that does the core work)
2. Identify **supporting skills** (e.g., github-manager for cloning + pushing)
3. Plan the execution sequence
4. Execute them in order — do not skip any

#### 0e. Confirm the plan with the user before executing

Always present what you found and what you're going to do:

```
📂 I cloned the repo and read the task instructions.

📋 What I found:
<Brief summary of what the instructions/task files say — in plain English>

🧠 My understanding:
<What the task is actually asking for — your reasoning>

🛠️ Skill(s) I'll use:
1. <skill 1> — <why>
2. <skill 2> — <why, if applicable>

📋 Execution plan:
  Step 1: <action>
  Step 2: <action>
  Step 3: <action>

Shall I proceed?
```

Wait for user confirmation before executing.

### ❌ What NOT to do:
- Do NOT read only the README and ignore other instruction files
- Do NOT assume a repo URL = "the task is about GitHub"
- Do NOT look for explicit skill names in the files — reason from the actual content
- Do NOT use only GitHub Manager when the instructions describe a domain task
- Do NOT start executing before confirming the plan

### ✅ The golden rule:
> **Clone the repo. Read ALL instruction files. Reason about what needs to be done. Pick the right skill(s). Confirm. Execute.**
> GitHub Manager is the transport layer — the instruction files tell you what skill drives the work.

---

---

## Part A — SDLC-Based Deployment Workflow

**This workflow is triggered ONLY after the user approves an SDLC document.**

### Step 1 — Build Confirmation

After SDLC approval, ask:
> "SDLC is approved. Do you want me to build the application now?"

If the user confirms, proceed to Step 2.

### Step 2 — Repository Request

Ask:
> "Please share the GitHub repository link where the project should be pushed."

Then handle one of two scenarios:

---

### Scenario A — User Provides Repo Link

#### A1. Validate Repository
```bash
gh repo view <owner>/<repo> --json name,owner,defaultBranchRef,isPrivate
```
Extract owner, repo name, and default branch.

#### A2. Check Collaborator Access
```bash
# Check for pending invitations first
gh api user/repository_invitations --jq '.[] | select(.repository.full_name=="<owner>/<repo>") | .id'
```

**If invitation is pending → auto-accept:**
```bash
gh api --method PATCH user/repository_invitations/<invitation_id>
```

**If already a collaborator → proceed to A3.**

**If no access and no invitation:**
> "I don't have push access to this repository. Please invite `mudigitalemployee-tech` as a collaborator:
> https://github.com/<owner>/<repo>/settings/access → Add people → `mudigitalemployee-tech` → Write access"

**Pause workflow.** On next user message, re-check invitations and continue.

#### A3. Clone, Build, Push
```bash
# Clone
cd /tmp && git clone https://x-access-token:$(gh auth token)@github.com/<owner>/<repo>.git
cd <repo>

# Copy project files (exclude node_modules, __pycache__, .git)
rsync -av --exclude='node_modules' --exclude='__pycache__' --exclude='.git' <project_path>/ .

# Pre-commit validation (MANDATORY)
git config user.name   # Must be mudigitalemployee-tech
git config user.email  # Must be mudigitalemployee-tech@users.noreply.github.com

# Commit and push
git add -A
git commit -m "feat: <Project Name> — <brief description>"
git branch -M main
git push -u origin main
```

**If repo is non-empty:** Create a feature branch instead of pushing to main:
```bash
git checkout -b feat/<project-name>
git push -u origin feat/<project-name>
# Then open PR:
gh pr create --title "feat: Add <Project Name>" --body "<description>" --base main
```

---

### Scenario B — User Does Not Provide Repo

Ask:
> "I can create a new repository in my GitHub account, push the project there, and share access with you. Please share your GitHub username."

#### B1. Create Repository
```bash
gh repo create <project-name> --public --description "<description>" --confirm
```

#### B2. Initialize, Build, Push
```bash
cd /tmp && mkdir <project-name> && cd <project-name> && git init
rsync -av --exclude='node_modules' --exclude='__pycache__' --exclude='.git' <project_path>/ .

# Pre-commit validation (MANDATORY)
git config user.name   # Must be mudigitalemployee-tech
git config user.email  # Must be mudigitalemployee-tech@users.noreply.github.com

git add -A
git commit -m "feat: <Project Name> — <brief description>"
git branch -M main
git remote add origin https://x-access-token:$(gh auth token)@github.com/mudigitalemployee-tech/<project-name>.git
git push -u origin main
```

#### B3. Add User as Collaborator
```bash
gh api --method PUT repos/mudigitalemployee-tech/<project-name>/collaborators/<username> \
  -f permission=write
```

#### B4. Share Link
> "✅ Project pushed! Here's your repo: https://github.com/mudigitalemployee-tech/<project-name>
> I've added you as a collaborator — check your GitHub email for the invitation."

---

### Pre-Commit Validation (MANDATORY — ALL scenarios)

Before EVERY commit, verify identity matches the agent's GitHub account:
```bash
# Check
git config user.name   # Expected: mudigitalemployee-tech
git config user.email  # Expected: mudigitalemployee-tech@users.noreply.github.com

# Fix if wrong
git config user.name "mudigitalemployee-tech"
git config user.email "mudigitalemployee-tech@users.noreply.github.com"
```

### Security Rules

- **Never log, echo, or expose PATs or OAuth tokens** in output or chat
- If a user provides a PAT, use it only in the git remote URL and scrub after use
- Use `$(gh auth token)` for the agent's own token — never hardcode
- Always use HTTPS + token auth (SSH key is misconfigured on this machine)

### Authentication Priority

1. **Agent's own repos:** `gh auth token` via HTTPS
2. **External repos (collaborator):** Accept invitation → `gh auth token` via HTTPS
3. **External repos (user PAT):** Token embedded in remote URL → scrub after push
4. **SSH:** Do NOT use (key mismatch with `Vishwavani-00`)

### Cleanup (MANDATORY)

After every push, remove temporary directories:
```bash
rm -rf /tmp/<project-name>
```

---

## Part A.2 — General Git Push & PR Management

For git operations outside the SDLC workflow (direct push requests, PR management, etc.).

### Fork-First Workflow (for contributing to external repos)

**When the user asks to make changes, fix something, or contribute to an external repo:**

Always fork first. Never push directly to someone else's repo (unless they've given collaborator access).

#### Steps:

1. **Fork the repo:**
   ```bash
   gh repo fork <owner>/<repo> --clone=true -- --depth=1
   cd <repo>
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b <descriptive-branch-name>
   ```

3. **Make the requested changes.**

4. **Commit and push to the fork:**
   ```bash
   git add -A
   git commit -m "<descriptive commit message>"
   git push -u origin <branch-name>
   ```

5. **Open a PR back to the original repo:**
   ```bash
   gh pr create --repo <original-owner>/<repo> --title "<PR title>" --body "<description>" --base main
   ```

#### When NOT to fork:
- The user explicitly says "push directly" or "I have write access"
- The repo is the user's own repo
- Collaborator access is confirmed

### Workflow (Own Repos / Local Folders)

#### Default: Push to new branch
1. Detect current branch and remote
2. Create a new branch: `feature/<current-branch>-<timestamp>`
3. `git add -A` → commit → push
4. Optionally open a PR against the default branch

#### Explicit branch: Push to a specific branch
1. Stash uncommitted changes
2. Checkout target branch (create from remote if needed)
3. Pull latest with rebase
4. Apply stash (stop on conflicts)
5. `git add -A` → commit → push

### PR Management

```bash
gh pr list                              # List PRs
gh pr view <number>                     # View PR details
gh pr view <number> --comments          # With review comments
gh pr checks <number>                   # CI status
gh pr merge <number> --squash           # Squash merge
gh pr create --title "..." --body "..." # Create PR
```

### Error handling

- No remote → ask user for repo URL
- Auth failure → prompt `gh auth login`
- Merge conflicts → stop, show conflicts, ask user
- Protected branch → fall back to new branch + PR

---

## Part B — Repository Documentation Generator

Generate structured HTML documentation for any Git repository — clone locally, analyze, and produce a self-contained MuSigma-template HTML report with architecture diagram and sidebar TOC.

### Quick Start (3 commands)

```bash
# 1. Clone & Analyze
git clone --depth 1 <repo-url> /tmp/<repo-name>
python3 <skill-dir>/scripts/analyze_repo.py /tmp/<repo-name> --output /tmp/<repo-name>-analysis.json

# 2. Generate Architecture Diagram (optional but recommended)
python3 <skill-dir>/scripts/generate_arch_diagram.py <spec.json> /tmp/<repo-name>-arch.png

# 3. Generate HTML Report
python3 <skill-dir>/scripts/generate_report.py \
    --analysis /tmp/<repo-name>-analysis.json \
    --arch /tmp/<repo-name>-arch.png \
    --repo-url <repo-url> \
    --output <workspace>/reports/<repo-name>-documentation-v<YY.MM.VV>.html
```

### Detailed Workflow

#### 1. Accept the Repository URL

Accept a Git repository URL from the user (GitHub, GitLab, Bitbucket, or any public Git remote).

#### 2. Clone the Repository

```bash
git clone --depth 1 <repo-url> /tmp/<repo-name>
```

Use `--depth 1` for shallow clone (faster, less disk). For private repos, ensure SSH keys or tokens are configured.

#### 3. Analyze Locally

```bash
python3 <skill-dir>/scripts/analyze_repo.py /tmp/<repo-name> --output /tmp/<repo-name>-analysis.json
```

**Output JSON contains:**
- Repository name and total file count
- File/folder tree (depth-limited to 4 levels)
- Detected languages and file counts
- Config file contents (package.json, requirements.txt, Dockerfile, etc.)
- README content
- **Key source file contents** (entry points, main files, routes, models — up to 30 files, scored by importance)

#### 4. Generate the Architecture Diagram (Optional)

After reading the analysis JSON and understanding the codebase, create a JSON spec describing the architecture:

```json
{
  "title": "System Architecture",
  "boxes": [
    {"id": "unique_id", "label": "Component Name\n(details)", "x": 0.5, "y": 0.85, "w": 0.4, "h": 0.1, "color": "#4E79A7"}
  ],
  "arrows": [
    {"from": "source_id", "to": "target_id", "label": "optional description"}
  ]
}
```

Save the spec and run:
```bash
python3 <skill-dir>/scripts/generate_arch_diagram.py <spec.json> /tmp/<repo-name>-arch.png
```

**Diagram color palette:**
- `#4E79A7` (blue) — input/data layers
- `#59A14F` (green) — processing/logic
- `#F28E2B` (orange) — output/results
- `#E15759` (red) — external/critical
- `#76B7B2` (teal) — utilities/helpers
- `#EDC948` (yellow) — storage/data

**Design guidelines:** 3–6 boxes ideal, up to 10 for complex projects. Top-to-bottom or left-to-right flow.

#### 5. Generate the HTML Report

```bash
python3 <skill-dir>/scripts/generate_report.py \
    --analysis /tmp/<repo-name>-analysis.json \
    --arch /tmp/<repo-name>-arch.png \
    --repo-url <original-repo-url> \
    --output <workspace>/reports/<repo-name>-documentation-v<YY.MM.VV>.html
```

**The report script automatically produces these sections:**
1. **Abstract** — project description, scope, key stats table, languages, README content
2. **Introduction** — generic intro: purpose of the document, intended audience, what's covered
3. **System Architecture** — base64-embedded PNG diagram (if `--arch` provided)
4. **Technology Stack** — language breakdown table + detected framework
5. **Project Structure** — ASCII file tree
6. **Implementation Details** — file summary table + code snippets for top 10 files
7. **API / Interface Reference** — exported functions per file
8. **Configuration & Setup** — config file contents + install instructions
9. **Code Quality & Patterns** — file categories + detected design patterns
10. **Challenges & Limitations** — analysis scope notes
11. **Future Enhancements** — suggested improvements
12. **Conclusion** — summary + next steps
13. **References** — repo links

**MuSigma template styling only — pure text, no code, no charts:**
- Bootstrap 3.3.5 + jQuery (for TOC)
- Auto-numbered CSS counter headings (never hardcoded)
- Fixed sidebar TOC with collapsible subheaders
- No alert boxes — plain `<p><strong>` callouts
- Self-contained HTML (inline CSS, CDN JS only)
- **NO code blocks** — everything presented as readable text, tables, and bullet lists
- **NO Plotly charts/graphs** — tables only for data
- Architecture diagram is the only visual (base64 PNG)
- Source files described with text summaries (extracted from docstrings/comments), not raw code

#### 6. Deliver

- **Filename:** `<repo-name>-documentation-v<YY.MM.VV>.html`
- **Save to:** `<workspace>/reports/`
- **Version format:** `YY.MM.VV` (e.g., `26.03.01`). Check `reports/` for existing versions and increment.
- Copy to `~/Desktop/` for easy access

**Channel-aware delivery (MANDATORY):**

| Channel | Delivery Method |
|---------|----------------|
| **webchat** | Present in browser / share file path |
| **WhatsApp** | Zip the HTML file → send via `message` tool with `media` pointing to the `.zip` file. Caption = report name + version. **All WhatsApp files MUST be zipped.** |
| **Telegram** | Send the HTML file directly via `message` tool with `media` pointing to the `.html` file |
| **Discord** | Send the HTML file directly via `message` tool with `media` pointing to the `.html` file |
| **Other** | Default to file path + summary in chat |

**WhatsApp delivery example:**
```bash
# 1. Zip the report
cd <workspace>/reports && zip <repo-name>-documentation-v<YY.MM.VV>.zip <repo-name>-documentation-v<YY.MM.VV>.html

# 2. Send via message tool
message(action=send, media="<workspace>/reports/<repo-name>-documentation-v<YY.MM.VV>.zip", caption="📄 <repo-name> Documentation v<YY.MM.VV>")
```

**This applies to ALL generated files** (reports, documentation, exports) — not just repo docs. Always check which channel the request came from and deliver the file accordingly.

#### 7. Cleanup

```bash
rm -rf /tmp/<repo-name>
```

---

## All Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `scripts/git-push.sh` | Push code to GitHub with branch/PR management | `<folder> [flags]` | Git push + optional PR |
| `scripts/analyze_repo.py` | Analyze cloned repo filesystem | `<repo-path>` | JSON summary (stdout or `--output`) |
| `scripts/generate_arch_diagram.py` | Generate PNG architecture diagram | `<spec.json> <output.png>` | PNG image |
| `scripts/generate_report.py` | **Generate full HTML report** | `--analysis <json> [--arch <png>] [--repo-url <url>]` | HTML report (MuSigma template) |
| `scripts/analyze_repo_remote.py` | **(Alternative)** GitHub API remote analysis | `<github-url>` | JSON summary (same format) |

---

## Rules

- **Clone locally.** All code is read from the cloned filesystem — no API rate limits.
- **Output format: HTML** using MuSigma template via `generate_report.py`. Never output markdown.
- **Architecture diagram: always a PNG image**, base64-embedded in the HTML via `--arch` flag.
- **The report is generated by the script** — the agent runs the script, does NOT manually build HTML.
- **For large repos**, focus analysis on the most important modules; the analyzer auto-selects top 30 files.
- **For private repos**, ensure SSH keys or git credentials are configured.
- **Cleanup** — always remove cloned repos from `/tmp/` after report generation.

---

## Part C — Intelligent Issue Resolution Agent

This workflow transforms GitHub issue inputs into fully implemented, validated, and pushed code changes — with mandatory confirmation gates and zero guesswork.

**Triggers:** "fix issue #N", "resolve this issue", "implement this feature", "work on milestone", issue URL, or feature description referencing a repo.

---

### Step 1 — Accept Input

Accept any of the following as input:
- Issue number: `#12` or `12`
- Issue URL: `https://github.com/<owner>/<repo>/issues/12`
- Milestone name: `v1.2`
- Feature description with repo URL

---

### Step 2 — Fetch Issue Details

```bash
# Fetch issue by number
gh issue view <number> --repo <owner>/<repo> --json title,body,labels,comments,assignees,milestone,state

# List issues in a milestone
gh issue list --repo <owner>/<repo> --milestone "<milestone-name>" --json number,title,body,labels,state

# Fetch linked PRs (if any)
gh pr list --repo <owner>/<repo> --search "closes #<number>" --json number,title,state,url
```

Extract and store:
- `issue_title` — short name of the issue
- `issue_body` — full description
- `comments` — all user comments for context
- `labels` — e.g., `bug`, `enhancement`, `help wanted`
- `linked_prs` — already open PRs for this issue

---

### Step 3 — Clone & Scan Repo

```bash
git clone --depth 1 https://x-access-token:$(gh auth token)@github.com/<owner>/<repo>.git /tmp/<repo>
cd /tmp/<repo>
```

Scan for relevant files by:
```bash
# Search for files referencing issue keywords
grep -r "<keyword>" /tmp/<repo> --include="*.py" --include="*.js" --include="*.ts" -l 2>/dev/null

# List all source files for context
find /tmp/<repo> -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" \) | head -40
```

Read the most relevant files to understand existing code style, patterns, and affected modules.

---

### Step 4 — Confidence Check (MANDATORY GATE)

Before planning, self-assess confidence:

- **Confidence ≥ 80%** → Proceed to Step 5 (Confirmation)
- **Confidence < 80%** → Enter Clarification Mode (Step 4a)

#### Step 4a — Clarification Mode

Ask the user 1–3 focused questions ONLY. Examples:
- "The issue mentions X — should the fix apply to frontend, backend, or both?"
- "Expected output format: JSON response or UI message?"
- "Should this handle edge case Y (e.g., empty input)?"
- "Is this a regression fix or a new feature addition?"

Wait for user response before continuing.

---

### Step 5 — Confirmation Step (MANDATORY — NEVER SKIP)

Always respond with a structured summary BEFORE making any changes:

```
I understand the issue as:

📌 Problem: <clear one-line summary>
🎯 Expected behavior: <what should happen>
📂 Affected files:
  - <file1> — <reason>
  - <file2> — <reason>

🛠️ Planned approach:
  1. <step 1>
  2. <step 2>
  3. <step 3>

🌿 Branch: fix/issue-<number>-<short-name>
📝 Commit: fix(issue-<number>): <short description>

Do you want me to proceed?
```

**DO NOT write any code or make any changes until the user explicitly confirms.**

Accepted confirmations: "yes", "proceed", "go ahead", "do it", "confirmed", "✅"

---

### Step 6 — Execute Changes

Once confirmed:

#### 6a. Create Feature Branch
```bash
cd /tmp/<repo>
git checkout -b fix/issue-<number>-<short-name>
```

Branch naming convention:
- Bug fix: `fix/issue-<number>-<short-name>`
- Feature: `feat/issue-<number>-<short-name>`
- Refactor: `refactor/issue-<number>-<short-name>`

#### 6b. Implement Changes
- Follow existing code style (indentation, naming conventions, imports)
- Read surrounding code before editing any file
- Make minimal, targeted changes — avoid scope creep
- Never modify unrelated files
- Never delete files unless explicitly required by the issue

#### 6c. Code Style Rules
- Match indentation of the existing file (tabs vs spaces)
- Use same import style (relative vs absolute)
- Follow existing naming patterns (camelCase, snake_case, etc.)
- Add comments only where logic is non-obvious
- Do NOT reformat unrelated code

---

### Step 7 — Validation Before Push

Run available checks before committing:

```bash
# Python — syntax check
python3 -m py_compile <changed_file>.py 2>&1

# Python — lint (if flake8/pylint available)
flake8 <changed_file>.py --max-line-length=120 2>/dev/null || true
pylint <changed_file>.py 2>/dev/null || true

# JavaScript/Node — syntax check
node --check <changed_file>.js 2>/dev/null || true

# Run existing tests (if present)
pytest /tmp/<repo> -x -q 2>/dev/null || true
npm test --prefix /tmp/<repo> 2>/dev/null || true

# Check for secrets/tokens accidentally added
grep -r "password\|secret\|token\|api_key" /tmp/<repo> --include="*.py" --include="*.js" -l 2>/dev/null
```

**If validation fails:**
- Fix the issue before pushing
- If unfixable, inform user: "Validation failed on `<file>` — `<error>`. Stopping to avoid pushing broken code."

**Files to NEVER commit:**
- `.env`, `.env.*`
- `*.pem`, `*.key`, `*.p12`
- `node_modules/`, `__pycache__/`, `*.pyc`
- `dist/`, `build/` (unless explicitly required)

---

### Step 8 — Commit & Push

#### 8a. Pre-Commit Identity Check (MANDATORY)
```bash
git config user.name "mudigitalemployee-tech"
git config user.email "mudigitalemployee-tech@users.noreply.github.com"
```

#### 8b. Commit with Conventional Format
```bash
git add <only changed files — never git add -A blindly>
git status  # Review what's staged
git commit -m "fix(issue-<number>): <short description>

- <bullet: what changed in file 1>
- <bullet: what changed in file 2>

Closes #<number>"
```

Commit message format:
- `fix(issue-N): <description>` — for bug fixes
- `feat(issue-N): <description>` — for features
- `refactor(issue-N): <description>` — for refactors

#### 8c. Push Branch
```bash
git push -u origin fix/issue-<number>-<short-name>
```

#### 8d. Create Pull Request
```bash
gh pr create \
  --repo <owner>/<repo> \
  --title "fix(issue-<number>): <short description>" \
  --body "## Summary
<what was changed and why>

## Changes
- <file1>: <what changed>
- <file2>: <what changed>

## Testing
- <how to verify the fix>

Closes #<number>" \
  --base main \
  --head fix/issue-<number>-<short-name>
```

---

### Step 9 — Completion Response

After successful push, always respond with:

```
✅ Issue #<number> — Done!

📋 Summary: <one-line description of what was implemented>

📂 Files Modified:
  - <file1> — <what changed>
  - <file2> — <what changed>

📝 Commit: fix(issue-<number>): <short description>
🌿 Branch: fix/issue-<number>-<short-name>
🔗 Repo: https://github.com/<owner>/<repo>
🔀 PR: <pr-url> (if created)
```

---

### Step 10 — Safety Rules (ALWAYS ENFORCED)

| Rule | Action |
|------|--------|
| Never overwrite critical config files | Ask user before modifying `config.py`, `settings.py`, `.env.example`, `docker-compose.yml` |
| Never expose tokens/secrets | Scan staged files for secrets before every commit |
| Never push broken code | Run validation first; stop if errors found |
| Never commit unrelated files | Use `git add <specific-files>` not `git add -A` |
| Never force push | Never use `--force` unless user explicitly requests it |
| Destructive actions | Always ask: "This will delete X. Are you sure?" |
| Large refactors | Break into smaller focused commits |

---

## 🛑 MANDATORY: Deletion Approval Gate (ALL deletion requests — NO EXCEPTIONS)

**Any request involving deletion of files, branches, repos, commits, or data MUST go through an explicit approval step before executing. Never delete anything silently.**

### What counts as a deletion:
- Deleting a file or folder from a repo
- Deleting a branch (`git branch -d`, `git push origin --delete`)
- Deleting a GitHub repository (`gh repo delete`)
- Force-pushing that overwrites/removes commits (`git push --force`)
- Reverting or squashing commits that remove changes
- Running `git clean`, `git reset --hard`, or `git stash drop`
- Removing collaborators or changing repo visibility
- Any `rm`, `rmdir`, `trash` on repo files requested by the user

### Approval format (MANDATORY — use this exact structure):

```
⚠️ Deletion Confirmation Required

You've asked me to delete:
🗑️ What: <exactly what will be deleted — file name, branch name, repo, etc.>
📍 Where: <repo / path / location>
⚡ Impact: <what will be lost — is this reversible?>

This action is [reversible / IRREVERSIBLE].

Type YES to confirm, or NO to cancel.
```

### Rules:
- **Do NOT execute the deletion until the user types "YES", "yes", "confirm", or "go ahead"**
- If the user says "no", "cancel", "stop", or anything unclear → abort and say "Deletion cancelled. Let me know if you'd like to do something else."
- If the user originally said "delete X" in their request → still pause and ask — do not treat the original request as approval
- `/tmp/` cleanup after pipeline runs is **exempt** — those are internal temp files, not user data

### Examples:

| User says | Wrong | Right |
|---|---|---|
| "Delete the feature branch" | Deletes immediately | Shows approval gate first |
| "Remove that file from the repo" | Commits deletion | Shows approval gate first |
| "Delete the repo" | Runs `gh repo delete` | Shows approval gate first |
| "Force push to overwrite history" | Force pushes | Shows approval gate with irreversible warning |
| "Clean up the /tmp folder after running" | N/A — exempt | Proceeds (internal cleanup) |

---

### Step 11 — Fallback Mode

If `gh` CLI fails or is unavailable:

```
⚠️ GitHub CLI encountered an error: <error message>

Manual steps to proceed:
1. Clone: git clone https://github.com/<owner>/<repo>.git
2. Branch: git checkout -b fix/issue-<number>-<short-name>
3. Make changes to: <files>
4. Commit: git commit -m "fix(issue-<number>): <description>"
5. Push: git push origin fix/issue-<number>-<short-name>
6. Open PR at: https://github.com/<owner>/<repo>/compare/fix/issue-<number>-<short-name>

Let me know once done and I can assist with the next step.
```

Common failure reasons and fixes:
- `gh: command not found` → `brew install gh` or `apt install gh`
- `authentication required` → `gh auth login`
- `403 forbidden` → Check collaborator access or fork the repo
- `422 unprocessable` → Branch already exists; use a unique name
- `merge conflict` → Stop, show conflicting files, ask user for resolution

---

### Workflow Decision Tree

```
Input received
    │
    ├─ Issue number / URL / milestone?
    │       └─ Fetch issue details (Step 2)
    │               └─ Clone & scan repo (Step 3)
    │                       └─ Confidence ≥ 80%?
    │                               ├─ YES → Confirmation (Step 5)
    │                               └─ NO  → Ask questions (Step 4a)
    │
    └─ User confirmed?
            ├─ YES → Execute → Validate → Commit → Push → PR → Report
            └─ NO  → "Okay, let me know when you'd like to proceed."
```

---

### Interactive Behavior Guidelines

- **Tone:** Conversational but professional
- **Verbosity:** Concise — no walls of text; use bullet points
- **Confirmations:** Always structured (Step 5 format)
- **Progress updates:** Send milestone updates for long-running tasks
- **Errors:** Explain clearly + suggest fix or fallback
- **Partial success:** Report what worked and what didn't separately
- **Ambiguity:** Ask ≤3 targeted questions; never assume silently

**Examples of good vs bad behavior:**

❌ Bad: Silently start writing code after receiving an issue URL
✅ Good: Fetch issue → scan repo → present structured summary → wait for "yes"

❌ Bad: Ask 7 questions before starting
✅ Good: Ask 1–2 questions only if confidence < 80%

❌ Bad: `git add -A` and push everything
✅ Good: `git add <specific files>` → review `git status` → commit → push
