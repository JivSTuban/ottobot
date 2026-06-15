/**
 * OwnerPanel — right panel of the split-screen demo UI.
 *
 * Shows conversation mirror (read-only), stage badge, and escalation alert.
 * Receives state from App.tsx via props (all driven by useWebSocket hook).
 */

import type { Message, Stage } from "./types";
import { stageToLeadStatus } from "./types";
import type { IndustryKey } from "./assets/personas";
import { PERSONA_ASSETS } from "./assets/personas";

interface OwnerPanelProps {
  messages: Message[];
  stage: Stage;
  escalated: boolean;
  industry: IndustryKey | null;
}

/** Maps LeadStatus to human-readable Filipino badge label */
function getBadgeLabel(stage: Stage): string {
  const status = stageToLeadStatus(stage);
  switch (status) {
    case "new":
      return "Bago";
    case "qualifying":
      return "Tinatasa";
    case "hot":
      return "HOT";
    case "booked":
      return "Naka-book";
  }
}

export function OwnerPanel({ messages, stage, escalated, industry }: OwnerPanelProps) {
  const asset = industry ? PERSONA_ASSETS[industry] : null;
  const badgeLabel = getBadgeLabel(stage);
  const leadStatus = stageToLeadStatus(stage);

  return (
    <section
      className="panel"
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        borderLeft: "1px solid #334155",
        // Industry background at very low opacity
        backgroundImage: asset ? `url(${asset.industrySrc})` : undefined,
        backgroundSize: "cover",
        backgroundPosition: "center",
      }}
    >
      {/* Background overlay to keep 8% opacity on background */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: "var(--bg-dominant)",
          opacity: 0.92,
          pointerEvents: "none",
          zIndex: 0,
        }}
      />

      {/* Escalation alert — slides down from top when escalated */}
      {escalated && (
        <div
          role="alert"
          className="escalation-alert"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: 64,
            background: "var(--destructive)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "14px",
            fontWeight: 600,
            color: "#ffffff",
            zIndex: 10,
            animation: "slideDown 200ms ease-in forwards",
          }}
        >
          HOT LEAD — Tawagan na!
        </div>
      )}

      {/* Header strip */}
      <div
        style={{
          height: 48,
          minHeight: 48,
          background: "var(--bg-secondary)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 var(--space-lg)",
          position: "relative",
          zIndex: 1,
        }}
      >
        <span
          style={{
            fontSize: "18px",
            fontWeight: 600,
            color: "var(--text-primary)",
          }}
        >
          Owner View
        </span>
        <span
          className={`badge badge-${leadStatus}`}
          style={{
            fontSize: "12px",
            fontWeight: 600,
            padding: "4px 8px",
            borderRadius: 4,
            transition: "background-color 200ms ease",
          }}
        >
          {badgeLabel}
        </span>
      </div>

      {/* Conversation mirror — read-only */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "var(--space-md)",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          position: "relative",
          zIndex: 1,
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`message-bubble ${msg.role === "user" ? "user" : "agent"}${
              msg.streaming ? " streaming-cursor" : ""
            }`}
            style={{
              background: msg.role === "user" ? "#2d2f3e" : "var(--bg-secondary)",
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              padding: "var(--space-sm)",
              borderRadius: 8,
              fontSize: "14px",
              color: "var(--text-primary)",
              maxWidth: "80%",
            }}
          >
            {msg.content}
          </div>
        ))}
      </div>
    </section>
  );
}
