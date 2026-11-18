import {
  ApiError,
  getApiBaseUrl,
  type ApiErrorPayload,
} from "./api-base";
import { silentRefreshSession } from "./auth-refresh";
import { getAuthSession } from "./auth-storage";

export { ApiError, getApiBaseUrl, type ApiErrorPayload };

export interface ApiRequestOptions extends RequestInit {
  auth?: boolean;
  skipAuthRefresh?: boolean;
}

const AUTH_PUBLIC_PATHS = new Set([
  "/api/v1/auth/login",
  "/api/v1/auth/refresh",
  "/api/v1/auth/register",
  "/api/v1/auth/confirm",
  "/api/v1/auth/resend-otp",
  "/api/v1/auth/forgot-password",
  "/api/v1/auth/reset-password",
]);

function shouldAttemptRefresh(
  normalizedPath: string,
  skipAuthRefresh: boolean
): boolean {
  if (skipAuthRefresh) {
    return false;
  }
  const pathWithoutQuery = normalizedPath.split("?")[0];
  return !AUTH_PUBLIC_PATHS.has(pathWithoutQuery);
}

/**
 * Send a JSON request to the FastAPI backend and parse RFC 7807 error responses.
 */
export async function apiRequest<TResponse>(
  path: string,
  options: ApiRequestOptions = {}
): Promise<TResponse> {
  const { auth = false, skipAuthRefresh = false, ...fetchOptions } = options;
  const baseUrl = getApiBaseUrl();
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;

  const headers = new Headers(fetchOptions.headers);
  if (!headers.has("Content-Type") && fetchOptions.body) {
    headers.set("Content-Type", "application/json");
  }

  let refreshAttempted = false;
  if (auth && !headers.has("Authorization")) {
    let session = getAuthSession();
    if (!session) {
      refreshAttempted = true;
      session = await silentRefreshSession();
    }
    if (!session?.tokens.accessToken) {
      throw new ApiError(401, "UNAUTHORIZED", "Phiên đăng nhập đã hết hạn");
    }
    headers.set("Authorization", `Bearer ${session.tokens.accessToken}`);
  }

  const executeFetch = (requestHeaders: Headers) =>
    fetch(`${baseUrl}${normalizedPath}`, {
      ...fetchOptions,
      credentials: fetchOptions.credentials ?? "include",
      headers: requestHeaders,
    });

  let response = await executeFetch(headers);

  if (
    response.status === 401 &&
    !refreshAttempted &&
    shouldAttemptRefresh(normalizedPath, skipAuthRefresh)
  ) {
    const refreshed = await silentRefreshSession();
    if (refreshed?.tokens.accessToken) {
      const retryHeaders = new Headers(headers);
      retryHeaders.set("Authorization", `Bearer ${refreshed.tokens.accessToken}`);
      response = await executeFetch(retryHeaders);
    }
  }

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
