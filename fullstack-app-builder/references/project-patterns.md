# Project Patterns Reference

> **These patterns are guidelines and inspiration, not rigid templates.** Adapt layout, colors, spacing, and component structure to create the best UI for each specific app. A clean, modern, professional result is the goal — not pixel-perfect replication of these examples.

## Design System

### Core Principles
- **Clean and modern**: professional look with consistent spacing and typography
- **Light backgrounds**: neutral page background with white content surfaces
- **Subtle depth**: soft shadows, hover elevation, rounded corners
- **Clear hierarchy**: distinct heading sizes, muted secondary text, colored accents
- **Consistent components**: reuse button, card, badge, and input styles across pages
- **Responsive**: works on desktop and tablet at minimum

### Reference Color Palette (Default — Indigo)
Use as a starting point. Choose a palette that suits the app's domain and audience.

- **Primary**: `#4F46E5` (indigo) — buttons, active tabs, accents
- **Page background**: `#F4F6F9` (light warm gray)
- **Card background**: `#FFFFFF` with `#E8ECF1` border
- **Text**: `#111827` primary, `#374151` secondary, `#6B7280` muted
- **Semantic**: Success `#059669`, Warning `#D97706`, Danger `#DC2626`, Info `#4F46E5`

### Alternative Palettes
Choose based on app domain — a health app might use teal/green, a finance app might use blue/navy.

| Palette | Primary | Accent | Best For |
|---------|---------|--------|----------|
| **Indigo** (default) | `#4F46E5` | `#059669` | General purpose, dashboards |
| **Teal** | `#0D9488` | `#F97316` | Health, environment, calm apps |
| **Emerald** | `#059669` | `#8B5CF6` | Finance, growth, nature |
| **Blue** | `#2563EB` | `#F59E0B` | Corporate, enterprise |
| **Dark Mode** | `#818CF8` on `#0F172A` | `#34D399` | Developer tools, media |

### Typography
- **Font**: Inter (Google Fonts CDN) or any clean sans-serif
- **Weights**: 400 body, 500 labels, 600 headings, 700 stats
- **Sizes**: adapt to content density — don't force a fixed scale

---

## Common Data Models

### CRUD Entity Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None

class Item(ItemBase):
    id: str
    created_at: str
    updated_at: str
```

### User/Auth Pattern (simple, no real auth)
```python
class UserBase(BaseModel):
    username: str
    email: str
    role: str = "user"

class User(UserBase):
    id: str
    created_at: str
```

---

## API Route Patterns

### Standard CRUD Router
```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/items", tags=["items"])

@router.get("/")
async def list_items(search: str = None, category: str = None):
    """List with optional filtering"""

@router.get("/{item_id}")
async def get_item(item_id: str):
    """Get by ID, 404 if not found"""

@router.post("/", status_code=201)
async def create_item(item: ItemCreate):
    """Create and return with generated ID"""

@router.put("/{item_id}")
async def update_item(item_id: str, item: ItemUpdate):
    """Partial update, 404 if not found"""

@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: str):
    """Delete, 404 if not found"""
```

---

## Frontend Component Patterns

### Navbar (Mandatory Branding + Flexible Design)

Every app MUST include these branding elements in the navbar:
- **MuSigma logo** (`/musigma_logo.png`, h-8) on the left
- **App name** (bold) + **version badge** ("v1.0", muted pill)
- **"System Ready" status pill** (green dot + text) on the right
- **User avatar** ("SS" initials) + **"Sayujaya Sharma"** name
- **Tab bar** with active colored underline + 1-2 disabled placeholder tabs
- **Content width**: `max-w-[1360px] mx-auto px-6 lg:px-8`

The **colors, background, and styling** adapt to the app's theme. Examples:

#### Light Navbar (default — white background)
```jsx
<nav className="bg-white border-b border-gray-200/80 sticky top-0 z-50"
     style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.04)' }}>
  <div className="max-w-[1360px] mx-auto px-6 lg:px-8">
    <div className="flex items-center justify-between h-14">
      {/* Left: MuSigma logo + divider + app icon + name + version */}
      <div className="flex items-center gap-3">
        <img src="/musigma_logo.png" alt="MuSigma" className="h-8" />
        <div className="h-5 w-px bg-gray-200" />
        <span className="text-lg font-bold text-gray-900">AppName</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-400 font-medium">v1.0</span>
      </div>

      {/* Right: Status pill + User avatar */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
             style={{ backgroundColor: '#D1FAE5', color: '#065F46' }}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#059669' }} />
          System Ready
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
               style={{ backgroundColor: '#4F46E5' }}>SS</div>
          <span className="text-sm font-medium text-gray-700 hidden sm:block">Sayujaya Sharma</span>
        </div>
      </div>
    </div>
  </div>

  {/* Tab bar */}
  <div className="border-t border-gray-100">
    <div className="max-w-[1360px] mx-auto px-6 lg:px-8 flex items-center gap-1 -mb-px">
      <NavLink to="/" end className={({isActive}) => `tab-item ${isActive ? 'active' : ''}`}>
        Dashboard
      </NavLink>
      {/* ... more tabs ... */}
      <span className="tab-item opacity-40 cursor-not-allowed">Settings</span>
    </div>
  </div>
</nav>
```

#### Dark Navbar (for apps with warm/dark themes)
```jsx
<nav className="sticky top-0 z-50" style={{ backgroundColor: '#1C1917' }}>
  <div className="max-w-[1360px] mx-auto px-6 lg:px-8">
    <div className="flex items-center justify-between h-14">
      <div className="flex items-center gap-3">
        <img src="/musigma_logo.png" alt="MuSigma" className="h-8" />
        <div className="w-px h-6" style={{ backgroundColor: '#44403C' }} />
        <span className="text-lg font-bold text-white">AppName</span>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
              style={{ backgroundColor: '#292524', color: '#A8A29E' }}>v1.0</span>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
             style={{ backgroundColor: 'rgba(5,150,105,0.15)', color: '#34D399' }}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: '#059669' }} />
          System Ready
        </div>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold"
               style={{ background: 'linear-gradient(135deg, #B45309, #92400E)' }}>SS</div>
          <span className="text-sm font-medium text-gray-300 hidden sm:block">Sayujaya Sharma</span>
        </div>
      </div>
    </div>
  </div>
  {/* Tab bar with amber active underline instead of indigo */}
