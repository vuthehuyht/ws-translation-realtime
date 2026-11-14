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
  userSub: string;
}

export interface ConfirmOtpPayload {
  email: string;
  otpCode: string;
}

export interface ConfirmOtpResponse {
  status: string;
  userSub: string;
  walletBalance: string;
  currency: string;
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
