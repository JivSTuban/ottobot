import type { TokenSet } from "./tokens.ts";

const KEBAB: Record<keyof TokenSet, string> = {
  bg: "bg", surface: "surface", surface2: "surface-2", border: "border",
  text: "text", textMuted: "text-muted", accent: "accent", accentFg: "accent-fg",
  statusNew: "status-new", statusQualifying: "status-qualifying", statusHot: "status-hot",
  statusBooked: "status-booked", statusEscalated: "status-escalated",
};

export function cssVars(set: TokenSet): string {
  return (Object.keys(set) as (keyof TokenSet)[])
    .map((k) => `--${KEBAB[k]}: ${set[k]};`)
    .join("\n");
}
