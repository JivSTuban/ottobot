/** @vitest-environment jsdom */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useAnimate } from "./useAnimate.ts";

function mockReducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: on && q.includes("reduce"), media: q,
    addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {},
  }));
}

describe("useAnimate", () => {
  beforeEach(() => vi.unstubAllGlobals());

  it("is disabled and ctx is a no-op under reduced motion", () => {
    mockReducedMotion(true);
    const { result } = renderHook(() => useAnimate());
    expect(result.current.enabled).toBe(false);
    const ran = vi.fn();
    expect(result.current.ctx(ran)).toBeUndefined();
    expect(ran).not.toHaveBeenCalled();
  });

  it("is enabled and ctx runs the fn when motion is allowed", () => {
    mockReducedMotion(false);
    const { result } = renderHook(() => useAnimate());
    expect(result.current.enabled).toBe(true);
    const ran = vi.fn(() => 42);
    result.current.ctx(ran);
    expect(ran).toHaveBeenCalledOnce();
  });
});
