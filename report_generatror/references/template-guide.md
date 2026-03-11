# MuSigma HTML Report Template — Quick Reference

## Template Location
- **Template:** `assets/template.html`
- **Example:** `references/example-report.html`

## Structure (non-negotiable)

```
<!DOCTYPE html>
<html>
<head>
  Bootstrap 3.3.5 CSS + jQuery 1.12.4 + jQuery UI 1.11.4 + Bootstrap JS + Plotly 2.27.0
  Inline <style> block (copy exactly from template)
</head>
<body>
  <div class="container-fluid main-container">
    <div class="row">
      <div class="col-xs-12 col-sm-4 col-md-3">  ← TOC sidebar (auto-generated)
        <div id="TOC"></div>
      </div>
      <div class="toc-content col-xs-12 col-sm-8 col-md-9">  ← Main content
        <div class="report-header">  ← MuSigma header (logo + title + author/date)
        <div class="section level2">  ← Each major section (h2) — auto-numbered 1, 2, 3…
          <div class="section level3">  ← Subsections (h3) — auto-numbered 1.1, 1.2, 2.1…
      </div>
    </div>
  </div>
  <script> Plotly charts </script>
  <script> TOC builder (copy exactly from template) </script>
</body>
</html>
```

## Chart Color Palette (mandatory)

```javascript
var P=["#4E79A7","#59A14F","#F28E2B","#E15759","#BAB0AC"];
// Primary (Blue), Secondary (Green), Highlight (Orange), Negative (Red), Neutral (Gray)
```

| Role | Color | Hex | Usage |
|------|-------|---------|-------|
| Primary | Blue | #4E79A7 | Main series, primary bars, default line color |
| Secondary | Green | #59A14F | Secondary series, positive indicators |
| Highlight | Orange | #F28E2B | Accents, highlights, callout data points |
| Negative | Red | #E15759 | Negative indicators, alerts, declines |
| Neutral | Gray | #BAB0AC | Neutral data, baselines, de-emphasized series |

Additional layout colors:
- **Background:** `#FFFFFF` (white)
- **Grid lines:** `#E5E5E5` (light gray)

Always use colors from this palette. Cycle through them for multiple series/categories.

## Header Format
```html
<div class="report-header">
  <div class="logo">
    <img src="http://upload.wikimedia.org/wikipedia/en/0/0c/Mu_Sigma_Logo.jpg" alt="Mu Sigma"/>
  </div>
  <div class="title-block">
    <div class="title-text">REPORT TITLE</div>
    <div class="author-date"><b>Author(s):</b> NAME | <b>Version:</b> YY.MM.VV | <b>Date:</b> DATE</div>
  </div>
  <div class="spacer"></div>
</div>
```

## Auto-Numbered Headings

Headings are numbered automatically via CSS counters. **Do NOT hardcode numbers in heading text.**

- `<h2>Executive Summary</h2>` renders as → **1. Executive Summary**
- `<h3>Revenue by Region</h3>` renders as → **1.1 Revenue by Region**
- `<h3>Revenue by Product</h3>` renders as → **1.2 Revenue by Product**
- `<h2>Sales Trends</h2>` renders as → **2. Sales Trends**
- `<h3>Monthly Trend</h3>` renders as → **2.1 Monthly Trend**

The TOC sidebar mirrors the same numbering automatically.

## Section Pattern
```html
<div id="unique-id" class="section level2">
  <h2>Section Title</h2>
  <p>Content...</p>
  <div id="sub-id" class="section level3">
    <h3>Subsection Title</h3>
    <div class="chart-container" id="chart-name"></div>
  </div>
</div>
```

## Chart Pattern
```javascript
var P=["#3B82F6","#6366F1","#8B5CF6","#EC4899","#F97316","#10B981"], H=370;
var L={font:{family:'"Helvetica Neue",Helvetica,Arial,sans-serif',size:11},
       paper_bgcolor:'#fff',plot_bgcolor:'#fff',margin:{t:50,b:60,l:60,r:30}};

Plotly.newPlot('chart-id', [{ /* traces */ }],
  $.extend(true,{},L,{ title:{text:'Title'}, height:H }), {responsive:true});
```

## Table Pattern
```html
<table>
<thead><tr><th>Col1</th><th>Col2</th></tr></thead>
<tbody>
<tr><td>val1</td><td>val2</td></tr>
</tbody>
</table>
```

## Callouts — NO Alert Boxes

**Do NOT use `<div class="alert ...">`.** Use plain text with bold labels instead:

```html
<p><strong>Critical Finding:</strong> Return rate of 24.8% is eroding margins significantly.</p>
<p><strong>Next Step:</strong> Schedule a deep-dive session with the product team.</p>
<p><strong>Note:</strong> Data covers Jan 2023 – Jun 2025 only.</p>
```

## Constraints
- **No alert boxes** — plain `<p><strong>` for all callouts
- **Auto-numbered headings** — CSS counters handle it; never put numbers in heading text
- **Professional palette** — always use the 6-color palette above
- **No KPI cards, no footer, no box-shadow, no border-bottom on headings or header** — clean continuous page
- **Self-contained:** All CSS inline, JS via CDN only
- **TOC auto-generates** from h2/h3 — never build TOC manually
- **Every section div needs a unique `id`**
- **Charts:** Always include value annotations via `text` + `textposition`
- **Tables:** Use `<thead>/<tbody>`, styling is automatic
