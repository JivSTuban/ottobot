import { describe, it, expect } from "vitest";
import { tokens } from "./tokens.ts";
import { mobileTokens } from "../../../mobile/theme/tokens.ts";

describe("web ↔ mobile token parity", () => {
  it("light values match exactly", () => {
    expect(mobileTokens.light).toEqual(tokens.light);
  });
  it("dark values match exactly", () => {
    expect(mobileTokens.dark).toEqual(tokens.dark);
  });
});
