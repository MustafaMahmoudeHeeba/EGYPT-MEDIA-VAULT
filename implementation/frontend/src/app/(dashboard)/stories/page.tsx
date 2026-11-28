"use client";
import Link from "next/link";
import { api } from "@/lib/api/services";
import { useFilters } from "@/hooks/use-filters";
import { useInfiniteList } from "@/hooks/use-infinite-list";
import { useApp } from "@/components/providers";
import { Async, Badge, Card, Field, FilterActions, PageHeader, TableWrap, Td, Th, inputCls } from "@/components/ui/primitives";
import { InfiniteListFooter, ResultCount } from "@/components/ui/infinite-list";
import { NO_VALUE, hasMultiSourceCoverage as multi } from "@/lib/utils/story";
import { fmtDate, fmtMinutes, fmtNum } from "@/lib/utils/format";

const INIT = { search: "", multi: false, from: "", to: "", order: "desc" };

export default function StoriesPage() {
  const { t, lang } = useApp();
  const f = useFilters(INIT);
  const a = f.applied;
  const list = useInfiniteList(
    (page, pageSize) => api.stories({
      page, page_size: pageSize, search: a.search, multi_source_only: a.multi,
      date_from: a.from, date_to: a.to, sort_order: a.order,
    }),
    [a],
  );

  return (
    <>
      <PageHeader title={t("Stories")} />
      <Card className="mb-4">
        <form onSubmit={(e) => { e.preventDefault(); f.apply(); }} className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3">
          <Field label={t("Search")}><input dir="auto" className={inputCls} value={f.draft.search} onChange={(e) => f.set("search", e.target.value)} /></Field>
          <Field label={t("From")}><input type="date" className={inputCls} value={f.draft.from} onChange={(e) => f.set("from", e.target.value)} /></Field>
          <Field label={t("To")}><input type="date" className={inputCls} value={f.draft.to} onChange={(e) => f.set("to", e.target.value)} /></Field>
          <Field label={t("Order")}>
            <select className={inputCls} value={f.draft.order} onChange={(e) => f.set("order", e.target.value)}>
              <option value="desc">{t("Newest first")}</option><option value="asc">{t("Oldest first")}</option>
            </select>
          </Field>
          <label className="flex items-center gap-2 self-end pb-2 text-sm"><input type="checkbox" checked={f.draft.multi} onChange={(e) => f.set("multi", e.target.checked)} />{t("Multi-source only")}</label>
          <FilterActions onReset={f.reset} />
        </form>
      </Card>

      <Async state={list.state} isEmpty={(items) => items.length === 0}>
        {(items) => (
          <>
            <ResultCount total={list.total} />
            <TableWrap>
              <thead><tr><Th>{t("Title")}</Th><Th>{t("Articles")}</Th><Th>{t("Sources")}</Th><Th>{t("Publishers")}</Th><Th>{t("First published")}</Th><Th>{t("Last published")}</Th><Th>{t("Coverage gap")}</Th></tr></thead>
              <tbody>
                {items.map((s) => (
                  <tr key={s.story_key} className="hover:bg-ivory">
                    <Td className="min-w-[240px]"><Link dir="auto" className="rtl-auto font-medium text-navy hover:text-gold-600" href={`/stories/${encodeURIComponent(s.story_id ?? String(s.story_key))}`}>{s.story_title ?? "—"}</Link></Td>
                    <Td>{fmtNum(s.article_count, lang)}</Td>
                    <Td>{s.is_multi_source ? <Badge tone="gold">{fmtNum(s.source_count, lang)}</Badge> : fmtNum(s.source_count, lang)}</Td>
                    <Td className="min-w-[160px] text-xs rtl-auto">{s.publisher_names ?? "—"}</Td>
                    <Td className="whitespace-nowrap">{multi(s) ? fmtDate(s.first_published_at, lang) : NO_VALUE}</Td>
                    <Td className="whitespace-nowrap">{multi(s) ? fmtDate(s.last_published_at, lang) : NO_VALUE}</Td>
                    <Td>{multi(s) ? fmtMinutes(s.coverage_gap_minutes, lang) : NO_VALUE}</Td>
                  </tr>
                ))}
              </tbody>
            </TableWrap>
            <InfiniteListFooter list={list} />
          </>
        )}
      </Async>
    </>
  );
}