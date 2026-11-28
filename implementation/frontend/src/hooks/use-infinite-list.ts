"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ApiState } from "@/hooks/use-api";
import type { Paginated } from "@/types/api";

/** Largest page_size the API accepts (documented maximum: 100). */
export const MAX_PAGE_SIZE = 100;

export type PageFetcher<T> = (
  page: number,
  pageSize: number
) => Promise<Paginated<T>>;

export interface InfiniteList<T> {
  state: ApiState<T[]>;
  total: number;
  hasMore: boolean;
  loadingMore: boolean;
  moreError: string | null;
  loadMore: () => void;
  retryMore: () => void;
}

/**
 * Continuous list over a paginated endpoint.
 * Loads the first page at the maximum page size and fetches the next page
 * only when the user scrolls near the end.
 */
export function useInfiniteList<T>(
  fetchPage: PageFetcher<T>,
  deps: unknown[]
): InfiniteList<T> {
  const fetchRef = useRef(fetchPage);

  useEffect(() => {
    fetchRef.current = fetchPage;
  });

  const generation = useRef(0);
  const inFlight = useRef(false);

  const [items, setItems] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [moreError, setMoreError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const gen = ++generation.current;

    inFlight.current = true;
    setLoading(true);
    setLoadingMore(false);
    setError(null);
    setMoreError(null);
    setItems([]);
    setTotal(0);
    setPage(0);
    setTotalPages(0);

    fetchRef.current(1, MAX_PAGE_SIZE)
      .then((r) => {
        if (gen !== generation.current) return;

        setItems(r.items);
        setTotal(r.total);
        setTotalPages(r.total_pages);
        setPage(1);
        setLoading(false);
        inFlight.current = false;
      })
      .catch((e: Error) => {
        if (gen !== generation.current) return;

        setError(e.message);
        setLoading(false);
        inFlight.current = false;
      });

    return () => {
      generation.current += 1;
    };

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const hasMore = page > 0 && page < totalPages;

  const loadMore = useCallback(() => {
    if (inFlight.current || !hasMore || moreError) return;

    const gen = generation.current;
    const next = page + 1;

    inFlight.current = true;
    setLoadingMore(true);

    fetchRef.current(next, MAX_PAGE_SIZE)
      .then((r) => {
        if (gen !== generation.current) return;

        setItems((prev) => [...prev, ...r.items]);
        setTotalPages(r.total_pages);
        setPage(next);
        setLoadingMore(false);
        inFlight.current = false;
      })
      .catch((e: Error) => {
        if (gen !== generation.current) return;

        setMoreError(e.message);
        setLoadingMore(false);
        inFlight.current = false;
      });
  }, [hasMore, moreError, page]);

  const reload = useCallback(() => {
    setTick((n) => n + 1);
  }, []);

  const retryMore = useCallback(() => {
    setMoreError(null);
  }, []);

  return {
    state: {
      data: page > 0 ? items : null,
      error,
      loading,
      reload,
    },
    total,
    hasMore,
    loadingMore,
    moreError,
    loadMore,
    retryMore,
  };
}