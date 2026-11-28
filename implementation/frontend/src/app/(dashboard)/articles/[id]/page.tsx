"use client";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { api } from "@/lib/api/services";
import { useApi } from "@/hooks/use-api";
import { useApp } from "@/components/providers";
import { Async, Badge, Card, PageHeader, Stat } from "@/components/ui/primitives";
import { ARTICLE_GRID, ArticleCard } from "@/components/shared/article-card";
import { fmtDate } from "@/lib/utils/format";

export default function ArticleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t, lang } = useApp();
  const art = useApi(() => api.article(id), [id]);
  const storyId = art.data?.story_id ?? "";
  const related = useApi(() => (storyId ? api.articles({ story_id: storyId, page_size: 12 }) : Promise.resolve(null)), [storyId]);

  return (
    <Async state={art}>
      {(a) => (
        <article className="mx-auto max-w-5xl">
          <PageHeader back={{ href: "/articles" }} title={a.article_title ?? "—"} />
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs">
            {a.source_name && <Badge tone="gold">{a.source_name}</Badge>}
            {a.category_name && <Badge>{a.category_name}</Badge>}
            {a.is_multi_source_story && <Badge tone="green">{t("Multi-source")}</Badge>}
          </div>
          {a.article_image_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={a.article_image_url} alt="" referrerPolicy="no-referrer" onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} className="mb-4 max-h-[420px] w-full rounded-xl object-cover" />
          )}
          {a.article_description && <p dir="auto" className="rtl-auto mb-4 text-lg leading-relaxed text-muted">{a.article_description}</p>}
          <Card className="mb-4">
            <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Stat label={t("Published")} value={fmtDate(a.publication_timestamp, lang)} />
              <Stat label={t("Updated")} value={fmtDate(a.article_updated_at, lang)} />
              <Stat label={t("Author")} value={<span className="rtl-auto">{a.author_name ?? "—"}</span>} />
              <Stat label={t("Timestamp validity")} value={a.timestamp_validity ?? "—"} />
              <Stat label={t("Syndication")} value={a.syndication_indicator ?? "—"} />
              <Stat label={t("Link")} value={a.link_availability ?? "—"} />
            </dl>
            {a.original_url && (
              <a href={a.original_url} target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex items-center gap-1 rounded-md bg-navy px-3 py-1.5 text-sm text-white hover:bg-navy-600"><ExternalLink size={14} />{t("Open original")}</a>
            )}
          </Card>
          <div dir="auto" className="rtl-auto whitespace-pre-line text-base leading-8 text-navy">
            {a.article_content || <span className="text-muted">{t("Content not available.")}</span>}
          </div>
          {a.story_id && (
            <Card title={t("Story")} className="mt-6">
              <Link dir="auto" href={`/stories/${encodeURIComponent(a.story_id)}`} className="rtl-auto text-sm font-medium text-navy hover:text-gold-600">{a.story_title ?? a.story_id}</Link>
              <div className="mt-1 text-xs text-muted">{a.story_article_count ?? 0} {t("Articles")} · {a.story_source_count ?? 0} {t("Sources")}</div>
              {related.data && (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-navy">{t("Related articles")}</h3>
                  <div className="mt-3 grid gap-4 sm:grid-cols-2">{related.data.items.filter((x) => x.article_id !== a.article_id).map((x) => <ArticleCard key={x.article_key} a={x} />)}</div>
                </div>
              )}
            </Card>
          )}
        </article>
      )}
    </Async>
  );
}
