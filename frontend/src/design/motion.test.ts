import { describe, it, expect, vi, beforeEach } from "vitest";
import { transition, easing } from "./motion.ts";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {},
  }));
}

describe("motion helpers", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("builds a transform+ease-out transition under 300ms by default", () => {
    mockReducedMotion(false);
    expect(transition("transform")).toBe(`transform 200ms ${easing.out}`);
  });

  it("honors the fast token", () => {
    mockReducedMotion(false);
    expect(transition("opacity", "fast")).toBe(`opacity 120ms ${easing.out}`);
  });

  it("returns 'none' when reduced motion is requested", () => {
    mockReducedMotion(true);
    expect(transition("transform")).toBe("none");
  });
});
