/**
 * MetricRow — 4 KPI cards in mono/tabular numerals.
 * GSAP count-up is gated by useAnimate; reduced motion renders final values immediately.
 */

import { useRef, useEffect } from "react";
import gsap from "gsap";
import { useAnimate } from "../motion/useAnimate.ts";
import { fmtNum } from "./format.ts";

export interface Metrics {
  leadsToday: number;
  booked: number;
  conversionPct: number;
  avgResponseSec: number;
}

interface KpiDef {
  label: string;
  value: number;
  display: (n: number) => string;
}

interface MetricRowProps {
  metrics: Metrics;
}

function KpiCard({ label, value, display, animate }: KpiDef & { animate: boolean }) {
  const numRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!animate || !numRef.current) return;
    const el = numRef.current;
    const obj = { val: 0 };
    const tween = gsap.to(obj, {
      val: value,
      duration: 0.28,
      ease: "power2.out",
      onUpdate() {
        if (el) el.textContent = display(Math.round(obj.val));
      },
    });
    return () => { tween.kill(); };
  }, [value, display, animate]);

  return (
    <div className="flex flex-col gap-1 px-4 py-3 border-r border-border last:border-r-0">
      <span className="text-xs text-muted-foreground uppercase tracking-wide">{label}</span>
      <span
        ref={numRef}
        className="text-2xl font-mono tabular-nums font-semibold text-foreground"
      >
        {display(value)}
      </span>
    </div>
  );
}

export function MetricRow({ metrics }: MetricRowProps) {
  const { enabled } = useAnimate();

  const kpis: KpiDef[] = [
    {
      label: "Leads today",
      value: metrics.leadsToday,
      display: (n) => fmtNum(n),
    },
    {
      label: "Booked",
      value: metrics.booked,
      display: (n) => fmtNum(n),
    },
    {
      label: "Conversion",
      value: metrics.conversionPct,
      display: (n) => `${n}%`,
    },
    {
      label: "Avg response",
      value: metrics.avgResponseSec,
      display: (n) => `${n}s`,
    },
  ];

  return (
    <div
      className="flex border border-border rounded-lg bg-surface overflow-hidden"
      role="list"
      aria-label="Key performance indicators"
    >
      {kpis.map((kpi) => (
        <div key={kpi.label} className="flex-1" role="listitem">
          <KpiCard {...kpi} animate={enabled} />
        </div>
      ))}
    </div>
  );
}
