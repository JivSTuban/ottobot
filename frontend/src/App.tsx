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

import { useState, useMemo } from "react";
import type { IndustryKey } from "./assets/personas";
import { PERSONA_ASSETS } from "./assets/personas";
import { IndustrySelector } from "./IndustrySelector";
import { LeadChat } from "./LeadChat";
import { OwnerPanel } from "./OwnerPanel";
import { useWebSocket } from "./useWebSocket";
import "./index.css";

function App() {
  const [industry, setIndustry] = useState<IndustryKey | null>(null);

  // threadId is stable for the lifetime of this page load — uuid4 per T-06-01
  const threadId = useMemo(() => crypto.randomUUID(), []);

  // WebSocket URL — useMemo ensures the hook only re-opens on URL change
  const wsUrl = useMemo(() => `ws://localhost:8000/ws/${threadId}`, [threadId]);

  const { messages, stage, escalated, systemAlert, send, wsError } = useWebSocket(wsUrl);

  function handleSend(text: string) {
    if (industry) {
      send(text, industry);
    }
  }

  const asset = industry ? PERSONA_ASSETS[industry] : null;

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
            height: "100vh",
          }}
        >
          <LeadChat
            messages={messages}
            onSend={handleSend}
            agentName={asset?.agentName ?? ""}
            industrySrc={asset?.industrySrc ?? ""}
          />
          <OwnerPanel
            messages={messages}
            stage={stage}
            escalated={escalated}
            industry={industry}
          />
        </main>
      )}
    </>
  );
}

export default App;
