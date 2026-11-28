/** Brand palette — the single source of truth. Tailwind (tailwind.config.ts) and charts both read from here. */
export const palette = {
  navy: "#17243A",
  navyLight: "#2B4166",
  gold: "#D5A84C",
  goldDark: "#B88B2F",
  goldSoft: "#F6EBD0",
  sand: "#F3EBDB",   // sidebar / subtle surfaces
  ivory: "#FBF8F2",  // page background
  line: "#E6DDC9",   // borders
  muted: "#6B6455",  // secondary text
} as const;
