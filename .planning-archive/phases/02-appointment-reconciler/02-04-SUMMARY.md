---
phase: 02-appointment-reconciler
plan: "04"
subsystem: frontend
tags: [ui, typescript, appointments, react, vitest]
dependency_graph:
  requires: [02-01, 02-02, 02-03]
  provides: [APPT-03]
  affects: [frontend/src/OwnerPanel.tsx, frontend/src/types.ts]
tech_stack:
  added: []
  patterns: [RTL within() for scoped queries, conditional JSX on stage prop]
key_files:
  created: []
  modified:
    - frontend/src/types.ts
    - frontend/src/OwnerPanel.tsx
    - frontend/src/OwnerPanel.test.tsx
decisions:
  - Used container.querySelector('.appointments-section') + within() to scope button queries and avoid ambiguity with multiple role=region elements
  - Added send/thread_id/proposed_appointment as optional props to maintain backward compatibility with existing renderPanel() test helper
metrics:
  duration: "~10 minutes"
  completed: "2026-06-16"
  tasks_completed: 2
  files_modified: 3
requirements: [APPT-03]
---

# Phase 02 Plan 04: Appointments UI Summary

Appointment proposal UI with Confirm and Counter-propose actions wired to the existing WebSocket send channel.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add TypeScript types and OwnerPanel Appointments section | 25bed10 | types.ts, OwnerPanel.tsx |
| 2 | Extend OwnerPanel.test.tsx with 4 appointment UI tests | bade04c | OwnerPanel.test.tsx |

## What Was Built

**types.ts** — Two new interfaces:
- `AvailabilitySlot { iso: string; display: string }` — for future slot picker use
- `AppointmentMessage { type: "confirm_appointment"; thread_id: string; proposed_time: string; action: "confirm" | "counter"; counter_time?: string }` — matches ws_handler expectation exactly

**OwnerPanel.tsx** — Extended with:
- Three new optional props: `proposed_appointment`, `thread_id`, `send`
- `handleConfirm()` — sends `{ type: confirm_appointment, action: confirm }` via `props.send`
- `handleCounter()` — sends `{ type: confirm_appointment, action: counter, counter_time }` via `props.send`
- `appointments-section` JSX rendered conditionally when `stage === "propose_appointment" && proposed_appointment`
- Counter-propose toggle with text input (`aria-label="Counter-propose time"`)

**OwnerPanel.test.tsx** — 4 new tests in "Appointments section" describe block:
1. Section hidden when stage != propose_appointment
2. Section visible with Confirm/Counter-propose buttons at propose_appointment stage
3. Confirm button sends correct confirm_appointment WebSocket message
4. Counter-propose sends counter message with counter_time

## Verification Results

- Frontend OwnerPanel: 15/15 tests pass (11 existing + 4 new)
- Frontend full suite: all tests pass
- TypeScript: `npx tsc --noEmit` — 0 errors
- Backend regression: 87 passed, 0 failures

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Button query ambiguity with multiple role=region elements**
- **Found during:** Task 2, test runs
- **Issue:** `getByRole("button", { name: /Confirm/i })` and `getByRole("region", { name: /Appointments/i })` returned multiple matches because the outer `<section class="panel">` and inner appointments section both become `region` elements
- **Fix:** Switched to `container.querySelector(".appointments-section")` + `within()` to scope all button queries to the appointments section element
- **Files modified:** `frontend/src/__tests__/OwnerPanel.test.tsx`
- **Commit:** bade04c

## Known Stubs

None — all appointment UI is fully wired to the WebSocket send channel.

## Threat Flags

None — no new network endpoints or trust boundaries introduced. The existing `validate_thread_id()` server-side guard (T-02-12) covers the `thread_id` field sent from UI.

## Self-Check: PASSED

- `frontend/src/types.ts` exists with AppointmentMessage and AvailabilitySlot
- `frontend/src/OwnerPanel.tsx` exists with appointments-section and confirm_appointment
- `frontend/src/__tests__/OwnerPanel.test.tsx` exists with 4 new appointment tests
- Commits 25bed10 and bade04c verified in git log
