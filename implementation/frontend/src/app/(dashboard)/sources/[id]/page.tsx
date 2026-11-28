"use client";
import { useParams } from "next/navigation";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Card, Kpi, PageHeader, Stat } from "@/components/ui/primitives";
import { LineCard } from "@/components/charts/charts";
import { fmtDate, fmtNum, fmtPct } from "@/lib/utils/format";

export default function SourceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t, lang } = useApp();
  // GET /sources/{source_id} has no documented response schema, so the documented list schema is used.
  const src = useApi(async () => {
    const list = await api.sources();
    const hit = list.find((x) => x.source_id === id);
    if (!hit) throw new Error(`Source "${id}" not found`);
    return hit;
  }, [id]);
  const daily = useApi(() => api.sourceDaily({ source_id: id }), [id]);

  return (
    <>
      <Async state={src}>
        {(s) => (
          <>
            <PageHeader back={{ href: "/sources" }} title={s.source_name} />
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
              <Kpi label={t("Total articles")} value={fmtNum(s.total_articles, lang)} hint={fmtPct(s.share_of_total_articles_pct, lang)} />
              <Kpi label={t("Stories covered")} value={fmtNum(s.stories_covered, lang)} />
              <Kpi label={t("Categories covered")} value={fmtNum(s.distinct_categories, lang)} />
              <Kpi label={t("Success rate")} value={fmtPct(s.success_rate_pct, lang)} />
            </div>
            <div className="mt-5 grid gap-5 lg:grid-cols-2">
              <Card title={t("Stories covered")}>
                <dl className="grid grid-cols-2 gap-4">
                  <Stat label={t("Shared stories")} value={fmtNum(s.stories_shared_with_other_sources, lang)} />
                  <Stat label={t("Exclusive stories")} value={fmtNum(s.stories_exclusive, lang)} />
                  <Stat label={t("First published")} value={fmtDate(s.first_published_at, lang)} />
                  <Stat label={t("Last published")} value={fmtDate(s.last_published_at, lang)} />
                </dl>
              </Card>
              <Card title={t("Collection runs")}>
                <dl className="grid grid-cols-2 gap-4">
                  <Stat label={t("Collection runs")} value={fmtNum(s.collection_runs, lang)} />
                  <Stat label={t("Successful / failed")} value={`${fmtNum(s.successful_collections, lang)} / ${fmtNum(s.failed_collections, lang)}`} />
                  <Stat label={t("Attempts")} value={`${fmtNum(s.total_attempts, lang)} (${fmtNum(s.retried_collections, lang)} ${t("retried")})`} />
                  <Stat label={t("Collected")} value={fmtNum(s.total_articles_collected, lang)} />
                  <Stat label={t("Rejected")} value={fmtNum(s.total_articles_rejected, lang)} />
                  <Stat label={t("Duplicates")} value={fmtNum(s.total_duplicate_records, lang)} />
                  <Stat label={t("Last successful run")} value={fmtDate(s.last_successful_run_date, lang, false)} />
                  <Stat label={t("Last failed run")} value={fmtDate(s.last_failed_run_date, lang, false)} />
                  <div className="col-span-2"><Stat label={t("Failures by step")} value={s.failures_by_step ?? "—"} /></div>
                </dl>
              </Card>
            </div>
          </>
        )}
      </Async>
      <Card title={t("Daily activity")} className="mt-5">
        <Async state={daily} isEmpty={(d) => d.length === 0}>
          {(d) => <LineCard data={d.map((x) => ({ name: x.publication_date, value: x.article_count }))} />}
        </Async>
      </Card>
    </>
  );
}
