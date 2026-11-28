// Types mirror the FastAPI OpenAPI schemas (nullable where the API marks fields nullable).
// Percent / minute metrics arrive as strings (or null); use utils `num()` to parse.
export type N<T> = T | null;
export interface Paginated<T> { items: T[]; total: number; page: number; page_size: number; total_pages: number }
export interface Story {
  story_id: N<string>; story_key: number; story_title: N<string>; article_count: N<number>; source_count: N<number>;
  is_multi_source: N<boolean>; publisher_ids: N<string>; publisher_names: N<string>; first_published_at: N<string>;
  last_published_at: N<string>; coverage_gap_minutes: N<string>; first_source_id: N<string>; first_source_name: N<string>;
  articles_missing_publication_time: N<number>; coverage_rank: N<number>;
}
export interface StoryTimelineItem {
  story_id: N<string>; story_key: number; story_title: N<string>; source_id: N<string>; source_name: N<string>;
  story_source_count: N<number>; article_count: N<number>; articles_missing_publication_time: N<number>;
  first_published_at: N<string>; last_published_at: N<string>; story_first_published_at: N<string>;
  minutes_after_story_first_publication: N<string>; publication_order: N<number>; is_first_source: N<boolean>;
}
export interface Article {
  article_key: number; article_id: string; article_title: N<string>; original_url: N<string>; story_id: N<string>;
  story_title: N<string>; story_membership_status: N<string>; story_article_count: N<number>; story_source_count: N<number>;
  is_multi_source_story: N<boolean>; source_id: N<string>; source_name: N<string>; category_key: N<number>;
  category_name: N<string>; author_name: N<string>; publication_timestamp: N<string>; has_publication_time: N<boolean>;
  ingestion_timestamp: string; article_updated_at: N<string>; has_content: N<boolean>; has_description: N<boolean>;
  has_image: N<boolean>; article_description: N<string>; article_image_url: N<string>; link_availability: N<string>;
}
export interface ArticleDetail extends Article {
  author_key: N<number>; timestamp_validity: N<string>; syndication_indicator: N<string>; article_content: N<string>;
}
export interface Source {
  source_id: string; source_key: number; source_name: string; is_enabled: N<boolean>; is_current_version: N<boolean>;
  version_effective_from: N<string>; version_count: N<number>; total_articles: N<number>; share_of_total_articles_pct: N<string>;
  activity_rank: N<number>; articles_with_publication_time: N<number>; distinct_categories: N<number>; stories_covered: N<number>;
  stories_shared_with_other_sources: N<number>; stories_exclusive: N<number>; first_published_at: N<string>;
  last_published_at: N<string>; last_ingested_at: N<string>; collection_runs: N<number>; successful_collections: N<number>;
  failed_collections: N<number>; success_rate_pct: N<string>; total_attempts: N<number>; avg_attempts_per_collection: N<string>;
  retried_collections: N<number>; total_articles_collected: N<number>; avg_articles_collected_per_run: N<string>;
  total_articles_rejected: N<number>; total_duplicate_records: N<number>; last_successful_run_date: N<string>;
  last_failed_run_date: N<string>; failures_by_step: N<string>;
}
export interface CategorySourceBreakdown {
  source_id: string; source_name: string; article_count: N<number>; share_of_source_pct: N<string>; source_share_of_category_pct: N<string>;
}
export interface Category {
  category_key: number; category_name: string; total_articles: number; source_count: number; activity_rank: N<number>;
  sources: CategorySourceBreakdown[];
}
export interface Overview {
  total_stories: number; multi_source_stories: number; single_source_stories: number; multi_source_story_pct: N<string>;
  avg_publishers_per_story: N<string>; total_articles_in_stories: number; total_sources: number; total_articles: number;
  successful_pipeline_runs: number; total_pipeline_runs: number;
}
export interface SourceDaily {
  publication_date: string; source_id: string; source_name: string; article_count: number; story_count: number;
  category_count: number; total_articles_on_date: number; share_of_date_pct: N<string>; activity_rank_on_date: N<number>;
  cumulative_articles: number;
}
export interface TimeActivity {
  publication_date: string; publication_hour: number; source_id: string; publication_day_name: N<string>;
  publication_iso_day_of_week: N<number>; publication_day_period: N<string>; publication_is_weekend: N<boolean | number>;
  article_count: number;
}
