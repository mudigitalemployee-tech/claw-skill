---
name: enterprise-arch-html
description: >
  Create professional HTML documents for ALL report types EXCEPT data science and data engineering.
  This is the DEFAULT HTML skill for: architecture diagrams, strategy comparisons, deployment option
  analysis, system architecture diagrams, technical flow diagrams, integration grids, risk comparisons,
  approval workflow diagrams, and ANY polished standalone HTML page that is not a DS/DE analytics report.
  SCOPE: Use for ANY HTML output request that is NOT explicitly a data science report, EDA report,
  ML model report, or data engineering output (those go to musigma-html-report-generator).
  Also trigger when the user mentions: architecture diagram, deployment comparison, system diagram,
  technical flow, hybrid search diagram, write path, approval workflow diagram, risk comparison,
  integration grid, or any request for a polished HTML page showing how systems fit together.
  Even if the user just says "make an HTML page showing how X works" or "create a diagram comparing
  option A vs B" — this skill applies.
  Think of this as: the go-to skill for every HTML deliverable outside the data science world.
---

# Enterprise Architecture HTML Documents

You create self-contained, presentation-quality HTML documents for enterprise architecture decisions. These are not throwaway sketches — they're polished artifacts meant to be shared with stakeholders, presented in meetings, and used as living reference documents.

## Before You Start

Read these reference files based on what the user needs:

- **Always read first:** `references/design-system.md` — the visual language (colors, typography, components, CSS patterns). Every document you create should follow this system for consistency.
- **Read based on document type:** `references/document-types.md` — detailed structure and HTML patterns for each document type (strategy comparisons, architecture diagrams, technical flows). Jump to the relevant section.

## Document Types

### 1. Strategy Comparison
**When:** The user wants to compare 2-3 deployment/implementation options and needs a recommendation.
**Output:** Single HTML file with option cards, comparison table, risk analysis, and clear recommendation.
**Think of it as:** A one-page decision brief that a VP can read in 5 minutes and know what to do.

### 2. Architecture Diagram
**When:** The user wants to show how systems are laid out — what runs where, what connects to what, where the boundaries are.
**Output:** Single HTML file with zone-based diagrams, firewall boundaries, component boxes, risk meters, and integration grids.
**Think of it as:** The technical companion to the strategy doc — shows the "how" behind the "what."

### 3. Technical Flow Diagram
**When:** The user wants to show how data, queries, or processes move through a system step by step.
**Output:** Single HTML file with horizontal step chains, split/merge flow diagrams, write path sequences, and worked examples.
**Think of it as:** An animated whiteboard explanation, frozen into a document.

## Core Principles

### Self-Contained Files
Every HTML file must work standalone. No external CSS imports, no JavaScript libraries, no image URLs that might break. Everything is inline styles or a `<style>` block in the `<head>`. This means the file can be opened in any browser, emailed as an attachment, or dropped into a shared folder and it just works.

### The Document Has a Job
Every document exists to help someone make a decision or understand a system. Before writing, be clear about what job the document does:
- Strategy docs help people **choose** between options
- Architecture docs help people **understand** how something is built
- Flow docs help people **see** how something works

This sounds obvious but it matters for structure. A strategy doc that doesn't have a clear recommendation has failed. An architecture doc that doesn't show boundaries has failed. A flow doc that doesn't have concrete examples has failed.

### Enterprise-Friendly Visual Style
These documents are designed for enterprise stakeholders — CTOs, CISOs, VPs. The visual language is professional, light-mode, and clean. Never use dark mode for the page background. The only dark element is the hero gradient section (`#1E293B` → `#0F172A`), which is used sparingly for high-impact framing messages.

Follow the design system in `references/design-system.md`. The color palette, typography scale, component patterns, and spacing are all designed to work together. Deviating for one element makes the whole document feel off.

Key rules:
- **Light background always:** Page body is `#F0F4F8`, cards are white. No dark themes.
- Use semantic colors consistently (green = recommended/good, amber = caution, red = risk/danger)
- Every diagram needs a legend
- Section headers use a colored left border (4px solid, color matches section theme)
- Cards have 12px border-radius, subtle box-shadow (`0 1px 3px rgba(0,0,0,0.08)`), 1px border `#E2E8F0`
- The dark gradient hero section is an exception — it's one contained block for emphasis, not the page style
- Font is `'Segoe UI', system-ui, -apple-system, sans-serif` — the standard enterprise font stack
- Avoid emoji overload. Use them for icon purposes in diagram nodes (one per box), not as decoration in text

### Concrete Over Abstract
Whenever you show a flow or process, include a specific example. "Query Classifier" is abstract. "E.g., 'Find the Regression Brick' → keyword | 'how to handle supply disruption' → semantic" is concrete. Every flow diagram should have an example for each path, and a "Why?" callout at the bottom explaining the design choice.

### Notes Are Arguments
The callout boxes at the bottom of sections aren't just summaries. They're where the persuasive argument lives. "Architecture note: Everything is one containerized product..." is doing real argumentative work. Write these deliberately — they're often the most-read part of a section.

## Workflow

1. **Clarify the document type** — ask what the user needs if ambiguous
2. **Read the design system** — `references/design-system.md`
3. **Read the relevant document type patterns** — `references/document-types.md`
4. **Draft the HTML** — follow the structure patterns, use the design system
5. **Validate** — check HTML structure is well-formed (no unclosed tags)
6. **Iterate** — the user will likely want to refine framing, add sections, adjust emphasis. These documents evolve through conversation.

## Common Additions the User May Request

- **Chat/Slack mockups** showing the system in use (dark background, message bubbles, artifact cards)
- **Flywheel diagrams** showing compounding value over time (circular flow with arrow stages)
- **Side-by-side comparison boxes** (Day 1 vs Day 30+, Option A vs Option B moats)
- **Phased timelines** (Month 1-2, Month 3-4, etc. as a grid)
- **CVE/security sections** with vulnerability tables
- **CISO conversation contrasts** showing how different options play out in security reviews

All of these have patterns in the design system and document type references. Read them before building.
