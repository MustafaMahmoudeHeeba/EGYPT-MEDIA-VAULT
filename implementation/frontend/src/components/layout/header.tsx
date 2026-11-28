"use client";
import { Languages } from "lucide-react";
import { useApp } from "@/components/providers";
import { LogoMark } from "./brand";

export function Header() {
  const { t, lang, setLang } = useApp();
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-line bg-ivory/90 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-2 lg:hidden"><LogoMark className="h-8 w-8" /><span className="text-sm font-extrabold tracking-wide">EGYPT-MEDIA-VAULT</span></div>
      <div className="hidden text-sm font-medium text-muted lg:block">{t("News Intelligence")}</div>
      <button onClick={() => setLang(lang === "en" ? "ar" : "en")} className="flex items-center gap-1.5 rounded-md border border-line bg-white px-3 py-1.5 text-xs font-medium text-navy hover:border-gold">
        <Languages size={14} />{lang === "en" ? "العربية" : "English"}
      </button>
    </header>
  );
}
