"use client";
import Link from "next/link";
import { useApp } from "@/components/providers";
import { AlertTriangle, ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import type { ApiState } from "@/hooks/use-api";

export const btnPrimary = "h-9 rounded-md bg-navy px-4 text-sm font-medium text-white transition hover:bg-navy-600";
export const btnSecondary = "h-9 rounded-md border border-line bg-white px-3 text-sm text-navy transition hover:border-gold";
export const inputCls =
  "h-9 rounded-md border border-line bg-white px-2.5 text-sm text-navy outline-none focus:border-gold focus:ring-1 focus:ring-gold";

export function Card({ title, action, children, className = "" }: { title?: string; action?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-white p-4 shadow-sm ${className}`}>
      {(title || action) && (
        <header className="mb-3 flex items-center justify-between gap-2">
          {title && <h2 className="text-sm font-semibold text-navy">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}

export function Kpi({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-line border-s-4 border-s-gold bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 text-2xl font-bold text-navy">{value}</div>
      {hint && <div className="mt-0.5 text-xs text-muted">{hint}</div>}
    </div>
  );
}

export function Badge({ children, tone = "slate" }: { children: React.ReactNode; tone?: "slate" | "green" | "red" | "gold" }) {
  const m = { slate: "bg-sand text-muted", green: "bg-emerald-100 text-emerald-800", red: "bg-red-100 text-red-800", gold: "bg-gold-100 text-gold-600" };
  return <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${m[tone]}`}>{children}</span>;
}

export function PageHeader({ title, subtitle, back }: { title: string; subtitle?: string; back?: { href: string } }) {
  const { t, lang } = useApp();
  const Arrow = lang === "ar" ? ArrowRight : ArrowLeft;
  return (
    <div className="mb-5">
      {back && <Link href={back.href} className="mb-2 inline-flex items-center gap-1 text-sm text-gold-600 hover:underline"><Arrow size={14} />{t("Back")}</Link>}
      <h1 className="rtl-auto text-xl font-bold text-navy sm:text-2xl">{title}</h1>
      {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
    </div>
  );
}

/** Renders loading / error / empty states, then the data. */
export function Async<T>({ state, children, isEmpty }: { state: ApiState<T>; children: (d: T) => React.ReactNode; isEmpty?: (d: T) => boolean }) {
  const { t } = useApp();
  if (state.loading && !state.data)
    return <div className="flex items-center justify-center gap-2 py-12 text-sm text-muted"><Loader2 className="animate-spin" size={18} />{t("Loading…")}</div>;
  if (state.error)
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-red-200 bg-red-50 p-6 text-center">
        <AlertTriangle className="text-red-600" />
        <div className="text-sm font-medium text-red-700">{t("Something went wrong")}</div>
        <div className="max-w-xl break-words text-xs text-red-600">{state.error}</div>
        <button onClick={state.reload} className={btnPrimary}>{t("Retry")}</button>
      </div>
    );
  if (state.data === null) return null;
  if (isEmpty?.(state.data)) return <div className="py-10 text-center text-sm text-muted">{t("No results found.")}</div>;
  return <div className={state.loading ? "opacity-60 transition-opacity" : ""}>{children(state.data)}</div>;
}

export function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="flex flex-col gap-1 text-xs font-medium text-muted">{label}{children}</label>;
}

export function TableWrap({ children }: { children: React.ReactNode }) {
  return <div className="overflow-x-auto rounded-lg border border-line"><table className="w-full min-w-[640px] text-sm">{children}</table></div>;
}
export const Th = ({ children }: { children?: React.ReactNode }) => <th className="whitespace-nowrap bg-sand px-3 py-2 text-start text-xs font-semibold uppercase tracking-wide text-muted">{children}</th>;
export const Td = ({ children, className = "" }: { children?: React.ReactNode; className?: string }) => <td className={`border-t border-line px-3 py-2 align-top ${className}`}>{children}</td>;

export function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return <div><dt className="text-xs text-muted">{label}</dt><dd className="mt-0.5 break-words text-sm font-medium text-navy">{value}</dd></div>;
}

export function FilterActions({ onReset }: { onReset: () => void }) {
  const { t } = useApp();
  return (
    <div className="flex items-end gap-2">
      <button type="submit" className={btnPrimary}>{t("Apply")}</button>
      <button type="button" onClick={onReset} className={btnSecondary}>{t("Reset")}</button>
    </div>
  );
}