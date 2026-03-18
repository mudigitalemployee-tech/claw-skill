# Design System Reference

This file defines the visual language for all enterprise architecture HTML documents. Every output should use these patterns for consistency.

## Core CSS Foundation

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: #F0F4F8;
  color: #1E293B;
  line-height: 1.5;
}
```

## Page Layout

```css
.page { max-width: 1200px; margin: 0 auto; padding: 40px 24px; }
```

For wider documents with flow diagrams, use `max-width: 1400px`.

## Color Palette

### Semantic Colors (use these for option/status coding)

| Purpose | Background | Border | Text | Fill class |
|---------|-----------|--------|------|------------|
| Recommended / Success | `#ECFDF5` / `#D1FAE5` | `#10B981` | `#065F46` | `.fill-green` → `#10B981` |
| Warning / Caution | `#FEF3C7` / `#FFF7ED` | `#F59E0B` / `#E8734A` | `#92400E` | `.fill-amber` → `#F59E0B` |
| Danger / Risk | `#FEE2E2` / `#FEF2F2` | `#EF4444` | `#991B1B` / `#DC2626` | `.fill-red` → `#EF4444` |
| Informational / Primary | `#EFF6FF` / `#DBEAFE` | `#3B82F6` | `#1E40AF` | — |
| Knowledge / Graph | `#F5F3FF` | `#7C3AED` | `#6D28D9` | — |

### Neutral Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `--slate-900` | `#0F172A` | Dark hero backgrounds |
| `--slate-800` | `#1E293B` | Headings, primary text |
| `--slate-500` | `#64748B` | Section descriptions |
| `--slate-400` | `#94A3B8` | Muted text, subtitles |
| `--slate-200` | `#E2E8F0` | Borders, dividers |
| `--slate-100` | `#F1F5F9` | Zone backgrounds |
| `--slate-50`  | `#F8FAFC` | Example backgrounds |

### Dark Hero Gradient

Used for "differentiator" or "key message" sections at the top:

```css
background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
border-radius: 14px;
padding: 32px;
color: white;
```

Cards inside dark hero use semi-transparent backgrounds:
```css
/* Blue card */  background: rgba(59,130,246,0.12); border: 1px solid rgba(59,130,246,0.3);
/* Green card */ background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3);
/* Purple card */ background: rgba(124,58,237,0.12); border: 1px solid rgba(124,58,237,0.3);
```

Text inside dark hero: headings `color: white`, body `color: #CBD5E1`, muted `color: #94A3B8`.

## Typography

| Element | Size | Weight | Color |
|---------|------|--------|-------|
| Page title (h1) | 28px | 700 | `#1E293B` |
| Section title | 20px | 700 | `#1E293B` |
| Card name | 20px | 700 | `#1E293B` |
| Hero heading | 22px | 700 | white |
| Body text | 13px | 400 | `#475569` |
| Labels/tags | 11px | 700, letter-spacing: 2px | varies |
| Small descriptions | 10-11px | 400 | `#64748B` |
| Micro text | 8-9px | 600 | `#94A3B8` |

## Component Patterns

### Section Headers

```css
.section-title {
  font-size: 20px; font-weight: 700; color: #1E293B;
  margin: 40px 0 8px;
  padding-left: 14px;
  border-left: 4px solid #3B82F6; /* color varies by section */
}
.section-desc {
  font-size: 13px; color: #64748B;
  margin: 0 0 20px 18px;
}
```

### Cards

```css
.card {
  background: white;
  border-radius: 12px;
  padding: 28px;
  margin-bottom: 32px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border: 1px solid #E2E8F0;
}
```

For recommended/highlighted cards, add `border: 2px solid #10B981;`.

### Verdict Badges

```css
.verdict-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
}
/* Positive */ background: #D1FAE5; color: #065F46;
/* Warning */  background: #FEF3C7; color: #92400E;
/* Negative */ background: #FEE2E2; color: #991B1B;
```

### Risk Meters

Horizontal bar charts for comparing dimensions across options:

```css
.risk-meter { display: flex; gap: 16px; margin: 20px 0; }
.risk-item { flex: 1; background: white; border-radius: 8px; padding: 14px; border: 1px solid #E2E8F0; }
.ri-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: #64748B; }
.ri-bar { height: 8px; border-radius: 4px; background: #E2E8F0; margin: 6px 0; overflow: hidden; }
.ri-fill { height: 100%; border-radius: 4px; }
/* Width set inline: style="width:85%" */
```

