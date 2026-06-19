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

interface OnboardingWizardProps {
  /** Called when onboarding completes — navigates to dashboard */
  onComplete?: (businessId: string) => void;
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

  return (
    <div
      className="onboarding-wizard"
      style={{
        minHeight: "100vh",
        background: "var(--bg-dominant)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "var(--space-lg)",
      }}
    >
      <div
        style={{
          background: "var(--bg-secondary)",
          borderRadius: 12,
          padding: "var(--space-lg)",
          width: "100%",
          maxWidth: 480,
        }}
      >
        {/* Step indicator */}
        <div
          className="step-indicator"
          style={{ display: "flex", gap: 8, marginBottom: "var(--space-lg)" }}
        >
          {([1, 2, 3, 4, 5] as const).map((s) => (
            <div
              key={s}
              style={{
                flex: 1,
                height: 4,
                borderRadius: 2,
                background: s <= step ? "var(--accent)" : "#334155",
              }}
            />
          ))}
        </div>

        {error && (
          <div
            role="alert"
            style={{
              background: "var(--destructive)",
              color: "#fff",
              padding: "8px 12px",
              borderRadius: 6,
              marginBottom: 12,
              fontSize: 14,
            }}
          >
            {error}
          </div>
        )}

        {/* Step 1: Account */}
        {step === 1 && (
          <div className="step step-1">
            <h2 style={{ color: "var(--text-primary)", marginBottom: 16 }}>
              Gumawa ng Account
            </h2>
            <label style={{ display: "block", marginBottom: 12 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Email</span>
              <input
                type="email"
                aria-label="Email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <label style={{ display: "block", marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Password</span>
              <input
                type="password"
                aria-label="Password"
                value={form.password}
                onChange={(e) => update("password", e.target.value)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <button onClick={handleStep1Next} style={{ width: "100%" }}>
              Susunod →
            </button>
          </div>
        )}

        {/* Step 2: Business basics */}
        {step === 2 && (
          <div className="step step-2">
            <h2 style={{ color: "var(--text-primary)", marginBottom: 16 }}>
              Business Info
            </h2>
            <label style={{ display: "block", marginBottom: 12 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Business Name</span>
              <input
                type="text"
                aria-label="Business Name"
                value={form.businessName}
                onChange={(e) => update("businessName", e.target.value)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <label style={{ display: "block", marginBottom: 12 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Industry</span>
              <select
                aria-label="Industry"
                value={form.industry}
                onChange={(e) => update("industry", e.target.value as IndustryOption)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              >
                <option value="dental">Dental</option>
                <option value="aesthetics">Aesthetics</option>
                <option value="real_estate">Real Estate</option>
              </select>
            </label>
            <label style={{ display: "block", marginBottom: 12 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>City</span>
              <input
                type="text"
                aria-label="City"
                value={form.city}
                onChange={(e) => update("city", e.target.value)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <label style={{ display: "block", marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>Phone</span>
              <input
                type="tel"
                aria-label="Phone"
                value={form.phone}
                onChange={(e) => update("phone", e.target.value)}
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setStep(1)} style={{ flex: 1 }}>← Bumalik</button>
              <button onClick={handleStep2Next} style={{ flex: 2 }}>Susunod →</button>
            </div>
          </div>
        )}

        {/* Step 3: Services + pricing */}
        {step === 3 && (
          <div className="step step-3">
            <h2 style={{ color: "var(--text-primary)", marginBottom: 16 }}>
              Mga Serbisyo at Presyo
            </h2>
            {(["service1", "service2", "service3"] as const).map((field, i) => (
              <label key={field} style={{ display: "block", marginBottom: 12 }}>
                <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                  Serbisyo {i + 1}{i > 0 ? " (optional)" : ""}
                </span>
                <input
                  type="text"
                  aria-label={`Service ${i + 1}`}
                  value={form[field]}
                  onChange={(e) => update(field, e.target.value)}
                  style={{ display: "block", width: "100%", marginTop: 4 }}
                />
              </label>
            ))}
            <label style={{ display: "block", marginBottom: 16 }}>
              <span style={{ fontSize: 13, color: "var(--text-secondary)" }}>
                Presyo / Price Range
              </span>
              <input
                type="text"
                aria-label="Pricing"
                value={form.pricing}
                onChange={(e) => update("pricing", e.target.value)}
                placeholder="e.g. P500-P2500"
                style={{ display: "block", width: "100%", marginTop: 4 }}
              />
            </label>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setStep(2)} style={{ flex: 1 }}>← Bumalik</button>
              <button onClick={handleStep3Next} disabled={loading} style={{ flex: 2 }}>
                {loading ? "Loading..." : "I-preview →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Preview */}
        {step === 4 && (
          <div className="step step-4">
            <h2 style={{ color: "var(--text-primary)", marginBottom: 16 }}>
              Preview ng Agent Persona
            </h2>
            <pre
              className="persona-preview"
              style={{
                background: "#0f172a",
                color: "var(--text-secondary)",
                padding: 12,
                borderRadius: 8,
                fontSize: 13,
                whiteSpace: "pre-wrap",
                maxHeight: 240,
                overflowY: "auto",
                marginBottom: 16,
              }}
            >
              {preview}
            </pre>
            <div style={{ display: "flex", gap: 8 }}>
              <button onClick={() => setStep(3)} style={{ flex: 1 }}>← Baguhin</button>
              <button onClick={handleSubmit} disabled={loading} style={{ flex: 2 }}>
                {loading ? "Sine-save..." : "Kumpirmahin at Magsimula →"}
              </button>
            </div>
          </div>
        )}

        {/* Step 5: Done */}
        {step === 5 && (
          <div className="step step-5">
            <h2 style={{ color: "var(--text-primary)", marginBottom: 8 }}>
              Tapos na! 🎉
            </h2>
            <p style={{ color: "var(--text-secondary)", marginBottom: 16 }}>
              Naka-set up na ang iyong OttoBot. Papunta na tayo sa dashboard.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
