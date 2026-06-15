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
