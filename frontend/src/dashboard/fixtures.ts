/**
 * fixtures.ts — demo data for the operator cockpit.
 * Replace with live API data in a later wave.
 */

import type { Stage } from "../types.ts";

export interface ConversationItem {
  id: string;
  name: string;
  stage: Stage;
  lastMessage: string;
  timestampIso: string;
}

export interface EscalationItem {
  id: string;
  name: string;
  reason: string;
  timestampIso: string;
}

export interface AvailabilityDay {
  label: string; // e.g. "Mon"
  date: string;  // e.g. "Jul 28"
  slots: number; // open slots
}

export const fixtureMetrics = {
  leadsToday: 128,
  booked: 41,
  conversionPct: 32,
  avgResponseSec: 47,
};

export const fixtureConversations: ConversationItem[] = [
  {
    id: "conv-1",
    name: "Maria Santos",
    stage: "confirm",
    lastMessage: "Oo, confirmed ang appointment ko sa Biyernes. Salamat!",
    timestampIso: "2026-07-30T09:42:00+08:00",
  },
  {
    id: "conv-2",
    name: "Jose Reyes",
    stage: "qualify",
    lastMessage: "Pwede ba bukas ng hapon? Hindi ako makakarating ngayon.",
    timestampIso: "2026-07-30T09:38:00+08:00",
  },
  {
    id: "conv-3",
    name: "Ana Cruz",
    stage: "pitch",
    lastMessage: "Magkano ang presyo ng package?",
    timestampIso: "2026-07-30T09:31:00+08:00",
  },
  {
    id: "conv-4",
    name: "Pedro Dela Cruz",
    stage: "escalate",
    lastMessage: "Hindi ko gusto ang ganyang setup. Gusto ko makausap manager.",
    timestampIso: "2026-07-30T09:22:00+08:00",
  },
  {
    id: "conv-5",
    name: "Liza Gomez",
    stage: "intro",
    lastMessage: "Hello, interested ako sa inyong serbisyo.",
    timestampIso: "2026-07-30T09:15:00+08:00",
  },
  {
    id: "conv-6",
    name: "Ramon Torres",
    stage: "objection_handling",
    lastMessage: "Medyo mahal naman. Wala ba kayong mas mura?",
    timestampIso: "2026-07-30T09:08:00+08:00",
  },
];

export const fixtureEscalations: EscalationItem[] = [
  {
    id: "esc-1",
    name: "Pedro Dela Cruz",
    reason: "Requested to speak with a manager",
    timestampIso: "2026-07-30T09:22:00+08:00",
  },
  {
    id: "esc-2",
    name: "Carlos Mendoza",
    reason: "Complaint about pricing",
    timestampIso: "2026-07-30T08:55:00+08:00",
  },
  {
    id: "esc-3",
    name: "Teresita Villanueva",
    reason: "No-show follow-up needed",
    timestampIso: "2026-07-30T08:30:00+08:00",
  },
];

export const fixtureAvailability: AvailabilityDay[] = [
  { label: "Mon", date: "Jul 28", slots: 3 },
  { label: "Tue", date: "Jul 29", slots: 5 },
  { label: "Wed", date: "Jul 30", slots: 2 },
  { label: "Thu", date: "Jul 31", slots: 7 },
  { label: "Fri", date: "Aug 1", slots: 4 },
  { label: "Sat", date: "Aug 2", slots: 1 },
  { label: "Sun", date: "Aug 3", slots: 0 },
];
