---
name: problem-definition
description: Generate, explain, or document business problem definitions in muAoPS-style format. ALWAYS triggers when the user says "problem definition", "give me the problem definition", "define the problem", "derive the problem definition", or shares a problem statement and asks for structured output. When a problem statement is present or implied, ALWAYS run the full Neo4j vector search workflow — embed → search muPDNA_embedding_index → traverse graph → synthesize canonical output. Only use explanation mode when the user explicitly asks to understand or document the structure without providing a problem statement.
---

# Problem Definition

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the problem-definition skill to answer this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp, webchat, Discord, Telegram.

---

## Overview

Use this skill to explain or generate **Problem Definition** in the workspace's preferred **muAoPS-style** framing.

When the user asks to **create**, **build**, **draft**, **derive**, **prepare**, or **generate** a problem definition, default to the **Neo4j vector search workflow** — embed the problem statement, retrieve semantically nearest muPDNA nodes, traverse the graph, and synthesize into the canonical output format.

When the user asks only for explanation, documentation, section design, or UI framing, answer conceptually without requiring Neo4j.

---

## Core Structure

Every Problem Definition has exactly these sections in this order:

1. **Problem Name** — one-line title
2. **Problem Statement** — 2–4 sentence business summary
3. **Situation** — Current State (3 bullets, max 50 words each) + Desired Future State (3 bullets, max 50 words each)
4. **muSearch** — table with columns: muSearch Terms | Synthesis | Tags | Sources
5. **Obvious Gap** — exactly 1 sentence, max 50 words
6. **Hypothesis → End Question → Data Sources → Key Fields** — nested per hypothesis (H1…H5)
7. **Answers** — table of expected outputs per hypothesis

Use this concise definition when the user wants a short version:

> Problem Definition in muAoPS is the structured representation of a business problem through the essential components needed to understand the situation, identify the gap, frame analytical reasoning, connect to evidence, capture answers, and make the problem discoverable through muSearch.

---

## Prompt Routing

### Mode 1: Explain or document

Use when the user asks:
- what is problem definition
- explain problem definition in muAoPS
- give me the tabs or sections
- write documentation for problem definition

In this mode: explain the structure cleanly, use product-style wording, do not invoke Neo4j.

### Mode 2: Generate from Neo4j (DEFAULT — triggers on ANY of these)

Use when the user says:
- "problem definition" (with or without a problem statement)
- create / generate / build / derive / prepare / give me a problem definition
- give me the problem definition for this problem statement
- define the problem
- use Neo4j / AoPS to generate the problem definition
- shares any problem statement or use case description

**If a problem statement is present → always run vector search workflow. No exceptions.**
**If no problem statement is given → ask for it first, then run vector search workflow.**

In this mode: **always use vector search first**. See generation workflow below.

---

## Generation Workflow (MANDATORY — follow exactly)

When generating a problem definition from a problem statement or use case:

### Step 1 — Read the recipes reference
Read `references/problem-definition-neo4j-recipes.md` for the full vector search implementation, Cypher queries, Python code, and output format rules.

### Step 2 — Embed the problem statement
Use `text-embedding-3-small` (OpenAI) to convert the problem statement into a 1536-dim embedding.

API key location: `/home/jarvis/Documents/openclaw-codebase/openclaw/.env` → `OPENAI_API_KEY`

### Step 3 — Vector search on muPDNA
Query `muPDNA_embedding_index` via:
```cypher
CALL db.index.vector.queryNodes('muPDNA_embedding_index', 5, $embedding)
YIELD node, score
RETURN node.name AS id, node.projectName AS projectName, node.summary AS summary, score
ORDER BY score DESC
```
Neo4j connection: `bolt://localhost:7680`, auth: `neo4j / password`

### Step 4 — Traverse graph for top 5 nodes
For each returned node, pull: CurrentState, DesiredFutureState, ObviousGap, Hypothesis, EndQuestion, DataSource, KeyField, Answer, muSearch.

### Step 5 — Merge and synthesize
- Merge content across all 5 nodes
- Deduplicate by meaning
- Select 4–5 best hypotheses for the domain
- Select 6–8 best muSearch entries
- Rewrite everything in clean business English — never copy-paste raw graph text or HTML

### Step 6 — Render in canonical output format
Follow the exact format defined in `references/problem-definition-neo4j-recipes.md` under **Output Format (CANONICAL)**.

---

## Canonical Output Format (Summary)

