#!/usr/bin/env python3
"""
Generate an HTML documentation report for a Git repository using the MuSigma template.

Usage:
    python3 generate_report.py --analysis <analysis.json> [--arch <architecture.png>] [--output <report.html>]

All content is presented as readable text, tables, and bullet lists.
NO code blocks, NO raw source code, NO Plotly charts.
Architecture diagram is the only visual (base64-embedded PNG).
"""

import argparse
import base64
import html as html_lib
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from collections import Counter


def esc(text: str) -> str:
    return html_lib.escape(str(text))


def flatten_tree(tree: list, parent: str = "") -> list:
    """Flatten tree into list of (path, is_dir, size) tuples."""
    items = []
    for node in tree:
        name = node.get("name", "").rstrip("/")
        children = node.get("children", [])
        full = f"{parent}/{name}" if parent else name
        if children:
            items.append((full, True, 0))
            items.extend(flatten_tree(children, full))
        else:
            items.append((full, False, node.get("size", 0)))
    return items


def detect_framework(configs: dict) -> str:
    pkg = configs.get("package.json", "")
    if "next" in pkg: return "Next.js"
    if "react" in pkg: return "React"
    if "vue" in pkg: return "Vue.js"
    if "angular" in pkg: return "Angular"
    if "express" in pkg: return "Express.js"
    reqs = configs.get("requirements.txt", "").lower()
    if "django" in reqs: return "Django"
    if "flask" in reqs: return "Flask"
    if "fastapi" in reqs: return "FastAPI"
    pom = configs.get("pom.xml", "").lower()
    if "spring" in pom: return "Spring Boot"
    gradle = configs.get("build.gradle", "").lower()
    if "spring" in gradle: return "Spring Boot"
    return ""


def classify_file(rel_path: str) -> tuple:
    name = Path(rel_path).stem.lower()
    if re.search(r"(test|spec)", name, re.I): return "Testing", "Test file"
    if name in ("main", "app", "index", "server", "manage"): return "Entry Point", "Application entry point"
    if re.search(r"(route|url|endpoint|api)", name, re.I): return "Routing", "Route/API definitions"
    if re.search(r"(model|schema|entity)", name, re.I): return "Data Model", "Data model/schema"
    if re.search(r"(view|template|page|component)", name, re.I): return "Presentation", "UI/View layer"
    if re.search(r"(controller|handler|service)", name, re.I): return "Business Logic", "Controller/Service"
    if re.search(r"(config|settings|env)", name, re.I): return "Configuration", "Configuration file"
    if re.search(r"(util|helper|common|shared)", name, re.I): return "Utility", "Helper/Utility"
    if re.search(r"(db|database|connect|migration)", name, re.I): return "Database", "Database layer"
    if re.search(r"(auth|login|signup|session|token)", name, re.I): return "Authentication", "Auth module"
    if re.search(r"(middleware|interceptor|filter)", name, re.I): return "Middleware", "Middleware/Filter"
    return "Source", "Source file"


