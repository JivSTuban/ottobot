# OttoBot Prototype — Wave 2: Web Screens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the three CRM web surfaces — `/demo`, `/onboarding`, `/dashboard` — into high-fidelity, animated, clickable screens built on the Wave 1 design system (signal-green, light-first), with GSAP motion that communicates state and exactly one hero "booked" beat.

**Architecture:** Screens consume the Wave 1 token/motion foundation. First a small foundation task hardens the theme (override shadcn's leftover indigo oklch defaults, add GSAP + a reduced-motion-safe GSAP bridge). Then each screen is migrated/built onto shadcn primitives + our tokens: the existing `/demo` and `/onboarding` components are migrated off now-dead legacy CSS vars, and `/dashboard` (a stub today) is built net-new. Logic and design-invariants are pinned by tests; pixel layout and GSAP timelines are implementer-crafted to a precise contract and verified against screenshots + `docs/design/guardrails.md`.

**Tech Stack:** Vite 8, React 19.2, TypeScript 6, Tailwind v4 + shadcn/ui (base-nova, `@base-ui/react`), GSAP + `@gsap/react`, vitest + @testing-library/react. Consumes Wave 1: `frontend/src/design/{tokens,cssVars,motion}.ts`, `frontend/src/styles/tokens.css`.

## Global Constraints

Copied from `docs/superpowers/specs/2026-07-30-ottobot-prototype-design.md` and `docs/design/guardrails.md`. Every task implicitly includes these; run the guardrails per-screen pre-ship checklist before marking any screen task done.

- Accent = Signal green (`--accent`, `bg-primary`), light `#059669` / dark `#10B981`, ONLY on the primary CTA and the `booked` state. No second accent, no gradient, no accent text runs.
- Forbidden (rule 7): indigo/purple, gradients, glows/orbs, glassmorphism, centered-in-void, gradient text, abstract decorative heroes. NO indigo hue (oklch hue ≈ 264) may reach any rendered element.
- Neutrals via tokens only (`--bg`,`--surface`,`--surface-2`,`--border`,`--text`,`--text-muted`) — never blue-tinted, never the removed legacy vars (`--bg-dominant`,`--bg-secondary`,`--text-primary`).
- Motion: GSAP/transition helpers, ease-out/spring, **≤300ms and transform+opacity only**, EXCEPT the single hero "booked" beat in `/demo` (may run longer, still transform+opacity). Every animation MUST have a `prefers-reduced-motion` fallback that renders the final state with no motion.
- Status colors (dots/badges only): new `--status-new`, qualifying `--status-qualifying`, hot `--status-hot`, booked `--status-booked` (= accent), escalated `--status-escalated`.
- Typography: Inter (UI), tabular numerals for all metrics, JetBrains/Geist Mono for KPI numbers/IDs/timestamps.
- Theme: light-first; every screen must be correct in light AND dark (toggle `.dark` on `<html>`).
- Existing types (do not redefine): `Stage`, `LeadStatus` (`"new"|"qualifying"|"hot"|"booked"`), `Message`, `stageToLeadStatus(stage)`, and `useWebSocket(url): UseWebSocketReturn` with `{ tokens, stage, escalated, systemAlert, escalationAlert, send, sendOutboundTrigger, messages, wsError }`.

---

### Task 1: Wave-2 foundation — kill leftover indigo, add GSAP + reduced-motion bridge

**Files:**
- Modify: `frontend/src/index.css` (override shadcn `@layer base` oklch defaults, esp. `.dark --sidebar-primary`)
- Modify: `frontend/package.json` (add `gsap`, `@gsap/react`)
- Create: `frontend/src/motion/useAnimate.ts` (GSAP bridge honoring reduced motion)
- Test: `frontend/src/motion/useAnimate.test.ts`, `frontend/src/design/no-indigo-oklch.test.ts`

**Interfaces:**
- Produces: `export function useAnimate(): { enabled: boolean; ctx: <T>(fn: () => T) => T | void }` — `enabled` is `false` when `prefersReducedMotion()` (from Wave 1 `design/motion.ts`) is true; `ctx(fn)` runs `fn` inside a `gsap.context` when enabled, and is a no-op returning `undefined` when disabled. (Screens call `useAnimate` to gate every timeline.)

- [ ] **Step 1: Install GSAP**

Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npm install gsap @gsap/react`
Verify `gsap` and `@gsap/react` appear in `package.json` dependencies.

- [ ] **Step 2: Write the failing no-indigo-oklch guard test**

```ts
// frontend/src/design/no-indigo-oklch.test.ts
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const indexCss = readFileSync(
  fileURLToPath(new URL("../index.css", import.meta.url)), "utf8",
);

describe("no leftover indigo oklch defaults", () => {
  // shadcn v4 ships `.dark --sidebar-primary: oklch(0.488 0.243 264.376)` — hue 264 = indigo.
  it("has no oklch color with an indigo/violet hue (250–290)", () => {
    const matches = [...indexCss.matchAll(/oklch\(\s*[\d.]+\s+[\d.]+\s+([\d.]+)/g)];
    const indigo = matches.map((m) => Number(m[1])).filter((h) => h >= 250 && h <= 290);
    expect(indigo).toEqual([]);
  });
});
```

- [ ] **Step 3: Run it to verify it fails**

Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npx vitest run src/design/no-indigo-oklch.test.ts`
Expected: FAIL — `.dark --sidebar-primary` hue 264 is present.

- [ ] **Step 4: Override the shadcn oklch defaults to our palette**

In `frontend/src/index.css`, inside the shadcn `@layer base` `.dark` (and `:root` where relevant), replace EVERY shadcn default color oklch var so none carries an indigo hue and all map to our tokens. At minimum set (both `:root` and `.dark`, using our vars): `--primary: var(--accent)`, `--primary-foreground: var(--accent-fg)`, `--secondary: var(--surface-2)`, `--accent: var(--surface-2)` (shadcn's "accent" is a hover surface, NOT our brand accent — keep brand accent only on `--primary`), `--ring: var(--accent)`, `--sidebar-primary: var(--accent)`, `--sidebar-primary-foreground: var(--accent-fg)`, and neutralize `--chart-1..5` to non-indigo values (`var(--status-qualifying)`, `--status-hot`, `--status-booked`, `--status-new`, `--status-escalated`). The concrete rule: after this edit, no `oklch(... 25x–29x ...)` hue remains anywhere in the file.

- [ ] **Step 5: Run the guard test to verify it passes**

Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npx vitest run src/design/no-indigo-oklch.test.ts` (also re-run `src/design/no-indigo.test.ts` — still green).
Expected: PASS.

- [ ] **Step 6: Write + pass the reduced-motion bridge test**

```ts
// frontend/src/motion/useAnimate.test.ts
/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useAnimate } from "./useAnimate.ts";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
  }));
}

