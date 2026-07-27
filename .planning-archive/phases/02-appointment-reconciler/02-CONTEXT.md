# Phase 02: Appointment Reconciler — Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss — see .planning/POLICY.md)

<domain>
## Phase Boundary

Agent can propose appointment time windows from the business owner's availability schedule, and confirmed appointments are stored in Supabase — no external calendar needed.

**Success criteria:**
1. Business owner can define weekly availability (days + hours) and it is saved to Supabase
2. Agent reads available slots and proposes time windows to the lead during conversation
3. Business owner can confirm or counter-propose an appointment time via the app
4. Confirmed appointment record (lead, business, time, status) is readable in Supabase

</domain>

<decisions>
## Implementation Decisions

### Data Layer
- **Availability storage:** Supabase table `business_availability` (id, business_id, day_of_week int 0-6, start_time time, end_time time)
- **Appointments table:** `appointments` (id, thread_id, business_id, proposed_time timestamptz, status: proposed/confirmed/cancelled, created_at)
- **No external calendar** (Google Calendar, Calendly) — Supabase only for v1
- **Business ID source:** For now, derive from industry + a placeholder UUID stored in env; real multi-business comes in Phase 5

### Agent Integration
- New LangGraph tool node `get_available_slots(business_id, days_ahead=7)` — queries Supabase, returns 2 slots max
- Add `proposed_appointment` field to `ConversationState` (str or None) — stores proposed ISO datetime
- Agent proposes slots only when stage reaches `propose_appointment`
- Slot format in Tagalog: "Mayroon kaming bakante sa [Day] ng [Date] sa [Time]"
- If no slots available: "Tatawagan ka namin para mag-ayos ng oras" (fallback phrase)

### API
- `POST /availability` — upsert weekly schedule for a business
- `GET /availability/{business_id}` — return available slots for next 7 days
- `POST /appointments/confirm` — business owner confirms a proposed slot
- All new endpoints use same `validate_thread_id` / `validate_business_id` guard patterns
- Keep behind existing FastAPI app (no separate service)

### UI (OwnerPanel extension)
- New "Appointments" section below existing escalation panel
- Shows proposed appointment time (if any) with Confirm / Counter-propose buttons
- Counter-propose: text input for owner to type alternate time (simple, no calendar picker)
- Confirmation triggers WebSocket message `confirm_appointment` → backend stores to Supabase

### WebSocket Protocol
- New message type from owner to server: `{ type: "confirm_appointment", thread_id, proposed_time, action: "confirm" | "counter", counter_time? }`
- New message type server to lead client: `{ type: "appointment_confirmed", confirmed_time }` — agent appends confirmation message to conversation

### Testing
- Unit tests: `test_appointment_slots.py` — test slot generation, time math, Tagalog formatting
- Unit tests: `test_appointment_api.py` — test availability API endpoints (mock Supabase)
- Frontend: `OwnerPanel.test.tsx` extended with appointment UI tests

### Skipped for this phase
- Appointment reminders (SMS/email to lead before appointment)
- Calendar sync (Google/Apple Calendar)
- Multi-business availability (Phase 5+)
- Recurring appointment patterns

</decisions>

<code_context>
## Existing Code Insights

Phase 1 established:
- `agent/state.py` — `ConversationState` TypedDict; add `proposed_appointment: str | None` here
- `agent/graph.py` — LangGraph builder; add new tool node for slot retrieval
- `api/main.py` — FastAPI app with lifespan; add availability + appointment routes
- `api/ws_handler.py` — WebSocket handler; add `confirm_appointment` message routing
- `frontend/src/OwnerPanel.tsx` — existing owner panel; extend with appointment section
- `frontend/src/types.ts` — add `AppointmentMessage` and `AvailabilitySlot` types
- Supabase AsyncPostgresSaver already initialized in lifespan — same client reused for new tables

Key patterns to follow:
- `Annotated[str | None, ...]` for new optional state fields (no reducer needed for scalar)
- `os.environ.get("SUPABASE_URL")` for env access
- Guard all state reads with `.get()` defaults

</code_context>

<specifics>
## Specific Ideas

- **Slot proposal limit:** Hard cap at 2 slots — "Mayroon kaming dalawang bakante" (we have two openings)
- **Day range:** Next 7 days only; don't propose slots that are < 2 hours from now
- **Time display:** 12-hour format with AM/PM in Filipino style: "ika-2 ng hapon" (2pm)
- **Agent confirmation message:** After business owner confirms, agent sends: "Napag-usapan natin ang inyong appointment sa [confirmed_time]. Magkita-kita tayo!"

</specifics>

<deferred>
## Deferred Ideas

- Appointment reminders (Phase 4 when SMS channel exists)
- Calendar integrations (future milestone)
- Lead-side rescheduling flow
- Appointment analytics dashboard

</deferred>
