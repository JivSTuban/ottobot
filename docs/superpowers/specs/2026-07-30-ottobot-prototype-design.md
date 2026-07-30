# OttoBot Prototype — Design Spec

**Date:** 2026-07-30
**Status:** Approved (design), pending implementation plan
**Branch:** `design/ottobot-prototype`

## Goal

Produce a high-fidelity, animated, clickable prototype of the entire OttoBot product across its two surfaces — the **CRM web app** and the **Expo mobile app** — with an intentional, non-AI-generated design language. The prototype is built in code (not Figma) so that motion (GSAP, Reanimated), one 3D moment, video/motion-graphics, and real state transitions are genuinely functional and port directly into production.

Figma was ruled out: write-to-canvas requires a paid Full/Dev seat (user is free-tier), and GSAP/3D/video do not run in Figma regardless. Coded prototype is both cheaper and the correct medium.

## Users & product context

OttoBot is a Filipino AI outbound sales agent (Tagalog/Taglish) that books SMB appointments (dental, aesthetics, real estate). **One persona — the SMB owner/admin — uses both surfaces.** Core objects: **leads → conversations → appointments**, per **business**, driven by an AI **persona**.

- **CRM web** = the demo/investor showpiece + onboarding + the daily operator cockpit.
- **Mobile** = the owner's on-the-go view: pipeline, conversations, availability.

## Design principles (rule 7 — anti-AI-generated)

Hard constraints applied to every screen:

- **No** indigo/purple, gradients, glows/orbs, glassmorphism, centered-in-void layouts, gradient text, or abstract decorative heroes.
- **One** solid brand color (signal green) reserved for the **primary action + `booked` state only**.
- Neutral grays are **true/warm, not blue-tinted** (blue-gray is itself a tell).
- Every screen is designed from the **owner's job**, not a visual style. Restraint > decoration. Solid surfaces > glass. Meaningful color > everything glowing.
- Motion follows the emil-design-eng bar: ease-out/spring, sub-300ms, transform+opacity only, reduced-motion fallbacks. **Motion only ever communicates state.**

## Design system

### Color tokens

Semantic tokens with light-first values; dark mirrors via the same token names.

| Token | Light | Dark |
|---|---|---|
| `--bg` | `#FFFFFF` | `#0B0C0E` |
| `--surface` | `#F7F7F8` | `#141517` |
| `--surface-2` | `#F0F0F2` | `#1B1D20` |
| `--border` | `#E8E8EA` | `#232428` |
| `--text` | `#18181B` | `#FAFAFA` |
| `--text-muted` | `#6B7280` | `#9CA3AF` |
| `--accent` (Signal green) | `#059669` | `#10B981` |
| `--accent-fg` (on accent) | `#FFFFFF` | `#04231A` |

**Accent usage rule:** `--accent` appears ONLY as (a) the primary CTA fill and (b) the `booked` status. Nowhere else. No gradient, no accent text runs, no second accent.

**Status colors** (low-chroma, used as small dots/badges/left-borders only):

| Status | Hue |
|---|---|
| new | slate `#64748B` |
| qualifying | blue `#3B82F6` |
| hot | amber `#F59E0B` |
| **booked** | **signal green `--accent`** |
| escalated | red `#EF4444` |

### Typography

- **UI:** Inter, real hierarchy. Body 14px; sizes 12 / 13 / 14 / 16 / 20 / 24 / 32. Tight letter-spacing on ≥20px.
- **Data:** Inter with **tabular numerals** (`font-variant-numeric: tabular-nums`) for all metrics/counts.
- **Metrics / IDs / mono texture:** JetBrains Mono (or Geist Mono) for KPI numbers, lead IDs, timestamps — gives the "operator tool" feel.

### Spacing / radius / elevation

- **Spacing:** 4px base scale (4–64), unchanged from current.
- **Radius:** inputs 6px, cards 8px, modals/sheets 10px. No pill-everything.
- **Elevation:** flat surfaces + hairline `--border`. Near-zero shadow. A single soft shadow token (`--shadow-overlay`) used only for popovers/modals/sheets.

### Motion tokens

- Durations: `fast` 120ms, `base` 200ms, `slow` 280ms. Nothing over 300ms except the one hero beat.
- Easing: `ease-out` for enters, spring for interactive/press, `ease-in-out` for reorders.
- Properties: `transform` + `opacity` only. Always gate behind `prefers-reduced-motion` / `useReducedMotion()`.

## Motion & richness — spent intentionally

Richness concentrates into a few earned moments; everything else stays calm.

- **GSAP (web):** choreographs the demo lead→booked run, dashboard metric count-ups, and route transitions.
- **The ONE hero moment:** "**lead just booked**" — in `/demo` the OwnerPanel stage flips to `booked` with a restrained green pulse + a checkmark stroke-draw. This is the single deliberately-delightful beat.
- **The ONE richer motion/video spot:** onboarding **persona preview** — a short muted loop / Lottie motion-graphic of "your agent, live." Not repeated elsewhere.
- **3D:** at most a single `react-three-fiber` moment (dashboard empty-state OR persona reveal), only if it earns its weight; otherwise a Lottie. Never on multiple screens.
- **Mobile (Reanimated/Moti):** pipeline list reorder, pull-to-refresh, tab transitions, message-stream entrance.

