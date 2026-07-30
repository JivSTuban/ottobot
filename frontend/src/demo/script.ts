/**
 * demo/script.ts — Scripted lead→booked demo sequence.
 *
 * A realistic Taglish qualify→pitch→propose→confirm conversation.
 * Last step's stage maps to "booked" via stageToLeadStatus.
 */

import type { Stage } from "../types.ts";

export interface DemoStep {
  author: "lead" | "agent";
  text: string;
  stage: Stage;
}

export const demoScript: DemoStep[] = [
  {
    author: "agent",
    text: "Magandang araw! Ako si Otto, ang AI sales assistant ng OttoBot. Paano kita matutulungan ngayon?",
    stage: "intro",
  },
  {
    author: "lead",
    text: "Naghahanap ako ng sistema para sa aming beauty salon. Marami kaming kliyente pero nahihirapan kaming mag-follow up.",
    stage: "qualify",
  },
  {
    author: "agent",
    text: "Naiintindihan ko! Ang OttoBot ay espesyal na dinisenyo para sa mga beauty salon — awtomatikong nag-fo-follow up sa mga kliyente mo 24/7. Ilan ba ang mga kliyente mo sa isang buwan?",
    stage: "qualify",
  },
  {
    author: "lead",
    text: "Mga 80 hanggang 100 kliyente sa isang buwan. Minsan hindi namin naaabutan ang lahat.",
    stage: "pitch",
  },
  {
    author: "agent",
    text: "Perpekto ang OttoBot para sa inyong salon! Ang aming sistema ay kayang humawak ng hanggang 500 kliyente — automatic ang appointment reminders, follow-ups, at even promotional messages. Gusto mo bang makita kung paano ito gumagana sa isang live demo?",
    stage: "pitch",
  },
  {
    author: "lead",
    text: "Paano ito nag-integrate sa aming existing booking system? At magkano ang presyo?",
    stage: "objection_handling",
  },
  {
    author: "agent",
    text: "Magaan ang integration — nakikipagtulungan kami sa mga kilalang booking platforms. Ang presyo ay nagsisimula sa ₱2,500 bawat buwan para sa basic plan. Ngunit mas magandang ipakita ko sa iyo ang lahat ng features sa isang 30-minutong demo. Pwede ka ba sa Miyerkules o Huwebes ng susunod na linggo?",
    stage: "propose_appointment",
  },
  {
    author: "lead",
    text: "Pwede sa Huwebes, siguro ika-2 ng hapon?",
    stage: "propose_appointment",
  },
  {
    author: "agent",
    text: "Napakagaling! Na-confirm na ang inyong demo appointment sa Huwebes, ika-2 ng hapon. Magpapadala kami ng calendar invite at meeting link sa inyong email. Salamat at abangan ang aming tawag!",
    stage: "confirm",
  },
];

/**
 * Advances the demo step index by 1, clamped to demoScript.length (inclusive).
 * Calling advance(demoScript.length) returns demoScript.length (no-op at end).
 */
export function advance(i: number): number {
  return Math.min(i + 1, demoScript.length);
}
