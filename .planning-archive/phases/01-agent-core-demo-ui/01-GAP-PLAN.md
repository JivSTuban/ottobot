---
phase: 01-agent-core-demo-ui
plan: GAP
type: execute
wave: 1
depends_on: []
files_modified:
  - agent/graph.py
  - agent/state.py
  - api/main.py
autonomous: true
requirements: [AGENT-01, AGENT-04, DEMO-03]
gap_closure: true

must_haves:
  truths:
    - "Reconnect with same threadId resumes conversation from Supabase checkpoint without Mistral extra_forbidden error"
    - "Escalation alert fires (escalated=true + system_alert event) when user sends a booking phrase"
    - "Stage advances beyond intro through qualify → pitch → escalate in a live conversation"
  artifacts:
    - path: "agent/graph.py"
      provides: "_normalize_message strips LangChain metadata; stage nodes registered; route_next_stage loops back to 'agent' via conditional edges"
    - path: "agent/state.py"
      provides: "system_alert field added to ConversationState"
    - path: "api/main.py"
      provides: "SUPABASE_DB_URI falls back to SUPABASE_DIRECT_URL before InMemorySaver"
  key_links:
    - from: "agent/graph.py route_next_stage"
      to: "agent node"
      via: "conditional edge returning 'agent' after updating stage in state"
      pattern: "add_conditional_edges.*agent.*route_next_stage"
    - from: "api/ws_handler.py"
      to: "state.system_alert"
      via: "aget_state → values.get('system_alert')"
      pattern: "system_alert"
---

<objective>
Close two UAT-blocking gaps in Phase 1:

1. Supabase checkpoint restore fails — Mistral API rejects LangChain message metadata fields
   (additional_kwargs, response_metadata, type, id) with extra_forbidden; Supabase pooler
   ENOTFOUND on projects <24h old (propagation lag) causes InMemorySaver fallback.

2. Escalation alert never fires — graph only has one node ('agent'); route_next_stage returns
   stage names that are not registered nodes, so LangGraph writes to unknown channels and routes
   to END; stage never advances past intro.

Purpose: UAT tests 2 and 5 must pass before Phase 1 is fully closed.
Output: Updated agent/graph.py, agent/state.py, api/main.py.
</objective>

<execution_context>
@/Users/jivtuban/.claude/gsd-core/workflows/execute-plan.md
@/Users/jivtuban/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@agent/graph.py
@agent/state.py
@api/main.py
@api/ws_handler.py
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Fix LangGraph routing — loop agent node with stage updates</name>
  <files>agent/graph.py, agent/state.py</files>
  <behavior>
    - route_next_stage("intro") → returns "agent" (loops back, stage updated to "qualify" in state)
    - route_next_stage("escalate") or booking phrase → returns END
    - After agent_node runs with stage="escalate", state.escalated == True and state.system_alert is set
    - stage advances: intro → qualify → pitch → objection_handling → propose_appointment → confirm → escalate
    - Tests in tests/test_graph_routing.py cover each stage transition and escalation trigger
  </behavior>
  <action>
    Root cause: add_conditional_edges("agent", route_next_stage) returns stage strings like "qualify"
    that are not registered nodes. LangGraph silently ignores them and routes to END.

    Fix approach — loop 'agent' back to itself with updated stage (not separate stage nodes):

    1. In agent/state.py — add system_alert field to ConversationState TypedDict:
       system_alert: str  # populated by agent_node when escalated=True; consumed by ws_handler state event

    2. In agent/graph.py — modify route_next_stage to return either "agent" or END:
       - Map all stage names to "agent" (loop back) except when current stage is "escalate" → return END
       - Before returning "agent", the CALLER (agent_node) must have already written next_stage to state.
         PROBLEM: route_next_stage is sync and reads state AFTER agent_node ran — it cannot write to state.

       CORRECT design: agent_node computes next_stage and writes it; route_next_stage just checks whether
       to continue or end:
         - agent_node: at the end of each turn, call route_next_stage logic inline to derive next_stage,
           write {"stage": next_stage} into its return dict.
         - route_next_stage (conditional edge): simply reads state["stage"] — if "escalate", return END;
           otherwise return "agent".
         - This means stage progression logic moves INTO agent_node's return value, and the conditional
           edge is a pure end-check.

    3. In agent_node — after computing reply, call a new helper _compute_next_stage(state, reply) that
       applies the same priority logic currently in route_next_stage:
         Priority 1: escalation_scorer(state)
         Priority 2: BOOKING_PHRASES_FAST in last lead msg
         Priority 3: visit_count guard
         Priority 4: D-08 bidirectional positive sentiment
         Priority 5: _STAGE_PROGRESSION[current]
       Return {"stage": next_stage, "escalated": next_stage == "escalate", "system_alert": alert_msg_or_empty}
       where alert_msg is set only when next_stage == "escalate":
         system_alert = f"Hot lead detected. Contact the lead now. Stage: {current}"

    4. Rename route_next_stage to _end_or_continue — it only returns END if state["stage"] == "escalate",
       else returns "agent". Keep the function name route_next_stage as a public export alias for backward
       compat with tests.

    5. Update add_conditional_edges call:
         builder.add_conditional_edges("agent", route_next_stage, {"agent": "agent", END: END})
       The path_map explicitly maps the two possible return values.

    6. Write tests/test_graph_routing.py covering:
       - _compute_next_stage returns "qualify" when stage="intro" (linear progression)
       - _compute_next_stage returns "escalate" when booking phrase present
       - _compute_next_stage returns "escalate" when escalation_scorer fires
       - route_next_stage returns "agent" when stage != "escalate"
       - route_next_stage returns END when stage == "escalate"
       - agent_node return dict includes "stage", "escalated", "system_alert" keys
       Use MemorySaver and a minimal ConversationState dict for all tests (no real LLM call — mock
       router.acompletion to return a fixture response).

    Do NOT use asyncio.run() in tests — use pytest-asyncio with @pytest.mark.asyncio.
    Do NOT add new nodes to the graph — single-node looping design is intentional.
  </action>
  <verify>
    <automated>cd /Users/jivtuban/Desktop/ottobot && source .venv/bin/activate && python -m pytest tests/test_graph_routing.py -x -v 2>&1 | tail -30</automated>
  </verify>
  <done>All routing tests pass. route_next_stage returns "agent" for non-terminal stages and END for "escalate". agent_node return dict contains stage, escalated, system_alert keys. No "wrote to unknown channel" log lines appear during pytest.</done>