## Screen specs

### Web — CRM

**1. `/demo` (investor showpiece)**
- Real industry picker (Dental / Aesthetics / Real Estate) — a product control, not a glowing hero.
- Split view: `LeadChat` (left, streaming conversation + input) and `OwnerPanel` (right, stage badge + escalation alerts + industry context).
- GSAP choreographs a scripted lead → qualifying → hot → booked run. Hosts the hero moment. Manual + scripted modes.

**2. `/onboarding` (5-step wizard)**
- Steps: account (email/password) → business basics → services/pricing → **persona preview** → confirm.
- Left step-rail (numbered, current highlighted), right content pane. Real left-aligned labels; no centered card floating in void.
- Persona-preview step carries the video/motion-graphic moment.

**3. `/dashboard` (operator cockpit — currently a stub, design real)**
- Top metric row: **Leads today · Booked · Conversion % · Avg response** — mono/tabular numbers with GSAP count-up on load/range-change.
- Live conversations list (status dot + last message + time).
- "**Needs you**" escalations panel (owner action queue).
- Availability-at-a-glance strip.
- Empty-state candidate for the optional 3D moment.

### Mobile — Expo/Tamagui (inherits the system)

**4. `/login`** — restrained redesign: solid green primary button, real labels, left-aligned, **no hero/gradient/glow/glass**. Closes the standing Task 6 (Neon+Clerk migration) design blocker.

**5. `/(tabs)/pipeline`** — sectioned lead list (new · in-progress · booked · escalated) with status dots, pull-to-refresh, animated reorder.

**6. `/(tabs)/conversation/[id]`** — message thread + lead header, inverted FlatList, streaming entrance.

**7. `/(tabs)/settings`** — availability day-grid (Mon–Sun) + business hours, default 9–5 weekdays.

## Build approach & tooling

- **Tailwind on the Vite CRM:** add Tailwind, migrate the existing `index.css` vanilla tokens → Tailwind theme + CSS variables (prerequisite for Onlook + shadcn). Preserve the same token *names* so migration is mechanical.
- **better-design (MCP):** generate the shadcn design-system/registry in our green+neutral tokens. This is the anti-slop enforcer — consistent primitives instead of improvised markup.
- **Onlook:** wire onto the CRM for visual editing of web screens (React/Tailwind only).
- **Mobile:** update Tamagui tokens to match (signal green, light-first, neutral ramp) + Moti/Reanimated for motion. Onlook/shadcn do **not** support React Native, so mobile is built in code and verified in the simulator / Expo web.
- **Motion libs:** GSAP (+ optional react-three-fiber / Lottie) on web; Reanimated/Moti on mobile.

## Implementation waves

The design is one coherent system; implementation decomposes into three ordered waves (each becomes its own plan slice):

1. **Foundation** — design tokens (light+dark) as the single source of truth; Tailwind migration on CRM; better-design shadcn registry; Onlook wired; Tamagui tokens updated on mobile; motion tokens + reduced-motion utilities. Exit: token parity across both surfaces, one shared design language, Storybook/registry of primitives.
2. **Web screens** — `/demo` (+ hero moment), `/onboarding` (+ persona motion spot), `/dashboard` (real cockpit). Exit: all three clickable with GSAP state choreography, light+dark.
3. **Mobile screens** — `/login` (closes Task 6), `/pipeline`, `/conversation/[id]`, `/settings`, with Reanimated/Moti. Exit: all four running in simulator, inheriting Wave-1 tokens.

## Success criteria

- All 7 screens exist as clickable, animated prototypes in light-first (dark supported).
- Zero items from the AI-Generated Design Tells checklist present; passes the pre-ship checklist.
- Signal green appears only on primary actions + `booked` state.
- Every animation ≤300ms (except the one hero beat), transform+opacity, reduced-motion safe.
- Web screens editable in Onlook; primitives sourced from the better-design/shadcn registry.
- Mobile `/login` resolves the Task 6 blocker (restrained, no gradient/glow/glass).
- Approved screens are real code that ports into production (not throwaway).

## Out of scope (YAGNI)

- Backend wiring / real data (prototype uses fixtures + the existing demo WebSocket where present).
- Auth flows beyond the login screen's visual design (Clerk plumbing already exists).
- Marketing site, billing, multi-account/agency surfaces (Phase 07).
- More than one 3D moment and one video moment.

## Verification / testing

- Per-screen visual verification via screenshots (web: Onlook/browser; mobile: simulator) against this spec.
- Reduced-motion pass: every screen re-checked with reduced motion enabled — no motion-dependent information loss.
- Anti-AI checklist run before each wave ships (vault `Reference/AI-Generated Design Tells.md`).
- Light + dark parity check on every web screen.
