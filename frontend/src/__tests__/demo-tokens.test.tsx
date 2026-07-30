// frontend/src/__tests__/demo-tokens.test.tsx
/** @vitest-environment node */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

const files = ["LeadChat.tsx", "OwnerPanel.tsx", "IndustrySelector.tsx"].map((f) =>
  readFileSync(fileURLToPath(new URL(`../${f}`, import.meta.url)), "utf8"),
).join("\n");

describe("demo components use the new token system", () => {
  it("references no removed legacy CSS vars", () => {
    for (const dead of ["--bg-dominant", "--bg-secondary", "--text-primary"]) {
      expect(files).not.toContain(dead);
    }
  });
  it("references no raw indigo hex", () => {
    expect(files.toLowerCase()).not.toContain("#6366f1");
  });
});
