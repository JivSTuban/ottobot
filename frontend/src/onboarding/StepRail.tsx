/**
 * StepRail — left vertical rail showing onboarding progress.
 *
 * Rules:
 * - Current step: aria-current="step", neutral text weight
 * - Completed steps: green check icon — the ONLY accent on the rail
 * - Upcoming steps: muted, no accent
 */

import { cn } from "@/lib/utils";

interface StepRailProps {
  steps: string[];
  current: number; // 0-based index
}

function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      className={cn("size-4 shrink-0", className)}
      aria-hidden="true"
    >
      <circle cx="8" cy="8" r="7" className="fill-primary" />
      <path
        d="M5 8l2 2 4-4"
        stroke="white"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function StepDot({
  status,
  index,
}: {
  status: "completed" | "current" | "upcoming";
  index: number;
}) {
  if (status === "completed") {
    return <CheckIcon />;
  }
  return (
    <div
      className={cn(
        "size-4 shrink-0 rounded-full border",
        status === "current"
          ? "border-foreground bg-transparent"
          : "border-muted-foreground/40 bg-transparent"
      )}
      aria-hidden="true"
    >
      {status === "current" && (
        <div className="m-auto mt-[3px] size-2 rounded-full bg-foreground" />
      )}
      {status === "upcoming" && (
        <span className="sr-only">{index + 1}</span>
      )}
    </div>
  );
}

export function StepRail({ steps, current }: StepRailProps) {
  return (
    <nav
      aria-label="Onboarding steps"
      className="flex w-40 shrink-0 flex-col gap-1 py-2"
    >
      {steps.map((label, i) => {
        const status =
          i < current ? "completed" : i === current ? "current" : "upcoming";

        return (
          <div key={label} className="flex flex-col">
            <div
              className={cn(
                "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm",
                status === "current" && "font-medium text-foreground",
                status === "completed" && "text-foreground/70",
                status === "upcoming" && "text-muted-foreground"
              )}
              {...(status === "current"
                ? { "aria-current": "step" as const }
                : {})}
            >
              <StepDot status={status} index={i} />
              <span>{label}</span>
            </div>
            {/* Connector line (not after last step) */}
            {i < steps.length - 1 && (
              <div
                className={cn(
                  "ml-[14px] h-5 w-px",
                  i < current ? "bg-primary/40" : "bg-border"
                )}
                aria-hidden="true"
              />
            )}
          </div>
        );
      })}
    </nav>
  );
}
