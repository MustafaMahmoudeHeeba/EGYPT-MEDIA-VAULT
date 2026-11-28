import { palette } from "@/config/theme";

/** Outline pyramid with two tier lines; inherits colour from `currentColor`. */
export function PyramidGlyph({ className = "h-8 w-8" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" aria-hidden="true">
      <polygon points="24,6 42,40 6,40" />
      <line x1="16.6" y1="20" x2="31.4" y2="20" />
      <line x1="11.3" y1="30" x2="36.7" y2="30" />
    </svg>
  );
}

/** App logo: navy tile, gold pyramid (Egypt), sun disc, stacked tiers (intelligence layers). */
export function LogoMark({ className = "h-10 w-10" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" className={className} aria-hidden="true">
      <rect width="48" height="48" rx="11" fill={palette.navy} />
      <circle cx="36" cy="12" r="3" fill={palette.goldSoft} />
      <polygon points="24,10 30,21 18,21" fill={palette.gold} />
      <polygon points="17,23.5 31,23.5 35,31 13,31" fill={palette.gold} opacity="0.8" />
      <polygon points="12,33.5 36,33.5 41,42 7,42" fill={palette.gold} opacity="0.6" />
    </svg>
  );
}

export function Brand({ subtitle }: { subtitle: string }) {
  return (
    <div className="flex items-center gap-3" dir="ltr">
      <LogoMark className="h-12 w-12" />
      <div className="leading-tight">
        <div className="text-[15px] font-extrabold tracking-wide text-navy">EGYPT-MEDIA-VAULT</div>
        <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-gold-600">{subtitle}</div>
      </div>
    </div>
  );
}

/**
 * Vector Giza-style skyline: three pyramids (lit + shadow faces), a sun disc and a dune line.
 * Purely decorative; size and opacity are controlled by the caller.
 */
export function PyramidScene({ className = "" }: { className?: string }) {
  const lit = palette.gold;
  const shade = palette.goldDark;
  return (
    <svg viewBox="0 0 260 140" preserveAspectRatio="xMidYMax meet" className={className} aria-hidden="true">
      <circle cx="205" cy="38" r="13" fill={palette.goldSoft} />
      {/* small right pyramid */}
      <polygon points="222,88 190,124 228,124" fill={lit} />
      <polygon points="222,88 228,124 262,124" fill={shade} />
      {/* medium left pyramid */}
      <polygon points="66,66 14,124 76,124" fill={lit} />
      <polygon points="66,66 76,124 118,124" fill={shade} />
      {/* great pyramid */}
      <polygon points="150,22 74,124 164,124" fill={lit} />
      <polygon points="150,22 164,124 236,124" fill={shade} />
      <line x1="112" y1="73" x2="193" y2="73" stroke={palette.goldSoft} strokeOpacity="0.55" strokeWidth="1" />
      <line x1="94" y1="98" x2="212" y2="98" stroke={palette.goldSoft} strokeOpacity="0.55" strokeWidth="1" />
      {/* dunes */}
      <path d="M0 122 Q65 110 130 122 T260 120 V140 H0 Z" fill={palette.goldSoft} />
      <path d="M0 132 Q80 122 150 132 T260 130 V140 H0 Z" fill={palette.gold} opacity="0.35" />
    </svg>
  );
}