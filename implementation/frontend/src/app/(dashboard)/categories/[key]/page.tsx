"use client";
import { useParams } from "next/navigation";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Card, Kpi, PageHeader, TableWrap, Td, Th } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { ARTICLE_GRID, ArticleCard } from "@/components/shared/article-card";
import { fmtNum, fmtPct, num } from "@/lib/utils/format";

export default function CategoryDetailPage() {
  const { key } = useParams<{ key: string }>();
  const { t, lang } = useApp();
  const cat = useApi(() => api.category(key), [key]);
  const name = cat.data?.category_name ?? "";
  const articles = useApi(() => (name ? api.articles({ category_name: name, page_size: 10 }) : Promise.resolve(null)), [name]);

  return (
    <>
      <Async state={cat}>
        {(c) => (
          <>
            <PageHeader back={{ href: "/categories" }} title={c.category_name} />
            <div className="grid grid-cols-3 gap-3">
              <Kpi label={t("Articles")} value={fmtNum(c.total_articles, lang)} />
              <Kpi label={t("Source count")} value={fmtNum(c.source_count, lang)} />
              <Kpi label={t("Rank")} value={fmtNum(c.activity_rank, lang)} />
            </div>
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <Card title={t("Articles / source")}><BarCard horizontal data={c.sources.map((s) => ({ name: s.source_name, value: num(s.article_count) ?? 0 }))} /></Card>
              <Card title={t("Source contribution")}>
                <TableWrap>
                  <thead><tr><Th>{t("Source")}</Th><Th>{t("Articles")}</Th><Th>{t("% of category")}</Th><Th>{t("% of source")}</Th></tr></thead>
                  <tbody>
                    {c.sources.map((s) => (
                      <tr key={s.source_id}><Td>{s.source_name}</Td><Td>{fmtNum(s.article_count, lang)}</Td><Td>{fmtPct(s.source_share_of_category_pct, lang)}</Td><Td>{fmtPct(s.share_of_source_pct, lang)}</Td></tr>
                    ))}
                  </tbody>
                </TableWrap>
              </Card>
            </div>
          </>
        )}
      </Async>
      <Card title={t("Related articles")} className="mt-5">
        <Async state={articles} isEmpty={(d) => !d || d.items.length === 0}>
          {(d) => <div className={ARTICLE_GRID}>{d?.items.map((a) => <ArticleCard key={a.article_key} a={a} />)}</div>}
        </Async>
      </Card>
    </>
  );
}
