"use client";
import { useParams } from "next/navigation";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Badge, Card, Kpi, PageHeader, Stat, TableWrap, Td, Th } from "@/components/ui/primitives";
import { BarCard } from "@/components/charts/charts";
import { ARTICLE_GRID, ArticleCard } from "@/components/shared/article-card";
import type { StoryTimelineItem } from "@/types/api";
import { NO_VALUE, hasMultiSourceCoverage } from "@/lib/utils/story";
import { fmtDate, fmtMinutes, fmtNum, num } from "@/lib/utils/format";

/** source_name is nullable in the API schema: fall back to source_id, then a dash. */
const timelineSourceLabel = (x: StoryTimelineItem): string => x.source_name ?? x.source_id ?? "—";

export default function StoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t, lang } = useApp();
  const story = useApi(() => api.story(id), [id]);
  const timeline = useApi(() => api.storyTimeline(id), [id]);
  const articles = useApi(() => api.articles({ story_id: id, page_size: 50, sort_order: "asc" }), [id]);

  return (
    <>
      <Async state={story}>
        {(s) => (
          <>
            <PageHeader back={{ href: "/stories" }} title={s.story_title ?? "—"} />
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi label={t("Articles")} value={fmtNum(s.article_count, lang)} />
              <Kpi label={t("Sources")} value={fmtNum(s.source_count, lang)} />
              <Kpi label={t("Coverage gap")} value={hasMultiSourceCoverage(s) ? fmtMinutes(s.coverage_gap_minutes, lang) : NO_VALUE} />
              <Kpi label={t("Rank")} value={fmtNum(s.coverage_rank, lang)} />
            </div>
            <Card className="mt-4">
              <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Stat label={t("Publishers")} value={<span className="rtl-auto">{s.publisher_names ?? "—"}</span>} />
                <Stat label={t("First source")} value={s.first_source_name ?? "—"} />
                <Stat label={t("First published")} value={hasMultiSourceCoverage(s) ? fmtDate(s.first_published_at, lang) : NO_VALUE} />
                <Stat label={t("Last published")} value={hasMultiSourceCoverage(s) ? fmtDate(s.last_published_at, lang) : NO_VALUE} />
              </dl>
            </Card>
          </>
        )}
      </Async>

      <Card title={t("Publication timeline")} className="mt-5">
        <Async state={timeline} isEmpty={(d) => d.length === 0}>
          {(d) => (
            <div className="grid gap-5 lg:grid-cols-2">
              <BarCard horizontal data={d.map((x) => ({ name: timelineSourceLabel(x), value: num(x.minutes_after_story_first_publication) ?? 0 }))} />
              <TableWrap>
                <thead><tr><Th>#</Th><Th>{t("Source")}</Th><Th>{t("First published")}</Th><Th>+</Th><Th>{t("Articles")}</Th></tr></thead>
                <tbody>
                  {d.map((x) => (
                    <tr key={`${x.source_id}-${x.publication_order}`}>
                      <Td>{fmtNum(x.publication_order, lang)}</Td>
                      <Td>{timelineSourceLabel(x)} {x.is_first_source && <Badge tone="gold">{t("1st")}</Badge>}</Td>
                      <Td className="whitespace-nowrap">{fmtDate(x.first_published_at, lang)}</Td>
                      <Td>{fmtMinutes(x.minutes_after_story_first_publication, lang)}</Td>
                      <Td>{fmtNum(x.article_count, lang)}</Td>
                    </tr>
                  ))}
                </tbody>
              </TableWrap>
            </div>
          )}
        </Async>
      </Card>

      <Card title={t("Related articles")} className="mt-5">
        <Async state={articles} isEmpty={(d) => d.items.length === 0}>
          {(d) => <div className={ARTICLE_GRID}>{d.items.map((a) => <ArticleCard key={a.article_key} a={a} />)}</div>}
        </Async>
      </Card>
    </>
  );
}
