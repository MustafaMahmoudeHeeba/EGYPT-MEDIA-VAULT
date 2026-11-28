"use client";
import Link from "next/link";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Card, Kpi, PageHeader, Td, Th, TableWrap } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { ARTICLE_GRID, ArticleCard } from "@/components/shared/article-card";
import { fmtDate, fmtNum, fmtPct, num } from "@/lib/utils/format";

export default function OverviewPage() {
  const { t, lang } = useApp();
  const ov = useApi(() => api.overview(), []);
  const stories = useApi(() => api.stories({ page_size: 6 }), []);
  const articles = useApi(() => api.articles({ page_size: 6 }), []);
  const sources = useApi(() => api.sources(), []);

  return (
    <>
      <PageHeader title={t("Overview")} />
      <Async state={ov}>
        {(o) => (
          <div className="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-3">
            <Kpi label={t("Total stories")} value={fmtNum(o.total_stories, lang)} />
            <Kpi label={t("Total articles")} value={fmtNum(o.total_articles, lang)} />
            <Kpi label={t("Multi-source stories")} value={fmtNum(o.multi_source_stories, lang)} hint={`${fmtNum(o.single_source_stories, lang)} ${t("single-source")}`} />
            <Kpi label={t("Multi-source %")} value={fmtPct(o.multi_source_story_pct, lang)} />
            <Kpi label={t("News sources")} value={fmtNum(o.total_sources, lang)} />
            <Kpi label={t("Avg publishers / story")} value={fmtNum(o.avg_publishers_per_story, lang, 2)} />
            <Kpi label={t("Articles in stories")} value={fmtNum(o.total_articles_in_stories, lang)} />
          </div>
        )}
      </Async>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card title={t("Articles by source")}>
          <Async state={sources} isEmpty={(d) => d.length === 0}>
            {(d) => <BarCard horizontal data={[...d].sort((a, b) => (num(b.total_articles) ?? 0) - (num(a.total_articles) ?? 0)).map((s) => ({ name: s.source_name, value: num(s.total_articles) ?? 0 }))} />}
          </Async>
        </Card>
        <Card title={t("Recent stories")} action={<Link href="/stories" className="text-xs text-gold-600 hover:underline">{t("Stories")} →</Link>}>
          <Async state={stories} isEmpty={(d) => d.items.length === 0}>
            {(d) => (
              <TableWrap>
                <thead><tr><Th>{t("Title")}</Th><Th>{t("Source count")}</Th><Th>{t("Last published")}</Th></tr></thead>
                <tbody>
                  {d.items.map((s) => (
                    <tr key={s.story_key}>
                      <Td><Link dir="auto" className="rtl-auto hover:text-gold-600" href={`/stories/${encodeURIComponent(s.story_id ?? String(s.story_key))}`}>{s.story_title ?? "—"}</Link></Td>
                      <Td>{fmtNum(s.source_count, lang)}</Td>
                      <Td className="whitespace-nowrap">{fmtDate(s.last_published_at, lang)}</Td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            )}
          </Async>
        </Card>
      </div>

      <Card title={t("Latest articles")} className="mt-5" action={<Link href="/articles" className="text-xs text-gold-600 hover:underline">{t("Articles")} →</Link>}>
        <Async state={articles} isEmpty={(d) => d.items.length === 0}>
          {(d) => <div className={ARTICLE_GRID}>{d.items.map((a) => <ArticleCard key={a.article_key} a={a} />)}</div>}
        </Async>
      </Card>
    </>
  );
}
