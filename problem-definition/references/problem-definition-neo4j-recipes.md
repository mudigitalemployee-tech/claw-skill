# Problem Definition Neo4j Recipes

Use these patterns when generating a problem definition from the Akasa / muAoPS graph.

## Goal

Retrieve enough graph structure to populate these sections in order:

1. Problem Name
2. Problem Statement
3. Situation (Current State + Future State)
4. muSearch
5. Obvious Gap
6. Hypothesis → End Question → Data Sources → Key Fields
7. Answers

Do not assume every section exists for every `muPDNA`. Never copy-paste raw graph content — always synthesize into business-readable language.

---

## Retrieval Strategy: Vector Search First (MANDATORY)

Always use vector search as the primary retrieval method. Never use keyword matching (`CONTAINS`) as the first approach.

### Step 1 — Embed the problem statement

Use `text-embedding-3-small` (OpenAI) to embed the problem statement or user query.
Dimension: 1536. This matches the `muPDNA_embedding_index`.

```python
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=problem_statement
)
embedding = response.data[0].embedding  # 1536-dim vector
```

OpenAI API key location: `/home/jarvis/Documents/openclaw-codebase/openclaw/.env`
Key: `OPENAI_API_KEY`

### Step 2 — Vector search on muPDNA

```cypher
CALL db.index.vector.queryNodes('muPDNA_embedding_index', 5, $embedding)
YIELD node, score
RETURN node.name AS id, node.projectName AS projectName, node.summary AS summary, score
ORDER BY score DESC
```

- Returns top 5 semantically nearest muPDNA nodes by cosine similarity
- Use top 5 to maximize coverage of hypotheses, muSearch entries, and situational context
- Score > 0.80 is a strong semantic match

Available vector indexes:
| Index | Node | Property | Dimensions | Similarity |
|---|---|---|---|---|
| `muPDNA_embedding_index` | muPDNA | embeddings | 1536 | Cosine |
| `muOBI_embedding_index` | muOBI | embeddings | 1536 | Cosine |
| `muUniverse_embedding_index` | muUniverse | embeddings | 1536 | Cosine |

### Step 3 — Traverse graph for each top node

For each node returned by vector search, run the full traversal:

```cypher
MATCH (p:muPDNA) WHERE p.name = $pid
OPTIONAL MATCH (p)-[:hasCurrentState]->(cs:CurrentState)
OPTIONAL MATCH (p)-[:hasDesiredFutureState]->(dfs:DesiredFutureState)
OPTIONAL MATCH (p)-[:hasGap]->(g:ObviousGap)
OPTIONAL MATCH (g)-[:hasHypothesis]->(h:Hypothesis)
OPTIONAL MATCH (h)-[:hasEndQuestion]->(q:EndQuestion)
OPTIONAL MATCH (q)-[:hasDataSource]->(ds:DataSource)
OPTIONAL MATCH (q)-[:hasKeyField]->(kf:KeyField)
OPTIONAL MATCH (q)-[:hasAnswer]->(a:Answer)
OPTIONAL MATCH (p)-[:hasmuSearch]->(ms:muSearch)
RETURN coalesce(p.projectName, p.name) AS problem,
       p.summary AS summary,
       collect(DISTINCT cs.name) AS currentStates,
       collect(DISTINCT dfs.name) AS desiredFutureStates,
       collect(DISTINCT g.name) AS gaps,
       collect(DISTINCT h.name) AS hypotheses,
       collect(DISTINCT q.name) AS endQuestions,
       collect(DISTINCT ds.name) AS dataSources,
       collect(DISTINCT kf.name) AS keyFields,
       collect(DISTINCT a.name) AS answers,
       collect(DISTINCT {name: ms.name, description: ms.description, source: ms.source}) AS muSearchEntries
```

### Step 4 — Merge and deduplicate

After retrieving data from top 5 nodes:
- Merge all currentStates, futureStates, gaps, hypotheses, muSearch entries
- Deduplicate by meaning (not just string match)
- Select the 3–5 most relevant hypotheses for the specific problem context
- Select 6–8 most relevant muSearch entries

---

## Python Script Reference

Full working vector search script: `/tmp/neo4j_vector_search.py`

Driver connection: `bolt://localhost:7680`, auth: `("neo4j", "password")`

