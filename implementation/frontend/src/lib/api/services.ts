import { apiGet, type Params } from "./client";
import type * as T from "@/types/api";

const enc = encodeURIComponent;
export const api = {
  overview: () => apiGet<T.Overview>("/analytics/overview"),
  stories: (p: Params) => apiGet<T.Paginated<T.Story>>("/stories", p),
  story: (id: string) => apiGet<T.Story>(`/stories/${enc(id)}`),
  storyTimeline: (id: string) => apiGet<T.StoryTimelineItem[]>(`/stories/${enc(id)}/timeline`),
  articles: (p: Params) => apiGet<T.Paginated<T.Article>>("/articles", p),
  article: (id: string) => apiGet<T.ArticleDetail>(`/articles/${enc(id)}`),
  sources: () => apiGet<T.Source[]>("/sources"),
  categories: () => apiGet<T.Category[]>("/categories"),
  category: (key: number | string) => apiGet<T.Category>(`/categories/${key}`),
  sourceDaily: (p: Params) => apiGet<T.SourceDaily[]>("/analytics/sources/daily", p),
  timeActivity: (p: Params) => apiGet<T.TimeActivity[]>("/analytics/time-activity", p),
};
