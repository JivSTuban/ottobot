/**
 * Dashboard — operator cockpit for OttoBot.
 * Dense, data-forward layout: KPI row → conversations + escalations + availability.
 * Flat surfaces, hairline borders, mono numerals. No gradients, glows, or glass.
 */

import { MetricRow } from "./dashboard/MetricRow.tsx";
import { ConversationsList } from "./dashboard/ConversationsList.tsx";
import { EscalationsPanel } from "./dashboard/EscalationsPanel.tsx";
import { AvailabilityGlance } from "./dashboard/AvailabilityGlance.tsx";
import {
  fixtureMetrics,
  fixtureConversations,
  fixtureEscalations,
  fixtureAvailability,
} from "./dashboard/fixtures.ts";

export function Dashboard() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="border-b border-border px-6 py-3 flex items-center justify-between bg-surface">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-foreground">OttoBot</span>
          <span className="text-xs text-muted-foreground">Operator cockpit</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-[var(--text-muted)]" />
          <span className="text-xs text-muted-foreground">Agent active</span>
        </div>
      </header>

      <main className="p-6 flex flex-col gap-5 max-w-[1400px] mx-auto">
        {/* KPI row */}
        <MetricRow metrics={fixtureMetrics} />

        {/* Main grid: conversations (wide) + right column */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-5 items-start">
          {/* Left — conversations list */}
          <div className="border border-border rounded-lg bg-surface overflow-hidden">
            <ConversationsList conversations={fixtureConversations} />
          </div>

          {/* Right column — escalations + availability */}
          <div className="flex flex-col gap-4">
            <div className="border border-border rounded-lg bg-surface overflow-hidden">
              <EscalationsPanel escalations={fixtureEscalations} />
            </div>
            <div className="border border-border rounded-lg bg-surface overflow-hidden">
              <AvailabilityGlance days={fixtureAvailability} />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
