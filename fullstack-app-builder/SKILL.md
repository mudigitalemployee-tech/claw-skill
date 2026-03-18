---
name: fullstack-app-builder
description: >
  Generate complete full-stack web applications with separate frontend and backend
  from user requirements. Use when: user asks to "build a full-stack app", "create
  an app with API", "build a web app with backend", "generate a CRUD app",
  "create a dashboard with API", "build an app with React and FastAPI", or any
  request requiring both frontend UI and backend API logic. Also triggers on:
  "full-stack", "frontend + backend", "build me an app with data storage",
  "create a web app that saves data", "build an API with a UI". Accepts requirements
  as text, documents, images, or data files (CSV/JSON). Default stack: React + Vite +
  TailwindCSS frontend, Python FastAPI backend, local JSON file storage. No database
  required. NOT for: frontend-only prototypes (use ui-app-generator), deployment
  configuration, cloud infrastructure, or mobile apps.
---

# Full-Stack App Builder

> ⚠️ **MANDATORY DISCLOSURE:** At the very end of every response using this skill, append:
> `_I used the fullstack-app-builder skill to answer this._ 🛠️`
> This is non-negotiable — applies on ALL channels including WhatsApp, webchat, Discord, Telegram.


Generate complete, working full-stack web applications with frontend, backend, and local data storage.

## Workflow (MANDATORY: SDLC-First)

**Every web app request MUST follow this 3-step flow. No exceptions.**

### Step 0. SDLC Document (MANDATORY — before ANY code)

**Before writing a single line of code**, generate an SDLC planning document for the requested app. This uses the sdlc-planning skill's template at `~/.openclaw/workspace/skills/sdlc-planning/references/sdlc-template.md`.

**What to generate:**
1. Read the SDLC template from `~/.openclaw/workspace/skills/sdlc-planning/references/sdlc-template.md`
2. Fill in all 10 sections specific to the requested application
3. Milestones MUST reflect Ved's AI build timeline (minutes), not human sprints
4. Include summary table with Ved's time per phase + equivalent human effort
5. **Generate as a MuSigma HTML report — NEVER dump as chat text**

### ⚠️ SDLC HTML Delivery (MANDATORY — NO EXCEPTIONS)

**The SDLC document MUST always be delivered as a self-contained HTML file using the MuSigma canonical template. Dumping the SDLC as raw chat text is STRICTLY FORBIDDEN.**

#### Steps (run every time):
1. Build the full SDLC HTML file using the MuSigma template from `skills/musigma-html-report-generator/assets/template.html`
2. Save to: `reports/<project-name>-sdlc-v<YY.MM.VV>.html`
3. Zip it: `reports/<project-name>-sdlc-v<YY.MM.VV>.zip`
4. **Channel-aware delivery:**

| Channel | Delivery |
|---------|---------|
| **WhatsApp** | `openclaw message send --channel whatsapp --target <number> --message "📋 SDLC doc for <project>" --media reports/<name>-sdlc-v<YY.MM.VV>.zip` |
| **Webchat** | Present HTML in browser / share file path |
| **Telegram/Discord** | Send `.html` file directly via message tool |

5. After sending, include a **brief chat summary** of what was sent (3–5 bullet points max — do NOT repeat the full SDLC in chat)

**After delivery, ask:**
> **Please review the SDLC document I just sent. You can:**
> 1. ✅ **Approve** — I'll proceed to build
> 2. ✏️ **Request changes** — tell me what to modify
> 3. ❌ **Cancel** — stop here
>
> Once approved, please share a **GitHub repository link** where I should push the code (or say "local only" to skip).

**Flow:**
- User requests app → Generate SDLC HTML → Zip → Send to channel → Brief summary in chat → Wait for approval
- User says "change X" → Update SDLC HTML → Re-zip → Re-send → Wait for approval
- User approves → Ask for GitHub repo link → Proceed to build
- User says "local only" or no GitHub → Build locally in `projects/`

**NEVER skip this step. NEVER deliver SDLC as chat text. Always HTML file first.**

### Step 0.5. GitHub Repository Setup (After Approval)

After SDLC approval, ask for a GitHub repository link:
> **Where should I push the code?** Share a GitHub repo URL, or say "local only" to keep it in the workspace.

If a GitHub link is provided:
- Clone or fork the repo
- Use the github-manager skill for all git operations
- Push completed code with proper commits

