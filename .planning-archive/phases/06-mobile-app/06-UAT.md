---
status: testing
phase: 06-mobile-app
source: 06-01-SUMMARY.md, 06-02-SUMMARY.md, 06-03-SUMMARY.md, 06-04-SUMMARY.md
started: 2026-06-19T00:00:00Z
updated: 2026-06-19T00:00:00Z
---

## Current Test

number: 7
name: Login Screen — Mag-login CTA
expected: |
  Open the Expo app (run `cd mobile && npx expo start` then open in Expo Go or iOS/Android simulator).
  App shows a login screen with email and password fields and a "Mag-login" button.
  Enter valid Supabase credentials and tap "Mag-login".
  You should land on the Pipeline tab (Lead Pipeline screen) after successful login.
awaiting: user response

## Tests

### 1. GET /leads — auth gate
expected: GET /leads with no Authorization header returns 401 {"detail":"Not authenticated"}
result: pass
auto: true

### 2. GET /leads/{id}/messages — auth gate
expected: GET /leads/{lead_id}/messages with no auth returns 401
result: pass
auto: true

### 3. POST /push/send — auth gate
expected: POST /push/send with no Authorization header returns 401
result: pass
auto: true

### 4. POST /push/send — expo token format validation
expected: POST /push/send with invalid token format (e.g. "BadToken") returns 422 Unprocessable Entity
result: pass
auto: true

### 5. All 3 Phase 06 routes registered
expected: /leads, /leads/{lead_id}/messages, /push/send all appear in the OpenAPI spec
result: pass
auto: true

### 6. Expo app cold start
expected: |
  Run `cd mobile && npx expo start`. Expo Dev Tools opens without errors.
  QR code appears. App loads on device/simulator.
  Unauthenticated user is redirected to the Login screen (not pipeline).
result: [pending]

### 7. Login Screen — Mag-login CTA
expected: |
  Login screen shows email + password fields and "Mag-login" button.
  Enter valid Supabase credentials → tap "Mag-login" → land on Pipeline tab.
result: [pending]

### 8. Lead Pipeline screen
expected: |
  Pipeline tab shows leads grouped by status (e.g. Bagong Lead, In Progress, Handa na).
  SectionList renders section headers with Tagalog labels.
  Pull-to-refresh updates the list. Tapping a lead row navigates to Conversation Detail.
result: [pending]

### 9. Conversation Detail screen
expected: |
  Chat screen shows messages newest at bottom (FlatList inverted).
  Each message bubble shows the message content with correct alignment (outbound right, inbound left).
  If the lead has an escalation, a banner is visible.
result: [pending]

### 10. Settings/Availability screen
expected: |
  Settings tab shows toggleable availability days (Mon–Sun or equivalent).
  Toggle a day on/off → tap "I-save" → success toast appears.
  API call to POST /availability fires with the updated schedule.
result: [pending]

### 11. Push notification fires on escalation
expected: |
  Trigger an escalation (simulate via WebSocket or existing demo UI).
  A push notification arrives on the registered device with title "Hot lead — tumawag na!"
  and body containing the lead's phone number.
result: [pending]

## Summary

total: 11
passed: 5
issues: 0
pending: 6
skipped: 0
blocked: 0

## Gaps

[none yet]
