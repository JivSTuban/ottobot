import { motion } from "./tokens.ts";

export const easing = {
  out: "cubic-bezier(0.16,1,0.3,1)",
  inOut: "cubic-bezier(0.65,0,0.35,1)",
} as const;

export function prefersReducedMotion(): boolean {
  return typeof matchMedia === "function"
    && matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function transition(prop: string, speed: keyof typeof motion = "base"): string {
  if (prefersReducedMotion()) return "none";
  return `${prop} ${motion[speed]}ms ${easing.out}`;
}
