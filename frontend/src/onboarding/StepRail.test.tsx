/** @vitest-environment jsdom */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StepRail } from "./StepRail.tsx";

describe("StepRail", () => {
  const steps = ["Account", "Business", "Services", "Persona", "Confirm"];

  it("marks the current step with aria-current", () => {
    const { getAllByText, container } = render(<StepRail steps={steps} current={2} />);
    expect(getAllByText("Services").length).toBeGreaterThanOrEqual(1);
    expect(container.querySelector('[aria-current="step"]')?.textContent).toContain("Services");
  });

  it("only one element has aria-current=step at a time", () => {
    const { container } = render(<StepRail steps={steps} current={1} />);
    const currentEls = container.querySelectorAll('[aria-current="step"]');
    expect(currentEls.length).toBe(1);
    expect(currentEls[0].textContent).toContain("Business");
  });

  it("completed steps render a check (svg) and no aria-current", () => {
    const { container } = render(<StepRail steps={steps} current={3} />);
    // Steps 0,1,2 are completed → 3 check icons (filled circles)
    const checks = container.querySelectorAll("svg circle.fill-primary");
    expect(checks.length).toBe(3);
    // Current step (3 = Persona) has aria-current
    const current = container.querySelector('[aria-current="step"]');
    expect(current?.textContent).toContain("Persona");
  });

  it("upcoming steps have no aria-current", () => {
    const { container } = render(<StepRail steps={steps} current={0} />);
    const currentEls = container.querySelectorAll('[aria-current="step"]');
    expect(currentEls.length).toBe(1);
    expect(currentEls[0].textContent).toContain("Account");
  });
});
