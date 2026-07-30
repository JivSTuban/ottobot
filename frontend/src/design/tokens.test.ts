import { describe, it, expect } from "vitest";
import { tokens, cssVars } from "./tokens.ts";
import { cssVars as cssVarsFn } from "./cssVars.ts";

describe("design tokens", () => {
  it("locks the signal-green accent for both themes", () => {
    expect(tokens.light.accent).toBe("#059669");
    expect(tokens.dark.accent).toBe("#10B981");
  });

  it("uses non-blue-tinted neutrals in light", () => {
    expect(tokens.light.bg).toBe("#FFFFFF");
    expect(tokens.light.border).toBe("#E8E8EA");
  });

  it("keeps identical token keys across light and dark (parity)", () => {
    expect(Object.keys(tokens.light).sort()).toEqual(Object.keys(tokens.dark).sort());
  });

  it("maps booked status to the accent", () => {
    expect(tokens.light.statusBooked).toBe(tokens.light.accent);
  });

  it("emits kebab-case CSS variables", () => {
    const out = cssVarsFn(tokens.light);
    expect(out).toContain("--accent: #059669;");
    expect(out).toContain("--surface-2: #F0F0F2;");
    expect(out).toContain("--text-muted: #6B7280;");
  });
});
