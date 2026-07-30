export interface TokenSet {
  bg: string; surface: string; surface2: string; border: string;
  text: string; textMuted: string; accent: string; accentFg: string;
  statusNew: string; statusQualifying: string; statusHot: string;
  statusBooked: string; statusEscalated: string;
}

const ACCENT_LIGHT = "#059669";
const ACCENT_DARK = "#10B981";

export const tokens: { light: TokenSet; dark: TokenSet } = {
  light: {
    bg: "#FFFFFF", surface: "#F7F7F8", surface2: "#F0F0F2", border: "#E8E8EA",
    text: "#18181B", textMuted: "#6B7280", accent: ACCENT_LIGHT, accentFg: "#FFFFFF",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: ACCENT_LIGHT, statusEscalated: "#EF4444",
  },
  dark: {
    bg: "#0B0C0E", surface: "#141517", surface2: "#1B1D20", border: "#232428",
    text: "#FAFAFA", textMuted: "#9CA3AF", accent: ACCENT_DARK, accentFg: "#04231A",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: ACCENT_DARK, statusEscalated: "#EF4444",
  },
};

export const radius = { input: 6, card: 8, modal: 10 } as const;
export const motion = { fast: 120, base: 200, slow: 280 } as const;

// Re-export so tests importing from "./tokens" also get cssVars.
export { cssVars } from "./cssVars.ts";
