/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
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
  beforeEach(() => vi.unstubAllGlobals());

  it("renders final metric values immediately under reduced motion", () => {
    mockRM(true);
    const { getByText } = render(
      <MetricRow
        metrics={{ leadsToday: 128, booked: 41, conversionPct: 32, avgResponseSec: 47 }}
      />
    );
    expect(getByText("128")).toBeTruthy();
    expect(getByText(/32%/)).toBeTruthy();
  });
});
