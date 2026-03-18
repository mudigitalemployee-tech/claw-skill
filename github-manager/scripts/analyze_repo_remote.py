#!/usr/bin/env python3
"""
Analyze a GitHub repository REMOTELY (no cloning) via the GitHub REST API.
Outputs the same JSON summary format as analyze_repo.py.

Usage:
    python3 analyze_repo_remote.py <github-url-or-owner/repo>

Requires: `gh` CLI authenticated, OR a GITHUB_TOKEN env var, OR falls back to unauthenticated API.
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.error
from collections import Counter
from pathlib import PurePosixPath

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

IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
    ".nuxt", "target", "bin", "obj", ".idea", ".vscode", ".eggs",
    "vendor", "bower_components", ".terraform", ".gradle",
}

CONFIG_FILES = {
    "package.json", "requirements.txt", "setup.py", "setup.cfg", "pyproject.toml",
    "Pipfile", "Cargo.toml", "go.mod", "go.sum", "pom.xml", "build.gradle",
    "Makefile", "Dockerfile", "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "tsconfig.json", "webpack.config.js", "vite.config.ts",
    "vite.config.js", "next.config.js", "nuxt.config.ts", "angular.json",
    "Gemfile", "composer.json", "CMakeLists.txt", "meson.build",
}

README_FILES = {"README.md", "README.rst", "README.txt", "README"}

MAX_CONFIG_BYTES = 3000
MAX_README_BYTES = 5000
MAX_SOURCE_FILES = 20        # max important source files to fetch content for
MAX_SOURCE_BYTES = 8000      # per source file


def parse_repo(url_or_slug):
    """Extract owner/repo from a GitHub URL or slug."""
    s = url_or_slug.strip().rstrip("/")
    if s.endswith(".git"):
        s = s[:-4]
    # Handle full URLs
    for prefix in ["https://github.com/", "http://github.com/", "git@github.com:"]:
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    parts = s.split("/")
    if len(parts) < 2:
        print(f"Error: Cannot parse owner/repo from '{url_or_slug}'", file=sys.stderr)
        sys.exit(1)
    return parts[0], parts[1]


def get_token():
    """Try to get a GitHub token from gh CLI or env."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return None


def api_get(url, token=None):
    """Make a GET request to GitHub API."""
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "repo-doc-generator")
    if token:
        req.add_header("Authorization", f"token {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Repository not found or private (404) — {url}", file=sys.stderr)
            sys.exit(1)
        raise


def api_get_raw(url, token=None, max_bytes=None, retries=2):
    """Fetch raw file content from GitHub with retry."""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/vnd.github.v3.raw")
            req.add_header("User-Agent", "repo-doc-generator")
            if token:
                req.add_header("Authorization", f"token {token}")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read(max_bytes) if max_bytes else resp.read()
                return data.decode("utf-8", errors="replace")
        except urllib.error.HTTPError:
            return None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt < retries:
                import time
                time.sleep(1 + attempt)
                continue
            print(f"Warning: Skipping {url.split('/')[-1]} after {retries+1} attempts: {e}", file=sys.stderr)
            return None


