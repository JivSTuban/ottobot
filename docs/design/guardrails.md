# OttoBot Design Guardrails

**Purpose:** Pre-ship checklist and concrete constraints for all screen builds (Waves 2–3). Prevents AI-generated aesthetic tells and enforces the spec's design principles.

---

## 1. Accent Discipline Rule

Signal green (`--accent`) appears **ONLY** in these two contexts:

- The **primary CTA fill** (buttons, actionable elements that drive core tasks)
- The **`booked` status indicator** (lead/appointment closed won)

**No exceptions:**
- ❌ Green text runs
- ❌ Green hover/focus states (use shift in darkness/lightness only, or outline)
- ❌ Second accent color
- ❌ Green gradients or glows
- ❌ Green badges/status dots (except `booked`)

**Token values:**
- Light mode: `--accent` = `#059669` (apply on solid surfaces)
- Dark mode: `--accent` = `#10B981`
- On-accent text: `--accent-fg` = `#FFFFFF` (light) / `#04231A` (dark)

Other statuses use low-chroma, small indicators only:
- `new` → slate `#64748B`
- `qualifying` → blue `#3B82F6`
- `hot` → amber `#F59E0B`
- `escalated` → red `#EF4444`

---

## 2. Forbidden List (Rule 7 — Anti-AI-Generated Tells)

Absolute no-fly zone for all surfaces:

- **Indigo/purple** — primary symptom of "AI-generated SaaS"
- **Gradients** — any color gradient, including subtle ones
- **Glows/orbs/blurred bloom effects** — kills hierarchy
- **Glassmorphism** — transparent cards, blur, thin white borders stacked
- **Centered-in-void layouts** — sections/cards floating with no spatial logic
- **Gradient text** — reduces contrast, competes with actions
- **Abstract decorative heroes** — 3D orbs, rings, ribbons, blobs unrelated to product

---

## 3. Neutral-Gray Rule

Grays used for text, borders, surfaces, and muted states **must be true or warm-tinted, never blue-tinted.**

**Approved neutral tokens (from spec):**

| Token | Light | Dark |
|---|---|---|
| `--bg` | `#FFFFFF` | `#0B0C0E` |
| `--surface` | `#F7F7F8` | `#141517` |
| `--surface-2` | `#F0F0F2` | `#1B1D20` |
| `--border` | `#E8E8EA` | `#232428` |
| `--text` | `#18181B` | `#FAFAFA` |
| `--text-muted` | `#6B7280` | `#9CA3AF` |

**Check before shipping:** all grays in DevTools must match tokens above (or be derived via opacity). If a gray feels "cool" or "digital blue," it's wrong.

---

## 4. Motion Rule

All motion serves a single purpose: **communicate state change or guide attention.** Decorative motion is forbidden.

**Constraints:**
- **Duration:** `fast` 120ms, `base` 200ms, `slow` 280ms. **Nothing over 300ms except the one hero beat** ("lead booked" in `/demo`).
- **Easing:** ease-out (enters), spring (interactive/press), ease-in-out (reorders).
- **Properties:** `transform` + `opacity` only. No color shifts, size jumps, shadow blooms, or complex nested timelines.
- **Reduced motion:** Every transition must respect `prefers-reduced-motion` / `useReducedMotion()`. Motion-dependent information (e.g., state conveyed only by a color fade) is forbidden.

**Example:** Button press = `scale(0.98)` + `opacity(0.85)` on press, 120ms ease-out; release = spring back to 1.0 / 1.0 in 200ms, spring easing.

---

## 5. Critical shadcn/Tailwind Warning

**shadcn v4 injected indigo-tinted oklch defaults that are not yet rendered in this project:**

- `--sidebar-primary` (indigo)
- `--ring` (indigo)
- `--chart-1` through `--chart-5` (indigo-leaning hues)
- `--primary`, `--secondary` (indigo-tinted)

**Before building any screen with sidebar, chart, form ring, or primary button:**

1. **Override every one of these tokens** in your Tailwind config or local CSS to our palette:
   - `--primary` → `--accent` (`#059669` light / `#10B981` dark)
   - `--ring` → neutral `--border`
   - `--sidebar-primary` → if rendered, must be `--text` (not indigo)
   - `--chart-*` → use actual data-driven colors from the spec; if uncertain, ask before shipping

2. **Test in DevTools:** inspect every `:focus-ring`, `<SidebarNav>`, `<Chart>`, and `<Button>` to confirm no indigo reaches the screen.

3. **Fallback:** if a shadcn component has indigo baked in and cannot be overridden, replace it rather than ship indigo.

---

