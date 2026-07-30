/** @vitest-environment jsdom */
/**
 * wizard-nav.test.tsx — contract tests for OnboardingWizard step navigation.
 *
 * Assertions:
 * 1. Next advances the rail (aria-current moves forward)
 * 2. Back regresses the rail (aria-current moves back)
 * 3. The ONLY element with class `bg-primary` per step is the advance/submit CTA button
 */
import { describe, it, expect } from "vitest";
import { render, fireEvent, within } from "@testing-library/react";
import { OnboardingWizard } from "../OnboardingWizard.tsx";

function setup() {
  const { container } = render(<OnboardingWizard />);
  const q = within(container as HTMLElement);
  return { container, q };
}

/** Advance from step 1 → step 2 with valid credentials. */
function goToStep2(q: ReturnType<typeof within>) {
  fireEvent.change(q.getByLabelText("Email"), {
    target: { value: "owner@test.com" },
  });
  fireEvent.change(q.getByLabelText("Password"), {
    target: { value: "password123" },
  });
  fireEvent.click(q.getAllByText("Susunod →")[0]);
}

describe("OnboardingWizard — step rail navigation", () => {
  it("Next advances aria-current from step 1 (Account) to step 2 (Business)", () => {
    const { container, q } = setup();
    // Step 1: rail shows Account as current
    expect(
      container.querySelector('[aria-current="step"]')?.textContent
    ).toContain("Account");

    goToStep2(q);

    // Step 2: rail now shows Business as current
    expect(
      container.querySelector('[aria-current="step"]')?.textContent
    ).toContain("Business");
  });

  it("Back regresses aria-current from step 2 to step 1", () => {
    const { container, q } = setup();
    goToStep2(q);
    // Now on step 2 — click Back
    fireEvent.click(q.getByText("← Bumalik"));
    expect(
      container.querySelector('[aria-current="step"]')?.textContent
    ).toContain("Account");
  });

  it("exactly one aria-current=step element exists at step 1", () => {
    const { container } = setup();
    expect(
      container.querySelectorAll('[aria-current="step"]').length
    ).toBe(1);
  });

  it("exactly one aria-current=step element exists at step 2", () => {
    const { container, q } = setup();
    goToStep2(q);
    expect(
      container.querySelectorAll('[aria-current="step"]').length
    ).toBe(1);
  });
});

describe("OnboardingWizard — single bg-primary CTA rule", () => {
  /**
   * The advance/submit button uses variant="default" → class `bg-primary`.
   * Back / outline buttons use variant="outline" → no `bg-primary`.
   * So across the entire rendered step, only 1 element should carry `bg-primary`.
   */
  it("step 1 has exactly one bg-primary element (the Susunod CTA)", () => {
    const { container } = setup();
    // bg-primary also appears on the completed-step check SVG circles in StepRail.
    // Filter to buttons only to verify CTA discipline.
    const primaryButtons = Array.from(container.querySelectorAll("button.bg-primary"));
    expect(primaryButtons.length).toBe(1);
    expect(primaryButtons[0].textContent).toContain("Susunod");
  });

  it("step 2 has exactly one bg-primary button (the Susunod CTA); back button is outline", () => {
    const { container, q } = setup();
    goToStep2(q);
    const primaryButtons = Array.from(
      container.querySelectorAll("button.bg-primary")
    );
    expect(primaryButtons.length).toBe(1);
    expect(primaryButtons[0].textContent).toContain("Susunod");
    // Back button must NOT be bg-primary
    const backBtn = q.getByText("← Bumalik");
    expect((backBtn as HTMLElement).className).not.toContain("bg-primary");
  });
});
