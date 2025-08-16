/**
 * Minimal PetPlantr SDK client for mesh generation.
 * - Idempotency-Key support
 * - 202 laddering with Retry-After clamp and Link header preference
 * - RFC7807 Problem+JSON error propagation
 */

export type Problem = {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: Array<Record<string, unknown>>;
};

export type CreateAccepted = {
  status_url: string;
  poll_after_s?: number;
  laddered?: boolean;
};

export type CreateOptions = {
  idempotencyKey?: string;
  signal?: AbortSignal;
  headers?: Record<string, string>;
};

// Allowed charset per server contract: A–Z a–z 0–9 . _ : @ - /
const IDEMPOTENCY_KEY_PATTERN = /^[A-Za-z0-9._:@\-\/]+$/;
export function generateIdempotencyKey(length = 44): string {
  const CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:@-/';
  const bytes = new Uint8Array(length);
  if (typeof crypto !== 'undefined' && 'getRandomValues' in crypto) {
    crypto.getRandomValues(bytes);
  } else {
    for (let i = 0; i < bytes.length; i++) bytes[i] = Math.floor(Math.random() * 256);
  }
  let out = '';
  for (let i = 0; i < bytes.length; i++) out += CHARS[bytes[i] % CHARS.length];
  out = out.slice(0, 200);
  if (!IDEMPOTENCY_KEY_PATTERN.test(out)) out = out.replace(/[^A-Za-z0-9._:@\-\/]/g, '');
  if (!out) out = 'k';
  return out;
}

function clampRetryAfter(v: unknown, fallback = 3): number {
  const n = typeof v === "string" ? parseInt(v, 10) : (v as number);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(120, Math.max(1, Math.floor(n)));
}

function parseLinkForMonitor(headers: Headers): string | undefined {
  const raw = headers.get("Link");
  if (!raw) return undefined;
  // Very small RFC8288 parser: split by comma, then look for rel
  // Prefer rel="monitor" then rel="status"
  const parts = raw.split(",");
  let monitor: string | undefined;
  let status: string | undefined;
  for (const p of parts) {
    const m = p.match(/<([^>]+)>\s*;\s*rel=\"([^\"]+)\"/i);
    if (!m) continue;
    const url = m[1];
    const rel = m[2];
    if (rel === "monitor" && !monitor) monitor = url;
    if (rel === "status" && !status) status = url;
  }
  return monitor ?? status ?? undefined;
}

export async function createMesh(
  endpoint: string,
  body: unknown,
  opts: CreateOptions = {}
): Promise<
  | { kind: "accepted"; statusUrl: string; retryAfter: number; laddered?: boolean; response: Response }
  | { kind: "problem"; problem: Problem; response: Response }
> {
  const headers = new Headers({ "content-type": "application/json", ...(opts.headers || {}) });
  if (opts.idempotencyKey) headers.set("Idempotency-Key", opts.idempotencyKey);

  const res = await fetch(endpoint, {
    method: "POST",
    headers,
    body: JSON.stringify(body ?? {}),
    signal: opts.signal,
  });

  // Problem+JSON on 4xx/5xx
  if (res.status >= 400 && res.headers.get("content-type")?.includes("application/problem+json")) {
    let problem: Problem;
    try {
      problem = (await res.json()) as Problem;
    } catch {
      problem = { title: res.statusText || "Error", status: res.status } as Problem;
    }
    return { kind: "problem", problem, response: res };
  }

  if (res.status === 202) {
    // Prefer Link rel="monitor"|"status" then Location, then legacy body.status_url
    const linkUrl = parseLinkForMonitor(res.headers);
    const loc = res.headers.get("Location") || undefined;
    let statusUrl = linkUrl ?? loc;
    let laddered: boolean | undefined;
    let retryAfter = clampRetryAfter(res.headers.get("Retry-After"), 3);

    try {
      const accepted = (await res.json()) as CreateAccepted;
      // Backfill from body if headers missing
      if (!statusUrl && accepted?.status_url) statusUrl = accepted.status_url;
      if (typeof accepted?.poll_after_s === "number") retryAfter = clampRetryAfter(accepted.poll_after_s, retryAfter);
      if (typeof accepted?.laddered === "boolean") laddered = accepted.laddered;
    } catch {
      // body may be empty on 202; that's ok
    }

    // Prefer header for laddered flag if present
    const ladderHdr = res.headers.get("X-Queue-Ladder");
    if (ladderHdr && typeof laddered === 'undefined') laddered = ladderHdr.toLowerCase() === 'true';

    if (!statusUrl) {
      // Contract guarantees a status URL; if missing treat as problem
      return {
        kind: "problem",
        problem: { title: "Missing status URL", status: 502, detail: "Upstream did not provide status URL" },
        response: res,
      };
    }

    return { kind: "accepted", statusUrl, retryAfter, laddered, response: res };
  }

  // Pass through other success responses as non-problem (not used today)
  return {
    kind: "problem",
    problem: { title: "Unexpected response", status: res.status, detail: await safeText(res) },
    response: res,
  };
}

async function safeText(res: Response): Promise<string | undefined> {
  try {
    return await res.text();
  } catch {
    return undefined;
  }
}

export async function pollStatus<T = unknown>(
  statusUrl: string,
  opts: { signal?: AbortSignal; headers?: Record<string, string> } = {}
): Promise<{ response: Response; data: T | Problem; isProblem: boolean }>
{
  const res = await fetch(statusUrl, {
    method: "GET",
    headers: opts.headers || {},
    signal: opts.signal,
  });
  const isProblem = res.headers.get("content-type")?.includes("application/problem+json") ?? false;
  let data: any = undefined;
  try {
    data = await res.json();
  } catch {
    // ignore
  }
  return { response: res, data: data as T | Problem, isProblem };
}

export async function pollUntil<T = unknown>(
  statusUrl: string,
  opts: { intervalMs?: number; timeoutMs?: number; signal?: AbortSignal; headers?: Record<string, string> } = {}
): Promise<{ final: T | Problem; response: Response }>
{
  const start = Date.now();
  const interval = Math.max(250, Math.min(10_000, Math.floor(opts.intervalMs ?? 1000)));
  // eslint-disable-next-line no-constant-condition
  while (true) {
    if (opts.timeoutMs && Date.now() - start > opts.timeoutMs) {
      throw new Error("Polling timed out");
    }
    if (opts.signal?.aborted) throw new DOMException("Aborted", "AbortError");

    const { response, data, isProblem } = await pollStatus<T>(statusUrl, opts);
    if (isProblem || response.status < 200 || response.status >= 300) {
      return { final: data, response };
    }
    // Heuristic: consider 200/201/204 final; 202 means keep polling
    if (response.status !== 202) return { final: data, response };
    await delay(interval, opts.signal);
  }
}

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const id = setTimeout(() => {
      cleanup();
      resolve();
    }, ms);
    const onAbort = () => {
      cleanup();
      reject(new DOMException("Aborted", "AbortError"));
    };
    const cleanup = () => {
      clearTimeout(id);
      if (signal) signal.removeEventListener("abort", onAbort);
    };
    if (signal) signal.addEventListener("abort", onAbort);
  });
}

