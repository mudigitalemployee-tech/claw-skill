#!/usr/bin/env python3
"""
Analyze a Git repository (cloned locally) and output a JSON summary for documentation generation.

Usage:
    python3 analyze_repo.py <repo-path> [--output <file.json>]

Outputs JSON with: repo metadata, file tree, languages, config files, READMEs,
and key source file contents (up to 30 files).
"""

import json
import os
import re
import sys
from pathlib import Path
from collections import Counter

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
    ".nuxt", "target", "bin", "obj", ".idea", ".vscode", ".eggs",
    "vendor", "bower_components", ".terraform", ".gradle",
}

IGNORE_FILES = {".DS_Store", "Thumbs.db", ".gitattributes"}

CONFIG_FILES = {
    "package.json", "requirements.txt", "setup.py", "setup.cfg", "pyproject.toml",
    "Pipfile", "Cargo.toml", "go.mod", "go.sum", "pom.xml", "build.gradle",
    "Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "tsconfig.json", "webpack.config.js", "vite.config.ts",
    "vite.config.js", "next.config.js", "nuxt.config.ts", "angular.json",
    "Gemfile", "composer.json", "CMakeLists.txt", "meson.build",
}

README_FILES = {"README.md", "README.rst", "README.txt", "README"}

LANG_MAP = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript (React)",
    ".jsx": "JavaScript (React)", ".java": "Java", ".kt": "Kotlin", ".go": "Go",
    ".rs": "Rust", ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".cpp": "C++",
    ".c": "C", ".h": "C/C++ Header", ".swift": "Swift", ".scala": "Scala",
    ".r": "R", ".R": "R", ".lua": "Lua", ".sh": "Shell", ".bash": "Shell",
    ".sql": "SQL", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".vue": "Vue", ".svelte": "Svelte", ".dart": "Dart", ".ex": "Elixir",
    ".exs": "Elixir", ".zig": "Zig", ".nim": "Nim", ".jl": "Julia",
}

# Extensions considered "source code" for reading
SOURCE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".go", ".rs", ".rb",
    ".php", ".cs", ".cpp", ".c", ".h", ".swift", ".scala", ".r", ".R",
    ".lua", ".sh", ".bash", ".sql", ".vue", ".svelte", ".dart", ".ex", ".exs",
    ".zig", ".nim", ".jl",
}

# Priority filenames for source file selection
PRIORITY_NAMES = {
    "main", "app", "index", "server", "routes", "models", "views", "controllers",
    "api", "config", "settings", "schema", "database", "db", "auth", "login",
    "handler", "middleware", "utils", "helpers", "service", "manager",
}

MAX_TREE_DEPTH = 4
MAX_CONFIG_BYTES = 3000
MAX_README_BYTES = 5000
MAX_SOURCE_FILES = 30
MAX_SOURCE_FILE_BYTES = 8000


def build_tree(root: Path, depth: int = 0) -> list:
    """Build a file tree list up to MAX_TREE_DEPTH."""
    entries = []
    if depth > MAX_TREE_DEPTH:
        return entries
    try:
        items = sorted(root.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except PermissionError:
        return entries
    for item in items:
        if item.name in IGNORE_DIRS or item.name in IGNORE_FILES:
            continue
        if item.is_dir():
            children = build_tree(item, depth + 1)
            entries.append({"name": item.name + "/", "children": children})
        else:
            entries.append({"name": item.name, "size": item.stat().st_size})
    return entries


def detect_languages(root: Path) -> dict:
    """Count files by language."""
    counter = Counter()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            ext = Path(f).suffix.lower()
            lang = LANG_MAP.get(ext)
            if lang:
                counter[lang] += 1
    return dict(counter.most_common(15))


def read_config_files(root: Path) -> dict:
    """Read snippets from known config files."""
    configs = {}
    for name in CONFIG_FILES:
        p = root / name
        if p.is_file():
            try:
                text = p.read_text(errors="replace")[:MAX_CONFIG_BYTES]
                configs[name] = text
            except Exception:
                configs[name] = "<read error>"
    return configs


def read_readmes(root: Path) -> dict:
    """Read README files."""
    readmes = {}
    for name in README_FILES:
        p = root / name
        if p.is_file():
            try:
                text = p.read_text(errors="replace")[:MAX_README_BYTES]
                readmes[name] = text
            except Exception:
                pass
    return readmes


def count_files(root: Path) -> int:
    total = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        total += len(filenames)
    return total


def score_source_file(rel_path: str) -> int:
    """Score a source file for importance (higher = more important)."""
    score = 0
    name = Path(rel_path).stem.lower()
    parent = Path(rel_path).parent.name.lower()

    # Priority names
    for pn in PRIORITY_NAMES:
        if pn in name:
            score += 10
            break

    # Entry points
    if name in ("main", "app", "index", "server", "manage"):
        score += 20

    # Top-level files are more important
    depth = len(Path(rel_path).parts)
    if depth <= 2:
        score += 5
    if depth == 1:
        score += 10

    # src/ directory files are important
    if "src" in Path(rel_path).parts:
        score += 5

    # Test files are less important
    if re.search(r"(test|spec|__test__|_test)", name, re.IGNORECASE):
        score -= 15

    return score


def read_source_files(root: Path) -> dict:
    """Read key source files from the repo (up to MAX_SOURCE_FILES)."""
    candidates = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            ext = Path(f).suffix.lower()
            if ext not in SOURCE_EXTS:
                continue
            full = Path(dirpath) / f
            rel = str(full.relative_to(root))
            try:
                size = full.stat().st_size
            except OSError:
                continue
            if size > MAX_SOURCE_FILE_BYTES * 2:
                continue  # skip very large files
            candidates.append((rel, score_source_file(rel), size))

    # Sort by score descending, take top N
    candidates.sort(key=lambda x: -x[1])
    selected = candidates[:MAX_SOURCE_FILES]

    sources = {}
    for rel, _score, _size in selected:
        full = root / rel
        try:
            content = full.read_text(errors="replace")[:MAX_SOURCE_FILE_BYTES]
            sources[rel] = content
        except Exception:
            sources[rel] = "<read error>"

    return sources


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Analyze a local Git repository")
    parser.add_argument("repo_path", help="Path to cloned repository")
    parser.add_argument("--output", "-o", help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    repo = Path(args.repo_path).resolve()
    if not repo.is_dir():
        print(f"Error: {repo} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {repo.name}...", file=sys.stderr)

    summary = {
        "repo_name": repo.name,
        "total_files": count_files(repo),
        "tree": build_tree(repo),
        "languages": detect_languages(repo),
        "config_files": read_config_files(repo),
        "readmes": read_readmes(repo),
        "source_files": read_source_files(repo),
    }

    output = json.dumps(summary, indent=2, default=str)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Analysis saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
