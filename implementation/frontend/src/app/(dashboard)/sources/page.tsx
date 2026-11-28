"use client";
import Link from "next/link";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Badge, Card, PageHeader, TableWrap, Td, Th } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { fmtNum, fmtPct, num } from "@/lib/utils/format";

export default function SourcesPage() {
  const { t, lang } = useApp();
  const state = useApi(() => api.sources(), []);
  return (
    <>
      <PageHeader title={t("Sources")} />
      <Async state={state} isEmpty={(d) => d.length === 0}>
        {(d) => (
          <div className="space-y-5">
            <div className="grid gap-5 lg:grid-cols-2">
              <Card title={t("Total articles")}><BarCard horizontal data={d.map((s) => ({ name: s.source_name, value: num(s.total_articles) ?? 0 }))} /></Card>
              <Card title={`${t("Stories covered")} — ${t("Shared stories")} / ${t("Exclusive stories")}`}>
                <BarCard horizontal data={d.map((s) => ({ name: s.source_name, value: num(s.stories_covered) ?? 0 }))} />
              </Card>
            </div>
            <TableWrap>
              <thead><tr><Th>{t("Rank")}</Th><Th>{t("Name")}</Th><Th>{t("Articles")}</Th><Th>{t("Share of total")}</Th><Th>{t("Stories covered")}</Th><Th>{t("Shared stories")}</Th><Th>{t("Exclusive stories")}</Th><Th>{t("Success rate")}</Th><Th>{t("Status")}</Th></tr></thead>
              <tbody>
                {d.map((s) => (
                  <tr key={s.source_id} className="hover:bg-ivory">
                    <Td>{fmtNum(s.activity_rank, lang)}</Td>
                    <Td><Link className="font-medium text-navy hover:text-gold-600" href={`/sources/${encodeURIComponent(s.source_id)}`}>{s.source_name}</Link></Td>
                    <Td>{fmtNum(s.total_articles, lang)}</Td>
                    <Td>{fmtPct(s.share_of_total_articles_pct, lang)}</Td>
                    <Td>{fmtNum(s.stories_covered, lang)}</Td>
                    <Td>{fmtNum(s.stories_shared_with_other_sources, lang)}</Td>
                    <Td>{fmtNum(s.stories_exclusive, lang)}</Td>
                    <Td>{fmtPct(s.success_rate_pct, lang)}</Td>
                    <Td>{s.is_enabled === null ? "—" : s.is_enabled ? <Badge tone="green">{t("Enabled")}</Badge> : <Badge tone="red">{t("Disabled")}</Badge>}</Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
          </div>
        )}
      </Async>
    </>
  );
}
