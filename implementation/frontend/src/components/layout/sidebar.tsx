"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useApp } from "@/components/providers";
import { NAV_ITEMS, isActiveRoute } from "@/config/navigation";
import { Brand, PyramidScene } from "./brand";

export function Sidebar() {
  const { t } = useApp();
  const path = usePathname();
  return (
    <aside className="fixed inset-y-0 start-0 z-30 hidden w-64 flex-col overflow-hidden border-e border-line bg-sand lg:flex">
      <div className="relative h-[190px] shrink-0 overflow-hidden border-b border-line bg-gradient-to-b from-ivory to-gold-100">
        <div className="relative z-10 px-5 pt-5"><Brand subtitle={t("News Intelligence")} /></div>
        <PyramidScene className="absolute inset-x-0 bottom-0 w-full" />
      </div>
      <nav className="relative z-10 flex flex-col gap-1 p-3" aria-label="Main">
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = isActiveRoute(path, href);
          return (
            <Link key={href} href={href} aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 rounded-lg border-s-4 px-3 py-2.5 text-sm font-medium transition ${active ? "border-gold bg-white text-navy shadow-sm" : "border-transparent text-muted hover:bg-white/60 hover:text-navy"}`}>
              <Icon size={18} className={active ? "text-gold-600" : ""} />{t(label)}
            </Link>
          );
        })}
      </nav>
      <PyramidScene className="pointer-events-none absolute inset-x-0 bottom-0 w-full opacity-30" />
    </aside>
  );
}