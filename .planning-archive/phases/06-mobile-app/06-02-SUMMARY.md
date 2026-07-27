---
phase: 06-mobile-app
plan: "02"
subsystem: mobile-infrastructure
tags: [expo, react-native, supabase, push-notifications, auth]
dependency_graph:
  requires: []
  provides:
    - mobile/lib/supabase.ts (Supabase client singleton)
    - mobile/lib/pushToken.ts (push token registration)
    - mobile/hooks/useAuth.tsx (auth session hook)
    - mobile/app/_layout.tsx (root layout with auth guard)
  affects:
    - All subsequent mobile screens depend on these infrastructure files
tech_stack:
  added:
    - expo@~56.0.12 (blank-typescript template)
    - expo-router@~56.2.11
    - expo-notifications@~56.0.18
    - expo-device@~56.0.4
    - expo-constants@~56.0.18
    - "@supabase/supabase-js@^2.108.2"
    - "@react-native-async-storage/async-storage@2.2.0"
    - react-native-safe-area-context@~5.7.0
    - "@expo/vector-icons@^15.0.2"
  patterns:
    - expo-router file-based navigation (entry via expo-router/entry)
    - Supabase AsyncStorage session persistence with detectSessionInUrl:false
    - Expo push token via Constants.expoConfig.extra.eas.projectId (not hardcoded)
    - Auth guard pattern — null splash while loading, Redirect to /login when unauthenticated
key_files:
  created:
    - mobile/app.json
    - mobile/package.json
    - mobile/.env.example
    - mobile/lib/supabase.ts
    - mobile/lib/pushToken.ts
    - mobile/hooks/useAuth.tsx
    - mobile/app/_layout.tsx
  modified:
    - .gitignore (added mobile/.env and mobile/node_modules/)
decisions:
  - package.json main changed from index.ts to expo-router/entry — required for file-based routing
  - blank-typescript template used (not expo-router template) — expo-router added via expo install
  - App.tsx left in place (not deleted) — harmless with expo-router/entry as main
  - EAS projectId set to placeholder REPLACE_WITH_EAS_PROJECT_ID — real ID needed at build time
  - Push token POST failure caught and logged (non-fatal) — T-06-08 mitigation
metrics:
  duration: 25m
  completed: "2026-06-19"
  tasks: 2
  files: 8
---

# Phase 06 Plan 02: Mobile Infrastructure Summary

Expo React Native app bootstrapped in `mobile/` with Supabase client (AsyncStorage session, `detectSessionInUrl: false`), push token registration helper (Device.isDevice guard), auth hook (onAuthStateChange + signOut), and root layout with auth guard redirecting unauthenticated users to /login.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Bootstrap Expo project + dependencies | 3091a12 | app.json, package.json, .env.example |
| 2 | Supabase client, push token, auth hook, root layout | 8b6cbd7 | lib/supabase.ts, lib/pushToken.ts, hooks/useAuth.tsx, app/_layout.tsx |

## Artifacts Produced

| Symbol | File | Type |
|--------|------|------|
| `supabase` | mobile/lib/supabase.ts | Supabase client singleton |
| `registerForPushNotificationsAsync` | mobile/lib/pushToken.ts | Push token helper function |
| `useAuth` | mobile/hooks/useAuth.tsx | React hook |
| `RootLayout` (default export) | mobile/app/_layout.tsx | Expo Router root layout |
| mobile/app.json | mobile/ | Expo config with scheme + EAS projectId |
| mobile/.env.example | mobile/ | Env var template |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] expo-router/entry main field**
- **Found during:** Task 1
- **Issue:** blank-typescript template sets `"main": "index.ts"` which breaks expo-router file-based routing
- **Fix:** Updated package.json main to `"expo-router/entry"` — required for expo-router to work
- **Files modified:** mobile/package.json
- **Commit:** 3091a12

## Known Stubs

None — infrastructure files have no data stubs. Screens are not built yet (Plans 03-04).

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: info-disclosure | mobile/.env.example | EXPO_PUBLIC_ vars documented; only anon key included, never service role key (T-06-06 accepted) |

## Self-Check: PASSED

- mobile/lib/supabase.ts — FOUND
- mobile/lib/pushToken.ts — FOUND
- mobile/hooks/useAuth.tsx — FOUND
- mobile/app/_layout.tsx — FOUND
- Commit 3091a12 — FOUND (Task 1)
- Commit 8b6cbd7 — FOUND (Task 2)
- `detectSessionInUrl: false` count: 1
- `Device.isDevice` count: 1
