import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--bg)",
        foreground: "var(--text)",
        muted: { DEFAULT: "var(--surface)", foreground: "var(--text-muted)" },
        border: "var(--border)",
        primary: { DEFAULT: "var(--accent)", foreground: "var(--accent-fg)" },
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)" },
        status: {
          new: "var(--status-new)",
          qualifying: "var(--status-qualifying)",
          hot: "var(--status-hot)",
          booked: "var(--status-booked)",
          escalated: "var(--status-escalated)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
};

export default config;