## 6. Per-Wave Pre-Ship Checklist

Run **before merging** each screen. Based on the vault reference's 86-point checklist, distilled for OttoBot.

### Purpose & Clarity
- [ ] User persona and primary task identifiable in the first 3s?
- [ ] Screen title / state clear (not ambiguous)?
- [ ] No marketing speak; copy is product-specific, not "Revolutionize your workflow"?

### Hierarchy & Information Architecture
- [ ] One obvious primary action (green button or the job the user came to do)?
- [ ] Secondary/tertiary actions visually recessed?
- [ ] Not everything in a card ("container soup")?
- [ ] Data organized by user decision/workflow, not feature parity?

### Design System Adherence
- [ ] All colors from the token palette (no arbitrary hex)?
- [ ] Grays are warm/true, not blue-tinted?
- [ ] Signal green appears only on primary CTA + `booked` status?
- [ ] No gradients, glows, orbs, glassmorphism, centered-in-void, gradient text?
- [ ] Borders use `--border` token; shadows use `--shadow-overlay` (if any)?
- [ ] Radius follows spec: inputs 6px, cards 8px, modals 10px?
- [ ] All shadcn overrides applied (no indigo in sidebar/chart/ring)?

### Typography & Readability
- [ ] Body text 14px, hierarchy sizes (12–32) applied correctly?
- [ ] Line length reasonable (not 1000px+ measure)?
- [ ] Tab-align numerals on metrics / KPIs (`font-variant-numeric: tabular-nums`)?
- [ ] Sufficient contrast (WCAG AA minimum 4.5:1 body text)?

### Motion & Interaction
- [ ] All animations ≤300ms (except one hero beat in `/demo`)?
- [ ] Easing: ease-out/spring, no bezier surprises?
- [ ] Transform + opacity only (no color/shadow/size shifts)?
- [ ] Reduced-motion fallback present and tested?
- [ ] Loading/empty/error/success states designed (not omitted)?

### Interaction Completeness
- [ ] Button hover/focus/disabled states distinct?
- [ ] Form validation shown (not silent until submit)?
- [ ] Destructive actions require confirmation?
- [ ] Undo available for risky operations?
- [ ] Keyboard navigation works (tab/Enter/Escape)?
- [ ] Focus visible (`:focus-visible` not removed)?

### Accessibility
- [ ] Light + dark modes tested and pairing checked?
- [ ] No color-only state indicators (e.g., red dot alone doesn't convey error)?
- [ ] Sufficient contrast verified (DevTools, Lighthouse, or WCAG checker)?
- [ ] Images alt-text present (if any)?
- [ ] Headings in logical order (h1 → h2 → h3)?

### Responsive & Mobile
- [ ] Tested on mobile (375px), tablet (768px), desktop (1440px)?
- [ ] Reflows, doesn't just shrink?
- [ ] Touch targets ≥48px?
- [ ] Text enlargement to 200% doesn't break layout?

### Product Quality
- [ ] Sample data is coherent and realistic (not "Lorem" or placeholder)?
- [ ] Charts (if present) answer a real user question?
- [ ] Tables scannable in 3–5s (not 30+ columns)?
- [ ] User can complete the core task in this screen without friction?

### Anti-AI Verification
- [ ] No purple/indigo/blue gradients?
- [ ] No abstract decorative elements unrelated to the product?
- [ ] No fake data (10,000+ testimonials, obviously AI-generated names)?
- [ ] No everything-is-centered void layout?
- [ ] No oversized typography as a substitute for hierarchy?
- [ ] Could this screen belong to 100 other SaaS products? If yes, redesign from the owner's job.

---

## How to Use This Document

**For screen builds (Wave 2–3):**

1. Before opening a design tool or starting code, read the **Accent Discipline Rule** (§1) and **Forbidden List** (§2).
2. Design the layout and information hierarchy.
3. Build with tokens from **§3** (Neutral Grays) and the spec's full palette.
4. Add motion thoughtfully, respecting **§4** (Motion Rule).
5. If using shadcn/Tailwind, apply **§5** (shadcn Warning) *before* rendering.
6. Before merge, run **§6** (Per-Wave Pre-Ship Checklist) as a checkbox list.

**For code review:**

Apply the pre-ship checklist to each PR. If any checkbox fails, request changes.

---

## Sources

- **Spec:** `docs/superpowers/specs/2026-07-30-ottobot-prototype-design.md` (Design Principles, Design System sections)
- **Anti-AI Reference:** `/Users/jivtuban/Second Brain/Reference/AI-Generated Design Tells.md` (65 tells + pre-ship checklist, adapted)
