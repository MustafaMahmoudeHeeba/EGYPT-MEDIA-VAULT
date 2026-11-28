"use client";
import Link from "next/link";
import { useApp } from "@/components/providers";
import { PyramidGlyph } from "@/components/layout/brand";
import { Badge } from "@/components/ui/primitives";
import { fmtDate } from "@/lib/utils/format";
import type { Article } from "@/types/api";

/** Shared responsive grid for article cards (more columns on wide screens). */
export const ARTICLE_GRID = "grid gap-5 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4";

export function ArticleCard({ a }: { a: Article }) {
  const { lang } = useApp();
  return (
    <Link href={`/articles/${encodeURIComponent(a.article_id)}`} className="group flex flex-col overflow-hidden rounded-xl border border-line bg-white shadow-sm transition hover:border-gold hover:shadow-md">
      <div className="relative aspect-[16/9] overflow-hidden bg-sand">
        <div className="absolute inset-0 grid place-items-center text-gold/50"><PyramidGlyph className="h-12 w-12" /></div>
        {a.article_image_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={a.article_image_url} alt="" referrerPolicy="no-referrer" loading="lazy"
            onError={(e) => { e.currentTarget.style.display = "none"; }}
            className="absolute inset-0 h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
        )}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted">
          {a.source_name && <Badge tone="gold">{a.source_name}</Badge>}
          {a.category_name && <span dir="auto" className="rtl-auto">{a.category_name}</span>}
        </div>
        <h3 dir="auto" className="rtl-auto line-clamp-3 text-base font-bold leading-snug text-navy group-hover:text-gold-600">{a.article_title ?? "—"}</h3>
        {a.article_description && <p dir="auto" className="rtl-auto mt-2 line-clamp-3 text-sm text-muted">{a.article_description}</p>}
        <div className="mt-auto pt-3 text-xs text-muted">{fmtDate(a.publication_timestamp, lang)}</div>
      </div>
    </Link>
  );
}
