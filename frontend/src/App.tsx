/**
 * App.tsx — Top-level layout for OttoBot demo UI.
 *
 * State machine:
 *   1. industry === null → IndustrySelector startup screen
 *   2. industry !== null → Split-screen (LeadChat | OwnerPanel)
 *
 * Security notes:
 *   - threadId: crypto.randomUUID() only — uuid4 format; backend validates with close 1008 (T-06-01)
 *   - No dangerouslySetInnerHTML anywhere in this tree (T-06-02)
 */

import { useState, useMemo, useEffect, useRef, useCallback } from "react";
import type { IndustryKey } from "./assets/personas";
import { PERSONA_ASSETS } from "./assets/personas";
import { IndustrySelector } from "./IndustrySelector";
import { LeadChat } from "./LeadChat";
import { OwnerPanel } from "./OwnerPanel";
import { OnboardingWizard } from "./OnboardingWizard";
import { Dashboard } from "./Dashboard";
import { useWebSocket } from "./useWebSocket";
import { demoScript, advance } from "./demo/script.ts";
import type { Message, Stage } from "./types.ts";
import { Button } from "./components/ui/button";
import "./index.css";

/** Simple path-based router — avoids react-router dependency for 2 routes. */
function useRoute(): "onboarding" | "dashboard" | "demo" {
  const path = window.location.pathname;
  if (path === "/onboarding") return "onboarding";
  if (path === "/dashboard") return "dashboard";
  return "demo";
}

const DEMO_STEP_INTERVAL_MS = 1200;

function App() {
  const route = useRoute();
  const [industry, setIndustry] = useState<IndustryKey | null>(null);

  // threadId is stable for the lifetime of this page load — uuid4 per T-06-01
  const threadId = useMemo(() => crypto.randomUUID(), []);

  // WebSocket URL — useMemo ensures the hook only re-opens on URL change
  const wsUrl = useMemo(() => `ws://localhost:8000/ws/${threadId}`, [threadId]);

  const { messages, stage, escalated, systemAlert, escalationAlert, send, sendOutboundTrigger, wsError } = useWebSocket(wsUrl);

  // Demo playback state — independent of WebSocket
  const [demoMessages, setDemoMessages] = useState<Message[]>([]);
  const [demoStage, setDemoStage] = useState<Stage>("intro");
  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStepIdx, setDemoStepIdx] = useState(0);
  const demoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Whether we're in "demo playback" mode (industry picked + demo started)
  const isDemoMode = industry !== null && (demoRunning || demoMessages.length > 0);

  // Displayed messages and stage: demo overrides WebSocket when running
  const displayMessages = isDemoMode ? demoMessages : messages;
  const displayStage = isDemoMode ? demoStage : stage;
  const displayEscalated = isDemoMode ? false : escalated;
  const displayEscalationAlert = isDemoMode ? null : escalationAlert;

  const startDemo = useCallback(() => {
    if (demoRunning) return;
    setDemoMessages([]);
    setDemoStage("intro");
    setDemoStepIdx(0);
    setDemoRunning(true);
  }, [demoRunning]);

  // Step through demoScript on an interval while demoRunning
  useEffect(() => {
    if (!demoRunning) return;

    if (demoStepIdx >= demoScript.length) {
      setDemoRunning(false);
      return;
    }

    const step = demoScript[demoStepIdx];
    demoTimerRef.current = setTimeout(() => {
      const msg: Message = {
        role: step.author === "lead" ? "user" : "assistant",
        content: step.text,
      };
      setDemoMessages((prev) => [...prev, msg]);
      setDemoStage(step.stage);
      setDemoStepIdx((idx) => advance(idx));
    }, DEMO_STEP_INTERVAL_MS);

    return () => {
      if (demoTimerRef.current) clearTimeout(demoTimerRef.current);
    };
  }, [demoRunning, demoStepIdx]);

  // When the user picks an industry and clicks Simulan, Otto fires first.
  useEffect(() => {
    if (industry !== null && !isDemoMode) {
      sendOutboundTrigger(industry);
    }
  }, [industry]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleSend(text: string) {
    if (industry && !isDemoMode) {
      send(text, industry);
    }
  }

  const asset = industry ? PERSONA_ASSETS[industry] : null;

  if (route === "onboarding") {
    return <OnboardingWizard />;
  }

  if (route === "dashboard") {
    return <Dashboard />;
  }

  return (
    <>
      {/* System-level alert banner (type:system_alert WebSocket event) */}
      {systemAlert && (
        <div
          role="alert"
          className="system-alert-banner"
        >
          {systemAlert}
        </div>
      )}

      {/* WebSocket disconnect error */}
      {wsError && industry !== null && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            padding: "12px var(--space-lg)",
            background: "#422006",
            color: "#fb923c",
            fontSize: "14px",
            fontWeight: 600,
            textAlign: "center",
            zIndex: 200,
          }}
        >
          Nawala ang koneksyon. I-reload ang page.
        </div>
      )}

      {industry === null ? (
        /* Startup screen */
        <IndustrySelector onSelect={setIndustry} />
      ) : (
        /* Split-screen */
        <main
          className="split"
          style={{
            display: "flex",
            flexDirection: "column",
            height: "100vh",
          }}
        >
          {/* Demo controls bar — secondary button, NOT green */}
          <div
            style={{
              height: 40,
              minHeight: 40,
              background: "var(--surface)",
              borderBottom: "1px solid var(--border)",
              display: "flex",
              alignItems: "center",
              padding: "0 var(--space-lg)",
              gap: "var(--space-sm)",
            }}
          >
            <Button
              variant="secondary"
              size="sm"
              onClick={startDemo}
              disabled={demoRunning}
              style={{ fontSize: "12px", height: 28 }}
            >
              {demoRunning ? "Running demo…" : "Run demo"}
            </Button>
          </div>

          {/* Chat + panel row */}
          <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
            <LeadChat
              messages={displayMessages}
              onSend={handleSend}
              agentName={asset?.agentName ?? ""}
              industrySrc={asset?.industrySrc ?? ""}
            />
            <OwnerPanel
              messages={displayMessages}
              stage={displayStage}
              escalated={displayEscalated}
              industry={industry}
              escalationAlert={displayEscalationAlert}
            />
          </div>
        </main>
      )}
    </>
  );
}

export default App;
