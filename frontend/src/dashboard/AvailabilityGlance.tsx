/**
 * AvailabilityGlance — week strip showing open appointment slots per day.
 */

import type { AvailabilityDay } from "./fixtures.ts";

function slotColor(slots: number): string {
  if (slots === 0) return "bg-surface-2 text-muted-foreground";
  if (slots <= 2) return "bg-[var(--status-hot)]/10 text-[var(--status-hot)]";
  return "bg-[var(--status-booked)]/10 text-[var(--status-booked)]";
}

interface AvailabilityGlanceProps {
  days: AvailabilityDay[];
}

export function AvailabilityGlance({ days }: AvailabilityGlanceProps) {
  return (
    <div className="flex flex-col">
      <div className="px-4 py-2 border-b border-border">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Availability this week
        </span>
      </div>
      <div className="flex gap-2 px-4 py-3 overflow-x-auto">
        {days.map((day) => (
          <div
            key={day.date}
            className={`flex flex-col items-center gap-1 rounded-md px-3 py-2 min-w-[52px] ${slotColor(day.slots)}`}
          >
            <span className="text-xs font-medium">{day.label}</span>
            <span className="text-lg font-mono tabular-nums font-semibold leading-none">
              {day.slots}
            </span>
            <span className="text-[10px] text-muted-foreground leading-none">{day.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
