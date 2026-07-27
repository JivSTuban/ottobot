# OttoBot Phase 1 — Manual Demo Verification Checklist

Run `scripts/dev.sh` before starting. Confirm all three services are healthy:
- Phoenix: `curl -s http://localhost:6006 | head -1`
- API: `curl -s http://localhost:8000/health` → `{"ok":true,"compiled":true}`
- Frontend: open `http://localhost:5173` in browser

For each item, mark pass / fail / blocked in the `Result` line.

---

## AGENT-01 — Stage Progression (7-Step Scripted Conversation)

- [x] AGENT-01 — Stage badge advances through the full 7-stage state machine during a scripted conversation

**Steps:**
1. Open `http://localhost:5173`, select **Dental**, click **Simulan**
2. Send: `"Hi po, ano ang mga serbisyo niyo?"`
   - Expected stage badge: **Tinatasa** (qualifying)
3. Send: `"Naghahanap ako ng murang whitening"`
   - Expected: agent pitches dental whitening services (badge → Nagbebenta)
4. Send: `"Mahal naman, may diskwento ba?"`
   - Expected: agent handles objection, may offer promo
5. Send: `"Pwede ba magpa-schedule?"`
   - Expected: agent proposes appointment (badge → Nag-aanyaya)
6. Send: `"Sige, bukas ng hapon"`
   - Expected: agent confirms appointment slot (badge → Naka-book or HOT)
7. Send: `"gusto ko mag-book bukas"` (if escalation not yet triggered)
   - Expected: escalation alert visible, badge → **HOT**

**Expected:** Stage badge transitions through at least 4 distinct stages during the conversation; no infinite loop at any stage; `aget_state()` state event delivered to owner panel after each turn.

Result: PASS

---

## AGENT-02 — LiteLLM Router Fallback (Groq → Gemini)

- [x] AGENT-02 — LiteLLM Router falls back from Groq to Gemini on rate-limit (429)

**Option A — Automated test (preferred):**

**Steps:**
1. From repo root (venv active): `pytest tests/test_llm_router.py::test_groq_429_falls_back_to_gemini -x -q`
2. Expected: 1 passed, 0 failed

**Option B — Live rate-limit saturation:**

**Steps:**
1. Open `http://localhost:5173`, select any industry
2. Send 31+ messages rapidly within 60 seconds to saturate Groq's free tier (30 RPM limit)
3. Watch `/tmp/uvicorn.log` — confirm a `litellm.RateLimitError` is logged followed by a successful response from `gemini/` model
4. The frontend holding message (type:system_alert) should flash briefly during the 30s backoff

**Expected:** Agent replies successfully even when Groq is rate-limited; fallback to Gemini Flash confirmed in logs; no unhandled 500 error to client.

Result: PASS

---

## AGENT-03 — Taglish Code-Switching Quality (Human-Judged)

- [x] AGENT-03 — Agent replies in Taglish matching the register of the lead message (no full-English fallback, no overly formal Tagalog)

**Steps:**
1. Open `http://localhost:5173`, select **Dental**, click **Simulan**
2. Type and send: `"Hi po, interested ako sa whitening, magkano?"`
3. Read the agent's reply carefully

**Expected:** Agent replies in natural Taglish — mixing Filipino and English words as a Filipino sales person would (e.g., "Hi po! Ang aming whitening package ay nagsi-start sa ₱3,500 per session..."). Must NOT be:
- Full English response (e.g., "Hello! Our whitening starts at...")
- Overly formal Baybayin/archaic Tagalog
- Mix of random words that feel unnatural

4. Try a follow-up in Filipino: `"Ano po ang kasamang libre?"`
5. Expected: agent continues in natural Taglish

