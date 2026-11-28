"use client";
import { useState } from "react";

/** Draft/applied filter state: edits stay in `draft` until `apply` commits them. */
export function useFilters<T extends Record<string, string | boolean>>(initial: T) {
  const [draft, setDraft] = useState<T>(initial);
  const [applied, setApplied] = useState<T>(initial);
  const set = <K extends keyof T>(k: K, v: T[K]) => setDraft((d) => ({ ...d, [k]: v }));
  const apply = () => setApplied(draft);
  const reset = () => { setDraft(initial); setApplied(initial); };
  return { draft, applied, set, apply, reset };
}