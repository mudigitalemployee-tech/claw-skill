# SDLC Document Template

Professional, milestone-driven format suitable for client review. Keep it concise — focus on deliverables, not lengthy technical explanations.

---

## 1. Project Overview

- **Project Name**: (derived from user request)
- **Description**: 2-3 sentences — what the application does and why
- **Target Users**: Who will use this (roles/personas)
- **Business Objectives**: 3-5 bullet points — measurable outcomes the application delivers

## 2. Scope of Work

### Features Included
Numbered list of features that WILL be built. Group by module if helpful.

### Features Excluded
Bullet list of what is explicitly OUT of scope (prevents scope creep).

### Assumptions & Constraints
- Assumptions about the environment, users, data volume
- Technical or business constraints (e.g., no database, local only, no auth)

## 3. Functional Requirements

### Core Application Features
Numbered list grouped by module/area. Each item = one user-facing capability.

### User Actions Supported
Bullet list of what a user can DO in the system (verb-driven):
- Add / Edit / Delete [entity]
- Search / Filter by [field]
- View [dashboard/report]
- Update [stock/status/etc.]

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| **Performance** | (response times, throughput) |
| **Security** | (auth needs, data protection) |
| **Scalability** | (expected data/user volume) |
| **Usability** | (responsive, accessible, intuitive) |
| **Browser Compatibility** | (target browsers) |

## 5. Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | ... | ... |
| Backend | ... | ... |
| Data Storage | ... | ... |
| Key Libraries | ... | ... |

## 6. System Architecture (High Level)

Brief description of three layers + communication flow. Include a simple ASCII diagram:

```
┌─────────────┐     REST API     ┌─────────────┐     Read/Write     ┌─────────────┐
│  Frontend   │ ◄──────────────► │   Backend   │ ◄────────────────► │  Storage    │
│  (React)    │    HTTP/JSON     │  (FastAPI)  │                    │  (JSON)     │
└─────────────┘                  └─────────────┘                    └─────────────┘
```

- **Frontend Layer**: What it handles (UI, routing, state)
- **Backend API Layer**: What it handles (validation, business logic, CRUD)
- **Data Storage Layer**: What it handles (persistence, seed data)
- **Communication Flow**: Frontend → REST API → Backend → JSON files → Response

## 7. Development Milestones

**IMPORTANT:** This project is built by **Ved (AI Digital Employee)**, not a human development team. Milestones reflect Ved's actual AI execution time — measured in **minutes**, not weeks. Always include a comparison to equivalent human team effort.

Each milestone must specify:
- **Milestone name** (numbered)
- **Features** implemented in this milestone (bullet list)
- **Deliverables** produced (bullet list)
- **Ved's estimated time** (in minutes — be realistic based on complexity)

### Summary Table (include at the top of milestones)

| Phase | Milestone | Ved's Time | Deliverables |
|-------|-----------|-----------|--------------|
| Phase 1 | Backend API & Core Logic | ~X min | (list key outputs) |
| Phase 2 | Frontend UI | ~X min | (list key outputs) |
| Phase 3 | Integration & Wiring | ~X min | (list key outputs) |
| Phase 4 | Documentation | ~X min | (list key outputs) |
| Phase 5 | Packaging & Delivery | ~X min | (list key outputs) |
| | **Total Ved Build Time** | **~X min** | |
| | **Equivalent Human Team Effort** | **X–X weeks (X-person team)** | |

### Standard 5-Milestone Structure:

---

**Milestone 1 — Backend API & Core Logic** (~3–5 min)

Features:
- Project directory structure and framework setup
- Data models and storage layer
- All CRUD API endpoints with validation
- Core business logic / processing services
- Seed data creation

Deliverables:
- Running backend server with all endpoints
- Storage layer with sample data

---

**Milestone 2 — Frontend UI** (~4–6 min)

Features:
- Frontend project setup (Vite + React + TailwindCSS)
- Design system and component library
- All pages and views built
- Navigation, forms, tables, modals, empty states
- API service layer connecting to backend

Deliverables:
- Complete, interactive frontend application
- All pages fully wired to backend API

---

**Milestone 3 — Integration & Polish** (~1–2 min)

Features:
- End-to-end frontend-backend integration verification
- Error handling, loading states, edge cases
- Responsive design verification
- Search, filter, sort functionality

Deliverables:
- Fully working application (frontend + backend)

---

**Milestone 4 — Documentation** (~1–2 min)

Features:
- README.md with setup instructions
- API endpoint reference
- Architecture overview
- Project structure guide

Deliverables:
- Complete project documentation

---

**Milestone 5 — Packaging & Delivery** (~1 min)

Features:
- Project zipped for delivery
- Sent to user via appropriate channel (WhatsApp/webchat/etc.)
- Summary of what was built

Deliverables:
- Delivered zip with full source code
- Setup-ready project

---

Adapt milestone names, features, and times to match the specific application. Simpler apps may take ~8–10 min total; complex apps may take ~15–25 min. Always provide the equivalent human team effort for context.

## 8. Testing Plan

### API Testing
- Key endpoints to test (list 4-6 specific test cases)
- Expected responses for valid and invalid inputs

### UI Testing
- Key user interactions to verify (list 4-6 scenarios)
- Form validation behavior

### End-to-End Workflow Testing
- 2-3 full user journeys to test from start to finish
- Example: "Create → Edit → Update Stock → Search → Delete"

## 9. Final Deliverables

Bullet list of everything the client receives:
- Full application source code (frontend + backend)
- Project folder structure
- Seed data / sample data
- Setup and run instructions
- README documentation
- API documentation (auto-generated Swagger)

## 10. Client Approval

After presenting the document, ask:

> **Please review the SDLC plan and milestones. Once approved, the system will begin building the application according to this plan.**
>
> You may request changes to any section before approval.
