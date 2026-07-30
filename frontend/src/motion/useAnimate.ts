import gsap from "gsap";
import { prefersReducedMotion } from "../design/motion.ts";

export function useAnimate() {
  const enabled = !prefersReducedMotion();
  function ctx<T>(fn: () => T): T | void {
    if (!enabled) return;
    let out: T | void = undefined;
    const c = gsap.context(() => { out = fn(); });
    c.revert; // keep reference; screens create their own scoped contexts in effects
    return out;
  }
  return { enabled, ctx };
}
