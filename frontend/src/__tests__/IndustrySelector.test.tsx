/**
 * IndustrySelector component tests — TDD RED phase
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { IndustrySelector } from "../IndustrySelector";
import { PERSONA_ASSETS } from "../assets/personas";

describe("IndustrySelector", () => {
  it("renders heading 'Piliin ang Industry'", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    expect(screen.getByText("Piliin ang Industry")).toBeTruthy();
  });

  it("renders three industry cards with correct cardLabel", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    expect(screen.getAllByText(PERSONA_ASSETS.dental.cardLabel).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(PERSONA_ASSETS.aesthetics.cardLabel).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(PERSONA_ASSETS.real_estate.cardLabel).length).toBeGreaterThanOrEqual(1);
  });

  it("renders agentName in each card", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    expect(screen.getAllByText(PERSONA_ASSETS.dental.agentName).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(PERSONA_ASSETS.aesthetics.agentName).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(PERSONA_ASSETS.real_estate.agentName).length).toBeGreaterThanOrEqual(1);
  });

  it("renders persona avatar images with correct src", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    const imgs = screen.getAllByRole("img");
    const srcs = imgs.map((img) => img.getAttribute("src"));
    expect(srcs).toContain(PERSONA_ASSETS.dental.avatarSrc);
    expect(srcs).toContain(PERSONA_ASSETS.aesthetics.avatarSrc);
    expect(srcs).toContain(PERSONA_ASSETS.real_estate.avatarSrc);
  });

  it("'Simulan' button is disabled until a card is selected", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    const simulanBtn = screen.getAllByText("Simulan")[0].closest("button")!;
    expect(simulanBtn.disabled).toBe(true);
  });

  it("clicking a card enables the Simulan button", () => {
    render(<IndustrySelector onSelect={vi.fn()} />);
    const dentalCard = screen.getAllByText(PERSONA_ASSETS.dental.cardLabel)[0].closest("button")!;
    fireEvent.click(dentalCard);
    const simulanBtn = screen.getAllByText("Simulan")[0].closest("button")!;
    expect(simulanBtn.disabled).toBe(false);
  });

  it("clicking Simulan calls onSelect with the selected IndustryKey", () => {
    const onSelect = vi.fn();
    const { container } = render(<IndustrySelector onSelect={onSelect} />);
    // Click the dental card button directly
    const cards = container.querySelectorAll<HTMLButtonElement>("button.industry-card");
    const dentalCard = Array.from(cards).find((c) =>
      c.textContent?.includes("Dental · Ate Ana")
    )!;
    fireEvent.click(dentalCard);
    // Click Simulan button
    const simulanBtns = container.querySelectorAll<HTMLButtonElement>("button:not(.industry-card)");
    const simulanBtn = Array.from(simulanBtns).find((b) => b.textContent === "Simulan")!;
    fireEvent.click(simulanBtn);
    expect(onSelect).toHaveBeenCalledWith("dental");
  });

  it("industry background image (industrySrc) is set as background-image style on each card", () => {
    const { container } = render(<IndustrySelector onSelect={vi.fn()} />);
    // Check that at least one card button has a background-image style containing the dental industry path
    const cards = container.querySelectorAll<HTMLButtonElement>("button.industry-card");
    expect(cards.length).toBe(3);
    const dentalCard = Array.from(cards).find((c) =>
      c.textContent?.includes("Dental · Ate Ana")
    );
    expect(dentalCard?.style.backgroundImage).toContain(PERSONA_ASSETS.dental.industrySrc);
  });
});