</task>

<task type="auto">
  <name>Task 2: Fix ws_handler to emit system_alert state event + fix Supabase direct URL fallback</name>
  <files>api/ws_handler.py, api/main.py</files>
  <action>
    GAP A — Supabase direct URL fallback (api/main.py):

    Supabase pooler hostnames use pgbouncer DNS that can take >24h to propagate on new projects.
    The direct connection URL (port 5432, not 6543) bypasses pgbouncer and resolves immediately.

    In the lifespan function, change the DB URI resolution order:
      db_uri = (
          os.environ.get("SUPABASE_DIRECT_URL")   # direct connection (port 5432) — try first
          or os.environ.get("SUPABASE_DB_URI", "")  # pooler (port 6543) — fallback
      )

    Also add SUPABASE_DIRECT_URL to the connection attempt log line so operators can see which
    URL was used:
      logger.info("Connecting to Postgres via: %s", db_uri[:40] + "…" if len(db_uri) > 40 else db_uri)

    Add SUPABASE_DIRECT_URL to .env.example (append line):
      SUPABASE_DIRECT_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres

    Note: The _normalize_message helper already exists in agent/graph.py (added during Plan 01-04)
    and is already called in agent_node. No additional message normalization changes are needed here.

    GAP B — Emit system_alert in ws_handler state event (api/ws_handler.py):

    After aget_state, the values dict now contains system_alert (added in Task 1).
    Update the {type:"state"} JSON payload to include it:

      await websocket.send_json({
          "type": "state",
          "stage": stage,
          "escalated": values.get("escalated", False),
          "system_alert": values.get("system_alert", ""),
      })

    The React OwnerPanel already reads the state event — it will display system_alert when
    escalated=True. No frontend changes needed (the field is additive; existing code ignores
    unknown keys).

    Do NOT change any LangGraph compilation logic beyond the URI resolution order.
    Do NOT remove the InMemorySaver fallback — it must remain for environments without Postgres.
  </action>
  <verify>
    <automated>cd /Users/jivtuban/Desktop/ottobot && source .venv/bin/activate && python -c "from api.main import lifespan, validate_thread_id; print('import OK')" 2>&1</automated>
  </verify>
  <done>api/main.py imports without error. SUPABASE_DIRECT_URL is tried before SUPABASE_DB_URI in lifespan. ws_handler state event JSON includes system_alert key. .env.example contains SUPABASE_DIRECT_URL line.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| WebSocket → LangGraph state | User text enters state.messages; already sanitized by guardrails |
| Postgres URL → lifespan | Connection string contains credentials; read from env only |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-GAP-01 | Information Disclosure | SUPABASE_DIRECT_URL log line | mitigate | Truncate URL to first 40 chars in log; password never logged |
| T-GAP-02 | Tampering | system_alert field in state | accept | system_alert is internal diagnostic string; not user-controlled input; never rendered as HTML |
| T-GAP-SC | Tampering | npm/pip/cargo installs | accept | No new packages installed in this gap plan |
</threat_model>

<verification>
Run full Phase 1 test suite after both tasks complete:

```
cd /Users/jivtuban/Desktop/ottobot && source .venv/bin/activate && python -m pytest tests/ -x -v --tb=short 2>&1 | tail -40
```

UAT recheck targets:
- Test 2 (Supabase persistence): Start API with SUPABASE_DIRECT_URL set — confirm "LangGraph compiled with AsyncPostgresSaver" in logs (not InMemorySaver fallback)
- Test 5 (Escalation alert): Send booking phrase "gusto ko mag-book" — confirm state event contains escalated=true and non-empty system_alert
</verification>

<success_criteria>
1. python -m pytest tests/test_graph_routing.py passes with 0 failures
2. No "wrote to unknown channel" warnings in pytest output or server logs
3. ws_handler {type:"state"} payload includes system_alert key
4. api/main.py resolves SUPABASE_DIRECT_URL before SUPABASE_DB_URI
5. .env.example documents SUPABASE_DIRECT_URL
6. Full test suite (tests/) passes without regression
</success_criteria>

<output>
Create `.planning/phases/01-agent-core-demo-ui/01-GAP-SUMMARY.md` when done
</output>
