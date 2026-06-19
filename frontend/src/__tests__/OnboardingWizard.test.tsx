/**
 * OnboardingWizard component tests — step navigation and validation.
 * Uses `within(container)` to avoid cross-test DOM accumulation.
 */
import { describe, it, expect } from "vitest";
import { render, fireEvent, within } from "@testing-library/react";
import { OnboardingWizard } from "../OnboardingWizard";

function setup() {
  const { container } = render(<OnboardingWizard />);
  const q = within(container as HTMLElement);
  return { container, q };
}

function goToStep2() {
  const { container, q } = setup();
  fireEvent.change(q.getByLabelText("Email"), { target: { value: "owner@test.com" } });
  fireEvent.change(q.getByLabelText("Password"), { target: { value: "password123" } });
  fireEvent.click(q.getAllByText("Susunod →")[0]);
  return { container, q };
}

describe("OnboardingWizard — step 1 (account)", () => {
  it("renders email and password inputs on step 1", () => {
    const { q } = setup();
    expect(q.getByLabelText("Email")).toBeTruthy();
    expect(q.getByLabelText("Password")).toBeTruthy();
  });

  it("shows error when email is missing and next is clicked", () => {
    const { q } = setup();
    fireEvent.click(q.getAllByText("Susunod →")[0]);
    expect(q.getByRole("alert")).toBeTruthy();
  });

  it("shows error when password is too short", () => {
    const { q } = setup();
    fireEvent.change(q.getByLabelText("Email"), { target: { value: "a@b.com" } });
    fireEvent.change(q.getByLabelText("Password"), { target: { value: "123" } });
    fireEvent.click(q.getAllByText("Susunod →")[0]);
    expect(q.getByRole("alert")).toBeTruthy();
  });

  it("advances to step 2 with valid credentials", () => {
    const { q } = setup();
    fireEvent.change(q.getByLabelText("Email"), { target: { value: "owner@test.com" } });
    fireEvent.change(q.getByLabelText("Password"), { target: { value: "password123" } });
    fireEvent.click(q.getAllByText("Susunod →")[0]);
    expect(q.getByLabelText("Business Name")).toBeTruthy();
  });
});

describe("OnboardingWizard — step 2 (business basics)", () => {
  it("shows business name, industry, city, phone inputs", () => {
    const { q } = goToStep2();
    expect(q.getByLabelText("Business Name")).toBeTruthy();
    expect(q.getByLabelText("Industry")).toBeTruthy();
    expect(q.getByLabelText("City")).toBeTruthy();
    expect(q.getByLabelText("Phone")).toBeTruthy();
  });

  it("back button returns to step 1", () => {
    const { q } = goToStep2();
    fireEvent.click(q.getByText("← Bumalik"));
    expect(q.getByLabelText("Email")).toBeTruthy();
  });

  it("shows error when required fields are missing", () => {
    const { q } = goToStep2();
    fireEvent.click(q.getAllByText("Susunod →")[0]);
    expect(q.getByRole("alert")).toBeTruthy();
  });
});

describe("OnboardingWizard — step indicator", () => {
  it("renders 5 step indicator bars", () => {
    const { container } = setup();
    const bars = container.querySelectorAll(".step-indicator > div");
    expect(bars.length).toBe(5);
  });
});
