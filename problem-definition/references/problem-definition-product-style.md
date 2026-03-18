# Problem Definition

## Overview

**Problem Definition** in **muAoPS** is the structured representation of a business problem so it can be understood, explored, and answered systematically.

It brings together the core elements required to:

- define the business situation
- identify the gap that matters
- frame testable reasoning
- connect the problem to evidence
- capture the resulting answers
- make the problem discoverable through **muSearch**

At its core, Problem Definition is built from these components:

- **Situation**
  - Current State
  - Future State
- **muSearch**
- **Obvious Gap**
- **Hypothesis**
- **End Question**
- **Data Sources**
- **Key Fields**
- **Answers**

## Purpose

Problem Definition helps users move from a loosely understood business issue to a structured analytical problem model.

It is designed to support:

- problem clarity
- reasoning consistency
- analytical exploration
- evidence-based answer generation
- discoverability and reuse

## Core Structure

### 1. Situation

The **Situation** captures the business context of the problem.

It includes:

- **Current State** — what is happening today
- **Future State** — what should be happening instead

This section establishes the starting point and the intended direction of improvement.

**Purpose**
- define the business context
- anchor the problem in reality
- clarify the change being sought

### 2. muSearch

**muSearch** is the supporting retrieval and context layer linked to the problem definition.

In the observed Akasa graph, `muSearch` behaves mostly as a set of linked knowledge snippets attached to `muPDNA`, typically with fields like:

- `name`
- `description`
- sometimes `source`

So in product terms, muSearch should be presented as:

- supporting knowledge context
- linked explanatory or reference snippets
- discovery cues related to the problem

**Purpose**
- improve discoverability
- attach contextual knowledge to the problem
- surface reusable supporting references

### 3. Obvious Gap

The **Obvious Gap** defines the visible difference between the Current State and the Future State.

It captures:

- what is missing
- what is underperforming
- what requires explanation or intervention

**Purpose**
- state the business problem clearly
- define what needs to be solved

### 4. Hypothesis

A **Hypothesis** is a possible explanation for the Obvious Gap.

It represents structured, testable reasoning about why the gap exists.

**Purpose**
- turn the problem into analytical reasoning
- provide possible explanations to investigate

### 5. End Question

An **End Question** translates a hypothesis into a specific analytical question.

It defines what must be answered in order to validate, reject, or refine the hypothesis.

**Purpose**
- make the hypothesis actionable
- guide analysis toward decision-relevant answers

### 6. Data Sources

**Data Sources** identify where the evidence for analysis will come from.

They may include:

- systems
- datasets
- repositories
- business-owned data assets

**Purpose**
- link the problem to evidence
- identify the source of required data

### 7. Key Fields

**Key Fields** define the important variables needed to answer the End Questions.

They may include:

- identifiers
- measures
- dimensions
- business-critical attributes

**Purpose**
- specify the analytical inputs required
- focus the data needed for answering the problem

### 8. Answers

**Answers** capture the outputs derived from analysis.

They represent:

- responses to End Questions
- findings from evidence
- conclusions relevant to the problem

**Purpose**
- close the loop from problem definition to insight
- record the outcome of structured reasoning

## How the Components Work Together

Problem Definition follows a connected flow:

**Situation -> Obvious Gap -> Hypothesis -> End Question -> Data Sources / Key Fields -> Answers**

with **muSearch** enabling the entire problem space to be:

- searchable
- connected
- reusable

This structure ensures that a business problem is not just described, but modeled in a way that supports analysis and discovery.

## Functional View

- **Situation** — Defines the business context through Current State and Future State
- **muSearch** — Makes the problem discoverable and connected
- **Obvious Gap** — States the visible problem to be solved
- **Hypothesis** — Provides possible explanations for the gap
- **End Question** — Defines what must be answered
- **Data Sources** — Identify where evidence comes from
- **Key Fields** — Specify the critical analytical inputs
- **Answers** — Capture the resulting insights or conclusions

## Minimal Definition

**Problem Definition** is the muAoPS construct that organizes a business problem into its essential components: **Situation, muSearch, Obvious Gap, Hypothesis, End Question, Data Sources, Key Fields, and Answers**.

Together, these components define the problem, support analysis, and enable answer discovery in a structured and searchable way.

## Suggested UI / Product Framing

### Tabs

1. **Situation**
2. **muSearch**
3. **Obvious Gap**
4. **Hypothesis**
5. **End Question**
6. **Data Sources**
7. **Key Fields**
8. **Answers**

### Optional grouped product model

1. **Situation**
   - Current State
   - Future State
2. **Discovery**
   - muSearch
3. **Problem**
   - Obvious Gap
   - Hypothesis
   - End Question
4. **Evidence**
   - Data Sources
   - Key Fields
5. **Answers**