describe("useAnimate", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("is disabled and ctx is a no-op under reduced motion", () => {
    mockReducedMotion(true);
    const { result } = renderHook(() => useAnimate());
    expect(result.current.enabled).toBe(false);
    const ran = vi.fn();
    expect(result.current.ctx(ran)).toBeUndefined();
    expect(ran).not.toHaveBeenCalled();
  });

  it("is enabled and ctx runs the fn when motion is allowed", () => {
    mockReducedMotion(false);
    const { result } = renderHook(() => useAnimate());
    expect(result.current.enabled).toBe(true);
    const ran = vi.fn(() => 42);
    result.current.ctx(ran);
    expect(ran).toHaveBeenCalledOnce();
  });
});
```

```ts
// frontend/src/motion/useAnimate.ts
import gsap from "gsap";
import { prefersReducedMotion } from "../design/motion.ts";

export function useAnimate() {
  const enabled = !prefersReducedMotion();
  function ctx<T>(fn: () => T): T | void {
    if (!enabled) return;
    let out: T | void;
    const c = gsap.context(() => { out = fn(); });
    c.revert; // keep reference; screens create their own scoped contexts in effects
    return out;
  }
  return { enabled, ctx };
}
```

Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npx vitest run src/motion/useAnimate.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/index.css frontend/package.json frontend/package-lock.json frontend/src/motion/useAnimate.ts frontend/src/motion/useAnimate.test.ts frontend/src/design/no-indigo-oklch.test.ts
git commit -m "feat(design): Wave2 foundation — override shadcn indigo oklch defaults + GSAP reduced-motion bridge"
```

---

### Task 2: `/demo` — migrate LeadChat / OwnerPanel / IndustrySelector to the design system

**Context:** Wave 1 removed the legacy vars `--bg-dominant`, `--bg-secondary`, `--text-primary` (the components still reference them → dead styles). `--text-muted`, `--accent`, and `--space-*` still exist. This task migrates the three demo components onto the new tokens + shadcn primitives, and fixes the stale test mock so the suite goes fully green.

