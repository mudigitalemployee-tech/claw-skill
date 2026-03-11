# Digital Employee Skill Repository

This repository contains a custom skill for Digital Employee.

Use this guide to:
- Clone this repository to your local machine
- Copy the cloned skill folder into your OpenClaw skills workspace

---

## List of Skills

### 1) Skill Name
`report_generatror`

### Why it is used
- Used to generate structured, interactive HTML analytics reports using the MuSigma canonical template.
- Useful for EDA summaries, business analytics reports, decision science reports, and dataset-based insights.

### Prerequisites for this skill
- OpenClaw skills directory available at `~/.openclaw/workspace/skills`
- Access to the skill files in `report_generatror/`
- Template files available:
	- `report_generatror/assets/template.html`
	- `report_generatror/references/template-guide.md`
- Data source available for report creation (CSV/Excel/JSON, etc.)

---

## Prerequisites

Before you begin, make sure you have:

- `git` installed
- Access to this repository URL
- OpenClaw installed with the skills directory available at:

```bash
~/.openclaw/workspace/skills
```

To verify Git installation:

```bash
git --version
```

---

## Step 1: Clone the repository locally

1. Open a terminal.
2. Move to any local folder where you want to keep the repository.

```bash
cd <YOUR_PREFERRED_PATH>
```

3. Clone the repository:

```bash
git clone https://gitlab.ird.mu-sigma.com/digital-employee/skill-repository/openclaw_skill.git
```

4. Enter the cloned folder:

```bash
cd openclaw_skill
```

5. Confirm files are present:

```bash
ls
```

You should see the repository files and one or more skill directories (for example, folders that contain a `SKILL.md` file).

---

## Step 2: Copy skill folder(s) into OpenClaw skills path

OpenClaw skill folders should be copied to:

```bash
~/.openclaw/workspace/skills
```

### Option A (recommended): copy one or more skill folders only

From inside your cloned repository, copy each skill folder (a skill folder usually contains `SKILL.md`) to the OpenClaw skills directory.

Example (single skill folder):

```bash
cp -r report_generatror ~/.openclaw/workspace/skills/
```

Example (single skill folder using relative path from repo root):

```bash
cp -r ./report_generatror ~/.openclaw/workspace/skills/
```

Example (multiple skill folders):

```bash
for d in */; do [ -f "$d/SKILL.md" ] && cp -r "$d" ~/.openclaw/workspace/skills/; done
```

### Option B: copy the full cloned repository (only if your setup requires it)

From the parent directory of the cloned repository:

```bash
cp -r <CLONED_REPO_FOLDER> ~/.openclaw/workspace/skills/
```

Use this option only if your OpenClaw setup expects the entire repository folder instead of individual skill folders.

---

## Step 3: Verify the copied skill

Run:

```bash
ls ~/.openclaw/workspace/skills
```

You should see:

- `report_generatror` (if you used Option A)
- or `claw-skill` (if you used Option B)

For deeper verification:

```bash
ls ~/.openclaw/workspace/skills/report_generatror
```

Expected structure includes:

- `SKILL.md`
- `assets/`
- `references/`

---

## Step 4: Update skill after future changes

If you make updates in this repository later, copy again to refresh the installed skill:

```bash
cp -r report_generatror ~/.openclaw/workspace/skills/
```

If prompted to overwrite, confirm as needed.

---

## Troubleshooting

### `No such file or directory` for OpenClaw path

Create the directory first:

```bash
mkdir -p ~/.openclaw/workspace/skills
```

Then run the copy command again.

### Permission denied

Check ownership/permissions of the OpenClaw workspace directory.

### Wrong repository URL

If clone fails, verify your repository URL and access permissions.

---

## Quick Copy Commands

Use the following commands:

```bash
git clone https://gitlab.ird.mu-sigma.com/digital-employee/skill-repository/openclaw_skill.git
cd openclaw_skill
cp -r report_generatror ~/.openclaw/workspace/skills/
ls ~/.openclaw/workspace/skills
```
