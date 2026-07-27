# Phase 6: Mobile App - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Business owners can monitor lead activity, read conversation history, manage their agent persona, and set availability — all from a mobile app with push notifications.

**Success Criteria:**
1. Business owner receives push notifications for hot leads, booked appointments, and conversation summaries
2. Business owner can read the full chat log for any lead
3. Pipeline dashboard shows all leads grouped by status (new, in-progress, booked, escalated, closed)
4. Business owner can edit agent name, tone, script, and offers post-onboarding
5. Business owner can mark days as open or blocked; changes update available slots immediately

</domain>

<decisions>
## Implementation Decisions

### From POLICY.md (pre-answered)

**Stack:** React Native with Expo (SDK 51+), not bare workflow
**Auth:** Reuse Supabase Auth tokens from Phase 5 — `@supabase/supabase-js` in Expo
**Push notifications:** Expo Push Notifications + `expo-notifications` — no FCM/APNs direct setup

**Screens (MVP only, 4 screens):**
1. Login (Supabase Auth)
2. Lead Pipeline (list, grouped by status: new / in-progress / booked / escalated)
3. Conversation detail (read-only chat log for a lead)
4. Settings (availability schedule — reuse Phase 2 API)

**Push trigger:** Phase 3 escalation email → also call `POST /push/send` with Expo token
**Expo push token:** Stored in `business_push_tokens` table, collected on app first launch

**Do NOT implement:** Persona editing, analytics dashboard, dark mode, iPad layout

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

- Backend: FastAPI on port 8000, existing `/availability` endpoints from Phase 2
- Auth: Supabase Auth (Phase 5) — JWT tokens reusable in mobile
- Escalation: Phase 3 escalation flow sends email via Resend — push notification hook goes here
- Existing tables: leads, messages, appointments, escalations, businesses

</code_context>

<specifics>
## Specific Ideas

- Create `mobile/` directory at project root for the Expo app
- Add `business_push_tokens` Supabase table (business_id, expo_token, created_at)
- Add `POST /push/send` endpoint to FastAPI backend
- Wire push send into escalation flow (Phase 3 code path)
- 4-screen Expo app: Login → Pipeline → Conversation → Settings

</specifics>

<deferred>
## Deferred Ideas

- iPad layout
- Dark mode
- Persona editing in mobile
- Analytics dashboard
- WhatsApp integration
- Multiple push tokens per device

</deferred>
