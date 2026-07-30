// mobile/theme/tokens.ts — pure values; keep in sync with frontend/src/design/tokens.ts
// NO tamagui/RN imports — this module is imported by the vitest parity test in the web project.
export const mobileTokens = {
  light: {
    bg: "#FFFFFF", surface: "#F7F7F8", surface2: "#F0F0F2", border: "#E8E8EA",
    text: "#18181B", textMuted: "#6B7280", accent: "#059669", accentFg: "#FFFFFF",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: "#059669", statusEscalated: "#EF4444",
  },
  dark: {
    bg: "#0B0C0E", surface: "#141517", surface2: "#1B1D20", border: "#232428",
    text: "#FAFAFA", textMuted: "#9CA3AF", accent: "#10B981", accentFg: "#04231A",
    statusNew: "#64748B", statusQualifying: "#3B82F6", statusHot: "#F59E0B",
    statusBooked: "#10B981", statusEscalated: "#EF4444",
  },
} as const;
