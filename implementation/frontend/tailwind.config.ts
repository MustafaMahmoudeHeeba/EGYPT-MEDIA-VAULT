import type { Config } from "tailwindcss";
import { palette } from "./src/config/theme";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: { DEFAULT: palette.navy, 600: palette.navyLight },
        gold: { DEFAULT: palette.gold, 600: palette.goldDark, 100: palette.goldSoft },
        sand: palette.sand,
        ivory: palette.ivory,
        line: palette.line,
        muted: palette.muted,
      },
    },
  },
  plugins: [],
};
export default config;
