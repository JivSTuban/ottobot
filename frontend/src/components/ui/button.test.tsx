/** @vitest-environment jsdom */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Button } from "./button.tsx";

describe("Button accent discipline", () => {
  it("primary variant uses the accent (bg-primary)", () => {
    const { container } = render(<Button>Book</Button>);
    const btn = container.querySelector("button")!;
    expect(btn.className).toContain("bg-primary");
  });

  it("secondary/ghost variants never use the accent fill", () => {
    const { container } = render(<Button variant="secondary">Cancel</Button>);
    const btn = container.querySelector("button")!;
    expect(btn.className).not.toContain("bg-primary");
  });
});
