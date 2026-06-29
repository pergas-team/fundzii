export type ApiErrorPayload = {
  errors?: Record<string, string[] | string> | string[] | string;
  detail?: string;
};

export class ApiError extends Error {
  status: number;
  payload?: ApiErrorPayload;

  constructor(status: number, payload?: ApiErrorPayload) {
    super(payload?.detail || "API request failed");
    this.status = status;
    this.payload = payload;
  }
}

export const API_PROXY_BASE = "/backend";

type ApiOptions = RequestInit & {
  formData?: boolean;
};

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const body = options.body;

  if (!options.formData && body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_PROXY_BASE}${path}`, {
    ...options,
    headers,
    credentials: "include",
    cache: options.cache ?? "no-store",
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : undefined;

  if (!response.ok) {
    throw new ApiError(response.status, payload);
  }

  return payload as T;
}

/** Extract a human-readable Persian message from an ApiError payload. */
export function apiErrorMessage(error: unknown, fallback = "خطایی رخ داد."): string {
  if (!(error instanceof ApiError)) return fallback;
  const { errors, detail } = error.payload || {};
  if (detail) return detail;
  if (typeof errors === "string") return errors;
  if (Array.isArray(errors)) return errors.join("، ");
  if (errors && typeof errors === "object") {
    const messages = Object.values(errors).flatMap((value) => (Array.isArray(value) ? value : [value]));
    if (messages.length) return messages.join("، ");
  }
  return fallback;
}

export function toQuery(params: Record<string, string | number | boolean | null | undefined>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}
