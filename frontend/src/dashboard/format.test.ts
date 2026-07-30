import { describe, it, expect } from "vitest";
import { conversionPct, fmtNum } from "./format.ts";

describe("dashboard formatters", () => {
  it("conversionPct is 0 when there are no leads", () => expect(conversionPct(0, 0)).toBe(0));
  it("conversionPct rounds to a whole percent", () => expect(conversionPct(9, 20)).toBe(45));
  it("fmtNum groups thousands", () => expect(fmtNum(3547)).toBe("3,547"));
});
