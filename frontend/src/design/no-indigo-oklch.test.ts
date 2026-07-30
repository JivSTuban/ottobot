/** @vitest-environment node */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const indexCss = readFileSync(
  fileURLToPath(new URL("../index.css", import.meta.url)), "utf8",
);

describe("no leftover indigo oklch defaults", () => {
  // shadcn v4 ships `.dark --sidebar-primary: oklch(0.488 0.243 264.376)` — hue 264 = indigo.
  it("has no oklch color with an indigo/violet hue (250–290)", () => {
    const matches = [...indexCss.matchAll(/oklch\(\s*[\d.]+\s+[\d.]+\s+([\d.]+)/g)];
    const indigo = matches.map((m) => Number(m[1])).filter((h) => h >= 250 && h <= 290);
    expect(indigo).toEqual([]);
  });

  // Regression guard: the brand --accent (signal green) must never be remapped to a
  // surface var — doing so cascades into --primary/--ring and renders the CTA gray.
  it("never remaps the brand --accent to a surface var", () => {
    expect(indexCss).not.toMatch(/--accent:\s*var\(--surface/);
  });

  it("keeps --color-primary wired to the brand --accent", () => {
    expect(indexCss).toMatch(/--color-primary:\s*var\(--accent\)/);
  });
});
