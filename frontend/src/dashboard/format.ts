/**
 * Dashboard formatters — pure functions, no side effects.
 */

/**
 * Returns the conversion percentage (booked / leads * 100), rounded to a whole number.
 * Returns 0 when leads is 0 to avoid division by zero.
 */
export function conversionPct(booked: number, leads: number): number {
  if (leads === 0) return 0;
  return Math.round((booked / leads) * 100);
}

/**
 * Formats a number with thousands separators (e.g. 3547 → "3,547").
 */
export function fmtNum(n: number): string {
  return n.toLocaleString("en-US");
}
