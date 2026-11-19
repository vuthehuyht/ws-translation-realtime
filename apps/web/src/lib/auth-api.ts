import { apiRequest } from "./api-client";

export interface RegisterHostPayload {
  fullName: string;
  email: string;
  password: string;
  role?: "HOST" | "LISTENER";
}

export interface RegisterHostResponse {
  status: string;
  email: string;
  userSub?: string | null;
}

export interface ConfirmOtpPayload {
  email: string;
  otpCode: string;
}

export interface ConfirmOtpResponse {
  status: string;
}

export interface ResendOtpPayload {
  email: string;
}

export interface ResendOtpResponse {
  status: string;
  email: string;
  retryAfter: number;
}

export function registerHost(
  payload: RegisterHostPayload
): Promise<RegisterHostResponse> {
  return apiRequest<RegisterHostResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      role: payload.role ?? "HOST",
    }),
  });
}

export function confirmRegistration(
  payload: ConfirmOtpPayload
): Promise<ConfirmOtpResponse> {
  return apiRequest<ConfirmOtpResponse>("/api/v1/auth/confirm", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resendOtp(
  payload: ResendOtpPayload
): Promise<ResendOtpResponse> {
  return apiRequest<ResendOtpResponse>("/api/v1/auth/resend-otp", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ForgotPasswordResponse {
  status: string;
  email: string;
  message: string;
}

export function forgotPassword(
  payload: ForgotPasswordPayload
): Promise<ForgotPasswordResponse> {
  return apiRequest<ForgotPasswordResponse>("/api/v1/auth/forgot-password", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRefresh: true,
  });
}

export interface ResetPasswordPayload {
  email: string;
  otpCode: string;
  newPassword: string;
}

export interface ResetPasswordResponse {
  status: string;
  message: string;
}

export function resetPassword(
  payload: ResetPasswordPayload
): Promise<ResetPasswordResponse> {
  return apiRequest<ResetPasswordResponse>("/api/v1/auth/reset-password", {
    method: "POST",
    body: JSON.stringify(payload),
    skipAuthRefresh: true,
  });
}

export interface LoginHostPayload {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginTokens {
  accessToken: string;
  idToken: string;
  refreshToken?: string | null;
  expiresIn: number;
  tokenType: string;
}

export interface UserProfile {
  id: string;
  email: string;
  role: string;
  status: string;
  fullName: string | null;
  defaultSourceLang: string | null;
  defaultTargetLangs: string[];
  timezone: string;
}

export interface LoginHostResponse {
  tokens: LoginTokens;
  user: UserProfile;
}

export interface RefreshSessionResponse {
  tokens: LoginTokens;
  user: UserProfile;
}

export function loginHost(
  payload: LoginHostPayload
): Promise<LoginHostResponse> {
  return apiRequest<LoginHostResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface LogoutHostOptions {
  /** Access token to authorize the request; may be expired (the backend checks signature only). */
  accessToken: string;
  /** Sign out every device instead of only the current one. */
  global?: boolean;
}

export function logoutHost(options: LogoutHostOptions): Promise<void> {
  return apiRequest<void>("/api/v1/auth/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${options.accessToken}` },
    body: JSON.stringify({ global: options.global ?? false }),
    // Refreshing here would hide whether the server-side session was really revoked.
    skipAuthRefresh: true,
  });
}

export function refreshHostSession(): Promise<RefreshSessionResponse> {
  return apiRequest<RefreshSessionResponse>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({}),
    skipAuthRefresh: true,
  });
}