If "local only":
- Build in `projects/{app-name}/`
- Zip and deliver

### 1. Analyze Requirements

Extract from all provided inputs (text, documents, images, data files):

- **Application purpose** — what problem does it solve?
- **Core features** — CRUD operations, search, filters, auth, etc.
- **Pages/views** — list each screen and its purpose
- **Data models** — entities, fields, relationships
- **API endpoints** — what operations the backend must support
- **UI requirements** — layout, style, branding, responsiveness
- **Tech preferences** — user-specified stack overrides

If requirements are incomplete, infer reasonable defaults. Ask **1-3 focused questions** only when critical information is missing.

### 2. Select Technology

Read `references/tech-selection.md` for the full decision matrix.

**Default stack** (when user doesn't specify):
- Frontend: React + Vite + TailwindCSS
- Backend: Python + FastAPI
- Storage: Local JSON files

**Override rules:**
- User specifies technologies → use them
- User provides CSV/JSON data → auto-configure storage around those files
- User provides UI mockups → analyze and replicate layout

### 3. Design Architecture

Before coding, define in a brief plan:

- **Data models**: entities with fields and types
- **API endpoints**: method, path, request/response shape
- **Frontend pages**: route, components, data flow
- **Storage format**: JSON file structure in `data/`

Consult `references/project-patterns.md` for standard patterns and the design system.

### 4. Generate Project Structure

Create the project at `projects/{app-name}/`:

```
{app-name}/
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── services/
│           └── api.js
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   │       └── json_store.py
│   └── storage/
├── data/
│   └── *.json
└── README.md
```

Use `assets/backend-template/` and `assets/frontend-template/` as scaffolds. Copy them first, then customize.

**Logo file**: Copy MuSigma logo to `frontend/public/musigma_logo.png`. Source: any existing project's `frontend/public/musigma_logo.png` or `C:\Users\admin1\Music\musigma_logo.png`.

### 5. Implement Backend

#### FastAPI Setup (`backend/main.py`)
- Import FastAPI, add CORS middleware (allow frontend origin)
- Mount route modules from `app/routes/`
- Run with `uvicorn main:app --reload --port 8000`

#### Data Models (`backend/app/models/`)
- Pydantic models for request/response validation
- One file per entity (e.g., `task.py`, `user.py`)

#### JSON Storage (`backend/app/utils/json_store.py`)
- Read `assets/backend-template/app/utils/json_store.py` for the reusable store class
- Thread-safe read/write with file locking
- CRUD operations: `get_all()`, `get_by_id()`, `create()`, `update()`, `delete()`
- Auto-generates UUIDs for new records
- Each entity gets its own JSON file in `storage/`

#### Routes (`backend/app/routes/`)
- One file per entity with full CRUD endpoints
- Standard REST: GET (list), GET/:id, POST, PUT/:id, DELETE/:id
- Request validation via Pydantic models
- Proper HTTP status codes and error handling

#### Requirements (`backend/requirements.txt`)
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
```

### 6. Implement Frontend

#### Design System (Guidelines)

The skill includes a **reference design system** in `assets/frontend-template/src/index.css` and component patterns in `references/project-patterns.md`. These serve as **inspiration and starting points** — not rigid templates that must be replicated exactly.

**Design principles to follow:**
- Clean, modern, and professional appearance
- Light page background with white content cards
- Consistent color palette with a clear primary accent
- Inter font (or comparable clean sans-serif) via Google Fonts
- Responsive layout with sensible max-width and padding
- Subtle depth through shadows, hover elevation, and rounded corners
- Pre-built CSS component classes in `index.css` for buttons, cards, badges, inputs, tables

**Reference palette (adapt as appropriate):**
- Primary: Indigo `#4F46E5` (or choose a palette that suits the app's domain)
- Page background: `#F4F6F9`, Card border: `#E8ECF1`
- Success/Warning/Danger semantic colors for badges and alerts
- Alternative palettes listed in `references/project-patterns.md`

**Component classes** in `index.css` (`.btn-primary`, `.card`, `.stat-card`, `.tab-item`, `.badge-*`, `.input`, `.table-*`) provide a solid baseline. Use them as-is, extend them, or create new classes — whatever produces the best UI for the specific app.

**Do NOT** copy the reference patterns blindly. Adapt layout, colors, spacing, and component structure to suit each application's purpose and content.

#### Branding & Professional Aesthetic (MANDATORY)

Every generated app MUST include these professional elements regardless of color palette or design variation:

1. **MuSigma Logo** in the navbar — `<img src="/musigma_logo.png" alt="MuSigma" className="h-8" />` on the left side
2. **Copy the logo file** from an existing project or `C:\Users\admin1\Music\musigma_logo.png` into `frontend/public/musigma_logo.png`
3. **App name + version badge** — e.g., "AppName" (bold) + "v1.0" (muted pill)
4. **"System Ready" status pill** — green dot + "System Ready" text, positioned on the right
5. **User avatar** — "SS" initials circle + "Sayujaya Sharma" name text
6. **Tab bar navigation** — active tab has colored underline; include 1-2 disabled placeholder tabs (grayed out, cursor-not-allowed) for polish
7. **Content max-width** — `max-w-[1360px] mx-auto px-6 lg:px-8` for both navbar and main content

These elements establish a consistent professional identity across all apps. The **colors, backgrounds, and styling** of these elements should adapt to match the app's chosen palette (e.g., dark navbar for BookShelf, white navbar for TaskFlow — both include the same branding elements).

#### Navbar Structure

Every navbar should follow this structure (adapt colors to the app's theme):

```
┌─────────────────────────────────────────────────────────────┐
│ [MuSigma Logo] | [App Icon] AppName  v1.0    ● System Ready │ [SS] Sayujaya Sharma │
├─────────────────────────────────────────────────────────────┤
│ Dashboard  Library  Stats  │  Recommendations  Settings     │
│ (active)   (links)         │  (disabled/grayed out)         │
└─────────────────────────────────────────────────────────────┘
```

Adapt the navbar layout to the app's complexity — but always include the logo, status, and user elements.

#### Vite + React Setup
- Read `assets/frontend-template/` for the scaffold
- `package.json` with react, react-dom, react-router-dom, tailwindcss, axios, recharts
- `vite.config.js` with API proxy to `http://localhost:8000`

#### Pages (`frontend/src/pages/`)
- One file per page/view
- Use React Router for navigation
- Fetch data from backend via `services/api.js`

#### Components (`frontend/src/components/`)
- Reusable UI components: Navbar, StatCard, Modal, Form, Table, EmptyState, Toast, etc.
- Use the pre-built CSS classes from `index.css` — avoid inline style duplication
- SVG icons inline (no icon library dependency needed)

#### API Service (`frontend/src/services/api.js`)
- Axios instance with baseURL `/api`
- One function per API endpoint
- Error handling with user-friendly messages

#### Implementation Rules
- **Responsive**: mobile-first, works at 320px+
- **Realistic content**: plausible placeholder/seed data, not "Lorem ipsum"
- **Interactive**: all CRUD operations work end-to-end
- **Clean code**: modular, readable, well-structured
- **Error states**: loading spinners, error messages, empty states
- **Professional polish**: consistent spacing, smooth transitions, attention to detail
- **Design freedom**: use the reference design system as inspiration — adapt colors, layout, and components to create the best UI for each specific app rather than forcing a one-size-fits-all look

### 7. Seed Data

- If user provides CSV/JSON data files → parse and use as seed data
- Otherwise → generate realistic seed data (5-15 records per entity)
- Place seed data in `data/` directory
- Backend copies seed data to `storage/` on first run if storage is empty

### 8. Generate README

Include in `README.md`:
- App description and features
- Architecture overview (brief)
- Setup instructions (step-by-step)
- API endpoint reference table
- Project structure overview

### 9. Output

- Save project to `projects/{app-name}/` (kebab-case)
- Provide a summary: what was built, pages, endpoints, data models
- Include setup instructions:

```bash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

- If user is on WhatsApp → zip the project before sending

## UI Mockup Handling

When user provides images/mockups:
1. Analyze layout structure, colors, typography, spacing
2. Identify components (cards, tables, forms, navbars, sidebars)
3. Map to React components with TailwindCSS classes
4. Use the reference design system as a starting point, then adapt to match the mockup's aesthetic
5. Capture the **spirit and style** of the mockup — don't force pixel-perfect replication if it conflicts with responsiveness or usability

## Data File Handling

When user provides CSV/JSON:
1. Analyze schema: column names, types, relationships
2. Generate matching Pydantic models
3. Create API endpoints for that data
4. Use provided data as seed data in `data/`
5. Build frontend views to display and interact with the data
