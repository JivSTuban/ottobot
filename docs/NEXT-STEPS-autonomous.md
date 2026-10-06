# Next steps: build the Filipinohomes MVP with minimal human involvement

**Written:** 2026-10-06. **Goal:** Jiv does one short unblock pass, then agents build the MVP to a machine-checked Definition of Done. Jiv reviews the finished result, not the work in progress.

**Principle:** nothing real-world-facing runs unattended. "MVP done" means pilot-ready and verified by tests and screenshots, in **shadow mode** (the agent drafts, nothing is sent to a real lead). Going live with real leads is a separate human decision after the build.

Source requirements: `docs/PRD-filipinohomes-mvp.md` (v2). Research: `docs/research/2026-10-06-filipinohomes-deep-research.md` (read its CONFIRMED section only).

---

## 0. Reconcile first (do this before any build step)

Another session wrote a **PRD v3.0** on `origin/docs/prd-filipino-homes-nurture` (`PRD.md` + `PRD.pdf`, commits `2e923fa`, `0bbf10a`, 2026-10-06 16:52 to 16:57). It says it combines this repo's v2 with a lead-nurture track and a GoHighLevel record layer. It was not read in the session that wrote this file, so what it adds or changes is **unverified**.

The run's first action: read it, diff it against v2, and produce **one** PRD (do not keep two). Rule: v3.0 wins where it is newer and consistent with the research file; anything in it that rests on an unverified claim is marked as such. Record the merge in `docs/PRD-filipinohomes-mvp.md`.

Also: the Mac Mini clone at `/Users/admin/agent-work/ottobot` is currently on `docs/prd-filipino-homes-nurture` with an untracked file, so another session is active there. Do not switch its branch or `git add -A` there.

---

## 1. What only a human can do

Batched so it happens once, up front. Ordered by how early it blocks something. **None of these block the build**; the ones marked GO-LIVE block only real leads.

| # | Item | Why a human | Blocks |
|---|---|---|---|
| H1 | **Revoke the GHL tokens** that were pasted into chat (the dealership location keys and the private integration token). Also rotate the Supabase token in `~/.claude.json`. | They are credentials to other people's systems, now in session transcripts. Only the owner can revoke. | Nothing, but do it now |
| H2 | Paste the launch command (section 6) | One action | Everything |
| H3 | Send the discovery message (appendix A) to the Filipinohomes contact | Needs a person-to-person conversation | GO-LIVE |
| H4 | Meta app and Page access for Lead Ads (App Review takes days, needs a Filipinohomes Page admin) | Business identity and approval | GO-LIVE (real lead ingestion) |
| H5 | Semaphore sender name, Viber sender registration | Business identity | GO-LIVE (real sends) |
| H6 | AI-disclosure policy (PRD D3) and a lawyer's view on broker-licensing exposure | Legal and product judgment | GO-LIVE |
| H7 | Physical-device walk for push notifications (closes Phase 06 UAT 6 to 11) | Needs a phone | Only UAT closure |
| H8 | Commercial terms with Filipinohomes | Business | Nothing technical |
| H9 | `claude login` on the Mac Mini, if you want runs there (verified 2026-10-06 evening: Claude Code 2.1.153 installed, `loggedIn: false`; `gh` is logged in as JivSTuban) | Browser OAuth | Only Mini runs |
| H10 | Give Gabe repo access and his handle, if Gabe should push (the repo is public to read, but pushing needs collaborator access) | Only the owner can invite | Only Gabe's direct pushes |

**Not in scope, by decision:** pulling real dealership conversations from the Crowdsnare client accounts. Access was not verified in writing, the tokens are stale or invalid, and the data is third-party customer PII. The eval set is built from synthetic Taglish conversations instead (item J7). No agent may use those credentials.

---

## 2. What agents do themselves (so you do not have to)