**Files:**
- Modify: `frontend/src/LeadChat.tsx`, `frontend/src/OwnerPanel.tsx`, `frontend/src/IndustrySelector.tsx`
- Modify: `frontend/src/index.css` (update `.message-bubble`, `.badge-*`, `.send-btn`, `.chat-input`, `.split`, `.panel` to token classes)
- Modify: `frontend/src/__tests__/App.test.tsx` (fix the stale `useWebSocket` mock)
- Test: `frontend/src/__tests__/demo-tokens.test.tsx` (new)

**Interfaces:**
- Consumes: Wave 1 tokens + shadcn `Button`, `Badge`, `Card`, `Input`; `stageToLeadStatus`.
- Preserves: existing component prop signatures (LeadChat `{messages,onSend,agentName,industrySrc}`, OwnerPanel `{messages,stage,escalated,industry,proposed_appointment?,thread_id?,send?,escalationAlert?}`, IndustrySelector `{onSelect}`) and existing Tagalog copy strings ("Piliin ang Industry", "Lead Chat", "Owner View", "Wala pang mensahe", "I-type ang mensahe mo sa ibaba para simulan ang usapan.").

- [ ] **Step 1: Fix the stale `useWebSocket` mock (unblocks the 2 failing App.test.tsx tests)**

In `frontend/src/__tests__/App.test.tsx`, the mocked `useWebSocket` return is missing `escalationAlert` and `sendOutboundTrigger`, so the component throws. Add them to the mock object: `escalationAlert: null` and `sendOutboundTrigger: vi.fn()` (matching `UseWebSocketReturn`).
Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npx vitest run src/__tests__/App.test.tsx` — expect the previously-failing tests to PASS now (suite goes to 0 unexpected failures).

- [ ] **Step 2: Write the failing demo-tokens guard test**

```tsx
// frontend/src/__tests__/demo-tokens.test.tsx
/** @vitest-environment jsdom */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const files = ["LeadChat.tsx", "OwnerPanel.tsx", "IndustrySelector.tsx"].map((f) =>
  readFileSync(fileURLToPath(new URL(`../${f}`, import.meta.url)), "utf8"),
).join("\n");

describe("demo components use the new token system", () => {
  it("references no removed legacy CSS vars", () => {
    for (const dead of ["--bg-dominant", "--bg-secondary", "--text-primary"]) {
      expect(files).not.toContain(dead);
    }
  });
  it("references no raw indigo hex", () => {
    expect(files.toLowerCase()).not.toContain("#6366f1");
  });
});
```

Run it (fails: components still contain `--bg-dominant` etc.).

- [ ] **Step 3: Migrate the three components**

Replace legacy inline-style vars and ad-hoc markup with the new system, preserving structure, props, and copy:
- Color mapping: `--bg-dominant` → `var(--bg)`; `--bg-secondary` → `var(--surface)`; `--text-primary` → `var(--text)`; keep `--text-muted`, `--accent`, `--space-*`.
- Replace hand-rolled buttons with shadcn `Button` (primary/default = green CTA only, e.g. IndustrySelector's "Simulan" and LeadChat "Send"); message input → shadcn `Input`; industry cards and panels → `Card`.
- Lead-stage badge in OwnerPanel: derive `stageToLeadStatus(stage)` and render a status dot/`Badge` using `--status-*` (booked → accent/green). This is the ONLY place accent appears besides the primary CTA.
- Update `.message-bubble/.badge-*/.send-btn/.chat-input/.split/.panel` in `index.css` to reference the new tokens.
- Keep all Tagalog copy verbatim.

- [ ] **Step 4: Run tests green**

Run: `cd /Users/jivtuban/Desktop/ottobot/frontend && npx vitest run` — the demo-tokens test passes, App.test.tsx passes, no previously-passing test regresses.

- [ ] **Step 5: Visual verification (both themes)**

`npm run dev`, open `/demo`: industry picker renders on our surfaces, "Simulan" is the only green CTA, selecting an industry shows the LeadChat/OwnerPanel split with correct neutrals; toggle `.dark` on `<html>` and confirm parity. Run the guardrails pre-ship checklist. No console errors, no indigo, no gradient/glow/glass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/LeadChat.tsx frontend/src/OwnerPanel.tsx frontend/src/IndustrySelector.tsx frontend/src/index.css frontend/src/__tests__/App.test.tsx frontend/src/__tests__/demo-tokens.test.tsx
git commit -m "feat(demo): migrate LeadChat/OwnerPanel/IndustrySelector to signal-green token system + fix stale ws mock"
```

