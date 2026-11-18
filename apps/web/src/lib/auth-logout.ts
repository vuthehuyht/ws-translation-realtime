import { ApiError } from "./api-base";
import { logoutHost } from "./auth-api";
import { cancelPendingRefreshes, silentRefreshSessionDetailed } from "./auth-refresh";
import { peekAuthSession } from "./auth-storage";

export class LogoutUnavailableError extends Error {
  constructor(message = "Không thể xác nhận thu hồi phiên đăng nhập") {
    super(message);
    this.name = "LogoutUnavailableError";
  }
}

/**
 * Revoke the server-side session (refresh cookie + tokens) before the caller clears local state.
 *
 * Resolves once the session is known to be dead server-side. Throws when it may still be alive
 * (outage, network error), so the caller keeps the user signed in and can retry instead of
 * leaving a live HttpOnly cookie that silent refresh would use to sign them back in.
 */
export async function signOutSession(options: {
  global?: boolean;
} = {}): Promise<void> {
  // A refresh already in flight (e.g. the layout's proactive one) must not save a fresh token
  // after the user asked to sign out.
  cancelPendingRefreshes();

  let accessToken = peekAuthSession()?.tokens.accessToken;

  if (!accessToken) {
    // No stored token (e.g. storage cleared): the cookie may still be live, so get a token.
    const outcome = await silentRefreshSessionDetailed();
    if (outcome.status === "rejected") {
      return;
    }
    if (outcome.status === "unavailable") {
      throw new LogoutUnavailableError();
    }
    accessToken = outcome.session.tokens.accessToken;
  }

  try {
    await logoutHost({ accessToken, global: options.global });
    return;
  } catch (error) {
    if (!(error instanceof ApiError && error.status === 401)) {
      throw error;
    }
  }

  // 401: the token was revoked, invalid, or (for global sign-out) expired. Only a definitive
  // refresh rejection proves the cookie is dead too; otherwise get a live token and retry once.
  const outcome = await silentRefreshSessionDetailed();
  if (outcome.status === "rejected") {
    return;
  }
  if (outcome.status === "unavailable") {
    throw new LogoutUnavailableError();
  }
  await logoutHost({
    accessToken: outcome.session.tokens.accessToken,
    global: options.global,
  });
}
