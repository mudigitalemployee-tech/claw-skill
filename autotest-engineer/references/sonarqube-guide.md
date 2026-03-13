# SonarQube Integration Guide

## Prerequisites

- SonarQube server running (local or remote)
- `sonar-scanner` CLI installed
- Project configured with `sonar-project.properties` or inline params

## Check if SonarQube is available

```bash
which sonar-scanner 2>/dev/null && echo "AVAILABLE" || echo "NOT_INSTALLED"
curl -sf http://localhost:9000/api/system/status 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','DOWN'))" || echo "SERVER_UNREACHABLE"
```

## Running Analysis

### Option 1: sonar-project.properties exists
```bash
cd <project-path>
sonar-scanner
```

### Option 2: Inline parameters
```bash
sonar-scanner \
  -Dsonar.projectKey=<project-name> \
  -Dsonar.sources=. \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=<token> \
  -Dsonar.language=<lang> \
  -Dsonar.sourceEncoding=UTF-8
```

### Language-specific extras
- **Python**: `-Dsonar.python.coverage.reportPaths=coverage.xml`
- **JS/TS**: `-Dsonar.javascript.lcov.reportPaths=coverage/lcov.info`
- **Java (Maven)**: `mvn sonar:sonar -Dsonar.host.url=http://localhost:9000`
- **Go**: `-Dsonar.go.coverage.reportPaths=coverage.out`

## Fetching Results via API

After analysis completes, wait ~10s then fetch metrics:

```bash
curl -s "http://localhost:9000/api/measures/component?component=<project-key>&metricKeys=bugs,code_smells,vulnerabilities,coverage,duplicated_lines_density,sqale_rating,reliability_rating,security_rating,sqale_debt_ratio" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
measures = {m['metric']: m.get('value','N/A') for m in data.get('component',{}).get('measures',[])}
print(json.dumps(measures, indent=2))
"
```

## When SonarQube is Unavailable

If sonar-scanner is not installed or the server is unreachable:
1. Skip the SonarQube section in the report
2. Note in the report: "SonarQube analysis skipped — scanner not installed or server unreachable"
3. Still generate all other sections normally
4. Optionally suggest: `pip install pylint flake8` or `npx eslint` as lightweight alternatives

## Interpreting Ratings

| Rating | Meaning |
|--------|---------|
| A | Best — no issues or minimal |
| B | Minor issues |
| C | Major issues present |
| D | Critical issues |
| E | Blocker issues |

## Key Metrics

- **Bugs**: Reliability issues that represent something wrong in the code
- **Code Smells**: Maintainability issues that make code confusing
- **Vulnerabilities**: Security issues that could be exploited
- **Coverage**: Percentage of code covered by tests
- **Duplications**: Percentage of duplicated lines
- **Technical Debt**: Estimated time to fix all code smells
