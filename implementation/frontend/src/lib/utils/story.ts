import type { Story } from "@/types/api";

/**
 * First/last publication and coverage gap only describe cross-source coverage,
 * so they are shown only for stories published by more than one source.
 * Presentation rule only — the API data is untouched.
 */
export const hasMultiSourceCoverage = (story: Pick<Story, "source_count">): boolean => (story.source_count ?? 0) > 1;

export const NO_VALUE = "—";
