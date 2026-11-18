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
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/+$/, "");
  }
  // In production behind ALB path routing (/api/* -> backend), use same-origin relative URLs
  // instead of hardcoding localhost:8000 at Docker build time.
  if (process.env.NODE_ENV === "production") {
    return "";
  }
  return "http://localhost:8000";
}
