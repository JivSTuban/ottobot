/**
 * EscalationsPanel — "Needs you" action queue for escalated conversations.
 */

import type { EscalationItem } from "./fixtures.ts";

function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-PH", { hour: "2-digit", minute: "2-digit", hour12: true });
}

interface EscalationsPanelProps {
  escalations: EscalationItem[];
}

export function EscalationsPanel({ escalations }: EscalationsPanelProps) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Needs you
        </span>
        {escalations.length > 0 && (
          <span className="inline-flex items-center justify-center h-4 min-w-4 rounded-full bg-[var(--status-escalated)] text-white text-[10px] font-bold px-1">
            {escalations.length}
          </span>
        )}
      </div>
      {escalations.length === 0 ? (
        <p className="px-4 py-4 text-xs text-muted-foreground">No escalations — all clear.</p>
      ) : (
        <ul className="divide-y divide-border">
          {escalations.map((esc) => (
            <li key={esc.id} className="flex items-start gap-3 px-4 py-3">
              <span className="mt-0.5 inline-block h-2 w-2 rounded-full bg-[var(--status-escalated)] shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground">{esc.name}</span>
                  <span className="text-xs font-mono tabular-nums text-muted-foreground shrink-0">
                    {fmtTime(esc.timestampIso)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">{esc.reason}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