---

### Task 3: `/demo` — GSAP scripted lead→booked run + the hero "booked" beat

**Files:**
- Create: `frontend/src/demo/script.ts` (scripted sequence data + a pure advancer)
- Create: `frontend/src/demo/BookedBeat.tsx` (the hero moment component)
- Modify: `frontend/src/App.tsx` (offer a "Run demo" affordance that plays the script through LeadChat/OwnerPanel), `frontend/src/OwnerPanel.tsx` (mount `BookedBeat` when status becomes `booked`)
- Test: `frontend/src/demo/script.test.ts`, `frontend/src/demo/BookedBeat.test.tsx`

**Interfaces:**
- Consumes: `useAnimate` (Task 1), `Stage`/`stageToLeadStatus`, tokens.
- Produces: `export interface DemoStep { author: "lead"|"agent"; text: string; stage: Stage }`; `export const demoScript: DemoStep[]` (a realistic Taglish qualify→pitch→propose→confirm sequence ending at a `Stage` that maps to `booked`); `export function advance(i: number): number` (returns next index, clamped to `demoScript.length`). `BookedBeat` renders a restrained green pulse + checkmark stroke-draw; under reduced motion it renders the final checked state statically.

- [ ] **Step 1: Write failing script tests**

```ts
// frontend/src/demo/script.test.ts
import { describe, it, expect } from "vitest";
import { demoScript, advance } from "./script.ts";
import { stageToLeadStatus } from "../types.ts";

describe("demo script", () => {
  it("ends in a booked state", () => {
    const last = demoScript[demoScript.length - 1];
    expect(stageToLeadStatus(last.stage)).toBe("booked");
  });
  it("advance walks to the end then clamps", () => {
    expect(advance(0)).toBe(1);
    expect(advance(demoScript.length - 1)).toBe(demoScript.length);
    expect(advance(demoScript.length)).toBe(demoScript.length);
  });
  it("alternates lead/agent authorship plausibly and is non-trivial", () => {
    expect(demoScript.length).toBeGreaterThanOrEqual(6);
    expect(new Set(demoScript.map((s) => s.author))).toEqual(new Set(["lead", "agent"]));
  });
});
```

Implement `frontend/src/demo/script.ts` with a concrete Taglish sequence (6+ steps) whose final `stage` maps to `booked` via `stageToLeadStatus`, and the `advance` clamp. Run → PASS.

- [ ] **Step 2: Write the failing BookedBeat reduced-motion test**

```tsx
// frontend/src/demo/BookedBeat.test.tsx
/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { BookedBeat } from "./BookedBeat.tsx";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
  }));
}

describe("BookedBeat", () => {
  beforeEach(() => vi.unstubAllGlobals());
  it("renders the booked confirmation content (accessible) in both motion modes", () => {
    mockReducedMotion(true);
    const { getByText } = render(<BookedBeat />);
    expect(getByText(/booked/i)).toBeTruthy(); // final state present without animation
  });
});
```

Implement `BookedBeat.tsx`: it gates its GSAP timeline behind `useAnimate().enabled`; when disabled it renders the final checked/booked state immediately (no timeline). Run → PASS.

- [ ] **Step 3: Wire the scripted run + beat**

In `App.tsx`, add a restrained "Run demo" control (a shadcn secondary button — NOT green) that plays `demoScript` step-by-step into the existing LeadChat/OwnerPanel (append messages on an interval, updating stage). In `OwnerPanel.tsx`, mount `BookedBeat` when `stageToLeadStatus(stage) === "booked"`. All timing via `useAnimate`/`transition` (the beat is the one allowed >300ms animation).

- [ ] **Step 4: Tests green + visual verify the beat**