</nav>
```

**Adaptation guidance** (design is flexible, branding is not):
- 2-page app → logo + 2 tabs + 1 disabled tab — still includes status pill and avatar
- Complex app (5+ pages) → full tabs + notification bell + dropdown
- Dark theme → dark navbar background, light text — same branding elements
- Light theme → white navbar, dark text — same branding elements

### Layout
```jsx
<div className="min-h-screen" style={{ backgroundColor: '#F4F6F9' }}>
  <Navbar />
  <main className="max-w-[1360px] mx-auto px-6 lg:px-8 py-6">
    <Routes>...</Routes>
  </main>
</div>
```

### Stat Card (with icon)
```jsx
<div className="stat-card flex items-center gap-3 text-left">
  <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
    <svg className="w-5 h-5 text-indigo-600">...</svg>
  </div>
  <div>
    <p className="text-lg font-bold text-gray-900 leading-tight">42</p>
    <p className="text-[11px] text-gray-500 font-medium">Metric Label</p>
  </div>
</div>
```

### Step Card (numbered process)
```jsx
<div className="rounded-lg border border-gray-100 p-4 hover:border-gray-200 transition-colors">
  <div className="flex items-center gap-2.5 mb-2.5">
    <span className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center
                     text-white text-[11px] font-bold">01</span>
    <h3 className="text-sm font-semibold text-gray-800">Step Title</h3>
  </div>
  <p className="text-xs text-gray-500 leading-relaxed">Description text.</p>
</div>
```

### Detail Row (key-value)
```jsx
<div className="flex items-center justify-between text-sm">
  <span className="text-gray-400 text-xs">Label</span>
  <span className="text-gray-700 text-xs font-medium">Value</span>
</div>
```

### Data Table
```jsx
<table className="w-full">
  <thead>
    <tr>
      <th className="table-header">Column</th>
    </tr>
  </thead>
  <tbody>
    <tr className="table-row">
      <td className="table-cell">Value</td>
    </tr>
  </tbody>
</table>
```

### Modal
```jsx
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
  <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 border border-gray-200">
    <div className="flex items-center justify-between mb-4">
      <h2 className="text-base font-semibold text-gray-900">Title</h2>
      <button className="icon-btn">✕</button>
    </div>
    {/* Content */}
    <div className="flex justify-end gap-2 mt-6">
      <button className="btn-ghost">Cancel</button>
      <button className="btn-primary">Confirm</button>
    </div>
  </div>
</div>
```

### Empty State
```jsx
<div className="empty-state">
  <div className="empty-state-icon">
    <svg className="w-6 h-6 text-gray-300">...</svg>
  </div>
  <p className="text-sm font-medium text-gray-500">No items yet</p>
  <p className="text-xs text-gray-400 mt-1">Create your first item to get started</p>
  <button className="btn-primary mt-4">+ Add Item</button>
</div>
```

### Form
```jsx
<form className="space-y-4">
  <div>
    <label className="label">Field Name</label>
    <input className="input" placeholder="Enter value..." />
  </div>
  <div className="flex justify-end gap-2 pt-2">
    <button type="button" className="btn-ghost">Cancel</button>
    <button type="submit" className="btn-primary">Save</button>
  </div>
</form>
```

### Toast / Notification
```jsx
<div className="fixed bottom-4 right-4 z-50 bg-white rounded-xl shadow-lg border border-gray-200 px-4 py-3
                flex items-center gap-3 animate-slide-up">
  <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center">
    <svg className="w-4 h-4 text-emerald-600">✓</svg>
  </div>
  <div>
    <p className="text-sm font-medium text-gray-900">Success</p>
    <p className="text-xs text-gray-500">Item created successfully</p>
  </div>
</div>
```

---

## Frontend Page Patterns

These are common patterns — not mandatory layouts. Mix, adapt, and create new patterns as needed.

### List Page
- Header with title, item count, and primary action button
- Optional filter/search bar
- Cards (visual items) or table (data-heavy items) — choose what fits
- Empty state, loading state, error state

### Detail Page
- Navigation back to list
- Full item display with actions (edit, delete)
- Related items section if applicable

### Dashboard Page
- Summary stat cards (3-6, with icons and colored accents)
- Charts (Recharts — bar, line, pie, area — pick what tells the story)
- Recent activity or quick-access lists
- Layout: adapt grid columns to content density

### Form Page (Create/Edit)
- Clean form layout with labeled inputs and validation
- Cancel + Submit actions
- Inline modals for quick edits, full pages for complex forms

---

## API Service Pattern (Frontend)

```javascript
import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

api.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('API Error:', err.response?.data?.detail || err.message);
    return Promise.reject(err);
  }
);

export const itemsApi = {
  getAll: (params) => api.get('/items', { params }),
  getById: (id) => api.get(`/items/${id}`),
  create: (data) => api.post('/items', data),
  update: (id, data) => api.put(`/items/${id}`, data),
  delete: (id) => api.delete(`/items/${id}`),
};

export default api;
```

## Vite Proxy Config

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
});
```
