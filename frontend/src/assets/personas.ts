/**
 * Persona asset manifest for OttoBot demo UI.
 *
 * Maps each industry key to its avatar image path, industry background image path,
 * display labels, and persona name as defined in:
 *   - .planning/phases/01-agent-core-demo-ui/01-CONTEXT.md (D-12)
 *   - .planning/phases/01-agent-core-demo-ui/01-UI-SPEC.md (Copywriting Contract)
 *
 * All image paths are Vite public-asset paths (leading slash) served by the dev
 * server at port 5173. Do NOT inline image bytes here.
 */

/** Union of valid industry keys — matches backend `Industry` enum in agent/models.py */
export type IndustryKey = "dental" | "aesthetics" | "real_estate";

/** Shape of a single persona's asset bundle */
export interface PersonaAsset {
  /** Industry key — matches IndustryKey */
  industry: IndustryKey;
  /** Human-readable industry label, e.g. "Dental" */
  industryLabel: string;
  /** Agent display name using Filipino honorific, e.g. "Ate Ana" */
  agentName: string;
  /** Combined card label shown on industry selector cards, e.g. "Dental · Ate Ana" */
  cardLabel: string;
  /** Vite public-asset path to the persona avatar PNG (square, 1024x1024) */
  avatarSrc: string;
  /** Vite public-asset path to the industry background PNG (landscape, 1280x720) */
  industrySrc: string;
}

/**
 * Canonical map of industry key → persona asset bundle.
 *
 * Source of truth for D-12 persona-to-industry mapping.
 * Consumed by: IndustrySelector, LeadChatHeader, OwnerPanelHeader, EscalationBackground.
 */
export const PERSONA_ASSETS: Record<IndustryKey, PersonaAsset> = {
  dental: {
    industry: "dental",
    industryLabel: "Dental",
    agentName: "Ate Ana",
    cardLabel: "Dental · Ate Ana",
    avatarSrc: "/images/personas/ate-ana.png",
    industrySrc: "/images/industries/dental.png",
  },
  aesthetics: {
    industry: "aesthetics",
    industryLabel: "Aesthetics",
    agentName: "Ate Bea",
    cardLabel: "Aesthetics · Ate Bea",
    avatarSrc: "/images/personas/ate-bea.png",
    industrySrc: "/images/industries/aesthetics.png",
  },
  real_estate: {
    industry: "real_estate",
    industryLabel: "Real Estate",
    agentName: "Kuya Marco",
    cardLabel: "Real Estate · Kuya Marco",
    avatarSrc: "/images/personas/kuya-marco.png",
    industrySrc: "/images/industries/real-estate.png",
  },
};

/**
 * Look up the persona asset bundle for a given industry key.
 *
 * @param industry - One of the valid IndustryKey values
 * @returns The PersonaAsset for that industry
 */
export function getPersonaAsset(industry: IndustryKey): PersonaAsset {
  return PERSONA_ASSETS[industry];
}