Run full vitest → green. `npm run dev`, run the demo end-to-end: watch the conversation advance and the `booked` beat fire once (green pulse + checkmark). Enable reduced motion → the beat shows the final state instantly, conversation still completes. Verify light + dark. Guardrails checklist.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/demo frontend/src/App.tsx frontend/src/OwnerPanel.tsx
git commit -m "feat(demo): GSAP scripted lead→booked run + hero booked beat (reduced-motion safe)"
```

---

### Task 4: `/onboarding` — 5-step wizard on the design system + persona-preview motion moment

**Files:**
- Modify: `frontend/src/OnboardingWizard.tsx`
- Create: `frontend/src/onboarding/StepRail.tsx`, `frontend/src/onboarding/PersonaPreview.tsx`
- Test: `frontend/src/onboarding/StepRail.test.tsx`, `frontend/src/onboarding/wizard-nav.test.tsx`

**Interfaces:**
- Consumes: shadcn `Input`/`Button`/`Card`, tokens, `useAnimate`. Preserves `OnboardingWizard` props (`{onComplete?}`), the 5 steps, industry values (`"dental"|"aesthetics"|"real_estate"`), the API calls (`POST /onboarding/preview`, `POST /onboarding/submit`), and Tagalog validation copy.
- Produces: `StepRail({ steps: string[]; current: number })` (left vertical rail, current step marked, completed steps checked) and `PersonaPreview({ persona })` (the one screen with a richer motion/Lottie moment — an "agent comes alive" reveal, reduced-motion static).

- [ ] **Step 1: Write failing StepRail + wizard-nav tests**

```tsx
// frontend/src/onboarding/StepRail.test.tsx
/** @vitest-environment jsdom */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StepRail } from "./StepRail.tsx";

describe("StepRail", () => {
  const steps = ["Account", "Business", "Services", "Persona", "Confirm"];
  it("marks the current step with aria-current", () => {
    const { getAllByText, container } = render(<StepRail steps={steps} current={2} />);
    expect(getAllByText("Services").length).toBeGreaterThanOrEqual(1);
    expect(container.querySelector('[aria-current="step"]')?.textContent).toContain("Services");
  });
});
```

```tsx
// frontend/src/onboarding/wizard-nav.test.tsx  — pin step navigation + primary-only-accent
/** @vitest-environment jsdom */
import { describe, it, expect } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { OnboardingWizard } from "../OnboardingWizard.tsx";
// Assert: Next advances the rail; Back regresses; the ONLY bg-primary element per step is the advance/submit CTA.
```

Implement `StepRail.tsx` (uses `aria-current="step"`, status-neutral rail, completed = green check — the check is the only accent) and the wizard-nav assertions. Run → PASS.

- [ ] **Step 2: Migrate the wizard onto the system**

Rebuild `OnboardingWizard.tsx` layout: left `StepRail`, right content `Card`; all inputs → shadcn `Input` with real left-aligned labels; the advance/submit button is the single green primary per step; step 4 renders `PersonaPreview`. Keep all existing state, validation, industry values, API calls, and Tagalog copy. No centered-in-void card; no gradient/glow.

- [ ] **Step 3: Build PersonaPreview motion moment**

`PersonaPreview.tsx`: a tasteful "agent reveal" (avatar + name + persona blurb animating in via `useAnimate`, ≤300ms staggered transform+opacity; optional small Lottie). Reduced motion → final state, no animation.

- [ ] **Step 4: Tests green + visual verify (light+dark)**

Full vitest green. `npm run dev` `/onboarding`: walk all 5 steps, confirm rail progression, single green CTA per step, persona reveal fires once, reduced-motion fallback. Guardrails checklist.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/OnboardingWizard.tsx frontend/src/onboarding
git commit -m "feat(onboarding): 5-step wizard on design system + persona-preview motion moment"
```

---

### Task 5: `/dashboard` — operator cockpit (net-new)

**Files:**
- Create: `frontend/src/Dashboard.tsx` + `frontend/src/dashboard/{MetricRow.tsx,ConversationsList.tsx,EscalationsPanel.tsx,AvailabilityGlance.tsx,fixtures.ts,format.ts}`
- Modify: `frontend/src/App.tsx` (route `/dashboard` → `<Dashboard/>` instead of the stub)
- Test: `frontend/src/dashboard/format.test.ts`, `frontend/src/dashboard/MetricRow.test.tsx`

**Interfaces:**
- Consumes: shadcn `Card`/`Badge`, tokens, `useAnimate`, `stageToLeadStatus`.
- Produces: `format.ts` → `export function conversionPct(booked: number, leads: number): number` (0 when leads=0; rounded whole %), `export function fmtNum(n: number): string` (tabular-friendly, thousands-separated). `MetricRow({ metrics })` renders 4 KPIs (Leads today · Booked · Conversion % · Avg response) with mono/tabular numerals and a GSAP count-up gated by `useAnimate` (instant final value under reduced motion). `fixtures.ts` supplies demo data (leads, conversations, escalations, availability).

- [ ] **Step 1: Write failing format + MetricRow tests**

