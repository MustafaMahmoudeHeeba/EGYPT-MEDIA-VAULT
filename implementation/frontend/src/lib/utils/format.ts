export type Lang = "en" | "ar";
export const num = (v: string | number | null | undefined): number | null => {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};
const loc = (l: Lang) => (l === "ar" ? "ar-EG" : "en-GB");
export const fmtNum = (v: string | number | null | undefined, l: Lang = "en", digits = 0) => {
  const n = num(v);
  return n === null ? "—" : n.toLocaleString(loc(l), { maximumFractionDigits: digits });
};
export const fmtPct = (v: string | number | null | undefined, l: Lang = "en") => {
  const n = num(v);
  return n === null ? "—" : `${n.toLocaleString(loc(l), { maximumFractionDigits: 1 })}%`;
};
export const fmtDate = (v: string | null | undefined, l: Lang = "en", withTime = true) => {
  if (!v) return "—";
  const d = new Date(v);
  if (isNaN(d.getTime())) return v;
  return d.toLocaleString(loc(l), withTime ? { dateStyle: "medium", timeStyle: "short" } : { dateStyle: "medium" });
};
export const fmtMinutes = (v: string | number | null | undefined, l: Lang = "en") => {
  const n = num(v);
  if (n === null) return "—";
  if (n >= 1440) return `${fmtNum(n / 1440, l, 1)} d`;
  if (n >= 60) return `${fmtNum(n / 60, l, 1)} h`;
  return `${fmtNum(n, l, 1)} min`;
};
