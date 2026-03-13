---
name: autotest-engineer
description: "Automatically analyze a project and perform comprehensive testing. Scans a codebase, detects language/framework, generates unit/integration/functional/edge-case tests, executes them, optionally runs SonarQube analysis, and produces a structured HTML report. Activate when a user provides a folder path, project name, or repository URL and asks to write test cases, run tests, generate tests, perform testing, or do QA on the project. Triggers on: 'test this project', 'write test cases for', 'run tests on', 'generate tests', 'perform testing', 'QA this repo', 'autotest', 'test coverage for'."
---

# AutoTest Engineer

Automated project analysis, test generation, execution, and reporting.

## Workflow

### Step 1: Locate the Project

- If user provides a **local path** → verify it exists, use directly
- If user provides a **project name** → search common locations: cwd, `~/`, `~/Music/`, `~/Desktop/`, `~/Documents/`, `~/projects/`
- If user provides a **Git URL** → clone to a temp directory first:
  ```bash
  git clone <url> /tmp/autotest-<name> && cd /tmp/autotest-<name>
  ```

### Step 2: Analyze the Project

Run the project analyzer script:

```bash
python3 <skill-dir>/scripts/analyze_project.py <project-path> --output /tmp/autotest-analysis.json
```

Read the output JSON. Key fields:
- `language` — primary language detected
- `framework` — framework (django, flask, express, spring, etc.)
- `test_framework` — recommended test framework
- `source_files` — list of files with their functions and classes
- `existing_tests` — already existing test files
- `total_functions`, `total_classes` — counts for coverage planning

### Step 3: Generate Test Cases

Using the analysis JSON, generate comprehensive tests for every identifiable component.

**Read** `references/test-patterns.md` for language-specific templates and patterns.

#### Test generation rules

1. **One test file per source module** — naming: `test_<module>.py` (Python), `<module>.test.js` (JS), `<Module>Test.java` (Java), `<module>_test.go` (Go)
2. **Test categories** — for each function/class, generate:
   - **Unit tests**: Normal input, expected output
   - **Boundary tests**: Min/max values, empty inputs, single element
   - **Edge cases**: Null/None/undefined, wrong types, unicode, very large input
   - **Error handling**: Invalid input → expected exception/error
   - **Integration tests**: Cross-module interactions (where detectable)
3. **Minimum coverage target**: At least one test per public function; 3+ tests for complex functions (>20 lines or multiple branches)
4. **Create `tests/` directory** if it doesn't exist
5. **Do not overwrite** existing test files — create new ones alongside or in a `tests/generated/` subdirectory
6. **Import paths** must match the project's actual module structure
7. **Use fixtures/setup** for shared test state (conftest.py, beforeAll, @BeforeEach)

#### Framework selection

| Language | Default Framework | Alternatives |
|----------|------------------|-------------|
| Python | pytest | unittest |
| JavaScript | jest | mocha, vitest |
| TypeScript | jest | vitest, mocha |
| Java | junit5 | testng |
| Go | go-test | — |
| Ruby | rspec | minitest |
| C# | xunit | nunit, mstest |
| Rust | cargo-test | — |
| PHP | phpunit | — |

Override if existing tests already use a specific framework (check `existing_tests` and config files).

### Step 4: Install Dependencies (if needed)

Before running tests, ensure test framework is installed:

```bash
# Python
pip install pytest 2>/dev/null

# JavaScript
npm install --save-dev jest 2>/dev/null || yarn add --dev jest 2>/dev/null

# Go — built-in, no install needed

# Java — handled by Maven/Gradle
```

### Step 5: Execute Tests

Run the test runner script:

```bash
python3 <skill-dir>/scripts/run_tests.py <project-path> \
  --framework <test-framework> \
  --test-dir tests \
  --output /tmp/autotest-results.json
```

Read the results JSON. If tests fail due to import errors or missing dependencies, fix the generated test files and re-run.

### Step 6: SonarQube Analysis (Optional)

Check if SonarQube is available. Read `references/sonarqube-guide.md` for details.

```bash
which sonar-scanner 2>/dev/null && echo "AVAILABLE" || echo "SKIP"
```

- If available → run analysis and fetch metrics to `/tmp/autotest-sonar.json`
- If unavailable → skip, note in report

### Step 7: Generate Report

```bash
python3 <skill-dir>/scripts/generate_report.py \
  --analysis /tmp/autotest-analysis.json \
  --results /tmp/autotest-results.json \
  --sonar /tmp/autotest-sonar.json \
  --output <project-path>/autotest-report.html
```

Omit `--sonar` if SonarQube was skipped.

### Step 8: Present Results

Summarize to the user:
- Project: name, language, framework
- Tests generated: count by category
- Results: passed / failed / skipped / errors
- Pass rate percentage
- Key failures (if any) with brief explanation
- SonarQube highlights (if run)
- Report file location

## Error Handling

- **Clone fails** → check URL, ask user for credentials/access
- **No source files found** → project may be empty or use unsupported language; inform user
- **Test execution fails entirely** → check dependency installation; try running one test file manually to diagnose
- **Import errors in generated tests** → fix import paths based on project structure and re-run
- **SonarQube unavailable** → skip gracefully, generate report without it

## Output Files

All generated files go inside the project directory:
- `tests/` or `tests/generated/` — generated test files
- `autotest-report.html` — full HTML report with charts
- Temp files in `/tmp/autotest-*.json` — intermediate analysis (can be cleaned up)
