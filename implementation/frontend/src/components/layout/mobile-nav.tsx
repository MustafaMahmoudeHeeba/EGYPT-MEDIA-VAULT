"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { LayoutGrid, X } from "lucide-react";
import { useApp } from "@/components/providers";
import { NAV_ITEMS, isActiveRoute } from "@/config/navigation";

export function MobileNav() {
  const { t } = useApp();
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const primary = NAV_ITEMS.filter((i) => i.mobilePrimary);
  const rest = NAV_ITEMS.filter((i) => !i.mobilePrimary);
  const moreActive = rest.some((i) => isActiveRoute(path, i.href));

  const tab = (active: boolean) => `flex flex-1 flex-col items-center gap-0.5 py-2 text-[11px] font-medium ${active ? "text-navy" : "text-muted"}`;
  const pill = (active: boolean) => `rounded-full px-4 py-1 ${active ? "bg-gold/25" : ""}`;

  return (
    <div className="lg:hidden">
      {open && (
        <div className="fixed inset-0 z-40">
          <div className="absolute inset-0 bg-navy/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-x-0 bottom-0 rounded-t-2xl border-t border-line bg-sand p-4 pb-24">
            <button aria-label="Close" onClick={() => setOpen(false)} className="absolute end-3 top-3 text-muted"><X size={20} /></button>
            <div className="mt-4 grid gap-2">
              {rest.map(({ href, label, icon: Icon }) => (
                <Link key={href} href={href} onClick={() => setOpen(false)} className={`flex items-center gap-3 rounded-lg border-s-4 px-3 py-3 text-sm font-medium ${isActiveRoute(path, href) ? "border-gold bg-white text-navy" : "border-transparent text-muted"}`}>
                  <Icon size={18} />{t(label)}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}
      <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-50 flex border-t border-line bg-sand pb-[env(safe-area-inset-bottom)]">
        {primary.map(({ href, label, icon: Icon }) => {
          const active = isActiveRoute(path, href);
          return (
            <Link key={href} href={href} aria-current={active ? "page" : undefined} className={tab(active)}>
              <span className={pill(active)}><Icon size={20} /></span>{t(label)}
            </Link>
          );
        })}
        <button onClick={() => setOpen(true)} className={tab(moreActive)}>
          <span className={pill(moreActive)}><LayoutGrid size={20} /></span>{t("More")}
        </button>
      </nav>
    </div>
  );
}
