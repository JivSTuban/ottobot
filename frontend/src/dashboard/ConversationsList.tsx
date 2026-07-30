/**
 * ConversationsList — live thread list with status dot + last message + mono timestamp.
 */

import { stageToLeadStatus } from "../types.ts";
import type { ConversationItem } from "./fixtures.ts";

function fmtTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-PH", { hour: "2-digit", minute: "2-digit", hour12: true });
}

function StatusDot({ status }: { status: "new" | "qualifying" | "hot" | "booked" | "escalated" }) {
  const colorMap: Record<string, string> = {
    new: "bg-[var(--status-new)]",
    qualifying: "bg-[var(--status-qualifying)]",
    hot: "bg-[var(--status-hot)]",
    booked: "bg-[var(--status-booked)]",
    escalated: "bg-[var(--status-escalated)]",
  };
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full shrink-0 mt-1.5 ${colorMap[status] ?? colorMap.new}`}
      aria-label={status}
    />
  );
}

interface ConversationsListProps {
  conversations: ConversationItem[];
}

export function ConversationsList({ conversations }: ConversationsListProps) {
  return (
    <div className="flex flex-col">
      <div className="px-4 py-2 border-b border-border">
        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Live threads
        </span>
      </div>
      <ul className="divide-y divide-border">
        {conversations.map((conv) => {
          const status = stageToLeadStatus(conv.stage);
          return (
            <li
              key={conv.id}
              className="flex items-start gap-3 px-4 py-3 hover:bg-surface-2 transition-colors"
            >
              <StatusDot status={status} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-foreground truncate">{conv.name}</span>
                  <span className="text-xs font-mono tabular-nums text-muted-foreground shrink-0">
                    {fmtTime(conv.timestampIso)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground truncate mt-0.5">{conv.lastMessage}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