---

## Content Generation Rules (MANDATORY)

### Never do this
- Copy-paste raw HTML or graph text (e.g. `<p>The team is responsible for...`)
- Dump node names as bullet points without synthesis
- Use relationship names like `hasCurrentState`, `hasGap` in the output
- Fabricate content not grounded in retrieved data

### Always do this
- Strip HTML tags from graph content before processing
- Rewrite all graph content into clean, business-readable English
- Synthesize across multiple muPDNA nodes — combine the best signals
- Ground every hypothesis in a real graph node; mark synthesized content clearly
- Adapt generic graph context to the specific domain in the problem statement (telecom, retail, pharma, etc.)

---

## Output Format (CANONICAL — DO NOT DEVIATE)

### Problem Name
One line. The name of the problem or use case.

### Problem Statement
2–4 sentences. The business problem in plain language. Use the user's input, refined if needed.

---

### 1. Situation

**Current State**
- Exactly 3 bullet points
- Max 50 words per bullet
- Written from the business team's perspective
- Ground in graph data; adapt to the domain

**Future State**
- Exactly 3 bullet points
- Max 50 words per bullet
- Describes the desired outcome and measurable change
- Ground in graph data; adapt to the domain

---

### 2. muSearch

Render as a table with exactly these 4 columns:

| muSearch Terms | Synthesis | Tags | Sources |
|---|---|---|---|

Rules:
- **muSearch Terms**: concept name from graph (clean, no jargon)
- **Synthesis**: 1–2 sentences — what this means for the business, not a definition
- **Tags**: 2–3 backtick-wrapped tags e.g. `retention` `prediction`
- **Sources**: hyperlinked label, use `source` field from graph node; if missing use EoC or domain reference
- Include 6–8 rows — curate the most relevant entries for the problem
- Never use raw URLs as the display label — always use a readable name

---

### 3. Obvious Gap

- Exactly 1 sentence
- Max 50 words
- States the visible difference between Current State and Future State
- Must be specific to the domain — not generic

---

### 4. Hypothesis → End Question → Data Sources → Key Fields

For each hypothesis, render in this exact structure:

```
### H{N} — {Hypothesis Title}

**Hypothesis**
{1–2 sentences. The testable reasoning behind the gap.}

**End Question**
{1 sentence. The specific analytical question that operationalizes the hypothesis.}

| # | Data Source | Key Fields |
|---|---|---|
| 1 | {Source name} | {field1, field2, field3} |
| 2 | {Source name} | {field1, field2, field3} |
...
```

Rules:
- 4–5 hypotheses per problem definition
- Each hypothesis has exactly 1 End Question
- Each End Question has 2–4 Data Sources
- Each Data Source has 3–5 Key Fields — specific, not generic
- Hypothesis titles should be action-oriented and business-readable
- End Questions should be answerable by an analyst — not philosophical
- Data Sources should be real systems or datasets a business would own
- Key Fields should be actual column-level specifics

---

### 5. Answers

Render as a table:

| Hypothesis | Expected Output |
|---|---|
| H{N} — {Title} | {What the analysis will produce — metric, model, ranking, playbook} |

- One row per hypothesis
- Expected outputs should be concrete and measurable
- Mark as "To be populated post-analysis" only when no answer nodes exist in graph

---

## Closing Note (always include)

End with a single italicized line:

```
*Retrieved via vector search: text-embedding-3-small + Neo4j muPDNA_embedding_index (cosine similarity). 
Top N nodes by semantic proximity. Graph traversal for Situation, Gap, Hypotheses, muSearch. 
End Questions, Data Sources, Key Fields synthesized from retrieved context.*
```

---

## Missing Data Policy

| Section | If missing in graph |
|---|---|
| Current State / Future State | Synthesize from summary + domain context |
| Obvious Gap | Derive from Current→Future delta |
| Hypotheses | Use graph nodes; supplement with domain reasoning if < 4 found |
| End Questions | Always synthesize — rarely populated in graph |
| Data Sources / Key Fields | Always synthesize — rarely populated in graph |
| Answers | Mark as "To be populated post-analysis" |
| muSearch | Use what's available; supplement with EoC references if < 6 entries |

Always state what was graph-backed vs. synthesized in the closing note.
