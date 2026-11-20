import { ApiError, apiRequest, getApiBaseUrl } from "./api-client";

export interface WalletSummary {
  balance: string;
  autoDegradeTts: boolean;
  autoTopupEnabled: boolean;
}

export interface UserPreferencesSettings {
  vadSensitivity?: "low" | "medium" | "high";
  subtitleMode?: "bilingual" | "target_only";
  uiLanguage?: "vi" | "en";
}

export interface UserMe {
  id: string;
  email: string;
  role: string;
  status: string;
  fullName: string;
  phoneNumber: string | null;
  bio: string | null;
  avatarUrl: string | null;
  timezone: string;
  defaultSourceLang: string;
  defaultTargetLangs: string[];
  companyName: string | null;
  taxCode: string | null;
  companyAddress: string | null;
  preferences: UserPreferencesSettings;
  wallet: WalletSummary | null;
}

export interface UpdateProfilePayload {
  fullName?: string;
  phoneNumber?: string | null;
  timezone?: string;
  bio?: string | null;
}

export interface UpdatePreferencesPayload {
  defaultSourceLang?: string;
  defaultTargetLangs?: string[];
  preferences?: UserPreferencesSettings;
}

export interface UpdateBillingInfoPayload {
  companyName: string | null;
  taxCode: string | null;
  companyAddress: string | null;
}

export interface AvatarUploadUrlPayload {
  fileName: string;
  fileType: "image/jpeg" | "image/png" | "image/webp";
  fileSizeBytes: number;
}

export interface AvatarUploadUrlResponse {
  uploadUrl: string;
  s3Key: string;
  fields: Record<string, string>;
  expiresIn: number;
  maxSizeBytes: number;
}

export interface AvatarConfirmResponse {
  avatarUrl: string;
  s3Key: string;
}

export interface ChangePasswordPayload {
  oldPassword: string;
  newPassword: string;
}

export interface ChangePasswordResponse {
  status: string;
  message: string;
}

export interface DeleteAccountPayload {
  confirmation: "DELETE";
}

export const SUPPORTED_LANGUAGE_OPTIONS = [
  { code: "vi-VN", label: "Tiếng Việt (vi-VN)" },
  { code: "en-US", label: "English - US (en-US)" },
  { code: "en-GB", label: "English - UK (en-GB)" },
  { code: "ja-JP", label: "日本語 (ja-JP)" },
  { code: "ko-KR", label: "한국어 (ko-KR)" },
  { code: "zh-CN", label: "中文 - Giản thể (zh-CN)" },
  { code: "zh-TW", label: "中文 - Phồn thể (zh-TW)" },
  { code: "fr-FR", label: "Français (fr-FR)" },
  { code: "de-DE", label: "Deutsch (de-DE)" },
  { code: "es-ES", label: "Español (es-ES)" },
  { code: "th-TH", label: "ไทย (th-TH)" },
  { code: "id-ID", label: "Bahasa Indonesia (id-ID)" },
] as const;

export interface TimezoneOption {
  value: string;
  label: string;
}

export const COMMON_TIMEZONE_OPTIONS: readonly TimezoneOption[] = [
  { value: "Asia/Ho_Chi_Minh", label: "Asia/Ho_Chi_Minh (GMT+7)" },
  { value: "Asia/Bangkok", label: "Asia/Bangkok (GMT+7)" },
  { value: "Asia/Singapore", label: "Asia/Singapore (GMT+8)" },
  { value: "Asia/Tokyo", label: "Asia/Tokyo (GMT+9)" },
  { value: "Asia/Seoul", label: "Asia/Seoul (GMT+9)" },
  { value: "Asia/Shanghai", label: "Asia/Shanghai (GMT+8)" },
  { value: "Europe/London", label: "Europe/London (GMT+0)" },
  { value: "Europe/Paris", label: "Europe/Paris (GMT+1)" },
  { value: "America/New_York", label: "America/New_York (GMT-5)" },
  { value: "America/Los_Angeles", label: "America/Los_Angeles (GMT-8)" },
  { value: "Australia/Sydney", label: "Australia/Sydney (GMT+10)" },
  { value: "UTC", label: "UTC (GMT+0)" },
] as const;

let cachedTimezoneOptions: readonly TimezoneOption[] | null = null;

