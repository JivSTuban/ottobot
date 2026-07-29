# Task 6 Report: OttoBot Mobile Login Screen

**Date:** 2026-07-29  
**Task:** Brand-moment Clerk login screen — Moti motion + hero image + expo-linear-gradient

---

## Library Choice

**Final stack: Moti + expo-image + expo-linear-gradient + RN core primitives (StyleSheet)**

**Tamagui was NOT attempted.** Rationale:
- No `babel.config.js` existed in the project — adding a Tamagui babel plugin on top of the custom config required for reanimated (reanimated/plugin must be last) creates ordering fragility.
- Expo SDK 56 bundles its own `babel-preset-expo@56.0.15`; Tamagui's transformer can conflict.
- The spec explicitly provides this fallback: "Moti + expo-image + accessible RN core primitives styled via a small StyleSheet — still library-driven motion/media, no hand-rolled component framework."
- Moti delivers all the required motion language natively; it runs on top of react-native-reanimated which is the recommended animation layer for Expo.

**gluestack-ui v2** was not tried — Moti achieved all motion requirements without it.

---

## What Was Built

### `mobile/app/login.tsx` (full replacement)

- **Hero backdrop:** `expo-image` full-bleed, `contentFit="cover"`, wrapped in `MotiView` Ken-Burns (scale 1.06→1.14 + translateY 0→-12, 6s loop, `repeatReverse: true`).
- **Scrim:** `expo-linear-gradient` 4-stop from transparent → rgba dark → `#0f1117`, lower-half.
- **Indigo glow:** Soft `MotiView` radial circle (border-radius-based) behind wordmark, opacity pulse 0.12→0.28 on 2.8s loop.
- **Wordmark "OttoBot":** Spring fade+rise (translateY 26→0, opacity 0→1) at 150ms delay.
- **Tagline "Manage your leads.":** Same, 300ms delay.
- **Glass card:** Slides up (translateY 40→0 + opacity) at 450ms; `rgba(26,29,39,0.88)` bg with `rgba(99,102,241,0.18)` border.
- **Email field:** Staggered spring reveal at 650ms; native RN `TextInput`.
- **Password field:** Staggered at 750ms.
- **Gradient CTA "Log in":** `expo-linear-gradient` `#6366f1`→`#8b5cf6`, spring reveal at 900ms; wraps `TouchableOpacity` for native press.
- **"Forgot password?" link:** `Pressable`, English copy.
- **`useReducedMotion()`** from `react-native-reanimated` — all animations short-circuit to final state when reduced motion is active.
- **Auth:** `useSignIn()` from `@clerk/clerk-expo`; on `status === 'complete'` calls `setActive({ session: result.createdSessionId })`; English error strings: `'Incorrect email or password. Please try again.'` and `"Can't connect. Check your internet."`.
- **KeyboardAvoidingView** with `padding`/`height` per platform.

### `mobile/babel.config.js` (new)

```js
module.exports = (api) => {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: ['react-native-reanimated/plugin'],
  };
};
```

`react-native-reanimated/plugin` must be last — this config satisfies that.

### `mobile/lib/supabase.ts` (new stub)