### Architecture Diagram Zones

For showing firewall boundaries and deployment zones:

```css
.zone-client { background: #F1F5F9; }
.zone-firewall {
  background: repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(239,68,68,0.03) 10px, rgba(239,68,68,0.03) 20px);
  width: 40px; min-width: 40px;
  border-left: 2px solid #EF4444;
  border-right: 2px solid #EF4444;
}
```

### Connectors / Arrows

```css
.connector { text-align: center; padding: 4px 0; color: #64748B; font-size: 11px; }
.connector .arrow { font-size: 14px; display: block; color: #94A3B8; }
.connector .label { font-size: 9px; font-weight: 600; letter-spacing: 0.5px; }
```

Use `↕` for vertical, `→` for horizontal flow. In grid layouts, use styled `<div>` arrows.

### Boxes Inside Diagrams

```css
.zone-box {
  background: white;
  border: 1.5px solid #CBD5E1;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  font-size: 12px;
}
/* Variants */
.zone-box.highlight { border-color: #3B82F6; background: #EFF6FF; }
.zone-box.success   { border-color: #10B981; background: #ECFDF5; }
.zone-box.danger    { border-color: #EF4444; background: #FEF2F2; }
.zone-box.purple    { border-color: #7C3AED; background: #F5F3FF; }
```

### Integration / Feature Grids

```css
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.grid-card {
  border: 1.5px solid #E2E8F0;
  border-radius: 8px;
  padding: 16px;
  background: white;
  border-top: 3px solid <accent-color>;
}
```

### Slack/Chat Mockups

Dark background chat interface for showing product interactions:

```css
.slack-mock { background: #1a1d21; border-radius: 10px; padding: 20px; color: #d1d2d3; font-size: 13px; }
.slack-channel { color: #e8912d; font-weight: 700; font-size: 14px; }
.slack-msg { display: flex; gap: 10px; margin-bottom: 14px; }
.slack-avatar { width: 32px; height: 32px; border-radius: 4px; }
.slack-user { font-weight: 700; color: white; font-size: 13px; }
.slack-time { font-size: 10px; color: #616061; }
.slack-artifact { background: #2c2d30; border-left: 3px solid #10B981; border-radius: 0 6px 6px 0; padding: 10px 14px; margin-top: 8px; }
```

### Flow Diagrams (Horizontal)

For showing search/retrieval/processing pipelines:

```css
/* Use CSS Grid for horizontal flows */
display: grid;
grid-template-columns: 1fr auto 1.2fr auto 1.2fr auto 1fr;
gap: 0;
align-items: center;
```

Arrow dividers between stages: `<div style="color: #CBD5E1; font-size: 18px;">→</div>`

Circular node icons:
```css
width: 56px; height: 56px; border-radius: 50%;
border: 2px solid <accent-color>;
background: <light-bg>;
display: flex; align-items: center; justify-content: center;
font-size: 22px; /* for emoji icons */
```

### Flywheel / Circular Diagrams

Use flexbox with arrow separators between stages:
```css
display: flex; gap: 0; justify-content: center; align-items: center;
/* Each stage is flex: 1 with a circular icon and label below */
/* Arrows: → between stages, ↩ to close the loop */
```

### Callout / Note Boxes

```css
/* Info note */
background: #F8FAFC; border-radius: 8px; padding: 12px 16px;
font-size: 11px; color: #475569; line-height: 1.6;

/* Contextual note (inside a themed section) */
background: #ECFDF5; /* match section color */
border-radius: 8px; padding: 14px 18px;
font-size: 12px; color: #065F46; line-height: 1.7;
```

### Side-by-Side Comparison Boxes

For Day 1 vs Day 30+, Option A vs Option B summaries:

```css
display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
/* Each side gets its own background color and border */
```

## Footer

```css
.footer {
  text-align: center; margin-top: 48px; padding-top: 20px;
  border-top: 1px solid #E2E8F0;
  color: #94A3B8; font-size: 12px;
}
```

Content: `Organization | Confidential | Month Year | Document Title`

## Responsive Notes

These documents are designed for desktop/presentation viewing (1200-1400px). They render well in browsers and can be screenshot/printed. No need for mobile breakpoints unless specifically requested.
