/**
 * OwnerPanel component tests — TDD RED phase
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
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

  it("escalation alert shows escalationAlert detail when provided", () => {
    const { container } = render(
      <OwnerPanel
        messages={noMessages}
        stage="escalate"
        escalated={true}
        industry="dental"
        escalationAlert="Hot lead detected. Contact the lead now. Stage: confirm"
      />
    );
    const alert = container.querySelector('[role="alert"]') as HTMLElement;
    expect(alert).toBeTruthy();
    expect(alert.textContent).toContain("Hot lead detected");
    expect(alert.querySelector(".escalation-detail")).toBeTruthy();
  });

  it("escalation alert does NOT show detail element when escalationAlert is absent", () => {
    const { container } = renderPanel("escalate", true);
    const alert = container.querySelector('[role="alert"]') as HTMLElement;
    expect(alert).toBeTruthy();
    expect(alert.querySelector(".escalation-detail")).toBeNull();
  });
});

describe("OwnerPanel — conversation mirror", () => {
  it("renders all messages in the mirror", () => {
    renderPanel("qualify", false, sampleMessages);
    expect(screen.getByText("Magandang araw po")).toBeTruthy();
    expect(screen.getByText("Kumusta! Ako si Ate Ana.")).toBeTruthy();
  });
});

describe("OwnerPanel — Appointments section", () => {
  const PROPOSED_TIME = "2026-06-20T14:00:00+08:00";
  const THREAD_ID = "test-thread-uuid";

  function renderWithAppointment(
    stage: Stage,
    proposed_appointment: string | null,
    send?: (msg: string) => void
  ) {
    return render(
      <OwnerPanel
        messages={noMessages}
        stage={stage}
        escalated={false}
        industry="dental"
        proposed_appointment={proposed_appointment}
        thread_id={THREAD_ID}
        send={send}
      />
    );
  }

  it("Appointments section is hidden when stage is not propose_appointment", () => {
    renderWithAppointment("pitch", PROPOSED_TIME);
    expect(screen.queryByText(/Appointment Proposal/i)).toBeNull();
  });

  it("Appointments section is visible at propose_appointment stage", () => {
    renderWithAppointment("propose_appointment", PROPOSED_TIME);
    expect(screen.getByText(/Appointment Proposal/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /Confirm/i })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Counter-propose/i })).toBeTruthy();
  });

  it("Confirm button sends correct confirm_appointment WebSocket message", () => {
    const mockSend = vi.fn();
    const { container } = renderWithAppointment("propose_appointment", PROPOSED_TIME, mockSend);
    const apptSection = container.querySelector(".appointments-section") as HTMLElement;
    fireEvent.click(within(apptSection).getByRole("button", { name: /Confirm/i }));
    expect(mockSend).toHaveBeenCalledOnce();
    const parsed = JSON.parse(mockSend.mock.calls[0][0]);
    expect(parsed.type).toBe("confirm_appointment");
    expect(parsed.action).toBe("confirm");
    expect(parsed.thread_id).toBe(THREAD_ID);
    expect(parsed.proposed_time).toBe(PROPOSED_TIME);
  });

  it("Counter-propose sends counter message with counter_time", () => {
    const mockSend = vi.fn();
    const { container } = renderWithAppointment("propose_appointment", PROPOSED_TIME, mockSend);
    const apptSection = container.querySelector(".appointments-section") as HTMLElement;
    fireEvent.click(within(apptSection).getByRole("button", { name: /Counter-propose/i }));
    fireEvent.change(within(apptSection).getByLabelText(/Counter-propose time/i), {
      target: { value: "Biyernes ng June 21 sa ika-3 ng hapon" },
    });
    fireEvent.click(within(apptSection).getByRole("button", { name: /Send Counter/i }));
    expect(mockSend).toHaveBeenCalledOnce();
    const parsed = JSON.parse(mockSend.mock.calls[0][0]);
    expect(parsed.type).toBe("confirm_appointment");
    expect(parsed.action).toBe("counter");
    expect(parsed.counter_time).toBe("Biyernes ng June 21 sa ika-3 ng hapon");
  });
});