```
# Problem Definition

**Problem Name**
{one line}

**Problem Statement**
{2–4 sentences}

---

## 1. Situation

**Current State**
- bullet 1 (max 50 words)
- bullet 2 (max 50 words)
- bullet 3 (max 50 words)

**Desired Future State**
- bullet 1 (max 50 words)
- bullet 2 (max 50 words)
- bullet 3 (max 50 words)

---

## 2. muSearch

| muSearch Terms | Synthesis | Tags | Sources |
|---|---|---|---|
| {term} | {1–2 sentence synthesis} | `tag1` `tag2` | [Label](url) |
... (6–8 rows)

---

## 3. Obvious Gap

{1 sentence, max 50 words}

---

## 4. Hypothesis → End Question → Data Sources → Key Fields

### H1 — {Title}

**Hypothesis**
{1–2 sentences}

**End Question**
{1 sentence}

| # | Data Source | Key Fields |
|---|---|---|
| 1 | {source} | {field1, field2, field3} |
...

(Repeat H2–H5)

---

## 5. Answers

| Hypothesis | Expected Output |
|---|---|
| H1 — {Title} | {concrete measurable output} |
...

---

*Retrieved via vector search: text-embedding-3-small + Neo4j muPDNA_embedding_index (cosine similarity). Top N nodes by semantic proximity. Graph traversal for Situation, Gap, Hypotheses, muSearch. End Questions, Data Sources, Key Fields synthesized from retrieved context.*
```

---

## Content Quality Rules

### Never do this
- Copy-paste raw HTML or graph text (`<p>The team is responsible for...`)
- Dump node names as bullets without synthesis
- Mention relationship names (`hasCurrentState`, `hasGap`, etc.) in output
- Use generic placeholder language ("the business wants to improve performance")
- Use excessive emojis — keep output clean and professional

### Always do this
- Strip HTML from all graph content before using it
- Rewrite in plain business English — readable by a non-technical stakeholder
- Adapt domain-generic graph content to the specific industry (telecom, retail, pharma, etc.)
- Make hypotheses action-oriented and testable
- Make end questions specific enough for an analyst to act on
- Make key fields column-level specifics, not category names
- Ground every section in retrieved graph data; synthesize what's missing

---

## muSearch Table Rules

Column definitions:
- **muSearch Terms**: clean concept name from the graph node
- **Synthesis**: 1–2 sentences on what this means for the business — not a textbook definition
- **Tags**: 2–3 backtick-wrapped tags, e.g. `retention` `early warning` `ML`
- **Sources**: hyperlinked readable label — never a raw URL as display text

Include 6–8 rows. Curate for relevance to the specific problem. Do not include every muSearch node blindly.

---

## Situation Rules

- Exactly **3 bullet points** per state (Current and Future)
- **Max 50 words per bullet**
- Current State: written from the business team's perspective — what they are experiencing today
- Future State: written as achieved outcomes — what will be true when the problem is solved
- No jargon, no graph relationship language

---

## Obvious Gap Rules

- Exactly **1 sentence**
- **Max 50 words**
- Bridges Current State → Desired Future State in plain language
- Must be specific to the domain — not "the team lacks insights"

---

## Hypothesis Block Rules

- **4–5 hypotheses** per problem definition
- Each hypothesis: 1–2 sentences, testable, grounded in graph data
- Each end question: 1 sentence, analytically answerable
- Each end question: **2–4 data sources**
- Each data source: **3–5 key fields** — specific column-level names
- Hypothesis titles: action-oriented, business-readable (e.g. "Usage Behavior Signals Churn Risk")

---

## Adaptation Rules

- If user gives a problem statement → generate full problem definition using Neo4j vector search
- If user asks for explanation → explain structure without invoking Neo4j
- If user asks for documentation → produce product-style documentation pattern
- If user asks about tabs or UI structure → use the grouped product model below
- If user asks for ontology/schema language → relate to `muPDNA`, `CurrentState`, `DesiredFutureState`, `ObviousGap`, `Hypothesis`, `EndQuestion`, `DataSource`, `KeyField`, `Answer`, `muSearch`

---

## Product Tab Structure (when asked)

Grouped model:

1. **Situation** — Current State + Desired Future State
2. **Discovery** — muSearch
3. **Problem** — Obvious Gap + Hypothesis + End Question
4. **Evidence** — Data Sources + Key Fields
5. **Answers**

---

## References

Read when needed:

- `references/problem-definition-neo4j-recipes.md` — full vector search implementation, Cypher queries, Python code, output format spec, missing data policy
- `references/problem-definition-product-style.md` — product-style wording and section descriptions for documentation mode
