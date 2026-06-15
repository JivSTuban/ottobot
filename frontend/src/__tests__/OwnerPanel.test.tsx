/**
 * OwnerPanel component tests — TDD RED phase
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { OwnerPanel } from "../OwnerPanel";
import type { Stage, Message } from "../types";
import type { IndustryKey } from "../assets/personas";

const noMessages: Message[] = [];
const sampleMessages: Message[] = [
  { role: "user", content: "Magandang araw po" },
  { role: "assistant", content: "Kumusta! Ako si Ate Ana." },
];

function renderPanel(
  stage: Stage,
  escalated = false,
  messages: Message[] = noMessages,
  industry: IndustryKey | null = "dental"
) {
  return render(
    <OwnerPanel
      messages={messages}
      stage={stage}
      escalated={escalated}
      industry={industry}
    />
  );
}

describe("OwnerPanel — stage badge labels", () => {
  it("shows 'Tinatasa' for stage intro", () => {
    // intro -> qualifying per stageToLeadStatus -> "Tinatasa"
    renderPanel("intro");
    expect(screen.getAllByText("Tinatasa").length).toBeGreaterThanOrEqual(1);
  });

  it("shows 'Tinatasa' for stage qualify", () => {
    renderPanel("qualify");
    expect(screen.getAllByText("Tinatasa").length).toBeGreaterThanOrEqual(1);
  });

  it("shows 'Tinatasa' for stage pitch", () => {
    renderPanel("pitch");
    expect(screen.getAllByText("Tinatasa").length).toBeGreaterThanOrEqual(1);
  });

  it("shows 'Naka-book' for stage confirm", () => {
    renderPanel("confirm");
    expect(screen.getAllByText("Naka-book").length).toBeGreaterThanOrEqual(1);
  });

  it("shows 'HOT' for stage escalate", () => {
    renderPanel("escalate");
    expect(screen.getAllByText("HOT").length).toBeGreaterThanOrEqual(1);
  });
});

describe("OwnerPanel — header", () => {
  it("renders 'Owner View' header label", () => {
    renderPanel("intro");
    expect(screen.getAllByText("Owner View").length).toBeGreaterThanOrEqual(1);
  });
});

describe("OwnerPanel — escalation alert", () => {
  it("escalation alert is NOT visible when escalated=false", () => {
    renderPanel("qualify", false);
    const alert = screen.queryByRole("alert");
    expect(alert).toBeNull();
  });

  it("escalation alert IS visible when escalated=true", () => {
    renderPanel("escalate", true);
    const alert = screen.getByRole("alert");
    expect(alert).toBeTruthy();
  });

  it("escalation alert has role='alert'", () => {
    renderPanel("escalate", true);
    expect(screen.getAllByRole("alert").length).toBeGreaterThanOrEqual(1);
  });

  it("escalation alert contains 'HOT LEAD — Tawagan na!'", () => {
    renderPanel("escalate", true);
    expect(screen.getAllByRole("alert")[0].textContent).toContain("HOT LEAD — Tawagan na!");
  });
});

describe("OwnerPanel — conversation mirror", () => {
  it("renders all messages in the mirror", () => {
    renderPanel("qualify", false, sampleMessages);
    expect(screen.getByText("Magandang araw po")).toBeTruthy();
    expect(screen.getByText("Kumusta! Ako si Ate Ana.")).toBeTruthy();
  });
});
