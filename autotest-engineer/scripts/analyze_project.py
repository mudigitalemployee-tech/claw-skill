#!/usr/bin/env python3
"""
Project Analyzer — Scans a codebase and outputs a structured JSON summary.

Usage:
    python3 scripts/analyze_project.py <project-path> [--output <file.json>]

Output JSON schema:
{
  "project_path": str,
  "language": str,           # "python" | "javascript" | "typescript" | "java" | "go" | "ruby" | "csharp" | "unknown"
  "framework": str | null,   # "django" | "flask" | "fastapi" | "express" | "nestjs" | "spring" | "react" | "vue" | "angular" | ...
  "test_framework": str,     # recommended test framework
  "package_manager": str | null,
  "source_files": [ { "path": str, "language": str, "lines": int, "functions": [str], "classes": [str] } ],
  "existing_tests": [ str ],
  "config_files": [ str ],
  "total_source_files": int,
  "total_lines": int,
  "total_functions": int,
  "total_classes": int
}
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".rs": "rust",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".scala": "scala",
    ".r": "r",
    ".R": "r",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
    ".nuxt", "target", "bin", "obj", ".gradle", ".idea", ".vscode",
    "vendor", "coverage", ".nyc_output", "htmlcov",
}

TEST_PATTERNS = re.compile(
    r"(^test_|_test\.py$|\.test\.(js|ts|jsx|tsx)$|\.spec\.(js|ts|jsx|tsx)$|Test\.java$|_test\.go$|_spec\.rb$)",
    re.IGNORECASE,
)

FRAMEWORK_INDICATORS = {
    # Python
    "requirements.txt": None,
    "setup.py": None,
    "pyproject.toml": None,
    "manage.py": "django",
    "wsgi.py": "django",
    "asgi.py": "django",
    # JS/TS
    "package.json": None,
    "next.config.js": "nextjs",
    "next.config.mjs": "nextjs",
    "next.config.ts": "nextjs",
    "nuxt.config.js": "nuxtjs",
    "nuxt.config.ts": "nuxtjs",
    "angular.json": "angular",
    "vue.config.js": "vue",
    "vite.config.ts": "vite",
    "vite.config.js": "vite",
    # Java
    "pom.xml": "maven",
    "build.gradle": "gradle",
    "build.gradle.kts": "gradle",
    # Go
    "go.mod": None,
    # Ruby
    "Gemfile": None,
    "Rakefile": None,
    # Rust
    "Cargo.toml": None,
}

TEST_FRAMEWORK_MAP = {
    "python": "pytest",
    "javascript": "jest",
    "typescript": "jest",
    "java": "junit5",
    "go": "go-test",
    "ruby": "rspec",
    "csharp": "xunit",
    "cpp": "gtest",
    "c": "unity",
    "rust": "cargo-test",
    "php": "phpunit",
    "swift": "xctest",
    "kotlin": "junit5",
    "scala": "scalatest",
    "r": "testthat",
}

# Regex patterns for function/class extraction per language
EXTRACTORS = {
    "python": {
        "function": re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE),
        "class": re.compile(r"^\s*class\s+(\w+)\s*[\(:]", re.MULTILINE),
    },
    "javascript": {
        "function": re.compile(
            r"(?:^|\s)(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?.*?\)?\s*=>|(\w+)\s*\(.*?\)\s*\{",
            re.MULTILINE,
        ),
        "class": re.compile(r"^\s*class\s+(\w+)", re.MULTILINE),
    },
    "typescript": {
        "function": re.compile(
            r"(?:^|\s)(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?.*?\)?\s*=>",
            re.MULTILINE,
        ),
        "class": re.compile(r"^\s*(?:export\s+)?class\s+(\w+)", re.MULTILINE),
    },
    "java": {
        "function": re.compile(
            r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+(?:,\s*\w+)*)?\s*\{",
            re.MULTILINE,
        ),
        "class": re.compile(r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)", re.MULTILINE),
    },
    "go": {
        "function": re.compile(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", re.MULTILINE),
        "class": re.compile(r"^type\s+(\w+)\s+struct\s*\{", re.MULTILINE),
    },
    "ruby": {
        "function": re.compile(r"^\s*def\s+(\w+)", re.MULTILINE),
        "class": re.compile(r"^\s*class\s+(\w+)", re.MULTILINE),
    },
    "csharp": {
        "function": re.compile(
            r"(?:public|private|protected|internal|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{",
            re.MULTILINE,
        ),
        "class": re.compile(r"(?:public|private|protected|internal)?\s*(?:abstract|sealed|static)?\s*class\s+(\w+)", re.MULTILINE),
    },
    "rust": {
        "function": re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)", re.MULTILINE),
        "class": re.compile(r"^\s*(?:pub\s+)?struct\s+(\w+)", re.MULTILINE),
    },
    "php": {
        "function": re.compile(r"^\s*(?:public|private|protected|static|\s)*function\s+(\w+)", re.MULTILINE),
        "class": re.compile(r"^\s*class\s+(\w+)", re.MULTILINE),
    },
}

# Share JS extractors for similar languages
EXTRACTORS["jsx"] = EXTRACTORS["javascript"]
EXTRACTORS["tsx"] = EXTRACTORS["typescript"]


def detect_framework_from_package_json(project_path: Path) -> tuple[str | None, str | None]:
    """Detect framework from package.json dependencies."""
    pkg = project_path / "package.json"
    if not pkg.exists():
        return None, None
    try:
        data = json.loads(pkg.read_text(errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None, None

    deps = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(data.get(key, {}))

    framework = None
    test_fw = None

    # Detect framework
    if "next" in deps:
        framework = "nextjs"
    elif "@angular/core" in deps:
        framework = "angular"
    elif "vue" in deps:
        framework = "vue"
    elif "react" in deps:
        framework = "react"
    elif "express" in deps:
        framework = "express"
    elif "@nestjs/core" in deps:
        framework = "nestjs"
    elif "fastify" in deps:
        framework = "fastify"
    elif "koa" in deps:
        framework = "koa"

    # Detect test framework
    if "jest" in deps:
        test_fw = "jest"
    elif "mocha" in deps:
        test_fw = "mocha"
    elif "vitest" in deps:
        test_fw = "vitest"
    elif "@playwright/test" in deps:
        test_fw = "playwright"
    elif "cypress" in deps:
        test_fw = "cypress"

    return framework, test_fw


def detect_python_framework(project_path: Path) -> tuple[str | None, str | None]:
    """Detect Python framework from config files and imports."""
    framework = None
    test_fw = None

    # Check for Django
    if (project_path / "manage.py").exists():
        framework = "django"
    else:
        # Check common files for Flask/FastAPI
        for pyfile in project_path.rglob("*.py"):
            if pyfile.stat().st_size > 500_000:
                continue
            rel = pyfile.relative_to(project_path)
            if any(part in SKIP_DIRS for part in rel.parts):
                continue
            try:
                content = pyfile.read_text(errors="replace")[:5000]
            except OSError:
                continue
            if "from fastapi" in content or "import fastapi" in content:
                framework = "fastapi"
                break
            elif "from flask" in content or "import flask" in content:
                framework = "flask"
                break
            elif "from starlette" in content:
                framework = "starlette"
                break

    # Check for pytest config
    for cfg in ("pytest.ini", "setup.cfg", "pyproject.toml", "conftest.py"):
        if (project_path / cfg).exists():
            test_fw = "pytest"
            break

    return framework, test_fw


def extract_symbols(content: str, language: str) -> tuple[list[str], list[str]]:
    """Extract function and class names from source code."""
    extractor = EXTRACTORS.get(language, {})
    functions = []
    classes = []

    fn_pat = extractor.get("function")
    cls_pat = extractor.get("class")

    if fn_pat:
        for m in fn_pat.finditer(content):
            name = next((g for g in m.groups() if g), None)
            if name and not name.startswith("_") and name not in ("if", "for", "while", "switch", "return"):
                functions.append(name)

    if cls_pat:
        for m in cls_pat.finditer(content):
            name = next((g for g in m.groups() if g), None)
            if name:
                classes.append(name)

    return functions, classes


def scan_project(project_path: Path) -> dict:
    """Scan a project and return structured analysis."""
    source_files = []
    existing_tests = []
    config_files = []
    lang_counts: dict[str, int] = {}

    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = Path(root).relative_to(project_path)

        for fname in files:
            fpath = Path(root) / fname
            rel_path = str(rel_root / fname)
            ext = fpath.suffix.lower()

            # Config files
            if fname in FRAMEWORK_INDICATORS:
                config_files.append(rel_path)
                ind = FRAMEWORK_INDICATORS[fname]
                continue

            # Source files
            lang = LANGUAGE_MAP.get(ext)
            if not lang:
                continue

            # Check if test file
            if TEST_PATTERNS.search(fname) or "/test/" in rel_path or "/tests/" in rel_path or "/__tests__/" in rel_path:
                existing_tests.append(rel_path)
                continue

            try:
                content = fpath.read_text(errors="replace")
            except OSError:
                continue

            lines = content.count("\n") + 1
            functions, classes = extract_symbols(content, lang)
            lang_counts[lang] = lang_counts.get(lang, 0) + lines

            source_files.append({
                "path": rel_path,
                "language": lang,
                "lines": lines,
                "functions": functions,
                "classes": classes,
            })

    # Determine primary language
    primary_lang = max(lang_counts, key=lang_counts.get) if lang_counts else "unknown"

    # Detect framework
    framework = None
    test_fw_override = None

    for cfg in config_files:
        fname = os.path.basename(cfg)
        ind = FRAMEWORK_INDICATORS.get(fname)
        if ind:
            framework = ind

    if primary_lang in ("javascript", "typescript"):
        fw, tf = detect_framework_from_package_json(project_path)
        if fw:
            framework = fw
        if tf:
            test_fw_override = tf
    elif primary_lang == "python":
        fw, tf = detect_python_framework(project_path)
        if fw:
            framework = fw
        if tf:
            test_fw_override = tf

    # Detect Java frameworks
    if primary_lang == "java":
        pom = project_path / "pom.xml"
        if pom.exists():
            try:
                pom_content = pom.read_text(errors="replace")
                if "spring-boot" in pom_content:
                    framework = "spring-boot"
                elif "spring" in pom_content:
                    framework = "spring"
            except OSError:
                pass

    test_framework = test_fw_override or TEST_FRAMEWORK_MAP.get(primary_lang, "unknown")

    # Package manager detection
    pkg_manager = None
    cfg_names = [os.path.basename(c) for c in config_files]
    if "package.json" in cfg_names:
        if (project_path / "yarn.lock").exists():
            pkg_manager = "yarn"
        elif (project_path / "pnpm-lock.yaml").exists():
            pkg_manager = "pnpm"
        else:
            pkg_manager = "npm"
    elif "pyproject.toml" in cfg_names or "setup.py" in cfg_names:
        if (project_path / "poetry.lock").exists():
            pkg_manager = "poetry"
        elif (project_path / "Pipfile").exists():
            pkg_manager = "pipenv"
        else:
            pkg_manager = "pip"
    elif "go.mod" in cfg_names:
        pkg_manager = "go-modules"
    elif "Gemfile" in cfg_names:
        pkg_manager = "bundler"
    elif "Cargo.toml" in cfg_names:
        pkg_manager = "cargo"
    elif "pom.xml" in cfg_names:
        pkg_manager = "maven"
    elif any("build.gradle" in c for c in cfg_names):
        pkg_manager = "gradle"

    total_functions = sum(len(f["functions"]) for f in source_files)
    total_classes = sum(len(f["classes"]) for f in source_files)
    total_lines = sum(f["lines"] for f in source_files)

    return {
        "project_path": str(project_path.resolve()),
        "language": primary_lang,
        "framework": framework,
        "test_framework": test_framework,
        "package_manager": pkg_manager,
        "source_files": source_files,
        "existing_tests": existing_tests,
        "config_files": config_files,
        "total_source_files": len(source_files),
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze a project for testing")
    parser.add_argument("project_path", help="Path to the project directory")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"Error: '{project_path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    result = scan_project(project_path)

    output = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Analysis written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