def extract_symbols(content: str, ext: str) -> tuple:
    classes, functions = [], []
    if ext in (".py",):
        classes = re.findall(r"^\s*class\s+(\w+)", content, re.M)
        functions = re.findall(r"^\s*(?:async\s+)?def\s+(\w+)", content, re.M)
    elif ext in (".java", ".kt"):
        classes = re.findall(r"(?:public|private|protected)?\s*(?:abstract|final)?\s*class\s+(\w+)", content)
        functions = re.findall(r"(?:public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+)?\s*\{", content)
    elif ext in (".js", ".ts", ".jsx", ".tsx"):
        classes = re.findall(r"(?:export\s+)?class\s+(\w+)", content)
        functions = re.findall(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", content)
        functions += re.findall(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(?", content)
    elif ext in (".go",):
        classes = re.findall(r"^type\s+(\w+)\s+struct\s*\{", content, re.M)
        functions = re.findall(r"^func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(", content, re.M)
    elif ext in (".r", ".R"):
        functions = re.findall(r"^(\w+)\s*<-\s*function\s*\(", content, re.M)
        functions += re.findall(r"^(\w+)\s*=\s*function\s*\(", content, re.M)
    elif ext in (".rb",):
        classes = re.findall(r"^\s*class\s+(\w+)", content, re.M)
        functions = re.findall(r"^\s*def\s+(\w+)", content, re.M)
    elif ext in (".rs",):
        classes = re.findall(r"^\s*(?:pub\s+)?struct\s+(\w+)", content, re.M)
        functions = re.findall(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+(\w+)", content, re.M)
    elif ext in (".php",):
        classes = re.findall(r"^\s*class\s+(\w+)", content, re.M)
        functions = re.findall(r"^\s*(?:public|private|protected|static|\s)*function\s+(\w+)", content, re.M)
    elif ext in (".cs",):
        classes = re.findall(r"(?:public|private|internal)?\s*(?:static|abstract|sealed)?\s*class\s+(\w+)", content)
        functions = re.findall(r"(?:public|private|protected|internal|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{", content)
    return classes, functions


def summarize_file(content: str, rel_path: str) -> str:
    """Extract a short text description from a source file (docstrings, comments, @description)."""
    lines = content.split("\n")
    desc_lines = []

    # Try R roxygen @description or @title
    for line in lines[:80]:
        m = re.match(r"^#'\s*@(?:title|description)\s+(.*)", line)
        if m:
            desc_lines.append(m.group(1).strip())
        elif re.match(r"^#'\s*@", line) and desc_lines:
            break
        elif re.match(r"^#'\s+(.+)", line) and desc_lines:
            desc_lines.append(re.match(r"^#'\s+(.*)", line).group(1).strip())

    if desc_lines:
        return " ".join(desc_lines)[:500]

    # Try Python/JS docstring
    for i, line in enumerate(lines[:30]):
        if '"""' in line or "'''" in line or "/**" in line:
            for j in range(i, min(i + 15, len(lines))):
                txt = lines[j].strip().strip("\"'/*# ")
                if txt and not txt.startswith("@") and len(txt) > 10:
                    desc_lines.append(txt)
            if desc_lines:
                return " ".join(desc_lines)[:500]

    # Try leading comments
    for line in lines[:20]:
        stripped = line.strip()
        if stripped.startswith(("#", "//", "*", "/*")):
            txt = stripped.lstrip("#/*/ ").strip()
            if len(txt) > 10:
                desc_lines.append(txt)
        elif stripped and not stripped.startswith(("import", "from", "package", "require", "use")):
            break

    if desc_lines:
        return " ".join(desc_lines)[:500]

    return "Source file in the project."


def format_size(size: int) -> str:
    if size > 1024 * 1024:
        return f"{size / 1024 / 1024:.1f} MB"
    elif size > 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size} bytes"


# ──────────────────────────────── CSS & TOC Script ────────────────────────────────

CSS = '''
body {
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 14px; line-height: 1.42857; color: #333; background: #fff;
}
div.container-fluid.main-container { max-width: 1200px; margin: auto; }
#TOC {
  position: fixed; top: 0; width: 20%; max-width: 260px; max-height: 85%;
  border: 1px solid #ccc; border-radius: 6px; overflow: auto;
  margin: 25px 0 20px 0; padding: 0; background: #fff; z-index: 1000;
}
#TOC ul { list-style: none; margin: 0; padding: 0; border: none; }
#TOC .tocify-subheader { display: none; }
#TOC .list-group-item {
  display: block; padding: 4px 15px; line-height: 30px; border: 0;
  border-radius: 0; background-color: inherit; color: #000;
  cursor: pointer; font-size: 14px; text-decoration: none;
}
#TOC .tocify-subheader .list-group-item { padding-left: 25px; font-size: 12.6px; }
#TOC .list-group-item:hover { background-color: #f5f5f5; }
#TOC .list-group-item.active, #TOC .list-group-item.active:hover {
  color: #fff; background-color: #337ab7; border-color: #337ab7;
}
.toc-content { padding-left: 30px; padding-right: 40px; counter-reset: h2counter; }
.toc-content h2 {
  font-size: 30px; font-weight: 400; color: #333; margin-top: 30px;
  counter-increment: h2counter; counter-reset: h3counter;
}
.toc-content h2::before { content: counter(h2counter) ". "; font-weight: 500; }
.toc-content h3 {
  font-size: 24px; font-weight: 400; color: #333; margin-top: 22px;
  counter-increment: h3counter;
}
.toc-content h3::before { content: counter(h2counter) "." counter(h3counter) " "; font-weight: 500; }
.section.level2 { margin-top: 20px; }
.section.level3 { margin-top: 14px; }
table { margin: 14px auto; border-collapse: collapse; border: none; font-size: 12px; color: #000; }
thead { border-bottom: 1px solid #000; vertical-align: bottom; }
tr, th, td { text-align: right; vertical-align: middle; padding: 0.5em 0.8em; border: none; }
th { font-weight: bold; }
td:first-child, th:first-child { text-align: left; }
tbody tr:nth-child(odd) { background: #f5f5f5; }
tbody tr:hover { background: rgba(66,165,245,0.15); }
.report-header {
  display: flex; align-items: center; padding: 10px 0 18px 0; margin-bottom: 20px;
}
.report-header .logo { flex: 0 0 120px; }
.report-header .logo img { height: 90px; }
.report-header .title-block { flex: 1; text-align: center; }
.report-header .title-block .title-text { font-size: 32px; font-weight: 500; color: #800000; }
.report-header .title-block .author-date { font-size: 18px; color: #666; margin-top: 4px; }
.report-header .spacer { flex: 0 0 120px; }
.badge-tag {
  display: inline-block; padding: 3px 10px; border-radius: 12px;
  font-size: 11px; font-weight: 600; margin: 2px 3px;
}
.badge-blue { background: #e3f2fd; color: #1565c0; }
.badge-green { background: #e8f5e9; color: #2e7d32; }
.badge-orange { background: #fff3e0; color: #e65100; }
.badge-red { background: #ffebee; color: #c62828; }
.badge-gray { background: #f5f5f5; color: #616161; }
.arch-diagram {
  text-align: center; margin: 20px 0; padding: 15px;
  background: #fafafa; border: 1px solid #e0e0e0; border-radius: 6px;
}
.arch-diagram img { max-width: 100%; height: auto; }
@media print {
  #TOC { display: none; }
  .col-sm-8 { width: 100%; }
  .toc-content { padding-left: 0; padding-right: 0; }
}
'''

TOC_SCRIPT = '''
$(document).ready(function() {
  var $toc = $('#TOC'), $content = $('.toc-content'), headers = [], hic = 0;
  $content.find('h2, h3').each(function() {
    var $h = $(this), level = this.tagName === 'H2' ? 2 : 3;
    var id = $h.attr('id');
    if (!id) { var $p = $h.closest('.section[id]'); if ($p.length) id = $p.attr('id'); }
    if (!id) { id = 'section-' + hic; $h.attr('id', id); }
    hic++;
    headers.push({ text: $h.text().trim(), id: id, level: level, el: $h });
  });
  if (!headers.length) return;
  var h2n = 0, h3n = 0, html = '', inH = false, inS = false, hIdx = 0;
  for (var i = 0; i < headers.length; i++) {
    var h = headers[i], label = '';
    if (h.level === 2) {
      h2n++; h3n = 0; label = h2n + '. ' + h.text;
      if (inS) { html += '</ul>'; inS = false; }
      if (inH) { html += '</ul>'; inH = false; }
      html += '<ul id="tocify-header' + hIdx + '" class="tocify-header list-group">';
      html += '<li class="tocify-item list-group-item" data-unique="' + h.id + '">' + label + '</li>';
      inH = true; hIdx++;
    } else if (h.level === 3) {
      h3n++; label = h2n + '.' + h3n + ' ' + h.text;
      if (!inS) { html += '<ul class="tocify-subheader list-group" data-tag="3">'; inS = true; }
      html += '<li class="tocify-item list-group-item" data-unique="' + h.id + '">' + label + '</li>';
    }
  }
  if (inS) html += '</ul>';
  if (inH) html += '</ul>';
  $toc.html(html);
  $toc.find('.list-group-item').first().addClass('active');
  function showSub() {
    var $a = $toc.find('.list-group-item.active');
    var $pu = $a.closest('.tocify-header');
    var $ts = $pu.length ? $pu.find('.tocify-subheader') : $a.closest('.tocify-subheader');
    $toc.find('.tocify-subheader').not($ts).slideUp(150);
    if ($ts && $ts.length && $ts.is(':hidden')) $ts.slideDown(250);
  }
  showSub();
  var scrolling = false;
  $toc.on('click', '.list-group-item', function(e) {
    e.preventDefault();
    var tid = $(this).data('unique'), $t = $('[id="' + tid + '"]').first();
    if ($t.length) {
      scrolling = true;
      $toc.find('.list-group-item').removeClass('active');
      $(this).addClass('active'); showSub();
      $('html, body').stop().animate({ scrollTop: $t.offset().top - 60 }, 400, function() {
        setTimeout(function() { scrolling = false; }, 100);
      });
    }
  });
  var st;
  $(window).on('scroll', function() {
    clearTimeout(st);
    st = setTimeout(function() {
      if (scrolling) return;
      var top = $(window).scrollTop() + 80, active = null;
      for (var j = headers.length - 1; j >= 0; j--) {
        var $el = headers[j].el, $s = $el.closest('.section[id]');
        if (($s.length ? $s : $el).offset().top <= top) { active = headers[j]; break; }
      }
      if (active) {
        var $items = $toc.find('.list-group-item');
        $items.removeClass('active');
        $items.filter('[data-unique="' + active.id + '"]').addClass('active');
        showSub();
      }
    }, 50);
  });
});
'''


# ──────────────────────────────── Report Builder ────────────────────────────────

def build_report(analysis: dict, arch_b64: str = "", repo_url: str = "") -> str:

    repo_name = analysis.get("repo_name", "Unknown Repository")
    total_files = analysis.get("total_files", 0)
    languages = analysis.get("languages", {})
    configs = analysis.get("config_files", {})
    readmes = analysis.get("readmes", {})
    source_files = analysis.get("source_files", {})
    tree = analysis.get("tree", [])
    stars = analysis.get("stars", "")
    forks = analysis.get("forks", "")
    topics = analysis.get("topics", [])
    description = analysis.get("description", "")
    license_name = analysis.get("license", "")
    default_branch = analysis.get("default_branch", "")

    today = date.today()
    version = f"{today.strftime('%y.%m')}.01"
    date_str = today.strftime("%B %d, %Y")

    primary_lang = list(languages.keys())[0] if languages else "Unknown"
    framework = detect_framework(configs)

    # Parse source files
    file_analysis = []
    for rel_path, content in source_files.items():
        if content == "<read error>":
            continue
        ext = Path(rel_path).suffix.lower()
        category, desc = classify_file(rel_path)
        classes, functions = extract_symbols(content, ext)
        line_count = content.count("\n") + 1
        summary = summarize_file(content, rel_path)
        file_analysis.append((rel_path, category, desc, classes, functions, line_count, summary))

    total_classes = sum(len(fa[3]) for fa in file_analysis)
    total_functions = sum(len(fa[4]) for fa in file_analysis)
    total_lines = sum(fa[5] for fa in file_analysis)

    # README — extract as text description, not code block
    readme_text = ""
    for _, v in readmes.items():
        # Strip markdown/HTML tags for cleaner text presentation
        text = re.sub(r'<[^>]+>', '', v)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # [text](url) → text
        text = re.sub(r'#{1,6}\s*', '', text)  # remove # headings
        text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # bold/italic
        text = re.sub(r'\n{3,}', '\n\n', text)
        readme_text = text.strip()[:4000]
        break

    # ── Language badges
    badge_colors = ["badge-blue", "badge-green", "badge-orange", "badge-red", "badge-gray"]
    lang_badges = " ".join(
        f'<span class="badge-tag {badge_colors[i % len(badge_colors)]}">{esc(lang)} ({count})</span>'
        for i, (lang, count) in enumerate(languages.items())
    )

    topic_badges = " ".join(
        f'<span class="badge-tag badge-blue">{esc(t)}</span>' for t in topics
    ) if topics else ""

    # ── Stats table
    stats = [
        ("Total Files", total_files),
        ("Languages", len(languages)),
        ("Source Files Analyzed", len(source_files)),
        ("Classes / Types", total_classes),
        ("Functions", total_functions),
        ("Lines of Code", f"{total_lines:,}"),
    ]
    if stars != "": stats.insert(0, ("Stars", stars))
    if forks != "": stats.insert(1, ("Forks", forks))
    stats_rows = "".join(f"<tr><td><strong>{esc(k)}</strong></td><td>{esc(str(v))}</td></tr>" for k, v in stats)

    # ── File summary table (text descriptions, no code)
    source_rows = ""
    for rp, cat, _, cls, fns, lc, summary in sorted(file_analysis, key=lambda x: x[0]):
        source_rows += f"<tr><td>{esc(rp)}</td><td>{esc(cat)}</td><td>{lc}</td><td>{len(cls)}</td><td>{len(fns)}</td></tr>\n"

    # ── Implementation detail subsections (text descriptions, no code)
    impl_sections = ""
    for idx, (rp, cat, _, cls, fns, lc, summary) in enumerate(file_analysis):
        cls_text = ", ".join(cls) if cls else "None"
        fn_text = ", ".join(fns[:20]) if fns else "None"
        if len(fns) > 20:
            fn_text += f" (and {len(fns) - 20} more)"

        impl_sections += f'''
<div id="impl-{idx}" class="section level3">
<h3>{esc(Path(rp).name)}</h3>
<p><strong>Path:</strong> {esc(rp)} &nbsp;|&nbsp; <strong>Category:</strong> {esc(cat)} &nbsp;|&nbsp; <strong>Lines:</strong> {lc}</p>
<p><strong>Description:</strong> {esc(summary)}</p>
{f'<p><strong>Classes / Types Defined:</strong> {esc(cls_text)}</p>' if cls else ''}
<p><strong>Functions Defined:</strong> {esc(fn_text)}</p>
</div>'''

    # ── Project structure as table (not code tree)
    flat_files = flatten_tree(tree)
    # Group by top-level directory
    dir_groups = {}
    root_files = []
    for path, is_dir, size in flat_files:
        parts = path.split("/")
        if len(parts) == 1 and not is_dir:
            root_files.append((path, size))
        elif len(parts) >= 1:
            top_dir = parts[0]
            if top_dir not in dir_groups:
                dir_groups[top_dir] = {"dirs": 0, "files": 0, "total_size": 0}
            if is_dir:
                dir_groups[top_dir]["dirs"] += 1
            else:
                dir_groups[top_dir]["files"] += 1
                dir_groups[top_dir]["total_size"] += size

    structure_rows = ""
    for dname, info in sorted(dir_groups.items()):
        structure_rows += f"<tr><td><strong>{esc(dname)}/</strong></td><td>Directory</td><td>{info['files']} files, {info['dirs']} subdirectories</td><td>{format_size(info['total_size'])}</td></tr>\n"
    for fname, fsize in root_files:
        structure_rows += f"<tr><td>{esc(fname)}</td><td>File</td><td>—</td><td>{format_size(fsize)}</td></tr>\n"

    # ── API / Interface table
    api_rows = ""
    for rp, cat, _, cls, fns, lc, _ in file_analysis:
        if fns:
            fn_text = ", ".join(fns[:15])
            if len(fns) > 15:
                fn_text += f" (+{len(fns)-15} more)"
            api_rows += f"<tr><td>{esc(rp)}</td><td>{esc(fn_text)}</td></tr>\n"

    # ── Config files as text description (no raw content)
    config_descriptions = ""
    for cname, ccontent in configs.items():
        # Extract key info from config
        desc = f"Configuration file ({format_size(len(ccontent))})"
        if cname == "package.json":
            try:
                pkg = json.loads(ccontent)
                pname = pkg.get("name", "")
                pver = pkg.get("version", "")
                deps = len(pkg.get("dependencies", {}))
                devdeps = len(pkg.get("devDependencies", {}))
                desc = f"Node.js package configuration"
                if pname: desc += f" — name: {pname}"
                if pver: desc += f", version: {pver}"
                desc += f". {deps} dependencies, {devdeps} dev dependencies."
            except: pass
        elif cname == "requirements.txt":
            count = len([l for l in ccontent.strip().split("\n") if l.strip() and not l.startswith("#")])
            desc = f"Python dependencies — {count} packages listed."
        elif cname == "Dockerfile":
            desc = "Docker container configuration for building and deploying the application."
        elif cname in ("pom.xml", "build.gradle"):
            desc = f"Build configuration file for the project."
        elif cname in ("Makefile",):
            desc = "Build automation via Make."
        config_descriptions += f"<tr><td><strong>{esc(cname)}</strong></td><td>{esc(desc)}</td></tr>\n"

    # ── Code quality
    cat_counts = Counter(fa[1] for fa in file_analysis)
    cat_rows = "".join(f"<tr><td>{esc(c)}</td><td>{n}</td></tr>" for c, n in cat_counts.most_common())

    patterns = []
    all_content = " ".join(fa[6] for fa in file_analysis)  # summaries
    # Check from raw source for patterns
    raw_sample = " ".join(source_files.get(fa[0], "")[:500] for fa in file_analysis[:15])
    if re.search(r"(class\s+\w+Controller|@Controller|@RestController)", raw_sample): patterns.append("MVC / Controller Pattern")
    if re.search(r"(Singleton|getInstance)", raw_sample): patterns.append("Singleton")
    if re.search(r"(Factory|create\w+)", raw_sample): patterns.append("Factory Pattern")
    if re.search(r"(Observer|EventEmitter|addEventListener)", raw_sample): patterns.append("Observer / Event-Driven")
    if re.search(r"(middleware|interceptor)", raw_sample, re.I): patterns.append("Middleware / Pipeline")
    if re.search(r"(async|await|Promise)", raw_sample): patterns.append("Async / Concurrent")
    if re.search(r"(test|spec|describe\(|it\(|def test_)", raw_sample, re.I): patterns.append("Test Suite Present")
    patterns_str = ", ".join(patterns) if patterns else "No specific patterns detected from analyzed files"

    # ── Architecture
    arch_html = '<p>No architecture diagram provided. Generate one using generate_arch_diagram.py and pass via --arch flag.</p>'
    if arch_b64:
        arch_html = f'''<div class="arch-diagram">
  <img src="data:image/png;base64,{arch_b64}" alt="{esc(repo_name)} Architecture"/>
  <p style="margin-top:10px;font-size:12px;color:#888"><em>System architecture diagram</em></p>
</div>'''

    repo_link = f'<p><strong>Repository:</strong> <a href="{esc(repo_url)}" target="_blank">{esc(repo_url)}</a></p>' if repo_url else ""

    # ──────────── Assemble HTML ────────────

    html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta http-equiv="X-UA-Compatible" content="IE=edge"/>
<title>{esc(repo_name)} — Project Documentation</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.5/css/bootstrap.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/1.12.4/jquery.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.11.4/jquery-ui.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.3.5/js/bootstrap.min.js"></script>
<style type="text/css">{CSS}</style>
</head>
<body>
<div class="container-fluid main-container">
<div class="row">

<div class="col-xs-12 col-sm-4 col-md-3"><div id="TOC"></div></div>

<div class="toc-content col-xs-12 col-sm-8 col-md-9">

<div class="report-header">
  <div class="logo"><img src="http://upload.wikimedia.org/wikipedia/en/0/0c/Mu_Sigma_Logo.jpg" alt="Mu Sigma"/></div>
  <div class="title-block">
    <div class="title-text">{esc(repo_name)} — Project Documentation</div>
    <div class="author-date"><b>Author(s):</b> Quant (AI Documentation Engine) &nbsp;|&nbsp; <b>Version:</b> {version} &nbsp;|&nbsp; <b>Date:</b> {date_str}</div>
  </div>
  <div class="spacer"></div>
</div>

<!-- 1. Abstract -->
<div id="abstract" class="section level2">
<h2>Abstract</h2>
{f'<p>{esc(description)}</p>' if description else ''}
<p>This document provides comprehensive technical documentation for the <strong>{esc(repo_name)}</strong> repository. It covers the project architecture, technology stack, file structure, implementation details, API reference, configuration, code quality analysis, and recommendations for future improvements. The repository contains {total_files} files written primarily in {esc(primary_lang)}, with {len(source_files)} key source files analyzed in detail comprising {total_classes} classes/types and {total_functions} functions across {total_lines:,} lines of code.</p>
{repo_link}
{f'<p><strong>Languages:</strong> {lang_badges}</p>' if lang_badges else ''}
{f'<p><strong>Topics:</strong> {topic_badges}</p>' if topic_badges else ''}
{f'<p><strong>License:</strong> {esc(license_name)}</p>' if license_name else ''}
<table>
<thead><tr><th>Metric</th><th>Value</th></tr></thead>
<tbody>{stats_rows}</tbody>
</table>
{f'<p>{esc(readme_text)}</p>' if readme_text else ''}
</div>

<!-- 2. Introduction -->
<div id="introduction" class="section level2">
<h2>Introduction</h2>
<p>This document serves as the technical reference for the <strong>{esc(repo_name)}</strong> project. It is intended for developers, contributors, and stakeholders who need to understand the codebase structure, architecture, and implementation details.</p>
<p>The documentation covers the system architecture, technology choices, project organization, a detailed walkthrough of the source code, public API surface, configuration and setup instructions, code quality observations, known limitations, and recommendations for future development.</p>
<p>All content has been auto-generated through static analysis of the repository source files and project metadata.</p>
</div>

<!-- 3. System Architecture -->
<div id="system-architecture" class="section level2">
<h2>System Architecture</h2>
{arch_html}
</div>

<!-- 4. Technology Stack -->
<div id="technology-stack" class="section level2">
<h2>Technology Stack</h2>
<table>
<thead><tr><th>Language</th><th>File Count</th></tr></thead>
<tbody>
{"".join(f'<tr><td>{esc(lang)}</td><td>{count}</td></tr>' for lang, count in languages.items())}
</tbody>
</table>
{f'<p><strong>Detected Framework:</strong> {esc(framework)}</p>' if framework else ''}
<p><strong>Primary Language:</strong> {esc(primary_lang)}</p>
</div>

<!-- 5. Project Structure -->
<div id="project-structure" class="section level2">
<h2>Project Structure</h2>
<p>The repository contains <strong>{total_files}</strong> files organized as follows:</p>
<table>
<thead><tr><th>Name</th><th>Type</th><th>Contents</th><th>Size</th></tr></thead>
<tbody>{structure_rows}</tbody>
</table>
</div>

<!-- 6. Implementation Details -->
<div id="implementation-details" class="section level2">
<h2>Implementation Details</h2>
<p>The following <strong>{len(source_files)}</strong> source files were analyzed, containing <strong>{total_classes}</strong> classes/types and <strong>{total_functions}</strong> functions across <strong>{total_lines:,}</strong> lines of code.</p>

<div id="file-summary" class="section level3">
<h3>File Summary</h3>
<table>
<thead><tr><th>File</th><th>Category</th><th>Lines</th><th>Classes</th><th>Functions</th></tr></thead>
<tbody>{source_rows}</tbody>
</table>
</div>

{impl_sections}
</div>

<!-- 7. API / Interface Reference -->
<div id="api-reference" class="section level2">
<h2>API / Interface Reference</h2>
<p>Public functions and interfaces exported from the analyzed source files:</p>
<table>
<thead><tr><th>File</th><th>Exported Functions</th></tr></thead>
<tbody>
{api_rows if api_rows else '<tr><td colspan="2">No public functions detected</td></tr>'}
</tbody>
</table>
</div>

<!-- 8. Configuration & Setup -->
<div id="configuration-setup" class="section level2">
<h2>Configuration &amp; Setup</h2>
{f"""<div id="config-files" class="section level3">
<h3>Configuration Files</h3>
<table>
<thead><tr><th>File</th><th>Description</th></tr></thead>
<tbody>{config_descriptions}</tbody>
</table>
</div>""" if config_descriptions else '<p>No standard configuration files detected in the repository root.</p>'}

<div id="installation" class="section level3">
<h3>Installation</h3>
<p>To get started with this project, clone the repository and follow the setup instructions provided in the README.</p>
<p><strong>Step 1:</strong> Clone the repository from {f'<a href="{esc(repo_url)}" target="_blank">{esc(repo_url)}</a>' if repo_url else 'the remote URL'}.</p>
<p><strong>Step 2:</strong> Install the required dependencies as specified in the project configuration files.</p>
<p><strong>Step 3:</strong> Follow any additional setup instructions in the project README.</p>
</div>
</div>

<!-- 9. Code Quality & Patterns -->
<div id="code-quality" class="section level2">
<h2>Code Quality &amp; Patterns</h2>

<div id="file-categories" class="section level3">
<h3>File Organization</h3>
<table>
<thead><tr><th>Category</th><th>File Count</th></tr></thead>
<tbody>{cat_rows}</tbody>
</table>
</div>

<div id="patterns-detected" class="section level3">
<h3>Design Patterns</h3>
<p><strong>Patterns detected:</strong> {esc(patterns_str)}</p>
</div>
</div>

<!-- 10. Challenges & Limitations -->
<div id="challenges" class="section level2">
<h2>Challenges &amp; Limitations</h2>
<p>This documentation was auto-generated from static analysis of the repository. The following limitations apply:</p>
<ul>
  <li>Up to {len(source_files)} of {total_files} files were analyzed in detail (prioritized by importance).</li>
  <li>Runtime behavior, dynamic imports, and generated code are not captured.</li>
  <li>Database schemas and external API contracts may not be fully documented.</li>
  <li>Configuration values and environment-specific settings require manual review.</li>
</ul>
</div>

<!-- 11. Future Enhancements -->
<div id="future-enhancements" class="section level2">
<h2>Future Enhancements</h2>
<p>Suggested improvements based on the codebase analysis:</p>
<ul>
  <li>Expand unit test coverage for core modules.</li>
  <li>Add CI/CD pipeline configuration for automated testing and deployment.</li>
  <li>Improve inline documentation and function-level comments.</li>
  <li>Consider adding type annotations where the language supports them.</li>
  <li>Add contribution guidelines (CONTRIBUTING.md) for open-source collaboration.</li>
</ul>
</div>

<!-- 12. Conclusion -->
<div id="conclusion" class="section level2">
<h2>Conclusion</h2>
<p>The <strong>{esc(repo_name)}</strong> repository is a {esc(primary_lang)}-based project containing {total_files} files. Analysis of {len(source_files)} key source files revealed {total_classes} classes/types and {total_functions} functions across {total_lines:,} lines of code. The project is organized into {len(dir_groups)} top-level directories with {len(languages)} programming language(s).</p>
<p><strong>Next Step:</strong> Review the Implementation Details section for an in-depth understanding of each module and its responsibilities.</p>
</div>

<!-- 13. References -->
<div id="references" class="section level2">
<h2>References</h2>
<ul>
  {f'<li><a href="{esc(repo_url)}" target="_blank">{esc(repo_url)}</a> — Source repository</li>' if repo_url else ''}
  <li>Documentation auto-generated by Quant (AI Documentation Engine) on {date_str}</li>
</ul>
</div>

</div><!-- /toc-content -->
</div><!-- /row -->
</div><!-- /main-container -->

<script>{TOC_SCRIPT}</script>
</body>
</html>'''

    return html


# ──────────────────────────────── CLI ────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate HTML documentation from repo analysis")
    parser.add_argument("--analysis", "-a", required=True, help="Analysis JSON path")
    parser.add_argument("--arch", help="Architecture diagram PNG (base64-embedded)")
    parser.add_argument("--output", "-o", help="Output HTML path (default: stdout)")
    parser.add_argument("--repo-url", help="Repository URL for links")
    args = parser.parse_args()

    with open(args.analysis, "r") as f:
        analysis = json.load(f)

    arch_b64 = ""
    if args.arch and os.path.isfile(args.arch):
        with open(args.arch, "rb") as f:
            arch_b64 = base64.b64encode(f.read()).decode("ascii")
        print(f"Architecture diagram loaded ({len(arch_b64)} bytes base64)", file=sys.stderr)

    report = build_report(analysis, arch_b64, args.repo_url or "")

    if args.output:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w") as f:
            f.write(report)
        print(f"Report saved to {args.output} ({len(report):,} bytes)", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