function formatTimezoneOffset(timeZone: string, referenceDate: Date): string {
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone,
      timeZoneName: "shortOffset",
    }).formatToParts(referenceDate);
    const offset = parts.find((p) => p.type === "timeZoneName")?.value;
    return offset ? `${timeZone} (${offset})` : timeZone;
  } catch {
    return timeZone;
  }
}

/**
 * Return the full list of IANA timezones supported by the runtime (Intl.supportedValuesOf),
 * formatted with current GMT offsets, falling back to COMMON_TIMEZONE_OPTIONS if unavailable.
 */
export function getAllTimezoneOptions(): readonly TimezoneOption[] {
  if (cachedTimezoneOptions) {
    return cachedTimezoneOptions;
  }

  const intlWithSupported = Intl as typeof Intl & {
    supportedValuesOf?: (key: "timeZone") => string[];
  };

  if (typeof intlWithSupported.supportedValuesOf !== "function") {
    cachedTimezoneOptions = COMMON_TIMEZONE_OPTIONS;
    return cachedTimezoneOptions;
  }

  try {
    const supported = intlWithSupported.supportedValuesOf("timeZone");
    const uniqueZones = Array.from(
      new Set(["UTC", "Asia/Ho_Chi_Minh", ...supported])
    ).sort((a, b) => a.localeCompare(b));
    const now = new Date();
    cachedTimezoneOptions = uniqueZones.map((tz) => ({
      value: tz,
      label: formatTimezoneOffset(tz, now),
    }));
    return cachedTimezoneOptions;
  } catch {
    cachedTimezoneOptions = COMMON_TIMEZONE_OPTIONS;
    return cachedTimezoneOptions;
  }
}

export const MAX_AVATAR_BYTES = 2 * 1024 * 1024;
export const ALLOWED_AVATAR_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
] as const;

export function getMe(): Promise<UserMe> {
  return apiRequest<UserMe>("/api/v1/users/me", {
    method: "GET",
    auth: true,
  });
}

export function updateProfile(payload: UpdateProfilePayload): Promise<UserMe> {
  return apiRequest<UserMe>("/api/v1/users/me/profile", {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export function updatePreferences(
  payload: UpdatePreferencesPayload
): Promise<UserMe> {
  return apiRequest<UserMe>("/api/v1/users/me/preferences", {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export function updateBillingInfo(
  payload: UpdateBillingInfoPayload
): Promise<UserMe> {
  return apiRequest<UserMe>("/api/v1/users/me/billing-info", {
    method: "PUT",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export function requestAvatarUploadUrl(
  payload: AvatarUploadUrlPayload
): Promise<AvatarUploadUrlResponse> {
  return apiRequest<AvatarUploadUrlResponse>(
    "/api/v1/users/me/avatar/upload-url",
    {
      method: "POST",
      auth: true,
      body: JSON.stringify(payload),
    }
  );
}

/**
 * Upload raw avatar bytes directly to the presigned S3 PUT URL (or local mock endpoint).
 */
export async function uploadAvatarBinary(
  uploadUrl: string,
  file: File
): Promise<void> {
  const targetUrl = uploadUrl.startsWith("/")
    ? `${getApiBaseUrl()}${uploadUrl}`
    : uploadUrl;
  const response = await fetch(targetUrl, {
    method: "PUT",
    headers: {
      "Content-Type": file.type,
    },
    body: file,
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      "AVATAR_UPLOAD_FAILED",
      "Không thể tải ảnh đại diện lên kho lưu trữ. Vui lòng thử lại."
    );
  }
}

export function confirmAvatarUpload(
  s3Key: string
): Promise<AvatarConfirmResponse> {
  return apiRequest<AvatarConfirmResponse>("/api/v1/users/me/avatar/confirm", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ s3Key }),
  });
}

export function changePassword(
  payload: ChangePasswordPayload
): Promise<ChangePasswordResponse> {
  return apiRequest<ChangePasswordResponse>("/api/v1/users/me/change-password", {
    method: "POST",
    auth: true,
    body: JSON.stringify(payload),
  });
}

export function deleteAccount(payload: DeleteAccountPayload): Promise<void> {
  return apiRequest<void>("/api/v1/users/me", {
    method: "DELETE",
    auth: true,
    body: JSON.stringify(payload),
  });
}
