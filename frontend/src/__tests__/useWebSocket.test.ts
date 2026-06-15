/**
 * useWebSocket hook tests — TDD RED phase
 * Tests WebSocket event handling: token, state, system_alert, send
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useWebSocket } from "../useWebSocket";
import type { Stage } from "../types";

// ---- WebSocket mock ----
class MockWebSocket {
  url: string;
  onmessage: ((e: MessageEvent) => void) | null = null;
  onopen: (() => void) | null = null;
  onerror: ((e: Event) => void) | null = null;
  onclose: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn();

  constructor(url: string) {
    this.url = url;
    // Simulate connection open on next tick
    setTimeout(() => this.onopen?.(), 0);
  }

  /** Helper to fire a message event from tests */
  simulateMessage(data: object) {
    const event = { data: JSON.stringify(data) } as MessageEvent;
    this.onmessage?.(event);
  }
}

let mockWsInstance: MockWebSocket;

beforeEach(() => {
  vi.useFakeTimers();
  // Replace global WebSocket with the mock class
  // @ts-expect-error — replacing global WebSocket with mock class
  global.WebSocket = class extends MockWebSocket {
    constructor(url: string) {
      super(url);
      mockWsInstance = this;
    }
  };
  // Also expose OPEN state constant
  // @ts-expect-error — adding constant
  global.WebSocket.OPEN = 1;
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

const WS_URL = "ws://localhost:8000/ws/test-thread-id";

describe("useWebSocket", () => {
  it("Test 1: token event appends to last assistant message (streaming)", () => {
    const { result } = renderHook(() => useWebSocket(WS_URL));

    act(() => {
      vi.runAllTimers(); // open
    });

    act(() => {
      mockWsInstance.simulateMessage({ type: "token", content: "Kumusta" });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe("assistant");
    expect(result.current.messages[0].content).toBe("Kumusta");
    expect(result.current.messages[0].streaming).toBe(true);

    // Second token appends to the same bubble
    act(() => {
      mockWsInstance.simulateMessage({ type: "token", content: " po!" });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe("Kumusta po!");
  });

  it("Test 2: state event finalizes streaming + sets stage + escalated", () => {
    const { result } = renderHook(() => useWebSocket(WS_URL));

    act(() => {
      vi.runAllTimers();
    });

    // First get a streaming token
    act(() => {
      mockWsInstance.simulateMessage({ type: "token", content: "Hello" });
    });

    expect(result.current.messages[0].streaming).toBe(true);
    expect(result.current.stage).toBe("intro");
    expect(result.current.escalated).toBe(false);

    // State event finalizes streaming and updates stage/escalated
    act(() => {
      mockWsInstance.simulateMessage({
        type: "state",
        stage: "qualify" as Stage,
        escalated: true,
      });
    });

    expect(result.current.stage).toBe("qualify");
    expect(result.current.escalated).toBe(true);
    // The last assistant message streaming flag should be cleared
    expect(result.current.messages[0].streaming).toBe(false);
  });

  it("Test 3: system_alert sets systemAlert; clears after 8000ms", () => {
    const { result } = renderHook(() => useWebSocket(WS_URL));

    act(() => {
      vi.runAllTimers();
    });

    act(() => {
      mockWsInstance.simulateMessage({
        type: "system_alert",
        content: "HOT LEAD alert!",
      });
    });

    expect(result.current.systemAlert).toBe("HOT LEAD alert!");

    // After 8000ms it should clear
    act(() => {
      vi.advanceTimersByTime(8000);
    });

    expect(result.current.systemAlert).toBeNull();
  });

  it("Test 4: send() pushes user message into messages and calls ws.send with JSON", () => {
    const { result } = renderHook(() => useWebSocket(WS_URL));

    act(() => {
      vi.runAllTimers();
    });

    act(() => {
      result.current.send("Magandang araw", "dental");
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("Magandang araw");

    expect(mockWsInstance.send).toHaveBeenCalledTimes(1);
    const sentPayload = JSON.parse(mockWsInstance.send.mock.calls[0][0]);
    expect(sentPayload).toEqual({ text: "Magandang araw", industry: "dental" });
  });
});
