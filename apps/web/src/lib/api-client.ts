export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown> | unknown[];
  };
  detail?: string | unknown[];
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown> | unknown[];

  constructor(
    status: number,
    code: string,
    message: string,
    details?: Record<string, unknown> | unknown[]
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

/**
 * Send a JSON request to the FastAPI backend and parse RFC 7807 error responses.
 */
export async function apiRequest<TResponse>(
  path: string,
  options: RequestInit = {}
): Promise<TResponse> {
  const baseUrl = getApiBaseUrl().replace(/\/+$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${baseUrl}${normalizedPath}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      // Non-JSON error body; fall back to HTTP status text
    }

    const code = payload?.error?.code ?? `HTTP_${response.status}`;
    const message =
      payload?.error?.message ??
      (typeof payload?.detail === "string" ? payload.detail : null) ??
      (response.statusText || `Yêu cầu thất bại (${response.status})`);

    throw new ApiError(response.status, code, message, payload?.error?.details);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}
