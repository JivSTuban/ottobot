# OttoBot Prototype — Wave 1: Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the shared design-system foundation (tokens, Tailwind+shadcn on web, motion utilities, Tamagui token parity on mobile) that Waves 2 (web screens) and 3 (mobile screens) build on.

**Architecture:** A single canonical, framework-free token module holds every color/type/spacing/motion value (light+dark). The web app (Vite+React) generates CSS variables from it and wires Tailwind + shadcn/ui to those variables; the mobile app (Expo+Tamagui) maps the same values into its Tamagui config. Cross-app parity is enforced by a vitest test that imports both apps' pure token modules in Node (side-stepping the Vite and Metro bundlers, neither of which likes cross-root imports).

**Tech Stack:** Web — Vite 8, React 19, TypeScript 6, Tailwind (via shadcn init), shadcn/ui, vitest + @testing-library/react. Mobile — Expo 56, Tamagui 2.6. Optional — better-design MCP (design principles + review rules).

## Global Constraints

Copied verbatim from `docs/superpowers/specs/2026-07-30-ottobot-prototype-design.md`. Every task's requirements implicitly include these.

- Accent = **Signal green**, light `#059669` / dark `#10B981`. Appears ONLY as (a) primary CTA fill and (b) `booked` status. No second accent, no gradient, no accent text runs.
- **Forbidden (rule 7):** indigo/purple, gradients, glows/orbs, glassmorphism, centered-in-void, gradient text, abstract decorative heroes.
- Neutrals are **true/warm gray, NOT blue-tinted**. Light: bg `#FFFFFF`, surface `#F7F7F8`, surface-2 `#F0F0F2`, border `#E8E8EA`, text `#18181B`, text-muted `#6B7280`. Dark: bg `#0B0C0E`, surface `#141517`, surface-2 `#1B1D20`, border `#232428`, text `#FAFAFA`, text-muted `#9CA3AF`.
- Status hues (dots/badges only): new `#64748B`, qualifying `#3B82F6`, hot `#F59E0B`, booked = accent, escalated `#EF4444`.
- Typography: Inter (UI) + tabular numerals for data + JetBrains Mono for metrics/IDs.
- Radius: input 6px, card 8px, modal 10px. Elevation: flat + hairline borders; one soft shadow token for overlays only.
- Motion: durations fast 120ms / base 200ms / slow 280ms; nothing >300ms except the single hero beat (not in this wave); `transform`+`opacity` only; always reduced-motion safe.
- Theme: **light-first**, dark supported via identical token keys.

---

### Task 1: Canonical design tokens + CSS-variable generator (web source of truth)

**Files:**
- Create: `frontend/src/design/tokens.ts`
- Create: `frontend/src/design/cssVars.ts`
- Test: `frontend/src/design/tokens.test.ts`

**Interfaces:**
- Produces: `export const tokens: { light: TokenSet; dark: TokenSet }` where `TokenSet = { bg, surface, surface2, border, text, textMuted, accent, accentFg, statusNew, statusQualifying, statusHot, statusBooked, statusEscalated: string }` (all `#rrggbb`). Also `export const radius = { input: 6, card: 8, modal: 10 }` and `export const motion = { fast: 120, base: 200, slow: 280 }` (ms).
- Produces: `export function cssVars(set: TokenSet): string` → newline-joined `--token-name: value;` lines using kebab-case names (`--surface-2`, `--text-muted`, `--accent-fg`, `--status-booked`, …).

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/design/tokens.test.ts
import { describe, it, expect } from "vitest";
import { tokens, cssVars } from "./tokens.ts";
import { cssVars as cssVarsFn } from "./cssVars.ts";

