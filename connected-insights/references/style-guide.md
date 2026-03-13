# Light-Mode Professional Theme — Style Guide

Clean, corporate BI theme. Text-based — no charts or graphs.

## CSS Variables

```css
:root {
  --bg-primary: #f8f9fa;
  --bg-secondary: #ffffff;
  --bg-card: #ffffff;
  --bg-card-hover: #f1f3f5;
  --border: #dee2e6;
  --border-light: #e9ecef;
  --text-primary: #212529;
  --text-secondary: #495057;
  --text-muted: #868e96;
  --accent-blue: #1971c2;
  --accent-green: #2f9e44;
  --accent-red: #e03131;
  --accent-amber: #e67700;
  --accent-purple: #7048e8;
  --accent-teal: #0c8599;
  --shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06);
}
```

## Typography

- Font stack: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- Load Inter: `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap`
- Body: 14px / 1.6 line-height
- KPI big numbers: 2.2rem, font-weight 700
- Section headers: 1.1rem, font-weight 600, uppercase, letter-spacing 0.05em

## KPI Cards

White card, 1px border, 10px radius, shadow. Big number prominent, label above, context line and change indicator below.

## Impact Table

- Header: bg-primary, bold uppercase, 2px bottom border
- Alternating rows: white / #f8f9fa
- Hover: #e9ecef
- Risk badges: inline-block, 4px radius, white text on colored background (red/amber/green)

## Alert Cards

- Critical: #fff5f5 background, 4px left border var(--accent-red)
- Warning: #fff9db background, 4px left border var(--accent-amber)
- Info: #e7f5ff background, 4px left border var(--accent-blue)
- Success: #ebfbee background, 4px left border var(--accent-green)

## Insight Cards

White card with colored category tag badge at top:
- tag-trend: #e7f5ff bg, blue text
- tag-risk: #fff5f5 bg, red text
- tag-opportunity: #ebfbee bg, green text
- tag-anomaly: #fff9db bg, amber text

## Layout

- Body background: #f8f9fa
- Max-width container: 1200px, centered
- Section spacing: 40px margin-top
- Card grid: CSS Grid / Flexbox, gap 16px
- Responsive: stack on < 768px
