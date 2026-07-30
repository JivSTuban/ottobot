/**
 * BookedBeat — hero "booked" moment component.
 *
 * Renders a solid green checkmark with a subtle scale+opacity pulse.
 * Gates the GSAP timeline behind useAnimate().enabled.
 * Under reduced motion: renders the final checked/booked state immediately.
 *
 * Design rules:
 * - Solid green only (--status-booked) — NO gradient/glow/glass
 * - transform + opacity only — no layout-affecting animations
 * - This is the ONE component allowed to exceed 300ms
 */

import { useRef, useEffect } from "react";
import gsap from "gsap";
import { useAnimate } from "../motion/useAnimate.ts";

interface BookedBeatProps {
  className?: string;
}

export function BookedBeat({ className }: BookedBeatProps) {
  const { enabled } = useAnimate();
  const containerRef = useRef<HTMLDivElement>(null);
  const checkRef = useRef<SVGSVGElement>(null);
  const circleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!enabled) return;

    const container = containerRef.current;
    const check = checkRef.current;
    const circle = circleRef.current;
    if (!container || !check || !circle) return;

    // Start from invisible
    gsap.set(container, { opacity: 0, scale: 0.8 });
    gsap.set(check, { opacity: 0 });

    const tl = gsap.timeline();

    // 1. Fade in + scale up the container (ease-out feel)
    tl.to(container, {
      opacity: 1,
      scale: 1,
      duration: 0.35,
      ease: "back.out(1.2)",
    });

    // 2. Checkmark stroke draw — animate opacity in quickly
    tl.to(
      check,
      {
        opacity: 1,
        duration: 0.25,
        ease: "power2.out",
      },
      "-=0.1"
    );

    // 3. Subtle pulse on the circle (scale down then back) — booked confirmation beat
    tl.to(
      circle,
      {
        scale: 1.08,
        duration: 0.2,
        ease: "power1.out",
        yoyo: true,
        repeat: 1,
      },
      "-=0.05"
    );

    return () => {
      tl.kill();
    };
  }, [enabled]);

  return (
    <div
      ref={containerRef}
      className={className}
      role="status"
      aria-label="Lead booked"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 12,
        padding: "24px 16px",
      }}
    >
      {/* Solid green circle with check — NO glow, NO gradient */}
      <div
        ref={circleRef}
        style={{
          width: 64,
          height: 64,
          borderRadius: "50%",
          background: "var(--status-booked)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <svg
          ref={checkRef}
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          aria-hidden="true"
        >
          <polyline
            points="6,17 13,24 26,10"
            stroke="#ffffff"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>

      {/* Accessible booked label */}
      <p
        style={{
          margin: 0,
          fontSize: "16px",
          fontWeight: 700,
          color: "var(--text)",
          letterSpacing: "-0.01em",
        }}
      >
        Booked
      </p>
      <p
        style={{
          margin: 0,
          fontSize: "13px",
          color: "var(--text-muted)",
          textAlign: "center",
        }}
      >
        Na-confirm na ang appointment!
      </p>
    </div>
  );
}
