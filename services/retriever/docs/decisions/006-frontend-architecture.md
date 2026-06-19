---
adr: 6
title: Frontend Architecture
status: superseded
date: 2024-12-18
tags:
  - frontend
  - jinja2
  - htmx
  - tailwind
supersedes: null
superseded_by: "SvelteKit migration (stack migration Phase 2)"
related: [1]
---

# 006: Frontend Architecture

> **Superseded:** Frontend migrated from Jinja2/HTMX to SvelteKit + Svelte 5 runes + Skeleton UI v4.

## Status

Superseded

## Context

Need a web interface for volunteers to ask questions. Requirements:
- Mobile-friendly (volunteers on phones)
- Fast initial load
- Simple to develop and maintain
- No complex build pipeline for MVP

## Decision

**Server-rendered with Jinja2 + HTMX + Tailwind CSS**

- Jinja2 templates (built into FastAPI)
- HTMX for dynamic updates without full page reloads
- Tailwind CSS via CDN for styling

## Alternatives Considered

| Alternative | Reason Not Chosen |
|-------------|-------------------|
| React SPA | Complex build, slower initial load, overkill |
| Vue.js | Same issues as React for MVP |
| Plain HTML | Poor UX without dynamic updates |
| Next.js | Adds Node.js dependency, complexity |

## Consequences

**Easier:**
- No JavaScript build step
- Fast initial page load (server-rendered)
- SEO-friendly (if needed)
- Simple mental model

**Harder:**
- Limited interactivity compared to SPA
- HTMX learning curve (minor)
- Harder to add complex UI features later

## Implementation

```html
<!-- templates/chat.html -->
<form hx-post="/api/v1/rag/ask"
      hx-target="#answer"
      hx-indicator="#loading">
    <input type="text" name="question"
           class="w-full p-4 border rounded-lg"
           placeholder="Ask a question...">
    <button type="submit"
            class="bg-blue-500 text-white px-6 py-2 rounded-lg">
        Ask
    </button>
</form>

<div id="loading" class="htmx-indicator">
    Loading...
</div>

<div id="answer" class="mt-4">
    <!-- Answer appears here -->
</div>
```

## Responsive Design

Mobile-first with Tailwind breakpoints:

| Device | Width | Layout |
|--------|-------|--------|
| Mobile | <640px | Single column, full-width |
| Tablet | 640-1024px | Centered container |
| Desktop | >1024px | Max-width container |

## Migration Path

If complex UI needed later:
1. Keep API unchanged (already REST/JSON)
2. Build React/Vue frontend
3. Deploy as separate static site
4. Point to same API
