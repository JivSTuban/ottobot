/**
 * Shared TypeScript types for OttoBot demo UI.
 *
 * Stage values match backend ConversationState["stage"] in agent/models.py.
 * LeadStatus values are derived for the OwnerPanel stage badge display.
 */

/** Backend conversation stage values */
export type Stage =
  | "intro"
  | "qualify"
  | "pitch"
  | "objection_handling"
  | "propose_appointment"
  | "confirm"
  | "escalate";

/** Lead status for OwnerPanel stage badge display */
export type LeadStatus = "new" | "qualifying" | "hot" | "booked";

/** A single message in the conversation */
export interface Message {
  role: "user" | "assistant";
  content: string;
  /** True while the assistant is still streaming tokens into this bubble */
  streaming?: boolean;
}

/**
 * Maps backend Stage to frontend LeadStatus for the OwnerPanel stage badge.
 *
 * Mapping per UI-SPEC stage badge table:
 * - intro -> qualifying (agent has opened conversation)
 * - qualify -> qualifying
 * - pitch / objection_handling / propose_appointment -> qualifying
 * - confirm -> booked
 * - escalate -> hot
 * - default -> new
 */
export interface AvailabilitySlot {
  iso: string;     // ISO 8601 datetime string, e.g. "2026-06-20T14:00:00+08:00"
  display: string; // Tagalog formatted string, e.g. "Mayroon kaming bakante sa..."
}

export interface AppointmentMessage {
  type: "confirm_appointment";
  thread_id: string;
  proposed_time: string;        // ISO 8601 datetime
  action: "confirm" | "counter";
  counter_time?: string;        // Only present when action == "counter"
}

export function stageToLeadStatus(stage: Stage): LeadStatus {
  switch (stage) {
    case "intro":
    case "qualify":
      return "qualifying";
    case "pitch":
    case "objection_handling":
    case "propose_appointment":
      return "qualifying";
    case "confirm":
      return "booked";
    case "escalate":
      return "hot";
    default:
      return "new";
  }
}
