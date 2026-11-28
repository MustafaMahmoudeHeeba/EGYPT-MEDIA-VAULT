# EGYPT-MEDIA-VAULT — Frontend

Next.js 14 (App Router) · TypeScript · Tailwind CSS · Recharts · lucide-react.
Consumes the existing FastAPI service (`/api/v1`). No mock data: every number comes from the API.

## Run

```bash
npm install
cp .env.example .env.local      # adjust API_PROXY_TARGET if the backend is not on :8000
npm run dev                     # http://localhost:3000
```

Checks / production:

```bash
npm run typecheck && npm run lint && npm run build && npm start
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | `/api/v1` | Base path the browser calls |
| `API_PROXY_TARGET` | `http://localhost:8000` | Backend that Next proxies `/api/v1/*`, `/health`, `/ready` to (avoids CORS) |

## Structure

```
src/app/(dashboard)/   routes: overview, stories[/id], articles[/id], sources[/id], categories[/key], time-activity
src/components/        ui/ (primitives), layout/ (shell, sidebar, mobile-nav, header, brand), charts/, shared/ (article card), providers.tsx (language)
src/lib/api/           client.ts (single fetch wrapper) + services.ts (one function per endpoint)
src/lib/utils/         format.ts (numbers/dates, nullable-safe), i18n.ts (Arabic dictionary)
src/config/            theme.ts (brand palette — single source for Tailwind + charts), navigation.ts, env.ts
src/hooks/             use-api.ts, use-filters.ts
src/types/api.ts       types mirroring the OpenAPI schemas
```

## API notes & limitations

- Sorting: the OpenAPI doc documents only the default `sort_by` values (`last_published_at` for stories, `publication_timestamp` for articles), so the UI sends no `sort_by` and only exposes `sort_order` (`asc`/`desc`).
- `GET /sources/{source_id}` has no documented response schema, so the Source Details page reads the documented `GET /sources` list and selects the matching `source_id`.
- Story and article ids are URL-encoded; the story page falls back to `story_key` if `story_id` is null.
- Time-activity charts and the heatmap are aggregated client-side from `/analytics/time-activity`.

## Design

Light theme only. Change brand colours in `src/config/theme.ts`; Tailwind and the charts both read from it.

## Verification status

Generated in a sandbox with no network access: `npm install` could not run, so type-check (with dependencies), ESLint, `next build` and in-browser testing have NOT been executed. Only a dependency-free TypeScript syntax and unused-code scan was run (clean). Run the commands above and fix anything they report.
