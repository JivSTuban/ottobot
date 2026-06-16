---
status: complete
phase: 01-agent-core-demo-ui
source: [01-VERIFICATION.md]
started: 2026-06-15T00:00:00Z
updated: 2026-06-15T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. End-to-end live demo
expected: Token streaming works; stage badge advances; OwnerPanel shows state events
result: pass

### 2. DEMO-03 Supabase persistence
expected: Send messages, close/reconnect with same threadId — conversation resumes from checkpoint
result: issue
reported: "Two blockers verified by automated WS test: (1) Mistral (LLM fallback) rejects checkpoint-restored messages — LangChain extra fields (additional_kwargs, response_metadata, type, id) cause extra_forbidden on Mistral API; (2) Supabase pooler returns ENOTFOUND (project <24h old, propagation lag) — API running on InMemorySaver fallback"
severity: major

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
result: issue
reported: "Escalation never fires. Graph has only one node ('agent') but route_next_stage returns stage names ('qualify', 'escalate', etc.) that don't exist as nodes — LangGraph logs 'wrote to unknown channel branch:to:qualify, ignoring it' and routes to END. Stage never advances beyond 'intro', escalated flag never set, system_alert never sent."
severity: major

## Summary

total: 5
passed: 3
issues: 2
pending: 0
skipped: 0
blocked: 0

## Gaps

- truth: "Reconnect with same threadId resumes conversation from checkpoint"
  status: failed
  reason: "Two blockers: (1) Mistral API rejects LangChain message metadata fields (additional_kwargs, response_metadata, type, id) on checkpoint restore — extra_forbidden error; (2) Supabase pooler ENOTFOUND — project propagation lag, API on InMemorySaver fallback"
  severity: major
  test: 2
  artifacts: []
  missing: []

- truth: "Escalation alert fires (system_alert + escalated=true) when user sends booking phrase"
  status: failed
  reason: "Graph only has one node ('agent'). route_next_stage returns stage names ('qualify','escalate') that are not registered nodes. LangGraph logs 'wrote to unknown channel branch:to:qualify, ignoring it' and routes to END. Stage never advances, escalated never set, system_alert never sent."
  severity: major
  test: 5
  artifacts:
    - path: "agent/graph.py"
      issue: "add_conditional_edges routes to non-existent stage nodes; only 'agent' node registered"
  missing:
    - "Register stage-named nodes or loop 'agent' node back with updated stage in state"