def fetch_tree(owner, repo, token):
    """Fetch the full recursive tree."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    data = api_get(url, token)
    return data.get("tree", [])


def is_ignored(path):
    """Check if any path segment is in IGNORE_DIRS."""
    parts = PurePosixPath(path).parts
    return any(p in IGNORE_DIRS for p in parts)


def build_tree_from_flat(items, max_depth=4):
    """Build a nested tree structure from flat GitHub tree API items."""
    root = {"name": "/", "children": []}

    for item in items:
        if is_ignored(item["path"]):
            continue
        parts = PurePosixPath(item["path"]).parts
        if len(parts) > max_depth:
            continue

        current = root
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            if is_last and item["type"] == "blob":
                current.setdefault("children", []).append({
                    "name": part,
                    "size": item.get("size", 0)
                })
            else:
                # Find or create directory
                existing = None
                for child in current.get("children", []):
                    if child["name"] == part + "/" or child["name"] == part:
                        existing = child
                        break
                if existing is None:
                    existing = {"name": part + "/", "children": []}
                    current.setdefault("children", []).append(existing)
                current = existing

    return root["children"]


def detect_languages(items):
    """Count files by language from flat tree items."""
    counter = Counter()
    for item in items:
        if item["type"] != "blob" or is_ignored(item["path"]):
            continue
        ext = PurePosixPath(item["path"]).suffix.lower()
        lang = LANG_MAP.get(ext)
        if lang:
            counter[lang] += 1
    return dict(counter.most_common(15))


def fetch_config_files(owner, repo, items, token):
    """Fetch content of known config files."""
    configs = {}
    config_paths = {}
    for item in items:
        if item["type"] == "blob":
            name = PurePosixPath(item["path"]).name
            # Only top-level config files (no / in path besides the filename)
            if name in CONFIG_FILES and "/" not in item["path"]:
                config_paths[name] = item["path"]

    for name, path in config_paths.items():
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        content = api_get_raw(url, token, MAX_CONFIG_BYTES)
        if content:
            configs[name] = content
    return configs


def fetch_readmes(owner, repo, items, token):
    """Fetch README files."""
    readmes = {}
    for item in items:
        if item["type"] == "blob":
            name = PurePosixPath(item["path"]).name
            if name in README_FILES and "/" not in item["path"]:
                url = f"https://api.github.com/repos/{owner}/{repo}/contents/{item['path']}"
                content = api_get_raw(url, token, MAX_README_BYTES)
                if content:
                    readmes[name] = content
    return readmes


def fetch_source_files(owner, repo, items, token):
    """Fetch key source files for deeper understanding."""
    # Prioritize: entry points, main files, index files, app files
    priority_names = {
        "main.py", "app.py", "index.js", "index.ts", "main.js", "main.ts",
        "server.py", "server.js", "server.ts", "cli.py", "cli.js",
        "index.jsx", "index.tsx", "App.jsx", "App.tsx", "App.js", "App.ts",
        "main.go", "main.rs", "lib.rs", "mod.rs",
        "views.py", "models.py", "urls.py", "routes.py", "routes.js", "routes.ts",
        "schema.py", "schema.js", "schema.ts", "schema.graphql",
        "manage.py", "wsgi.py", "asgi.py",
    }

    source_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".php", ".cs", ".cpp", ".c", ".swift", ".kt", ".scala"}

    candidates = []
    for item in items:
        if item["type"] != "blob" or is_ignored(item["path"]):
            continue
        name = PurePosixPath(item["path"]).name
        ext = PurePosixPath(item["path"]).suffix.lower()
        if ext not in source_exts:
            continue
        # Score: priority names get 0, shallow paths get 1, deep paths get 2
        depth = len(PurePosixPath(item["path"]).parts)
        if name in priority_names:
            score = 0
        elif depth <= 2:
            score = 1
        else:
            score = 2
        candidates.append((score, depth, item["path"]))

    candidates.sort()
    selected = candidates[:MAX_SOURCE_FILES]

    sources = {}
    import time
    for i, (_, _, path) in enumerate(selected):
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        content = api_get_raw(url, token, MAX_SOURCE_BYTES)
        if content:
            sources[path] = content
        # Small delay to avoid rate limit / SSL issues
        if i < len(selected) - 1:
            time.sleep(0.3)
    return sources


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_repo_remote.py <github-url-or-owner/repo>", file=sys.stderr)
        sys.exit(1)

    owner, repo = parse_repo(sys.argv[1])
    token = get_token()

    if not token:
        print("Warning: No GitHub token found. Using unauthenticated API (60 req/hr limit).", file=sys.stderr)

    # Fetch repo metadata
    repo_info = api_get(f"https://api.github.com/repos/{owner}/{repo}", token)

    # Fetch full tree
    items = fetch_tree(owner, repo, token)

    blob_count = sum(1 for i in items if i["type"] == "blob" and not is_ignored(i["path"]))

    summary = {
        "repo_name": repo,
        "repo_full_name": f"{owner}/{repo}",
        "description": repo_info.get("description", ""),
        "default_branch": repo_info.get("default_branch", "main"),
        "stars": repo_info.get("stargazers_count", 0),
        "forks": repo_info.get("forks_count", 0),
        "topics": repo_info.get("topics", []),
        "license": (repo_info.get("license") or {}).get("spdx_id", "Unknown"),
        "total_files": blob_count,
        "tree": build_tree_from_flat(items),
        "languages": detect_languages(items),
        "config_files": fetch_config_files(owner, repo, items, token),
        "readmes": fetch_readmes(owner, repo, items, token),
        "source_files": fetch_source_files(owner, repo, items, token),
    }

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