**Expected:** Subjective quality check — developer signs off that register matches a real Filipino sales manager conversation style (AI-SPEC Section 1b rubric: warm, informal, code-switching matches lead's register).

Result: PASS

---

## AGENT-04 — Industry Persona Templates (3 Industries)

- [x] AGENT-04 — Agent introduces with the correct persona name for each industry (Ate Ana / Ate Bea / Kuya Marco)

**Steps:**
1. Open **Tab 1**: `http://localhost:5173`, select **Dental**, click **Simulan**, send `"Hello"`
   - Expected: agent introduces as **Ate Ana** (dental persona)
2. Open **Tab 2**: `http://localhost:5173`, select **Aesthetics**, click **Simulan**, send `"Hello"`
   - Expected: agent introduces as **Ate Bea** (aesthetics persona)
3. Open **Tab 3**: `http://localhost:5173`, select **Real Estate**, click **Simulan**, send `"Hello"`
   - Expected: agent introduces as **Kuya Marco** (real estate persona)

**Expected:** Each tab gets a distinct thread_id (UUID v4 via `crypto.randomUUID()`); each agent intro message uses the correct name and industry context; no persona bleeds across tabs.

Result: PASS

---

## AGENT-05 — Escalation Alert (Booking Phrase Detection)

- [x] AGENT-05 — Escalation alert appears in the owner panel within 5 seconds of explicit booking phrase

**Steps:**
1. Open `http://localhost:5173`, select any industry, click **Simulan**
2. Send any opener to establish a session (e.g., `"Magandang hapon"`)
3. Wait for the agent reply
4. Send: `"gusto ko mag-book bukas"`
5. Start timer

**Expected:** Within 5 seconds:
- Stage badge in owner panel changes to **HOT** (red)
- Escalation alert banner appears with text "HOT LEAD — Tawagan na!" (role="alert")
- Alert auto-dismisses after ~8 seconds OR persists until next message

Result: PASS

---

## DEMO-01 — WebSocket Server Health + Thread ID Validation

- [x] DEMO-01 — API health endpoint returns expected JSON; invalid thread IDs are rejected

**Steps:**
1. Run: `curl -s http://localhost:8000/health`
   - Expected response: `{"ok":true,"compiled":true}`
2. Test invalid thread ID rejection (not a UUID):
   ```bash
   python3 -c "
   import asyncio, websockets, json

   async def test():
       try:
           async with websockets.connect('ws://localhost:8000/ws/not-a-uuid') as ws:
               await ws.recv()
       except websockets.exceptions.ConnectionClosedError as e:
           print(f'Close code: {e.code}')  # Expected: 1008

   asyncio.run(test())
   "
   ```
   - Expected: WebSocket closes with code **1008** (Policy Violation)
3. Confirm a valid UUID v4 connects successfully:
   ```bash
   python3 -c "
   import asyncio, websockets, uuid, json

   async def test():
       tid = str(uuid.uuid4())
       async with websockets.connect(f'ws://localhost:8000/ws/{tid}') as ws:
           await ws.send(json.dumps({'industry': 'dental', 'text': 'Test'}))
           msg = await ws.recv()
           print('Received:', msg[:80])

   asyncio.run(test())
   "
   ```
   - Expected: Receives a `{"type":"token",...}` or `{"type":"state",...}` JSON message

**Expected:** Health endpoint returns `{"ok":true,"compiled":true}`. Invalid thread IDs rejected with code 1008. Valid UUID4 receives streaming events.

Result: PASS

---

## DEMO-02 — Split-Screen UI Layout

- [x] DEMO-02 — Both panels visible at 50/50 split; owner panel mirrors lead's conversation; stage badge updates after each turn

**Steps:**
1. Open `http://localhost:5173`, select **Dental**, click **Simulan**
2. Visually verify: left panel (LeadChat) and right panel (OwnerPanel) each occupy ~50% of the viewport width
3. Send a message in the left (lead) panel
4. Verify:
   a. Message appears in the left panel chat bubble as "Ikaw"
   b. Same message appears in the right panel (OwnerPanel conversation mirror) as "Lead"
   c. Stage badge in the right panel reflects the current conversation stage (e.g., "Tinatasa")
5. Wait for agent reply
6. Verify:
   a. Agent reply appears streamed token-by-token in the left panel
   b. Agent reply appears in the right panel as "Agent"
   c. Stage badge updates to reflect new stage after agent reply
7. Resize browser window to < 768px width (if applicable) — panels should remain usable

**Expected:** Both panels always visible side-by-side; no overflow clipping on typical 1280px+ display; stage badge text matches the `stageToLeadStatus` mapping (Tinatasa / HOT / Naka-book / Bago).

Result: PASS

---

## DEMO-03 — Conversation Persistence (Page Reload)

- [x] DEMO-03 — Conversation history survives a page reload (same thread_id resumes prior turns)

**Steps:**
1. Open `http://localhost:5173`, select **Dental**, click **Simulan**
2. Note the thread_id shown in the browser URL bar or copy it from browser localStorage (key: `ottobot_thread_id`, or inspect the WebSocket URL in DevTools → Network → WS → Headers)
3. Send 3 messages and wait for agent replies after each
4. Note the current stage badge value
5. Reload the page (Cmd+R / F5)
6. If the UI auto-reconnects to the same thread_id: verify the 3 prior messages re-appear in the chat
7. If thread_id is reset on reload: paste the saved UUID into the URL or localStorage and reload

**Expected:** After reload, all 3 prior turns are visible in the chat panel; the stage badge shows the same stage as before reload; the conversation continues from where it left off (no restart to intro stage).

Result: PASS

---

## NPC 2024-04 — AI Disclosure on First Contact

- [x] NPC 2024-04 — The agent's intro message contains an "AI assistant" disclosure before any data-collection question

**Steps:**
1. Open `http://localhost:5173`, select any industry, click **Simulan**
2. Send: `"Hello"` (or wait for auto-intro if applicable)
3. Read the first agent message carefully

**Expected:** The first agent message (intro stage) contains the phrase "AI assistant" (or equivalent Filipino phrasing such as "AI na assistant") BEFORE asking any personal information (name, contact number, etc.). Example acceptable disclosure: "Ako si Ate Ana, ang AI assistant ng [clinic name]..."

4. Confirm no data-collection question precedes the disclosure

Result: PASS

---

## Summary

| Requirement | Description | Result |
|-------------|-------------|--------|
| AGENT-01 | Stage progression (7 stages) | PASS |
| AGENT-02 | LiteLLM fallback (Groq → Gemini) | PASS |
| AGENT-03 | Taglish code-switching quality | PASS |
| AGENT-04 | Persona templates (3 industries) | PASS |
| AGENT-05 | Escalation alert < 5s | PASS |
| DEMO-01 | WebSocket health + UUID validation | PASS |
| DEMO-02 | Split-screen UI 50/50 | PASS |
| DEMO-03 | Conversation persistence on reload | PASS |
| NPC 2024-04 | AI disclosure before data collection | PASS |

**Overall:** 9 / 9 pass

**Tester:** Developer (getatchris@gmail.com)  **Date:** 2026-06-15
