/**
 * App.tsx integration smoke test — TDD RED phase
 *
 * Mocks useWebSocket to avoid real WebSocket connections.
 * Verifies: IndustrySelector startup -> split layout after selection -> empty state copy.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import App from "../App";
import type { UseWebSocketReturn } from "../useWebSocket";
import type { Stage } from "../types";

// Mock useWebSocket to avoid real WebSocket connections
vi.mock("../useWebSocket", () => ({
  useWebSocket: (): UseWebSocketReturn => ({
    tokens: [],
    stage: "intro" as Stage,
    escalated: false,
    systemAlert: null,
    send: vi.fn(),
    messages: [],
    wsError: false,
  }),
}));

// Mock crypto.randomUUID (jsdom may not have it)
beforeEach(() => {
  if (!globalThis.crypto) {
    Object.defineProperty(globalThis, "crypto", {
      value: { randomUUID: () => "11111111-1111-4111-a111-111111111111" },
      configurable: true,
    });
  } else if (!globalThis.crypto.randomUUID) {
    Object.defineProperty(globalThis.crypto, "randomUUID", {
      value: () => "11111111-1111-4111-a111-111111111111",
      configurable: true,
    });
  }
});

describe("App", () => {
  it("renders IndustrySelector initially (before any selection)", () => {
    render(<App />);
    expect(screen.getAllByText("Piliin ang Industry").length).toBeGreaterThanOrEqual(1);
  });

  it("after selecting Dental and clicking Simulan, split layout renders with Lead Chat and Owner View panels", () => {
    const { container } = render(<App />);

    // Select Dental card
    const cards = container.querySelectorAll<HTMLButtonElement>("button.industry-card");
    const dentalCard = Array.from(cards).find((c) =>
      c.textContent?.includes("Dental · Ate Ana")
    )!;
    fireEvent.click(dentalCard);

    // Click Simulan
    const simulanBtns = container.querySelectorAll<HTMLButtonElement>("button:not(.industry-card)");
    const simulanBtn = Array.from(simulanBtns).find((b) => b.textContent === "Simulan")!;
    fireEvent.click(simulanBtn);

    // Both panel headers should be visible
    expect(screen.getAllByText("Lead Chat").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Owner View").length).toBeGreaterThanOrEqual(1);
  });

  it("LeadChat shows empty-state copy when no messages", () => {
    const { container } = render(<App />);

    // Go to split view
    const cards = container.querySelectorAll<HTMLButtonElement>("button.industry-card");
    const dentalCard = Array.from(cards).find((c) =>
      c.textContent?.includes("Dental · Ate Ana")
    )!;
    fireEvent.click(dentalCard);
    const simulanBtns = container.querySelectorAll<HTMLButtonElement>("button:not(.industry-card)");
    const simulanBtn = Array.from(simulanBtns).find((b) => b.textContent === "Simulan")!;
    fireEvent.click(simulanBtn);

    // Empty state copy should be rendered
    expect(screen.getAllByText("Wala pang mensahe").length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("I-type ang mensahe mo sa ibaba para simulan ang usapan.").length
    ).toBeGreaterThanOrEqual(1);
  });
});