Created to fix a pre-existing Metro resolution failure: `settings.tsx` still imports `../../lib/supabase` (Task 5 removed the real Supabase client but didn't update settings.tsx). This stub is intentionally minimal and clearly marked for removal when Task 7 migrates settings.tsx.

### `mobile/package.json` (modified)

Added:
- `moti@^0.30.0`
- `react-native-reanimated@^4.5.3`
- `react-native-worklets@^0.4.0` (reanimated v4 peer dep)
- `expo-image@^57.0.1`
- `expo-linear-gradient@^57.0.1`
- `expo-linking@^57.0.4` (expo-router peer dep, missing after npm churn)
- `expo-auth-session@^57.0.5` (clerk-expo peer dep, was missing)
- `expo-web-browser@^57.0.2` (clerk-expo peer dep, was missing)
- `react-dom@^19.2.8` (@clerk/clerk-react peer dep, was missing)
- `babel-preset-expo@^56.0.15` (devDep, pinned to SDK 56 matching version)

**Note:** `--legacy-peer-deps` was required throughout (pre-existing Expo peer tree requirement, same as Task 5).

**Critical discovery:** The original project (Task 5's Clerk setup) had a broken `expo export` bundle before my changes — `@clerk/clerk-expo` requires `expo-auth-session`, `expo-web-browser`, and `@clerk/clerk-react` requires `react-dom`, none of which were installed. My work fixed this pre-existing breakage as a side effect of getting the bundle clean.

---

## Motion Mapping (spec → implementation)

| Spec | Implementation |
|------|---------------|
| Hero Ken-Burns: scale 1.06→1.14 + upward drift, ~6s loop | `MotiView` wrapping `expo-image`: `from={scale:1.06,translateY:0}` `animate={scale:1.14,translateY:-12}`, timing 6000ms, loop+repeatReverse |
| Wordmark spring fade+rise, ~150ms | `MotiText` spring, delay 150ms, translateY 26→0, opacity 0→1 |
| Tagline, ~300ms delay | `MotiText` spring, delay 300ms |
| Glass card slides up, ~450ms | `MotiView` spring, delay 450ms, translateY 40→0 |
| Email field, ~650ms | `MotiView` spring, delay 650ms |
| Password field, ~750ms | `MotiView` spring, delay 750ms |
| CTA button, ~900ms | `MotiView` spring, delay 900ms |
| Radial glow, slow opacity pulse | `MotiView` timing 2800ms loop+repeatReverse, opacity 0.12→0.28 |
| `prefers-reduced-motion` | `useReducedMotion()` from reanimated — all `from`/`animate`/`transition` props omitted when true |

All springs use `damping: 20, stiffness: 220` — settles only, no overshoot bounce. Timing animations (Ken-Burns, glow pulse) use `type: 'timing'` as appropriate for looping effects.

---

## Gate Results

### tsc (`npx tsc --noEmit`)

Exit code 2 — errors present, but **login.tsx has zero errors**. All 5 remaining errors are in the pre-existing unmigrated screens:
- `app/(tabs)/conversation/[id].tsx`: 1 error (`.session` on useAuth)
- `app/(tabs)/pipeline.tsx`: 1 error (`.session` on useAuth)
- `app/(tabs)/settings.tsx`: 3 errors (`.session` + supabase stub type gaps + implicit any)

This is within the spec's allowed residual error set ("The ONLY residual errors allowed are in the still-unmigrated screens settings.tsx, pipeline.tsx, conversation/[id].tsx").

### expo export (`npx expo export --platform ios`)

**PASS — clean bundle.** Output:
```
iOS Bundled 5567ms node_modules/expo-router/entry.js (2074 modules)
› ios bundles (1):
  _expo/static/js/ios/entry-5a871027d5e2285ca8156e8d43e4834b.hbc (5.6MB)
```

The hero image (`assets/login-hero.png`, 1MB) was included in the 43 bundled assets.

---

## Visual Verification

No simulator available in this environment. The screen design was verified structurally through:
1. TypeScript type-checking (zero errors in login.tsx)
2. Metro bundle (all 2074 modules resolved, including expo-image, moti, reanimated, expo-linear-gradient)
3. Code review against the motion spec

Visual confirmation requires running on a device or simulator. The entrance animations, Ken-Burns effect, gradient CTA, and glass card should all render correctly given the clean bundle.

---

## Concerns

1. **`lib/supabase.ts` stub**: This stub has minimal typing — settings.tsx's supabase calls won't work at runtime (they'll get `Error('Supabase removed')`). This is correct behavior (settings.tsx is unmigrated) but Task 7 must remove the stub or replace it with real Clerk-based data fetching.

2. **react-native-worklets v0.4.0 + reanimated v4.5.3**: This is a new combination. Worklets is a first-party Reanimated peer dep (same org, Software Mansion). Bundle verified clean. Runtime behavior on device should be confirmed in first device test.

3. **Pre-existing Clerk peer dep gap (now fixed)**: The Task 5 Clerk integration was missing `expo-auth-session`, `expo-web-browser`, and `react-dom`. These are now installed. This means the Clerk sign-in hook should now have all its runtime deps.

4. **Glow blur**: Expo doesn't support native blur without `expo-blur`. The glow is an opacity-pulsing circle — softer-than-spec but avoids adding another dependency. Task 7 could add expo-blur if the visual needs sharpening.

---

## Files Changed

- `mobile/app/login.tsx` — full replacement
- `mobile/babel.config.js` — new
- `mobile/lib/supabase.ts` — new stub
- `mobile/package.json` — new deps added
- `mobile/package-lock.json` — updated

---
---

# Fix Report: Migration to Tamagui (no babel optimizer)

**Date:** 2026-07-29 (follow-up)  
**Change:** Per user requirement, migrated the login **form primitives** to **Tamagui** components while keeping everything else from the Moti+RN-core version (expo-image hero, Moti entrance motion, Clerk useSignIn flow, English copy, gradient CTA, glow pulse, reduced-motion gate).

## Tamagui setup used

- **Packages installed:** `tamagui@^2.6.0`, `@tamagui/config@^2.6.0` (both `--legacy-peer-deps`), plus `react-native-web@^0.21.2` (a hard peer dep — Tamagui unconditionally imports it in some views like `Anchor`; without it Metro/node resolution fails).
- **`tamagui.config.ts`** (new): `import { defaultConfig } from '@tamagui/config/v4'` → `createTamagui(...)`. Note the v4 export is named **`defaultConfig`**, NOT `config` (the coordinator's suggested `import { config }` name does not exist in `@tamagui/config@2.6.0`). Added the `declare module 'tamagui'` TS augmentation.
  - Two v4 default settings were relaxed so we could pass **longhand style props** and **raw brand hex** directly on components: `onlyAllowShorthands: false` and `allowedStyleValues: false`. (v4 defaults to `onlyAllowShorthands: true` + `allowedStyleValues: 'somewhat-strict-web'`, which reject `backgroundColor`/`justifyContent` longhands and non-token hex values.)
- **NO `@tamagui/babel-plugin`** was added — confirmed the fix. `babel.config.js` is unchanged: `babel-preset-expo` preset + `react-native-reanimated/plugin` (last). Tamagui components work at runtime without the optimizer plugin. This is what removed the Expo SDK 56 babel-ordering conflict.
- **No `metro.config.js` / `@tamagui/metro-plugin` needed.** The `expo export` bundle succeeded WITHOUT any metro plugin — so it was not added (YAGNI).

## Component mapping (RN-core → Tamagui)

| Before (RN core) | After (Tamagui) |
|---|---|
| `View` root / content / card | `YStack` (flex/justify/padding via props) |
| `TextInput` email + password | `Input` (bg/border/height/focus-border via props) |
| `TouchableOpacity` + `LinearGradient` CTA | `Button` (transparent, `overflow="hidden"`) with `LinearGradient` absolute-filled behind + `Spinner` for loading |
| `Text` (error, button label, forgot link) | Tamagui `Text` |
| `Pressable` forgot-password | `Button chromeless` |

**Unchanged:** expo-image Ken-Burns hero (MotiView), the LinearGradient scrim, the indigo glow pulse, all Moti spring reveal delays (wordmark 150 / tagline 300 / card 450 / email 650 / password 750 / CTA 900ms), `useReducedMotion()` gate, Clerk `useSignIn` + `setActive`, and the English copy/errors. `MotiView` wraps the Tamagui components with no issue.

One small type accommodation: Tamagui's `Input` types `placeholderTextColor` as `ColorTokens` (theme-token strings only), so the raw brand hex `#94a3b8` is passed via a centralized `mutedPlaceholder` cast const — runtime value is preserved.

## Gate results (Tamagui)

- **`npx tsc --noEmit`**: `login.tsx` and `tamagui.config.ts` are **error-free**. The only residual errors are the same 5 pre-existing ones in the unmigrated `settings.tsx` / `pipeline.tsx` / `conversation/[id].tsx` (`.session` on useAuth + the supabase-stub type gaps). Within spec.
- **`npx expo export --platform ios`**: **PASS — clean bundle.** `iOS Bundled 5620ms node_modules/expo-router/entry.js (2536 modules)` (up from 2074 pre-Tamagui — the delta is Tamagui's runtime). HBC output produced (6.9MB). Output dir deleted after. **This is the real proof that Tamagui-without-babel-plugin bundles cleanly on Expo SDK 56.**

## Files changed (this fix)

- `mobile/tamagui.config.ts` — new (createTamagui from v4 defaultConfig, relaxed shorthand/value settings)
- `mobile/app/_layout.tsx` — `TamaguiProvider config={tamaguiConfig} defaultTheme="dark"` wrapping inside `ClerkProvider`
- `mobile/app/login.tsx` — form primitives replaced with Tamagui `YStack`/`Input`/`Button`/`Text`/`Spinner`
- `mobile/package.json` + `package-lock.json` — added `tamagui`, `@tamagui/config`, `react-native-web`
- `mobile/babel.config.js` — **unchanged** (no Tamagui plugin, by design)

## Concerns

- **No visual verification** (no simulator): gates remain tsc + a clean Metro bundle only. The Tamagui `Input` focus-border, gradient `Button`, and glass `YStack` should render per props, but on-device confirmation is still pending.
- **`allowedStyleValues: false`** disables Tamagui's compile/runtime style-value validation globally. That is the intended trade-off to use raw brand hex freely; it slightly reduces Tamagui's guardrails. A future pass could migrate the brand palette into the Tamagui theme tokens and re-enable stricter validation.
- **`react-native-web`** is now a dependency even though this is a native-only app — it is a mandatory Tamagui peer, not optional.
- The `lib/supabase.ts` stub and the added Clerk peer deps (`expo-auth-session`, `expo-web-browser`, `react-dom`) from the first pass are retained — still required for a clean bundle until Task 7 migrates the tab screens.

---
---

# Fix Report: emil-design-eng craft pass

**Date:** 2026-07-29 (follow-up 2)  
**Scope:** `mobile/app/login.tsx` only. 3 changes, transform+opacity only, no new deps.

1. **Tighter entrance stagger.** Retimed the reveal delays from 150/300/450/650/750/900ms to snappy 30–80ms gaps: wordmark **0**, tagline **70**, card **140**, email **210**, password **280**, CTA **350** (ms). Same spring preset (damping 20 / stiffness 220). Net settle drops from ~1.3s to ~0.7s.
2. **Scale press feedback.** Added `scale: 0.97` to the Log-in `Button` `pressStyle` (alongside existing opacity 0.85), and `scale: 0.98` to the "Forgot password?" chromeless button `pressStyle`. Button now physically depresses on press.
3. **Static reduced-motion glow.** Replaced the `{!reduceMotion && <MotiView.../>}` removal with a branch: when `reduceMotion` is true, render the glow as a plain `View` at `opacity: 0.2` (its mid/rest value) so reduced-motion users keep the design layer — movement removed, opacity/color kept. Added `View` to the react-native import.

**Gate results:**
- `npx tsc --noEmit`: `login.tsx` clean; only the same 5 residual errors in the 3 unmigrated tab screens (settings/pipeline/conversation).
- `npx expo export --platform ios`: clean bundle — `iOS Bundled 5609ms (2536 modules)`, no errors. Output dir deleted.
