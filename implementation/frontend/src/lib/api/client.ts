import { env } from "@/config/env";

export type Params = Record<string, string | number | boolean | null | undefined>;

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

/** Centralised GET helper. Drops empty params, surfaces FastAPI validation errors. */
export async function apiGet<T>(path: string, params?: Params): Promise<T> {
  const base = env.apiBaseUrl.replace(/\/$/, "");
  const url = new URL(base + path, window.location.origin);
  Object.entries(params ?? {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") url.searchParams.set(k, String(v));
  });
  let res: Response;
  try { res = await fetch(url.toString(), { headers: { Accept: "application/json" } }); }
  catch { throw new ApiError("Cannot reach the API. Check that the backend is running and the API settings in .env.", 0); }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const j = await res.json();
      if (typeof j?.detail === "string") detail = j.detail;
      else if (Array.isArray(j?.detail)) detail = j.detail.map((d: { msg: string }) => d.msg).join("; ");
    } catch { /* ignore */ }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}
