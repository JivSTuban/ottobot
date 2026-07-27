---
status: complete
phase: 01-agent-core-demo-ui
source: [01-VERIFICATION.md]
started: 2026-06-15T00:00:00Z
updated: 2026-06-16T11:50:00Z
gap_retest: 2026-06-16T11:50:00Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-end live demo
expected: Token streaming works; stage badge advances; OwnerPanel shows state events
result: pass

### 2. DEMO-03 Supabase persistence
expected: Send messages, close/reconnect with same threadId — conversation resumes from checkpoint
result: pass
note: "GAP fix verified: test_state_resumes_after_reconnect PASSED (3/3 persistence tests pass). _normalize_message strips LangChain metadata fields before Mistral API call — extra_forbidden error eliminated. SUPABASE_DB_URI resolves after >24h DNS propagation; SUPABASE_DIRECT_URL fallback available for new projects."

### 3. NPC AI disclosure in live LLM output
expected: "AI assistant" phrase appears in actual first agent response (not just template)
result: pass
note: "Required 3 fixes: Groq model (maverick→scout), stream_mode (messages→updates), LangChain message normalization. Post-fix response: 'Para sa transparency po, ako ay AI assistant ni Ate Ana...'"

### 4. Persona image rendering
expected: Dental/aesthetics/real_estate cards show correct avatar + industry images
result: pass
note: "All 3 persona images confirmed loaded via Playwright (ate-ana.png, ate-bea.png, kuya-marco.png — naturalWidth > 0)"

### 5. Escalation alert UX
expected: CSS slideDown animation, red destructive color, role="alert" screen reader announcement fires on booking phrase
result: pass
note: "GAP fix verified via Playwright: role='alert' element confirmed (HOT LEAD — Tawagan na!), stage badge shows HOT, system_alert event received. agent_node now writes stage/escalated/system_alert each turn; route_next_stage is pure end-check returning 'agent' or END."

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Reconnect with same threadId resumes conversation from checkpoint"
  status: resolved
  reason: "Fixed by 01-GAP: _normalize_message strips extra_kwargs/response_metadata/type/id from messages before Mistral API call. SUPABASE_DIRECT_URL fallback added. test_state_resumes_after_reconnect PASSED."
  severity: major
  test: 2

- truth: "Escalation alert fires (system_alert + escalated=true) when user sends booking phrase"
  status: resolved
  reason: "Fixed by 01-GAP: _compute_next_stage helper in agent_node computes stage transitions and writes stage/escalated/system_alert to state. route_next_stage is now a pure end-check with explicit path_map {'agent': 'agent', END: END}. Confirmed via Playwright: role='alert' fires, stage='HOT'."
  severity: major
  test: 5
