---
status: testing
phase: 01-agent-core-demo-ui
source: [01-VERIFICATION.md]
started: 2026-06-15T00:00:00Z
updated: 2026-06-15T00:00:00Z
---

## Current Test

number: 1
name: End-to-end live demo with Taglish token streaming
expected: |
  Start server with real API keys; send a Taglish message ("Hi po, interested ako sa whitening");
  verify token streaming appears in LeadChat and stage badge advances in OwnerPanel.
awaiting: user response

## Tests

### 1. End-to-end live demo
expected: Token streaming works; stage badge advances; OwnerPanel shows state events
result: [pending]

### 2. DEMO-03 Supabase persistence
expected: Send messages, close/reconnect with same threadId — conversation resumes from checkpoint
result: [pending]

### 3. NPC AI disclosure in live LLM output
expected: "AI assistant" phrase appears in actual first agent response (not just template)
result: [pending]

### 4. Persona image rendering
expected: Dental/aesthetics/real_estate cards show correct avatar + industry images
result: [pending]

### 5. Escalation alert UX
expected: CSS slideDown animation, red destructive color, role="alert" screen reader announcement fires on booking phrase
result: [pending]

## Summary

total: 5
passed: 0
issues: 0
pending: 5
skipped: 0
blocked: 0

## Gaps
