# Technology Selection Guide

## Default Stack

| Layer     | Technology              | Why                                          |
|-----------|-------------------------|----------------------------------------------|
| Frontend  | React + Vite + Tailwind | Fast dev, component model, utility-first CSS |
| Backend   | Python + FastAPI        | Async, auto-docs, Pydantic validation        |
| Storage   | Local JSON files        | Zero setup, portable, no DB dependency       |

## When to Override

### Frontend Alternatives

| User Says                        | Use Instead        | Notes                        |
|----------------------------------|--------------------|------------------------------|
| "Use Vue" / "Vue.js"            | Vue 3 + Vite       | Composition API, same Vite   |
| "Use Svelte"                    | SvelteKit          | Compiled, minimal bundle     |
| "Plain HTML" / "No framework"   | Vanilla + Tailwind | CDN-based, no build step     |
| "Use Next.js"                   | Next.js            | SSR/SSG, file-based routing  |

### Backend Alternatives

| User Says                        | Use Instead        | Notes                        |
|----------------------------------|--------------------|------------------------------|
| "Use Flask"                     | Flask              | Simpler, less opinionated    |
| "Use Express" / "Use Node"     | Express.js         | JS everywhere                |
| "Use Django"                    | Django REST        | Batteries-included           |

### Storage Alternatives

| User Says                        | Use Instead        | Notes                        |
|----------------------------------|--------------------|------------------------------|
| "Use SQLite"                    | SQLite + SQLAlchemy| Lightweight SQL, single file |
| "Use TinyDB"                   | TinyDB             | Document-oriented, Pythonic  |

**Default rule**: If the user doesn't specify → use the default stack. Don't ask.

## Default Design System

The `assets/frontend-template/src/index.css` provides a **reference design system** — a solid starting point, not a rigid template. Use it as inspiration and adapt to each app's needs.

**Core aesthetic (maintain these principles):**
- Clean, modern, professional appearance
- Light page background with white content cards
- Consistent primary accent color (default: Indigo `#4F46E5`)
- Inter font via Google Fonts CDN
- Pre-built CSS component classes as a baseline

**Adapt freely:**
- Color palette — choose colors that suit the app's domain
- Layout — vary grid columns, spacing, and page structure
- Component style — extend or modify the reference classes
- Navigation — tabs, sidebar, or minimal header depending on complexity

See `references/project-patterns.md` for component examples and alternative palettes.

## Decision Flow

```
User provides tech preference?
  YES → Use specified tech
  NO  → Use defaults (React+Vite+Tailwind / FastAPI / JSON)

User provides data files?
  CSV/JSON → Auto-generate models from schema
  None     → Design models from requirements

User provides UI mockups?
  YES → Analyze and replicate layout
  NO  → Design clean, modern UI from requirements
```
