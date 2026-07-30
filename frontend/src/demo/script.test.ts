import { describe, it, expect } from "vitest";
import { demoScript, advance } from "./script.ts";
import { stageToLeadStatus } from "../types.ts";

describe("demo script", () => {
  it("ends in a booked state", () => {
    const last = demoScript[demoScript.length - 1];
    expect(stageToLeadStatus(last.stage)).toBe("booked");
  });
  it("advance walks to the end then clamps", () => {
    expect(advance(0)).toBe(1);
    expect(advance(demoScript.length - 1)).toBe(demoScript.length);
    expect(advance(demoScript.length)).toBe(demoScript.length);
  });
  it("alternates lead/agent authorship plausibly and is non-trivial", () => {
    expect(demoScript.length).toBeGreaterThanOrEqual(6);
    expect(new Set(demoScript.map((s) => s.author))).toEqual(new Set(["lead", "agent"]));
  });
});
