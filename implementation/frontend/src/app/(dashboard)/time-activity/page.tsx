"use client";
import { useMemo, useState } from "react";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Card, Field, PageHeader, inputCls } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { fmtNum } from "@/lib/utils/format";
import type { TimeActivity } from "@/types/api";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const isWeekend = (r: TimeActivity) => r.publication_is_weekend === true || r.publication_is_weekend === 1;

function Analysis({ rows }: { rows: TimeActivity[] }) {
  const { t, lang } = useApp();
  const m = useMemo(() => {
    const hour = new Array(24).fill(0) as number[];
    const dow = new Array(7).fill(0) as number[];
    const grid = Array.from({ length: 7 }, () => new Array(24).fill(0) as number[]);
    const period: Record<string, number> = {};
    let weekend = 0, weekday = 0;
    for (const r of rows) {
      const h = r.publication_hour; const d = (r.publication_iso_day_of_week ?? 0) - 1;
      if (h >= 0 && h < 24) hour[h] += r.article_count;
      if (d >= 0 && d < 7) { dow[d] += r.article_count; if (h >= 0 && h < 24) grid[d][h] += r.article_count; }
      const p = r.publication_day_period ?? "—"; period[p] = (period[p] ?? 0) + r.article_count;
      if (isWeekend(r)) weekend += r.article_count; else weekday += r.article_count;
    }
    return { hour, dow, grid, period, weekend, weekday, max: Math.max(1, ...grid.flat()) };
  }, [rows]);

  return (
    <div className="space-y-5">
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title={t("Activity by hour")}><BarCard data={m.hour.map((v, i) => ({ name: String(i), value: v }))} /></Card>
        <Card title={t("Activity by weekday")}><BarCard data={m.dow.map((v, i) => ({ name: DAYS[i], value: v }))} /></Card>
        <Card title={t("Day periods")}><BarCard data={Object.entries(m.period).map(([name, value]) => ({ name, value }))} /></Card>
        <Card title={t("Weekday vs weekend")}><BarCard data={[{ name: t("Weekday"), value: m.weekday }, { name: t("Weekend"), value: m.weekend }]} /></Card>
      </div>
      <Card title={t("Heatmap (weekday × hour)")}>
        <div dir="ltr" className="overflow-x-auto">
          <div className="min-w-[640px]">
            <div className="ms-10 grid grid-cols-[repeat(24,minmax(0,1fr))] gap-0.5 text-[10px] text-muted">{Array.from({ length: 24 }, (_, h) => <div key={h} className="text-center">{h}</div>)}</div>
            {m.grid.map((row, d) => (
              <div key={d} className="mt-0.5 flex items-center gap-1">
                <div className="w-9 text-xs text-muted">{DAYS[d]}</div>
                <div className="grid flex-1 grid-cols-[repeat(24,minmax(0,1fr))] gap-0.5">
                  {row.map((v, h) => <div key={h} title={`${DAYS[d]} ${h}:00 — ${fmtNum(v, lang)}`} className="aspect-square rounded-sm bg-gold" style={{ opacity: v === 0 ? 0.07 : 0.15 + 0.85 * (v / m.max) }} />)}
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  );
}

export default function TimeActivityPage() {
  const { t } = useApp();
  const [from, setFrom] = useState(""); const [to, setTo] = useState(""); const [source, setSource] = useState("");
  const sources = useApi(() => api.sources(), []);
  const state = useApi(() => api.timeActivity({ date_from: from, date_to: to, source_id: source }), [from, to, source]);
  return (
    <>
      <PageHeader title={t("Time Activity")} />
      <Card className="mb-4">
        <div className="grid gap-3 sm:grid-cols-3">
          <Field label={t("Source")}>
            <select className={inputCls} value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="">{t("All")}</option>
              {(sources.data ?? []).map((s) => <option key={s.source_id} value={s.source_id}>{s.source_name}</option>)}
            </select>
          </Field>
          <Field label={t("From")}><input type="date" className={inputCls} value={from} onChange={(e) => setFrom(e.target.value)} /></Field>
          <Field label={t("To")}><input type="date" className={inputCls} value={to} onChange={(e) => setTo(e.target.value)} /></Field>
        </div>
      </Card>
      <Async state={state} isEmpty={(d) => d.length === 0}>{(d) => <Analysis rows={d} />}</Async>
    </>
  );
}
