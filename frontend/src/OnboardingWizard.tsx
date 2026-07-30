/**
 * OnboardingWizard — 5-step business onboarding form.
 *
 * Steps:
 *   1. Account creation (email + password) — Supabase Auth signup
 *   2. Business basics (name, industry, city, phone)
 *   3. Services + pricing (free text, 3 fields max)
 *   4. Agent persona preview (POST /onboarding/preview)
 *   5. Confirmation + submit (POST /onboarding/submit → /dashboard)
 *
 * Per POLICY.md: no OAuth, no billing, no email verification flow.
 * No react-router — uses window.location for final navigation to /dashboard.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { StepRail } from "@/onboarding/StepRail";
import { PersonaPreview } from "@/onboarding/PersonaPreview";

type IndustryOption = "dental" | "aesthetics" | "real_estate";

interface OnboardingState {
  email: string;
  password: string;
  businessName: string;
  industry: IndustryOption;
  city: string;
  phone: string;
  service1: string;
  service2: string;
  service3: string;
  pricing: string;
}

const INITIAL_STATE: OnboardingState = {
  email: "",
  password: "",
  businessName: "",
  industry: "dental",
  city: "",
  phone: "",
  service1: "",
  service2: "",
  service3: "",
  pricing: "",
};

const STEPS = ["Account", "Business", "Services", "Persona", "Confirm"];

interface OnboardingWizardProps {
  /** Called when onboarding completes — navigates to dashboard */
  onComplete?: (businessId: string) => void;
}