```ts
// frontend/src/dashboard/format.test.ts
import { describe, it, expect } from "vitest";
import { conversionPct, fmtNum } from "./format.ts";
describe("dashboard formatters", () => {
  it("conversionPct is 0 when there are no leads", () => expect(conversionPct(0, 0)).toBe(0));
  it("conversionPct rounds to a whole percent", () => expect(conversionPct(9, 20)).toBe(45));
  it("fmtNum groups thousands", () => expect(fmtNum(3547)).toBe("3,547"));
});
```

```tsx
// frontend/src/dashboard/MetricRow.test.tsx
/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { MetricRow } from "./MetricRow.tsx";
function mockRM(on: boolean){ vi.stubGlobal("matchMedia",(q:string)=>({matches:on&&q.includes("reduce"),media:q,addEventListener(){},removeEventListener(){},addListener(){},removeListener(){}})); }
describe("MetricRow", () => {
  beforeEach(()=>vi.unstubAllGlobals());
  it("renders final metric values immediately under reduced motion", () => {
    mockRM(true);
    const { getByText } = render(<MetricRow metrics={{ leadsToday: 128, booked: 41, conversionPct: 32, avgResponseSec: 47 }} />);
    expect(getByText("128")).toBeTruthy();
    expect(getByText(/32%/)).toBeTruthy();
  });
});
```

Implement `format.ts` and `MetricRow.tsx` (count-up via `useAnimate`; reduced motion renders the final numbers with no tween). Run → PASS.

- [ ] **Step 2: Build the cockpit + route it**

Build `Dashboard.tsx` composing `MetricRow` (top), `ConversationsList` (live threads: status dot via `stageToLeadStatus` + last message + mono timestamp), `EscalationsPanel` ("Needs you" queue), `AvailabilityGlance` (week strip). Feed from `fixtures.ts`. In `App.tsx`, route `/dashboard` to `<Dashboard/>`. Dense, data-forward, hairline borders, flat surfaces; accent only on a primary CTA (if any) + booked dots.

- [ ] **Step 3: Tests green + visual verify (light+dark)**

Full vitest green. `npm run dev` `/dashboard`: metrics count up once on load (instant under reduced motion), lists render with correct status colors, no indigo/gradient/glow. Light + dark parity. Guardrails checklist.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/Dashboard.tsx frontend/src/dashboard frontend/src/App.tsx
git commit -m "feat(dashboard): operator cockpit — KPI count-up, conversations, escalations, availability"
```

---

## Self-Review

**1. Spec coverage (spec §Screen specs → Web):** `/demo` picker+split+hero → Tasks 2–3; `/onboarding` 5-step+persona motion → Task 4; `/dashboard` real cockpit → Task 5. Motion philosophy + one hero beat → Task 3. GSAP + reduced-motion + indigo-cleanup foundation → Task 1. Light+dark + guardrails checklist → every screen task's visual step.

**2. Placeholder scan:** No TBD/TODO. Logic units carry real test code; visual/motion layers carry a precise contract + acceptance + guardrails gate (appropriate for pixel/timeline work, which pure transcription can't specify honestly). `wizard-nav.test.tsx` describes its assertions in a comment because the exact queries depend on the migrated markup the implementer authors in the same task — the implementer writes the concrete assertions to the stated contract (single `bg-primary` CTA per step; Next/Back move the rail).

**3. Type consistency:** Uses existing `Stage`, `LeadStatus`, `stageToLeadStatus`, `UseWebSocketReturn` fields verbatim from the map. New symbols (`useAnimate`, `DemoStep`/`demoScript`/`advance`, `StepRail`, `PersonaPreview`, `conversionPct`/`fmtNum`, `MetricRow`) are each defined in the task that introduces them and consumed only afterward.

## Dependencies / notes
- Task 1 is a hard prerequisite for 3/4/5 (GSAP + `useAnimate` + indigo-clean theme). Tasks 2→3 are ordered (3 builds on the migrated demo). Tasks 4 and 5 are independent of each other (both depend only on Task 1).
- Backend/live-data wiring stays out of scope (spec YAGNI): `/dashboard` uses fixtures; `/demo` may use the existing WebSocket where already present, else the scripted run.

## Next wave
- **Wave 3 — Mobile screens:** `/login` (closes Neon+Clerk Task 6), `/pipeline`, `/conversation/[id]`, `/settings`, with Reanimated/Moti — its own plan against the Wave 1 Tamagui tokens.
