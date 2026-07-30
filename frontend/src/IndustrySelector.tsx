/**
 * IndustrySelector — startup screen for OttoBot demo UI.
 *
 * Shows three industry cards (dental/aesthetics/real_estate) with persona avatars
 * and industry background images from PERSONA_ASSETS (Plan 02 / D-12).
 * Calls onSelect(industry) when user clicks "Simulan" after selecting a card.
 */

import { useState } from "react";
import type { IndustryKey } from "./assets/personas";
import { PERSONA_ASSETS } from "./assets/personas";
import { Button } from "./components/ui/button";
import { Card } from "./components/ui/card";

interface IndustrySelectorProps {
  onSelect: (industry: IndustryKey) => void;
}

export function IndustrySelector({ onSelect }: IndustrySelectorProps) {
  const [selected, setSelected] = useState<IndustryKey | null>(null);

  const industries: IndustryKey[] = ["dental", "aesthetics", "real_estate"];

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        gap: "var(--space-2xl)",
        padding: "var(--space-lg)",
        background: "var(--bg)",
      }}
    >
      <h1
        style={{
          fontSize: "24px",
          fontWeight: 600,
          lineHeight: 1.2,
          margin: 0,
          color: "var(--text)",
        }}
      >
        Piliin ang Industry
      </h1>

      {/* Three-card row */}
      <div
        style={{
          display: "flex",
          gap: "var(--space-xl)",
          flexWrap: "wrap",
          justifyContent: "center",
        }}
      >
        {industries.map((key) => {
          const asset = PERSONA_ASSETS[key];
          const isSelected = selected === key;
          return (
            <button
              key={key}
              className="industry-card"
              onClick={() => setSelected(key)}
              style={{
                width: 200,
                height: 160,
                padding: "var(--space-md)",
                borderRadius: 8,
                background: "var(--surface)",
                border: isSelected
                  ? "2px solid var(--accent)"
                  : "1px solid var(--border)",
                boxShadow: "none",
                cursor: "pointer",
                transition: "border-color 150ms ease",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "var(--space-sm)",
                backgroundImage: `url(${asset.industrySrc})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
                backgroundBlendMode: "overlay",
                // Low opacity industry background via overlay blend
                position: "relative",
                color: "var(--text)",
              }}
              aria-pressed={isSelected}
            >
              {/* Low-opacity overlay for the industry background */}
              <div
                style={{
                  position: "absolute",
                  inset: 0,
                  background: "var(--surface)",
                  opacity: 0.85,
                  borderRadius: 7,
                  pointerEvents: "none",
                }}
              />
              {/* Card content (above overlay) */}
              <div
                style={{
                  position: "relative",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: "var(--space-xs)",
                }}
              >
                <img
                  src={asset.avatarSrc}
                  alt={asset.agentName}
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: "50%",
                    objectFit: "cover",
                  }}
                />
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color: "var(--text)",
                    textAlign: "center",
                  }}
                >
                  {asset.cardLabel}
                </span>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: "var(--text-muted)",
                    textAlign: "center",
                  }}
                >
                  {asset.agentName}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Simulan button — primary green CTA */}
      <Button
        onClick={() => {
          if (selected) onSelect(selected);
        }}
        disabled={selected === null}
        style={{
          height: 44,
          maxWidth: 320,
          width: "100%",
          fontSize: "16px",
          fontWeight: 600,
        }}
      >
        Simulan
      </Button>
    </div>
  );
}
