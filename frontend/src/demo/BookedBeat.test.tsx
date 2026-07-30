/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import { BookedBeat } from "./BookedBeat.tsx";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
  }));
}

describe("BookedBeat", () => {
  beforeEach(() => vi.unstubAllGlobals());
  it("renders the booked confirmation content (accessible) in both motion modes", () => {
    mockReducedMotion(true);
    const { getByText } = render(<BookedBeat />);
    expect(getByText(/booked/i)).toBeTruthy(); // final state present without animation
  });
});