| Was manual | How it is removed |
|---|---|
| Clerk test user + business row | Clerk Backend API: `POST /users`, `POST /sign_in_tokens`, `POST /sessions/{id}/tokens` (all present in Clerk's spec version 2026-05-12, verified). Needs `CLERK_SECRET_KEY`, which an agent can copy from the logged-in Clerk dashboard via Playwright (clipboard route, never printed). First E2E assertion: the minted token carries the `email` claim. Password is generated and stored in the macOS Keychain. |
| Phone E2E | API-level E2E with a real Clerk token against Neon; `tsc`, `expo export --platform ios`, and an Expo **web** render checked with Playwright screenshots. Push delivery is covered by unit tests at the Expo push layer; the real device walk stays H7. |
| Test data isolation | A Neon `test` branch (copy-on-write) so tests never touch `production`. |
| Real channels not available yet | Fixture payloads and a fake sender: Meta leadgen webhook (`leadgen_id`, then Graph fetch, per Meta docs updated 2026-05-21), Messenger, Semaphore. Contract tests assert what would have been sent. |
| Fear of the AI messaging a real lead | `SEND_MODE=shadow` by default: replies are stored as drafts (`messages.status='draft'`), nothing is sent. `live` requires a deliberate env change plus H3 to H6. |
| Eval data for Taglish | Agent-authored synthetic set of 30 conversations (budget, location, pre-selling vs ready-for-occupancy, financing, OFW, viewing), scored by script. |
| Model choice | Bake-off on that set using the keys already in `.env` (Groq, Mistral). Winner recorded in `litellm_config.yaml` with the scores. |
| Reviews | `/dev-review` and a code-review pass per wave, fixed by the agent. |

---

## 3. Run order (waves, with gates)

Method: `superpowers:subagent-driven-development` (fresh implementer + reviewer per task, ledger in `.superpowers/sdd/`). Item IDs are from PRD section 7.

**Wave 0, setup:** section 0 reconcile; allowlist pass (`/fewer-permission-prompts`); `CLERK_SECRET_KEY` into `.env`; Neon `test` branch; freeze `docs/api-contract.md` (lead object, message object, handoff payload, metrics events, `/leads` `/metrics` `/agents` shapes).

**Wave 1 (parallel):**
- G1: plan Tasks 7, 8, 10; wire the restrained login into `mobile/app/login.tsx`; delete `mobile/lib/supabase.ts`; `git grep -i supabase` must reach zero outside docs and archive.
- J1 + J7: real-estate agent v2 (qualification fields), synthetic eval set, model bake-off.
- J2: lead ingestion (leadgen fetch, CSV, dedupe), fixtures only.

**Wave 2:** J3 tenant routing (replace `BUSINESS_ID` env, two-tenant isolation test) + shadow mode; J5 consent, opt-out, audit log; J6 metrics events and `/metrics`; G3 inbox; G4 roster and assignment.

**Wave 3:** J4 handoff (assigned agent, summary, push); G5 pilot dashboard; G6 mobile screens.

**Wave 4:** integration E2E, Playwright screenshots of every new screen, docs in the same commits (`README.md`, `.env.example`, `docs/api-contract.md`), open **one PR** (do not merge).

**Gate after every wave:** `pytest` green, `cd mobile && npx tsc --noEmit` clean, `npx expo export --platform ios` clean, `cd frontend && npm test` green, `/dev-review` clean, `graphify update .`. A red gate is fixed before the next wave starts.

Gabe's items (G1 to G6) are filed as GitHub issues labeled `gabe` so he can claim any of them; if unclaimed when its wave starts, an agent takes it. No wave waits on a person.

---

## 4. Definition of Done (all machine-checkable)

1. `pytest` all green, including a two-tenant isolation test and a shadow-mode test (no outbound send recorded).
2. Mobile `tsc` and `expo export --platform ios` clean; frontend tests green.
3. `git grep -i supabase` returns only docs and archive.
4. API E2E script passes with a real Clerk token: `/me/business`, `/leads`, `/leads/{id}/messages`, handoff, `/metrics`.
5. A Meta leadgen **fixture** creates exactly one deduped lead and one shadow first reply within the test's time budget.
6. Qualification fields (RE-01) are stored and shown for a scripted conversation; eval pass rate and the chosen model are recorded.
7. Opt-out stops all sends within one turn; consent and opt-out are queryable.
8. Dashboard shows median first-reply (AI vs human), funnel, and per-agent table, proven by Playwright screenshots in `docs/mvp-report/`.
9. `docs/MVP-REPORT.md` exists: DoD results, screenshots, decisions taken on defaults, everything blocked.
10. One PR open, not merged, CI-equivalent checks green locally.

---

## 5. Stop rules (write to `BLOCKED.md`, keep working on other items, never ask)

Agents must **not**, without a human: send any message to a real person or lead; use the Crowdsnare or GHL credentials in any way; merge or force-push, or touch `main`; spend money or start a paid plan; run destructive SQL on Neon `production`; state any fact about Filipinohomes that is not in the research file's CONFIRMED section; or switch the Mac Mini clone's branch.

Same failure three times: write a `FAILURES.md` entry, mark the item blocked, move on to an independent item.

---

## 6. Launch (one paste)

In a fresh session in `~/Desktop/ottobot` (keep the laptop awake with `caffeinate -dimsu`):

```
/refresh
/loop Execute docs/NEXT-STEPS-autonomous.md from section 0 through section 4. Never ask me anything; follow section 5 for blockers. Stop only when the Definition of Done is fully green or every remaining item is in BLOCKED.md.
```

To run on the Mac Mini instead (survives a closed laptop): do H9, then in tmux there run the same prompt with `claude` in `/Users/admin/agent-work/ottobot` on a **separate branch** (not the one currently checked out there). Frontend and mobile `node_modules` are not installed on the Mini yet (verified), so Wave 0 there must run `npm ci` in `frontend/` and `mobile/` first (`--legacy-peer-deps` for mobile).

---

## 7. What you check when you come back (about 10 minutes)

1. `docs/MVP-REPORT.md` and the screenshots.
2. The PR (diff and checks).
3. `BLOCKED.md`: each entry is a decision only you can make.
4. The go-live checklist: H3 to H6, then flip `SEND_MODE=live` for a small agent group.

---

## Appendix A: message to the Filipinohomes contact (copy, edit, send)

> Hi [name], we have a working first version of an assistant that answers buyer inquiries in Tagalog, Taglish or English within seconds, asks the key questions (budget, location, pre-selling or ready-for-occupancy, financing, OFW or not), and hands the lead to the right agent with a summary. Before we pilot it with your team, could you tell us:
> 1. Where do inquiries reach your agents today (the site's message button, email, Facebook lead ads, calls)? Can we get a webhook or an email forward?
> 2. Roughly how many inquiries per month, and what is the real first-reply time today?
> 3. Which channels do your buyers actually use (Messenger, Viber, SMS, calls)?
> 4. Who manages your Facebook Page and ad accounts?
> 5. Which agents would join a small pilot, and how should leads be assigned?
> 6. What privacy or consent wording do your forms use today?
> 7. Are inquiries handled on behalf of licensed brokers, and who supervises?
> 8. How would you like to handle the pilot commercially?
>
> We would start in "shadow mode": the assistant drafts replies and your agents send them, so no buyer gets an automated message until you are comfortable.
