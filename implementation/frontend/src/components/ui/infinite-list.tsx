"use client";

import { useEffect, useRef } from "react";
import { Loader2 } from "lucide-react";
import { useApp } from "@/components/providers";
import { btnSecondary } from "@/components/ui/primitives";
import type { InfiniteList } from "@/hooks/use-infinite-list";

function Sentinel({
  enabled,
  onVisible,
}: {
  enabled: boolean;
  onVisible: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;

    if (!enabled || !el) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          onVisible();
        }
      },
      { rootMargin: "800px" }
    );

    observer.observe(el);

    return () => observer.disconnect();
  }, [enabled, onVisible]);

  return <div ref={ref} aria-hidden className="h-px" />;
}

export function ResultCount({ total }: { total: number }) {
  const { t, lang } = useApp();

  return (
    <p className="mb-3 text-sm text-muted">
      {total.toLocaleString(lang === "ar" ? "ar-EG" : "en-GB")}{" "}
      {t("results")}
    </p>
  );
}

export function InfiniteListFooter<T>({
  list,
}: {
  list: InfiniteList<T>;
}) {
  const { t } = useApp();

  return (
    <div className="py-6 text-center text-sm text-muted">
      <Sentinel
        enabled={list.hasMore && !list.moreError}
        onVisible={list.loadMore}
      />

      {list.loadingMore && (
        <span className="inline-flex items-center gap-2">
          <Loader2 className="animate-spin" size={16} />
          {t("Loading more…")}
        </span>
      )}

      {list.moreError && (
        <div className="flex flex-col items-center gap-2">
          <span className="max-w-xl break-words text-red-700">
            {list.moreError}
          </span>

          <button
            onClick={list.retryMore}
            className={btnSecondary}
          >
            {t("Retry")}
          </button>
        </div>
      )}

      {!list.hasMore &&
        !list.loadingMore &&
        !list.moreError && (
          <span>{t("All results loaded")}</span>
        )}
    </div>
  );
}