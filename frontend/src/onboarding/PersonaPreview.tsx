/**
 * PersonaPreview — "agent comes alive" reveal on onboarding step 4.
 *
 * Motion: avatar → name → blurb stagger, ≤300ms, transform+opacity only.
 * Reduced motion: render final state immediately, no animation.
 * No gradient, glow, or glass effects.
 */

import { useEffect, useRef } from "react";
import gsap from "gsap";
import { useAnimate } from "@/motion/useAnimate";

interface PersonaPreviewProps {
  persona: string;
}

/** Derive a short display name from the persona blurb (first sentence or 60 chars). */
function extractAgentName(persona: string): string {
  const match = persona.match(/(?:my name is|i(?:'m| am)|call me)\s+([A-Z][a-z]+)/i);
  if (match) return match[1];
  return "Otto";
}

function AgentAvatar({ name }: { name: string }) {
  const initials = name.slice(0, 2).toUpperCase();
  return (
    <div
      className="flex size-16 items-center justify-center rounded-full bg-surface-2 text-lg font-semibold text-foreground"
      aria-hidden="true"
    >
      {initials}
    </div>
  );
}

export function PersonaPreview({ persona }: PersonaPreviewProps) {
  const { enabled } = useAnimate();
  const avatarRef = useRef<HTMLDivElement>(null);
  const nameRef = useRef<HTMLParagraphElement>(null);
  const blurbRef = useRef<HTMLParagraphElement>(null);

  const agentName = extractAgentName(persona);

  useEffect(() => {
    const targets = [avatarRef.current, nameRef.current, blurbRef.current].filter(Boolean);
    if (!enabled) {
      // Reduced motion: ensure final state is visible
      targets.forEach((el) => {
        if (el) {
          (el as HTMLElement).style.opacity = "1";
          (el as HTMLElement).style.transform = "none";
        }
      });
      return;
    }

    // Set initial hidden state
    gsap.set(targets, { opacity: 0, y: 12 });

    // Motion budget: the last tween must finish ≤300ms.
    // avatar: 0 → 120ms.
    // name:  starts at 120-50=70ms, 100ms → ends 170ms.
    // blurb: starts at 170-50=120ms, 100ms → ends 220ms total ≤ 300ms.
    const tl = gsap.timeline();
    tl.to(avatarRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.12,
      ease: "power2.out",
    })
      .to(
        nameRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 0.1,
          ease: "power2.out",
        },
        "-=0.05"
      )
      .to(
        blurbRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 0.1,
          ease: "power2.out",
        },
        "-=0.05"
      );

    return () => {
      tl.kill();
    };
  }, [enabled, persona]);

  return (
    <div
      className="persona-preview flex flex-col gap-4"
      data-testid="persona-preview"
    >
      <div ref={avatarRef} className="flex justify-start">
        <AgentAvatar name={agentName} />
      </div>
      <p
        ref={nameRef}
        className="text-base font-semibold text-foreground"
      >
        {agentName}
      </p>
      <p
        ref={blurbRef}
        className="text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap"
      >
        {persona}
      </p>
    </div>
  );
}
