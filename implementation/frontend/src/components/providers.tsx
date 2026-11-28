"use client";
import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { ar } from "@/lib/utils/i18n";
import type { Lang } from "@/lib/utils/format";

interface Ctx { lang: Lang; setLang: (l: Lang) => void; t: (k: string) => string }
const C = createContext<Ctx | null>(null);

export function Providers({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");
  useEffect(() => {
    try { const l = localStorage.getItem("emv-lang"); if (l === "ar" || l === "en") setLangState(l); } catch { /* storage unavailable */ }
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  }, [lang]);
  const setLang = (l: Lang) => { setLangState(l); try { localStorage.setItem("emv-lang", l); } catch { /* */ } };
  const t = useCallback((k: string) => (lang === "ar" ? ar[k] ?? k : k), [lang]);
  return <C.Provider value={{ lang, setLang, t }}>{children}</C.Provider>;
}

export function useApp(): Ctx {
  const v = useContext(C);
  if (!v) throw new Error("useApp must be used inside Providers");
  return v;
}
