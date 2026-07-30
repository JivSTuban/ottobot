/**
 * OwnerPanel — right panel of the split-screen demo UI.
 *
 * Shows conversation mirror (read-only), stage badge, escalation alert,
 * and Appointments section (visible when stage == propose_appointment).
 * Receives state from App.tsx via props (all driven by useWebSocket hook).
 */

import { useState } from "react";
import type { Message, Stage, AppointmentMessage } from "./types";
import { stageToLeadStatus } from "./types";
import type { IndustryKey } from "./assets/personas";
import { PERSONA_ASSETS } from "./assets/personas";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { BookedBeat } from "./demo/BookedBeat.tsx";

interface OwnerPanelProps {
  messages: Message[];
  stage: Stage;
  escalated: boolean;
  industry: IndustryKey | null;
  /** Present when stage == propose_appointment */
  proposed_appointment?: string | null;
  /** Thread ID for confirm_appointment WebSocket message */
  thread_id?: string;
  /** WebSocket send function from useWebSocket hook */
  send?: (msg: string) => void;
  /** system_alert detail from the escalate state event */
  escalationAlert?: string | null;
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

/** Returns inline style color for the status dot based on LeadStatus */
function getStatusDotColor(leadStatus: ReturnType<typeof stageToLeadStatus>): string {
  switch (leadStatus) {
    case "new":
      return "var(--status-new)";
    case "qualifying":
      return "var(--status-qualifying)";
    case "hot":
      return "var(--status-hot)";
    case "booked":
      return "var(--status-booked)";
  }
}

export function OwnerPanel({ messages, stage, escalated, industry, proposed_appointment, thread_id, send, escalationAlert }: OwnerPanelProps) {
  const asset = industry ? PERSONA_ASSETS[industry] : null;
  const badgeLabel = getBadgeLabel(stage);
  const leadStatus = stageToLeadStatus(stage);
  const statusColor = getStatusDotColor(leadStatus);

  const [counterTime, setCounterTime] = useState("");
  const [showCounter, setShowCounter] = useState(false);

  const handleConfirm = () => {
    if (!send) return;
    const msg: AppointmentMessage = {
      type: "confirm_appointment",
      thread_id: thread_id ?? "",
      proposed_time: proposed_appointment ?? "",
      action: "confirm",
    };
    send(JSON.stringify(msg));
  };

  const handleCounter = () => {
    if (!counterTime.trim() || !send) return;
    const msg: AppointmentMessage = {
      type: "confirm_appointment",
      thread_id: thread_id ?? "",
      proposed_time: proposed_appointment ?? "",
      action: "counter",
      counter_time: counterTime.trim(),
    };
    send(JSON.stringify(msg));
    setCounterTime("");
    setShowCounter(false);
  };

  return (
    <section
      className="panel"
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        position: "relative",
        borderLeft: "1px solid var(--border)",
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
          background: "var(--bg)",
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
            minHeight: 64,
            background: "var(--destructive)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "8px 16px",
            fontSize: "14px",
            fontWeight: 600,
            color: "#ffffff",
            zIndex: 10,
            animation: "slideDown 200ms ease-in forwards",
          }}
        >
          <span>HOT LEAD — Tawagan na!</span>
          {escalationAlert && (
            <span
              className="escalation-detail"
              style={{ fontSize: "12px", fontWeight: 400, marginTop: 4, opacity: 0.9 }}
            >
              {escalationAlert}
            </span>
          )}
        </div>
      )}

      {/* Header strip */}
      <div
        style={{
          height: 48,
          minHeight: 48,
          background: "var(--surface)",
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
            color: "var(--text)",
          }}
        >
          Owner View
        </span>
        <Badge
          className={`badge badge-${leadStatus}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            fontSize: "12px",
            fontWeight: 600,
            transition: "background-color 200ms ease",
          }}
        >
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: statusColor,
              display: "inline-block",
              flexShrink: 0,
            }}
          />
          {badgeLabel}
        </Badge>
      </div>

      {/* Appointments section — visible only at propose_appointment stage */}
      {stage === "propose_appointment" && proposed_appointment && (
        <section
          className="appointments-section"
          aria-label="Appointments"
          style={{ position: "relative", zIndex: 1, padding: "var(--space-md)", borderTop: "1px solid var(--border)" }}
        >
          <h3 style={{ margin: "0 0 8px", fontSize: "14px", fontWeight: 600, color: "var(--text)" }}>
            Appointment Proposal
          </h3>
          <p className="proposed-time" style={{ margin: "0 0 12px", fontSize: "14px", color: "var(--text-muted)" }}>
            {proposed_appointment}
          </p>
          <div className="appointment-actions" style={{ display: "flex", gap: 8 }}>
            <Button variant="outline" onClick={handleConfirm}>Confirm</Button>
            <Button variant="outline" onClick={() => setShowCounter(!showCounter)}>Counter-propose</Button>
          </div>
          {showCounter && (
            <div className="counter-propose" style={{ marginTop: 8, display: "flex", gap: 8 }}>
              <Input
                type="text"
                value={counterTime}
                onChange={(e) => setCounterTime(e.target.value)}
                placeholder="e.g. Biyernes ng June 21 sa ika-3 ng hapon"
                aria-label="Counter-propose time"
                style={{ flex: 1 }}
              />
              <Button variant="outline" onClick={handleCounter}>Send Counter</Button>
            </div>
          )}
        </section>
      )}

      {/* BookedBeat hero moment — fires once when status reaches booked */}
      {leadStatus === "booked" && (
        <div
          style={{
            position: "relative",
            zIndex: 1,
            borderTop: "1px solid var(--border)",
          }}
        >
          <BookedBeat />
        </div>
      )}

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
          >
            {msg.content}
          </div>
        ))}
      </div>
    </section>
  );
}
