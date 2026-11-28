"use client";
import Link from "next/link";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Card, Kpi, PageHeader, TableWrap, Td, Th } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { fmtNum } from "@/lib/utils/format";

export default function CategoriesPage() {
  const { t, lang } = useApp();
  const state = useApi(() => api.categories(), []);
  return (
    <>
      <PageHeader title={t("Categories")} />
      <Async state={state} isEmpty={(d) => d.length === 0}>
        {(d) => {
          const sorted = [...d].sort((a, b) => b.total_articles - a.total_articles);
          return (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <Kpi label={t("Categories")} value={fmtNum(d.length, lang)} />
                <Kpi label={t("Total articles")} value={fmtNum(d.reduce((s, c) => s + c.total_articles, 0), lang)} />
              </div>
              <Card title={t("Total articles")}><BarCard horizontal data={sorted.slice(0, 15).map((c) => ({ name: c.category_name, value: c.total_articles }))} /></Card>
              <TableWrap>
                <thead><tr><Th>{t("Rank")}</Th><Th>{t("Category")}</Th><Th>{t("Articles")}</Th><Th>{t("Source count")}</Th></tr></thead>
                <tbody>
                  {sorted.map((c) => (
                    <tr key={c.category_key} className="hover:bg-ivory">
                      <Td>{fmtNum(c.activity_rank, lang)}</Td>
                      <Td><Link dir="auto" className="rtl-auto font-medium text-navy hover:text-gold-600" href={`/categories/${c.category_key}`}>{c.category_name}</Link></Td>
                      <Td>{fmtNum(c.total_articles, lang)}</Td>
                      <Td>{fmtNum(c.source_count, lang)}</Td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </div>
          );
        }}
      </Async>
    </>
  );
}
