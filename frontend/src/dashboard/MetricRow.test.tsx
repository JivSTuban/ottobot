/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import gsap from "gsap";
import { MetricRow } from "./MetricRow.tsx";

function mockRM(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"),
    media: q,
    addEventListener() {},
    removeEventListener() {},
    addListener() {},
    removeListener() {},
  }));
}

describe("MetricRow", () => {
  beforeEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders final metric values immediately under reduced motion and runs no tween", () => {
    mockRM(true);
    const gsapTo = vi.spyOn(gsap, "to");
    const { getByText } = render(
      <MetricRow
        metrics={{ leadsToday: 128, booked: 41, conversionPct: 32, avgResponseSec: 47 }}
      />
    );
    // Final values are present synchronously on first render — no rAF/tween required.
    expect(getByText("128")).toBeTruthy();
    expect(getByText(/32%/)).toBeTruthy();
    // Non-vacuous: assert no count-up tween fired under reduced motion.
    expect(gsapTo).not.toHaveBeenCalled();
  });
});
