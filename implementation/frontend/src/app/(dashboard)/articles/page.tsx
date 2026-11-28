"use client";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useFilters } from "@/hooks/use-filters";
import { useInfiniteList } from "@/hooks/use-infinite-list";
import { useApp } from "@/components/providers";
import { Async, Card, Field, FilterActions, PageHeader, inputCls } from "@/components/ui/primitives";
import { InfiniteListFooter, ResultCount } from "@/components/ui/infinite-list";
import { ARTICLE_GRID, ArticleCard } from "@/components/shared/article-card";

const INIT = { search: "", source: "", category: "", from: "", to: "", order: "desc" };

export default function ArticlesPage() {
  const { t } = useApp();
  const f = useFilters(INIT);
  const a = f.applied;
  const sources = useApi(() => api.sources(), []);
  const cats = useApi(() => api.categories(), []);
  const list = useInfiniteList(
    (page, pageSize) => api.articles({
      page, page_size: pageSize, search: a.search, source_id: a.source, category_name: a.category,
      date_from: a.from, date_to: a.to, sort_order: a.order,
    }),
    [a],
  );

  return (
    <>
      <PageHeader title={t("Articles")} />
      <Card className="mb-4">
        <form onSubmit={(e) => { e.preventDefault(); f.apply(); }} className="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3">
          <Field label={t("Search")}><input dir="auto" maxLength={300} className={inputCls} value={f.draft.search} onChange={(e) => f.set("search", e.target.value)} /></Field>
          <Field label={t("Source")}>
            <select className={inputCls} value={f.draft.source} onChange={(e) => f.set("source", e.target.value)}>
              <option value="">{t("All")}</option>
              {(sources.data ?? []).map((s) => <option key={s.source_id} value={s.source_id}>{s.source_name}</option>)}
            </select>
          </Field>
          <Field label={t("Category")}>
            <select className={inputCls} value={f.draft.category} onChange={(e) => f.set("category", e.target.value)}>
              <option value="">{t("All")}</option>
              {(cats.data ?? []).map((c) => <option key={c.category_key} value={c.category_name}>{c.category_name}</option>)}
            </select>
          </Field>
          <Field label={t("From")}><input type="date" className={inputCls} value={f.draft.from} onChange={(e) => f.set("from", e.target.value)} /></Field>
          <Field label={t("To")}><input type="date" className={inputCls} value={f.draft.to} onChange={(e) => f.set("to", e.target.value)} /></Field>
          <Field label={t("Order")}>
            <select className={inputCls} value={f.draft.order} onChange={(e) => f.set("order", e.target.value)}>
              <option value="desc">{t("Newest first")}</option><option value="asc">{t("Oldest first")}</option>
            </select>
          </Field>
          <FilterActions onReset={f.reset} />
        </form>
      </Card>
      <Async state={list.state} isEmpty={(items) => items.length === 0}>
        {(items) => (
          <>
            <ResultCount total={list.total} />
            <div className={ARTICLE_GRID}>{items.map((x) => <ArticleCard key={x.article_key} a={x} />)}</div>
            <InfiniteListFooter list={list} />
          </>
        )}
      </Async>
    </>
  );
}