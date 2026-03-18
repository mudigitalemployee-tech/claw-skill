---
name: sdlc-planning
description: >
  Generate a professional, milestone-driven SDLC (Software Development Life Cycle)
  plan for any application request before code generation begins. The output is a
  concise, client-review-ready document focused on deliverables and development
  phases — not lengthy technical explanations. This skill is now INTEGRATED into
  the fullstack-app-builder workflow — every web app request automatically generates
  an SDLC document first. Can also be invoked standalone when user explicitly asks
  for "SDLC plan", "project plan", "requirements document", etc. Use when: user
  asks to "plan an app", "create an SDLC plan", "plan before building", "SDLC
  document", "project plan for an app", "software planning", "design an application",
  "architecture plan", or any request that explicitly asks for planning, requirements
  gathering, or architecture design before implementation. Also triggers on: "plan
  first then build", "SDLC", "requirements document", "technical specification",
  "system design document", "milestone plan". NOT for: code-only tasks, debugging,
  or non-application planning.
---

# SDLC Planning Skill

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the sdlc-planning skill to answer this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp, webchat, Discord, Telegram.


Generate a professional, milestone-driven SDLC plan. Present for client approval before any code is generated.

**Integration Note:** This skill's template (`references/sdlc-template.md`) is used automatically by the **fullstack-app-builder** skill as a mandatory first step for ALL web app requests. The SDLC document is generated, presented for user approval, and only after approval + GitHub link does code generation begin.

## Workflow

### 1. Analyze the Request

Extract from the user's input:
- Application type and purpose
- Core features and functionality
- Tech stack preferences
- Data entities involved
- UI expectations
- Constraints or requirements

If the request is vague, ask **1-3 focused questions** to clarify scope. Infer reasonable defaults for everything else.

### 2. Generate the SDLC Document

Read `references/sdlc-template.md` for the 10-section structure.

The document has 10 sections:
1. Project Overview
2. Scope of Work
3. Functional Requirements
4. Non-Functional Requirements
5. Technology Stack
6. System Architecture (High Level)
7. Development Milestones ← **the core section**
8. Testing Plan
9. Final Deliverables
10. Client Approval

Key principles:
- **Concise and professional** — suitable for client review
- **Milestone-driven** — every milestone has features, deliverables, and timeline
- **AI-execution framed** — milestones reflect Ved's actual build timeline (minutes), not human team sprints (weeks). Include equivalent human effort for comparison.
- **Deliverable-focused** — what gets produced, not how it's coded
- **No excessive technical detail** — high-level architecture, not implementation specifics
- **Specific to the app** — no generic filler; every item reflects the actual application

### 3. Present for Approval

End the document with:

> **Please review the SDLC plan and milestones. Once approved, the system will begin building the application according to this plan.**

### 4. Handle Feedback

If changes requested → update affected sections → re-present → ask for approval again.

### 5. Handoff to Builder (After Approval)

On approval, pass the SDLC document to the **fullstack-app-builder** skill as the specification:
- Scope → feature list
- Functional requirements → pages and components
- Data entities → Pydantic models + JSON storage
- API design (from milestones) → FastAPI routes
- Architecture → project structure
- Tech stack → dependencies and config

## Critical Rules

1. **Never generate application code** during the planning phase
2. **Always wait for explicit user approval** before proceeding to build
3. **Keep it concise** — focus on milestones and deliverables, not code-level details
4. **Every section must be specific** to the requested application
5. **Use tables and bullet lists** — make it scannable
6. **Standard 5-milestone structure** — adapt names/content to the app; merge or split as needed
7. **AI-execution milestones** — milestones MUST reflect Ved's actual AI build time (minutes/hours), NOT human developer sprints (weeks/months). Always include a comparison row showing equivalent human team effort. Ved builds the entire app — there is no "team" of FE/BE/QA developers.
