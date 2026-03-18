# Document Type Patterns

This reference covers the three core document types the skill produces. Each has a distinct purpose and structure. Read the relevant section based on what the user is asking for.

## Table of Contents

1. [Strategy Comparison Documents](#1-strategy-comparison)
2. [Architecture Diagrams](#2-architecture-diagrams)
3. [Technical Flow Diagrams](#3-technical-flow-diagrams)

---

## 1. Strategy Comparison

**Purpose:** Help decision-makers compare 2-3 deployment/implementation options with a clear recommendation.

### Structure

```
1. Header + subtitle (frames the core question)
2. [Optional] Hero section (key differentiator or framing message)
3. Option A card
   - Label, name, tagline
   - Verdict badge (warning/caution)
   - Detailed content (architecture overview, features, tradeoffs)
   - Callout note
4. Option B card (recommended)
   - Same structure but with green "recommended" styling
   - border: 2px solid #10B981
5. Comparison table
   - Side-by-side rows for key dimensions
   - Color-coded cells (green = strong, amber = moderate, red = weak)
6. [Optional] Flywheel / compounding value section
7. Supporting sections (security, timeline, integration details)
8. Recommendation summary
9. Footer
```

### Key Patterns

**Option cards** should have:
- A colored label (`OPTION A`, `OPTION B — RECOMMENDED`)
- A clear name and italicized tagline
- A verdict badge in the header (top-right)
- Content that focuses on *what this means for the decision-maker*, not just technical specs
- A callout note at the bottom summarizing the architectural implication

**Comparison tables** work well as styled HTML tables or as grid layouts with alternating rows. Each dimension should be color-coded per option:
```html
<div style="display: grid; grid-template-columns: 200px 1fr 1fr; gap: 1px; background: #E2E8F0;">
  <!-- Header row -->
  <!-- Dimension rows with colored backgrounds per cell -->
</div>
```

**The recommendation** should be clear and justified, not wishy-washy. Strategy docs exist to help people decide. State what you recommend and why.

### Example Sections

**Hero section** (when there's a key message to lead with):
```html
<div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border-radius: 14px; padding: 32px; color: white;">
  <div style="font-size: 22px; font-weight: 700;">The Key Insight</div>
  <div style="font-size: 13px; color: #94A3B8;">Supporting context...</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px;">
    <!-- Pillar cards with semi-transparent backgrounds -->
  </div>
</div>
```

**Phased timeline:**
```html
<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;">
  <!-- Phase cards with numbered headers and milestone descriptions -->
</div>
```

---

## 2. Architecture Diagrams

**Purpose:** Show the technical layout of a system — what components exist, where they run, how they connect, and where the boundaries are.

### Structure

```
1. Header + subtitle
2. [Optional] Context/differentiator hero
3. Option A architecture card
   - Legend (color coding what each box represents)
   - Diagram (zones, boxes, connectors, firewall boundaries)
   - Architecture note (key takeaway)
   - Risk meters (4 horizontal bars rating key dimensions)
4. Option B architecture card (same structure)
5. Interaction mockup (Slack/Teams showing the system in use)
6. Flywheel / compounding diagram
7. Integration grid (how the system connects to client tools)
8. Footer
```

### Diagram Construction

Architecture diagrams use a **zone-based layout** with CSS flexbox:

```html
<div class="diagram" style="display: flex; gap: 0; min-height: 280px;">
  <!-- Main zone (the system being described) -->
  <div class="zone zone-client" style="flex: 1;">
    <div class="zone-title">ZONE TITLE</div>
    <!-- Nested boxes and connectors -->
  </div>

  <!-- Firewall boundary -->
  <div class="zone zone-firewall"><span>FIREWALL</span></div>

  <!-- External zone (what's blocked / outside) -->
  <div class="zone" style="flex: 0.3; ...">
    🚫 NO EXTERNAL CONNECTIONS
  </div>
</div>
```

**Nested containers** show system boundaries:
```html
<!-- Outer system boundary -->
<div style="background: #gradient; border: 2px solid #color; border-radius: 10px; padding: 16px;">
  <div style="font-size: 11px; font-weight: 700; letter-spacing: 1.5px;">SYSTEM NAME</div>

  <!-- Inner components as grid -->
  <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 6px;">
    <div class="zone-box success">Component 1</div>
    <div class="zone-box success">Component 2</div>
    <!-- ... -->
  </div>
</div>
```

**Risk meters** provide at-a-glance comparison across dimensions:
```html
<div class="risk-meter">
  <div class="risk-item">
    <div class="ri-label">DIMENSION NAME</div>
    <div class="ri-bar"><div class="ri-fill fill-green" style="width:90%"></div></div>
    <div class="ri-value" style="color:#059669;">Strong — explanation</div>
  </div>
  <!-- More dimensions... -->
</div>
```

Use 3-5 dimensions. Common ones: IP Protection, Data Security, Compliance/Approval, Performance, Maintainability, Moat/Lock-in.

### Integration Grids

Show how the system connects to surrounding tools:

```html
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
  <div class="int-card" style="border-top: 3px solid #3B82F6;">
    <div style="font-size: 10px; font-weight: 600; color: #3B82F6;">CATEGORY</div>
    <h4>Tool Names</h4>
    <p>What the integration does</p>
  </div>
  <!-- More cards... -->
</div>
```

---

## 3. Technical Flow Diagrams

**Purpose:** Show how data, queries, or processes move through a system step by step. Used for retrieval pipelines, search architectures, write paths, and processing sequences.

### Structure

```
1. Header + subtitle
2. [Optional] Scenario banner (concrete example to ground the flow)
3. Sequential flow (horizontal step chain)
4. Detailed flow diagrams (one per subsystem)
   - Each: input → classifier/router → parallel paths → merger → output
5. [Optional] Worked example showing the flow in action
6. Footer
```

### Horizontal Step Chains

For showing a linear sequence of 6-8 steps:

```html
<div style="display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; align-items: center;">
  <div class="rf-step">
    <div style="font-size: 20px;">📩</div>
    <div style="font-size: 10px; font-weight: 700;">Step Name</div>
    <div style="font-size: 8px; color: #94A3B8;">Description</div>
    <span class="rf-level" style="background: #DBEAFE; color: #1E40AF;">TAG</span>
  </div>
  <!-- More steps... each with ::after arrow except last -->
</div>
```

### Hybrid/Split Flow Diagrams

For showing a query that splits into multiple paths and merges:

```html
<div style="display: grid; grid-template-columns: 1fr auto 1.2fr auto 1.2fr auto 1fr; gap: 0; align-items: center;">
  <!-- Input (circular icon + label) -->
  <!-- Arrow → -->
  <!-- Classifier/Router box -->
  <!-- Arrow → -->
  <!-- Parallel paths (stacked vertically in one grid cell) -->
  <!-- Arrow → -->
  <!-- Merger/Output -->
</div>
```

**Classifier boxes** show the routing logic:
```html
<div style="background: #F0F4F8; border: 2px solid #64748B; border-radius: 10px; padding: 14px; text-align: center;">
  <div style="font-size: 12px; font-weight: 700;">🎯 Query Classifier</div>
  <div>
    <span style="background: #DBEAFE; padding: 1px 6px; border-radius: 4px; font-size: 9px;">PATH A</span>
    or
    <span style="background: #F5F3FF; padding: 1px 6px; border-radius: 4px; font-size: 9px;">PATH B</span>
  </div>
  <div style="font-size: 9px; color: #94A3B8;">Example: "exact query" → Path A | "vague query" → Path B</div>
</div>
```

**Parallel path boxes** (stacked):
```html
<div>
  <div style="background: #DBEAFE; border: 1.5px solid #3B82F6; border-radius: 10px; padding: 12px; margin-bottom: 8px;">
    <div style="font-size: 11px; font-weight: 700; color: #1E40AF;">Path A Name</div>
    <div style="font-size: 9px; color: #475569;">What this path handles</div>
    <div style="font-size: 8px; color: #3B82F6; font-weight: 600;">→ result type</div>
  </div>
  <div style="background: #F5F3FF; border: 1.5px solid #7C3AED; border-radius: 10px; padding: 12px;">
    <div style="font-size: 11px; font-weight: 700; color: #6D28D9;">Path B Name</div>
    <!-- ... -->
  </div>
</div>
```

### Write Path / Workflow Diagrams

Vertical step sequences for showing governance/approval flows:

```html
<div style="display: flex; flex-direction: column; gap: 8px;">
  <div style="background: #EFF6FF; border-radius: 8px; padding: 10px 14px;">
    <div style="font-size: 11px; font-weight: 700;">1. Step Name</div>
    <div style="font-size: 10px; color: #475569;">Description</div>
  </div>
  <div style="text-align: center; color: #CBD5E1;">↓</div>
  <!-- Highlight critical steps with colored borders -->
  <div style="background: #FEF3C7; border: 1px solid #F59E0B; border-radius: 8px; padding: 10px 14px;">
    <div style="font-size: 11px; font-weight: 700; color: #92400E;">3. Approval/Quality Gate</div>
  </div>
  <!-- ... -->
</div>
```

### "Why" Callout Boxes

Every flow diagram should end with a brief explanation of why this design was chosen:

```html
<div style="background: #F8FAFC; border-radius: 8px; padding: 12px 16px; margin-top: 16px; font-size: 11px; color: #475569; line-height: 1.6;">
  <strong>Why this approach?</strong> Concrete example showing when Path A is used vs Path B...
</div>
```

---

## General Principles

1. **Lead with the decision, not the details.** Strategy docs frame a choice. Architecture docs show the layout. Flow docs show the mechanism. Don't mix purposes — make separate documents.

2. **Use consistent color coding within a document.** If Option A is blue and Option B is green, maintain that everywhere — in legends, boxes, risk meters, and callouts.

3. **Every diagram needs a legend.** Even if the colors seem obvious, include a small legend at the top.

4. **Concrete examples ground abstract flows.** When showing a search pipeline or retrieval flow, include a specific example query for each path ("Find the Regression Brick" → keyword, "how to handle supply disruption" → semantic).

5. **Notes and callouts are persuasive tools.** The callout box at the bottom of each section isn't decoration — it's where the key insight lives. Write it deliberately.

6. **Keep documents self-contained.** Each HTML file should work standalone with no external dependencies (no CSS imports, no JS libraries, inline styles or `<style>` block only).