/** Left-aligned field label + shadcn Input combo. */
function Field({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label
        htmlFor={htmlFor}
        className="text-sm font-medium text-foreground"
      >
        {label}
      </label>
      {children}
    </div>
  );
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState<1 | 2 | 3 | 4 | 5>(1);
  const [form, setForm] = useState<OnboardingState>(INITIAL_STATE);
  const [preview, setPreview] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const update = (field: keyof OnboardingState, value: string) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const servicesString = [form.service1, form.service2, form.service3]
    .filter(Boolean)
    .join(", ");

  async function handleStep1Next() {
    if (!form.email || !form.password) {
      setError("Email at password ay kailangan.");
      return;
    }
    if (!form.email.includes("@")) {
      setError("Lagyan ng tamang email address.");
      return;
    }
    if (form.password.length < 6) {
      setError("Password ay dapat hindi bababa sa 6 na character.");
      return;
    }
    setError("");
    setStep(2);
  }

  async function handleStep2Next() {
    if (!form.businessName || !form.city || !form.phone) {
      setError("Punan ang lahat ng fields.");
      return;
    }
    setError("");
    setStep(3);
  }

  async function handleStep3Next() {
    if (!form.service1) {
      setError("Maglagay ng kahit isang serbisyo.");
      return;
    }
    if (!form.pricing) {
      setError("Maglagay ng presyo o price range.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const resp = await fetch("/onboarding/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_email: form.email,
          name: form.businessName,
          industry: form.industry,
          phone: form.phone,
          city: form.city,
          services: servicesString,
          pricing: form.pricing,
        }),
      });
      if (!resp.ok) throw new Error("Preview failed");
      const data = await resp.json();
      setPreview(data.preview ?? "");
      setStep(4);
    } catch {
      setError("Hindi ma-load ang preview. Subukan ulit.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    setLoading(true);
    setError("");
    try {
      const resp = await fetch("/onboarding/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          owner_email: form.email,
          name: form.businessName,
          industry: form.industry,
          phone: form.phone,
          city: form.city,
          services: servicesString,
          pricing: form.pricing,
        }),
      });
      if (!resp.ok) throw new Error("Submit failed");
      const data = await resp.json();
      const businessId: string = data.business_id ?? "";
      setStep(5);
      if (onComplete) {
        onComplete(businessId);
      } else {
        window.location.href = "/dashboard";
      }
    } catch {
      setError("May error sa pag-save. Subukan ulit.");
    } finally {
      setLoading(false);
    }
  }

  // StepRail uses 0-based index; step state is 1-based
  const railCurrent = step - 1;

  return (
    <div className="onboarding-wizard flex min-h-screen items-start justify-center bg-background px-4 py-12">
      <div className="flex w-full max-w-3xl gap-8">
        {/* Left: step rail */}
        <div className="hidden pt-1 sm:block">
          <StepRail steps={STEPS} current={railCurrent} />
        </div>

        {/* Right: step content */}
        <Card className="flex-1">
          <CardContent className="py-6">
            {/* Mobile step indicator (no rail on mobile) */}
            <div
              className="step-indicator mb-6 flex gap-1.5 sm:hidden"
              aria-hidden="true"
            >
              {([1, 2, 3, 4, 5] as const).map((s) => (
                <div
                  key={s}
                  className={[
                    "h-1 flex-1 rounded-full",
                    s <= step ? "bg-primary" : "bg-border",
                  ].join(" ")}
                />
              ))}
            </div>

            {error && (
              <div
                role="alert"
                className="mb-4 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
              >
                {error}
              </div>
            )}

            {/* Step 1: Account */}
            {step === 1 && (
              <div className="step step-1 flex flex-col gap-5">
                <h2 className="text-lg font-semibold text-foreground">
                  Gumawa ng Account
                </h2>
                <Field label="Email" htmlFor="email">
                  <Input
                    id="email"
                    type="email"
                    aria-label="Email"
                    value={form.email}
                    onChange={(e) => update("email", e.target.value)}
                  />
                </Field>
                <Field label="Password" htmlFor="password">
                  <Input
                    id="password"
                    type="password"
                    aria-label="Password"
                    value={form.password}
                    onChange={(e) => update("password", e.target.value)}
                  />
                </Field>
                <Button className="w-full" onClick={handleStep1Next}>
                  Susunod →
                </Button>
              </div>
            )}

            {/* Step 2: Business basics */}
            {step === 2 && (
              <div className="step step-2 flex flex-col gap-5">
                <h2 className="text-lg font-semibold text-foreground">
                  Business Info
                </h2>
                <Field label="Business Name" htmlFor="businessName">
                  <Input
                    id="businessName"
                    type="text"
                    aria-label="Business Name"
                    value={form.businessName}
                    onChange={(e) => update("businessName", e.target.value)}
                  />
                </Field>
                <div className="flex flex-col gap-1.5">
                  <label
                    htmlFor="industry"
                    className="text-sm font-medium text-foreground"
                  >
                    Industry
                  </label>
                  <select
                    id="industry"
                    aria-label="Industry"
                    value={form.industry}
                    onChange={(e) =>
                      update("industry", e.target.value as IndustryOption)
                    }
                    className="h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
                  >
                    <option value="dental">Dental</option>
                    <option value="aesthetics">Aesthetics</option>
                    <option value="real_estate">Real Estate</option>
                  </select>
                </div>
                <Field label="City" htmlFor="city">
                  <Input
                    id="city"
                    type="text"
                    aria-label="City"
                    value={form.city}
                    onChange={(e) => update("city", e.target.value)}
                  />
                </Field>
                <Field label="Phone" htmlFor="phone">
                  <Input
                    id="phone"
                    type="tel"
                    aria-label="Phone"
                    value={form.phone}
                    onChange={(e) => update("phone", e.target.value)}
                  />
                </Field>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setStep(1)}
                  >
                    ← Bumalik
                  </Button>
                  <Button className="flex-[2]" onClick={handleStep2Next}>
                    Susunod →
                  </Button>
                </div>
              </div>
            )}

            {/* Step 3: Services + pricing */}
            {step === 3 && (
              <div className="step step-3 flex flex-col gap-5">
                <h2 className="text-lg font-semibold text-foreground">
                  Mga Serbisyo at Presyo
                </h2>
                {(["service1", "service2", "service3"] as const).map(
                  (field, i) => (
                    <Field
                      key={field}
                      label={`Serbisyo ${i + 1}${i > 0 ? " (optional)" : ""}`}
                      htmlFor={field}
                    >
                      <Input
                        id={field}
                        type="text"
                        aria-label={`Service ${i + 1}`}
                        value={form[field]}
                        onChange={(e) => update(field, e.target.value)}
                      />
                    </Field>
                  )
                )}
                <Field label="Presyo / Price Range" htmlFor="pricing">
                  <Input
                    id="pricing"
                    type="text"
                    aria-label="Pricing"
                    value={form.pricing}
                    onChange={(e) => update("pricing", e.target.value)}
                    placeholder="e.g. P500-P2500"
                  />
                </Field>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setStep(2)}
                  >
                    ← Bumalik
                  </Button>
                  <Button
                    className="flex-[2]"
                    onClick={handleStep3Next}
                    disabled={loading}
                  >
                    {loading ? "Loading..." : "I-preview →"}
                  </Button>
                </div>
              </div>
            )}

            {/* Step 4: Persona preview */}
            {step === 4 && (
              <div className="step step-4 flex flex-col gap-6">
                <h2 className="text-lg font-semibold text-foreground">
                  Preview ng Agent Persona
                </h2>
                <PersonaPreview persona={preview} />
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => setStep(3)}
                  >
                    ← Baguhin
                  </Button>
                  <Button
                    className="flex-[2]"
                    onClick={handleSubmit}
                    disabled={loading}
                  >
                    {loading ? "Sine-save..." : "Kumpirmahin at Magsimula →"}
                  </Button>
                </div>
              </div>
            )}

            {/* Step 5: Done */}
            {step === 5 && (
              <div className="step step-5 flex flex-col gap-3">
                <h2 className="text-lg font-semibold text-foreground">
                  Tapos na! 🎉
                </h2>
                <p className="text-sm text-muted-foreground">
                  Naka-set up na ang iyong OttoBot. Papunta na tayo sa
                  dashboard.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