describe("design tokens", () => {
  it("locks the signal-green accent for both themes", () => {
    expect(tokens.light.accent).toBe("#059669");
    expect(tokens.dark.accent).toBe("#10B981");
  });

  it("uses non-blue-tinted neutrals in light", () => {
    expect(tokens.light.bg).toBe("#FFFFFF");
    expect(tokens.light.border).toBe("#E8E8EA");
  });

  it("keeps identical token keys across light and dark (parity)", () => {
    expect(Object.keys(tokens.light).sort()).toEqual(Object.keys(tokens.dark).sort());
  });

  it("maps booked status to the accent", () => {
    expect(tokens.light.statusBooked).toBe(tokens.light.accent);
  });

  it("emits kebab-case CSS variables", () => {
    const out = cssVarsFn(tokens.light);
    expect(out).toContain("--accent: #059669;");
    expect(out).toContain("--surface-2: #F0F0F2;");
    expect(out).toContain("--text-muted: #6B7280;");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/design/tokens.test.ts`
Expected: FAIL — cannot resolve `./tokens.ts` / `./cssVars.ts`.

- [ ] **Step 3: Write the token module**

```ts
// frontend/src/design/tokens.ts
export interface TokenSet {
  bg: string; surface: string; surface2: string; border: string;
  text: string; textMuted: string; accent: string; accentFg: string;
  statusNew: string; statusQualifying: string; statusHot: string;
  statusBooked: string; statusEscalated: string;
}

const ACCENT_LIGHT = "#059669";
const ACCENT_DARK = "#10B981";

export const tokens: { light: TokenSet; dark: TokenSet } = {
  light: {
    bg: "#FFFFFF", surface: "#F7F7F8", surface2: "#F0F0F2", border: "#E8E8EA",
    text: "#18181B", textMuted: "#6B7280", accent: ACCENT_LIGHT, accentFg: "#FFFFFF",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: ACCENT_LIGHT, statusEscalated: "#EF4444",
  },
  dark: {
    bg: "#0B0C0E", surface: "#141517", surface2: "#1B1D20", border: "#232428",
    text: "#FAFAFA", textMuted: "#9CA3AF", accent: ACCENT_DARK, accentFg: "#04231A",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: ACCENT_DARK, statusEscalated: "#EF4444",
  },
};

export const radius = { input: 6, card: 8, modal: 10 } as const;
export const motion = { fast: 120, base: 200, slow: 280 } as const;

// Re-export so tests importing from "./tokens" also get cssVars.
export { cssVars } from "./cssVars.ts";
```

```ts
// frontend/src/design/cssVars.ts
import type { TokenSet } from "./tokens.ts";

const KEBAB: Record<keyof TokenSet, string> = {
  bg: "bg", surface: "surface", surface2: "surface-2", border: "border",
  text: "text", textMuted: "text-muted", accent: "accent", accentFg: "accent-fg",
  statusNew: "status-new", statusQualifying: "status-qualifying", statusHot: "status-hot",
  statusBooked: "status-booked", statusEscalated: "status-escalated",
};

export function cssVars(set: TokenSet): string {
  return (Object.keys(set) as (keyof TokenSet)[])
    .map((k) => `--${KEBAB[k]}: ${set[k]};`)
    .join("\n");
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/design/tokens.test.ts`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/design/tokens.ts frontend/src/design/cssVars.ts frontend/src/design/tokens.test.ts
git commit -m "feat(design): canonical token module + CSS-var generator (signal-green, light+dark)"
```

---

### Task 2: Tailwind + shadcn/ui on the Vite CRM, themed to tokens

**Files:**
- Create: `frontend/tailwind.config.ts`, `frontend/postcss.config.js`, `frontend/components.json`, `frontend/src/lib/utils.ts`
- Create: `frontend/src/styles/tokens.css` (emitted `:root` + `.dark` variable blocks)
- Create: `frontend/src/components/ui/button.tsx`, `.../badge.tsx`, `.../card.tsx`, `.../input.tsx` (via shadcn CLI)
- Modify: `frontend/src/index.css` (add Tailwind entry + `@import "./styles/tokens.css"`)
- Modify: `frontend/src/main.tsx` (ensure `index.css` imported — likely already)
- Test: `frontend/src/components/ui/button.test.tsx`

**Interfaces:**
- Consumes: token CSS variable names from Task 1 (`--accent`, `--bg`, `--surface`, `--border`, `--text`, `--status-*`).
- Produces: shadcn primitives whose `primary` variant resolves to `--accent`. Tailwind theme exposes `bg-background`, `text-foreground`, `border-border`, `bg-primary`, `text-primary-foreground`, and status utilities `text-status-booked` etc.

- [ ] **Step 1: Scaffold Tailwind + shadcn (setup — no test yet)**

Run (from `frontend/`), following the shadcn Vite guide (https://ui.shadcn.com/docs/installation/vite); accept defaults, choose CSS variables = yes, base color = neutral:
```bash
cd frontend
npx shadcn@latest init
npx shadcn@latest add button badge card input
```
This creates `tailwind.config.ts`, `postcss.config.js`, `components.json`, `src/lib/utils.ts`, and `src/components/ui/*`. If the CLI writes tokens into `index.css`, that's expected — we override them in Step 2.

- [ ] **Step 2: Generate `tokens.css` from the canonical module and map Tailwind theme to our variables**

Create `frontend/src/styles/tokens.css` (paste the output of `cssVars(tokens.light)` under `:root` and `cssVars(tokens.dark)` under `.dark`; to generate it run `cd frontend && npx tsx -e "import {tokens,cssVars} from './src/design/tokens.ts'; console.log(':root{\n'+cssVars(tokens.light)+'\n}\n.dark{\n'+cssVars(tokens.dark)+'\n}')"`):
```css
:root {
  --bg: #FFFFFF;
  --surface: #F7F7F8;
  --surface-2: #F0F0F2;
  --border: #E8E8EA;
  --text: #18181B;
  --text-muted: #6B7280;
  --accent: #059669;
  --accent-fg: #FFFFFF;
  --status-new: #64748B;
  --status-qualifying: #3B82F6;
  --status-hot: #F59E0B;
  --status-booked: #059669;
  --status-escalated: #EF4444;
  --radius: 0.5rem; /* 8px card default */
}
.dark {
  --bg: #0B0C0E;
  --surface: #141517;
  --surface-2: #1B1D20;
  --border: #232428;
  --text: #FAFAFA;
  --text-muted: #9CA3AF;
  --accent: #10B981;
  --accent-fg: #04231A;
  --status-new: #64748B;
  --status-qualifying: #3B82F6;
  --status-hot: #F59E0B;
  --status-booked: #10B981;
  --status-escalated: #EF4444;
}
```

In `frontend/tailwind.config.ts`, extend the theme to reference the variables (replace the shadcn defaults so `primary` = accent):
```ts
// inside theme.extend.colors
colors: {
  background: "var(--bg)",
  foreground: "var(--text)",
  muted: { DEFAULT: "var(--surface)", foreground: "var(--text-muted)" },
  border: "var(--border)",
  primary: { DEFAULT: "var(--accent)", foreground: "var(--accent-fg)" },
  surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)" },
  status: {
    new: "var(--status-new)", qualifying: "var(--status-qualifying)",
    hot: "var(--status-hot)", booked: "var(--status-booked)",
    escalated: "var(--status-escalated)",
  },
},
```
Add `@import "./styles/tokens.css";` at the top of `frontend/src/index.css` (after the Tailwind entry line).

- [ ] **Step 3: Write the failing test (accent discipline)**

```tsx
// frontend/src/components/ui/button.test.tsx
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Button } from "./button.tsx";

describe("Button accent discipline", () => {
  it("primary variant uses the accent (bg-primary)", () => {
    const { getByRole } = render(<Button>Book</Button>);
    expect(getByRole("button").className).toContain("bg-primary");
  });

  it("secondary/ghost variants never use the accent fill", () => {
    const { getByRole } = render(<Button variant="secondary">Cancel</Button>);
    expect(getByRole("button").className).not.toContain("bg-primary");
  });
});
```

- [ ] **Step 4: Run to verify it fails, then passes**

Run: `cd frontend && npx vitest run src/components/ui/button.test.tsx`
Expected: FAIL first (shadcn default primary may map elsewhere); after Step 2's theme mapping ensures the `default` variant class is `bg-primary`, re-run → PASS. If shadcn's button variant is named `default` not `primary`, keep the class `bg-primary` on that variant.

- [ ] **Step 5: Visually verify the dev server renders themed**

Run: `cd frontend && npm run dev`, open the app, confirm a `<Button>` renders green and toggling `.dark` on `<html>` swaps neutrals. No console errors.

- [ ] **Step 6: Commit**

```bash
git add frontend/tailwind.config.ts frontend/postcss.config.js frontend/components.json frontend/src/lib/utils.ts frontend/src/styles/tokens.css frontend/src/components/ui frontend/src/index.css frontend/src/components/ui/button.test.tsx
git commit -m "feat(design): Tailwind + shadcn/ui themed to signal-green tokens (light+dark)"
```

---

### Task 3: Motion tokens + reduced-motion-safe helpers (web)

**Files:**
- Create: `frontend/src/design/motion.ts`
- Test: `frontend/src/design/motion.test.ts`

**Interfaces:**
- Consumes: `motion` durations from Task 1.
- Produces: `export const easing = { out: "cubic-bezier(0.16,1,0.3,1)", inOut: "cubic-bezier(0.65,0,0.35,1)" }`; `export function prefersReducedMotion(): boolean`; `export function transition(prop: string, speed?: keyof typeof motion): string` → e.g. `"transform 200ms cubic-bezier(0.16,1,0.3,1)"`, returning `"none"` when reduced motion is on.

- [ ] **Step 1: Write the failing test**

```ts
// frontend/src/design/motion.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { transition, easing } from "./motion.ts";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {},
  }));
}

describe("motion helpers", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("builds a transform+ease-out transition under 300ms by default", () => {
    mockReducedMotion(false);
    expect(transition("transform")).toBe(`transform 200ms ${easing.out}`);
  });

  it("honors the fast token", () => {
    mockReducedMotion(false);
    expect(transition("opacity", "fast")).toBe(`opacity 120ms ${easing.out}`);
  });

  it("returns 'none' when reduced motion is requested", () => {
    mockReducedMotion(true);
    expect(transition("transform")).toBe("none");
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd frontend && npx vitest run src/design/motion.test.ts`
Expected: FAIL — cannot resolve `./motion.ts`.

- [ ] **Step 3: Implement**

```ts
// frontend/src/design/motion.ts
import { motion } from "./tokens.ts";

export const easing = {
  out: "cubic-bezier(0.16,1,0.3,1)",
  inOut: "cubic-bezier(0.65,0,0.35,1)",
} as const;

export function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function"
    && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function transition(prop: string, speed: keyof typeof motion = "base"): string {
  if (prefersReducedMotion()) return "none";
  return `${prop} ${motion[speed]}ms ${easing.out}`;
}
```

- [ ] **Step 4: Run to verify it passes**

Run: `cd frontend && npx vitest run src/design/motion.test.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/design/motion.ts frontend/src/design/motion.test.ts
git commit -m "feat(design): web motion tokens + reduced-motion-safe transition helper"
```

---

### Task 4: Mobile Tamagui token parity

**Files:**
- Create: `mobile/theme/tokens.ts` (pure values, NO tamagui import)
- Modify: `mobile/tamagui.config.ts` (consume `mobile/theme/tokens.ts` for color tokens + light/dark themes; light default)
- Test: `frontend/src/design/tokens.parity.test.ts` (runs in Node via vitest, imports both apps' pure token modules)

**Interfaces:**
- Consumes: canonical values must equal `frontend/src/design/tokens.ts`.
- Produces: `export const mobileTokens: { light: {...}; dark: {...} }` with the SAME keys/hex as web `tokens`. Tamagui config maps these into `createTokens` colors and `themes.light` (default) / `themes.dark`.

- [ ] **Step 1: Write the failing parity test**

```ts
// frontend/src/design/tokens.parity.test.ts
import { describe, it, expect } from "vitest";
import { tokens } from "./tokens.ts";
import { mobileTokens } from "../../../mobile/theme/tokens.ts";

describe("web ↔ mobile token parity", () => {
  it("light values match exactly", () => {
    expect(mobileTokens.light).toEqual(tokens.light);
  });
  it("dark values match exactly", () => {
    expect(mobileTokens.dark).toEqual(tokens.dark);
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd frontend && npx vitest run src/design/tokens.parity.test.ts`
Expected: FAIL — cannot resolve `../../../mobile/theme/tokens.ts`.

- [ ] **Step 3: Create the mobile token mirror**

```ts
// mobile/theme/tokens.ts  — pure values; keep in sync with frontend/src/design/tokens.ts
export const mobileTokens = {
  light: {
    bg: "#FFFFFF", surface: "#F7F7F8", surface2: "#F0F0F2", border: "#E8E8EA",
    text: "#18181B", textMuted: "#6B7280", accent: "#059669", accentFg: "#FFFFFF",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: "#059669", statusEscalated: "#EF4444",
  },
  dark: {
    bg: "#0B0C0E", surface: "#141517", surface2: "#1B1D20", border: "#232428",
    text: "#FAFAFA", textMuted: "#9CA3AF", accent: "#10B981", accentFg: "#04231A",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: "#10B981", statusEscalated: "#EF4444",
  },
} as const;
```

- [ ] **Step 4: Run to verify parity passes**

Run: `cd frontend && npx vitest run src/design/tokens.parity.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 5: Wire tokens into `mobile/tamagui.config.ts`**

Map `mobileTokens` into the Tamagui config: define `createTokens({ color: { bg, surface, surface2, border, text, textMuted, accent, accentFg, statusNew, ... } })` from `mobileTokens.light` for the shared palette, then `themes: { light: {...mobileTokens.light}, dark: {...mobileTokens.dark} }`, and set light as the default theme. Replace any existing `#6366f1` indigo references with `accent`.

- [ ] **Step 6: Verify mobile still type-checks**

Run: `cd mobile && npx tsc --noEmit`
Expected: no type errors from the config change. (If `tsc` is not configured, run `cd mobile && npx expo-doctor` or start `npx expo start` and confirm no bundling error on load.)

- [ ] **Step 7: Commit**

```bash
git add mobile/theme/tokens.ts mobile/tamagui.config.ts frontend/src/design/tokens.parity.test.ts
git commit -m "feat(design): mobile Tamagui token parity with web (signal-green, light-first)"
```

---

### Task 5: better-design MCP wiring + design-guardrail doc (optional — needs API key)

**Files:**
- Modify/Create: project MCP config (`.mcp.json` at repo root)
- Create: `docs/design/guardrails.md`

**Interfaces:**
- Consumes: an API key from https://better-design.com (user-provided). If no key is available, SKIP the MCP wiring and still author `guardrails.md` from the vault reference — the foundation does not depend on this task.

- [ ] **Step 1: Add the better-design MCP server (only if the user provides an API key)**

Create/merge `.mcp.json` at repo root:
```json
{
  "mcpServers": {
    "better-design": {
      "url": "https://better-design.com/api/mcp",
      "headers": { "Authorization": "Bearer ${BETTER_DESIGN_API_KEY}" }
    }
  }
}
```
Then restart Claude Code and confirm the `better-design` tools load (`resolve-design-system`, `get-ui-principle`, `get-review-rules`).

- [ ] **Step 2: Capture the confident-operator guardrail into the repo**

If better-design loaded: call `resolve-design-system` for "dense data-forward operator CRM, restraint, one accent" (expect it to resolve to Linear/Vercel-family), then `get-ui-principle` for hierarchy/spacing/motion/forms and `get-review-rules`, and distill the results into `docs/design/guardrails.md`.
If better-design is unavailable: author `docs/design/guardrails.md` directly from the vault reference `Reference/AI-Generated Design Tells.md` — the 65 tells + pre-ship checklist — plus this spec's Design Principles section. Either way the doc MUST contain: the accent-discipline rule, the forbidden-list, the neutral-gray rule, the motion rule, and a per-wave pre-ship checklist.

- [ ] **Step 3: Commit**

```bash
git add .mcp.json docs/design/guardrails.md
git commit -m "chore(design): wire better-design MCP (optional) + repo design guardrail doc"
```

---

## Self-Review

**1. Spec coverage:** Foundation section of the spec → Task 1 (tokens), Task 2 (Tailwind+shadcn), Task 3 (motion tokens+reduced-motion), Task 4 (Tamagui parity), Task 5 (better-design + guardrail). Onlook was dropped (Next.js-only; incompatible with the Vite CRM) — noted here as an intentional deviation from the spec's tooling list; the design outcome is unaffected. GSAP / react-three-fiber / Lottie installs deferred to Wave 2 (they are applied on the web screens, not the foundation). Mobile Reanimated/Moti deferred to Wave 3.

**2. Placeholder scan:** No TBD/TODO. Every code + test step contains real content. Task 5 is explicitly conditional (API key) with a fully-specified fallback, not a placeholder.

**3. Type consistency:** `TokenSet` keys are identical across `tokens.ts`, `cssVars.ts` (`KEBAB` map), and `mobile/theme/tokens.ts`; the parity test enforces this at test time. `motion` keys (`fast|base|slow`) are consistent between `tokens.ts` and `motion.ts`. `cssVars` is defined in `cssVars.ts` and re-exported from `tokens.ts`; both import sites in the tests are covered.

## Deviations from spec (flagged)

- **Onlook dropped.** The OSS editor is Next.js+Tailwind only; the CRM is Vite+React and must stay so (prototype ports back to prod). better-design (framework-agnostic MCP) plus our own token/shadcn system deliver the same anti-slop outcome. Revisit Onlook only if a separate Next.js sandbox is ever stood up.
- **better-design needs a paid/free API key** from better-design.com and is therefore optional in Task 5, with a vault-reference fallback so the foundation never blocks on it.

## Next waves (separate plans, authored after this lands)

- **Wave 2 — Web screens:** `/demo` (+ hero "booked" beat), `/onboarding` (+ persona motion/video spot), `/dashboard` (real cockpit). Adds GSAP (+ optional r3f/Lottie). Consumes Task 1–3 APIs.
- **Wave 3 — Mobile screens:** `/login` (closes Task 6 of the Neon+Clerk migration), `/pipeline`, `/conversation/[id]`, `/settings`. Adds Reanimated/Moti. Consumes Task 4 tokens.
