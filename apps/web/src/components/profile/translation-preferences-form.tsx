"use client";

import React, { useState } from "react";
import { CheckCircle2, Globe2, Loader2, Save } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import {
  SUPPORTED_LANGUAGE_OPTIONS,
  type UserMe,
  type UserPreferencesSettings,
  updatePreferences,
} from "@/lib/user-api";
import { cn } from "@/lib/utils";

interface TranslationPreferencesFormProps {
  user: UserMe;
  onUpdated: (nextUser: UserMe) => void;
}

export function TranslationPreferencesForm({
  user,
  onUpdated,
}: TranslationPreferencesFormProps) {
  const [defaultSourceLang, setDefaultSourceLang] = useState(
    user.defaultSourceLang
  );
  const [defaultTargetLangs, setDefaultTargetLangs] = useState<string[]>(
    user.defaultTargetLangs.length > 0 ? user.defaultTargetLangs : ["en-US"]
  );
  const [vadSensitivity, setVadSensitivity] = useState<
    NonNullable<UserPreferencesSettings["vadSensitivity"]>
  >(user.preferences?.vadSensitivity ?? "medium");
  const [subtitleMode, setSubtitleMode] = useState<
    NonNullable<UserPreferencesSettings["subtitleMode"]>
  >(user.preferences?.subtitleMode ?? "bilingual");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const toggleTargetLang = (code: string) => {
    setError(null);
    setDefaultTargetLangs((prev) => {
      if (prev.includes(code)) {
        return prev.filter((item) => item !== code);
      }
      if (prev.length >= 10) {
        setError("Chỉ được chọn tối đa 10 ngôn ngữ đích mặc định.");
        return prev;
      }
      return [...prev, code];
    });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (defaultTargetLangs.length === 0) {
      setError("Vui lòng chọn ít nhất 1 ngôn ngữ đích mặc định.");
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updatePreferences({
        defaultSourceLang,
        defaultTargetLangs,
        preferences: {
          vadSensitivity,
          subtitleMode,
        },
      });
      onUpdated(updated);
      setSuccess("Đã lưu cấu hình dịch thuật mặc định.");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể lưu cài đặt dịch thuật. Vui lòng thử lại.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2.5 border-b border-border/80 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-600">
          <Globe2 className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Cài đặt dịch thuật mặc định
          </h2>
          <p className="text-xs text-muted-foreground">
            Tự động điền sẵn khi tạo phòng mới (tối đa 10 ngôn ngữ đích).
          </p>
        </div>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-5">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <label
              htmlFor="pref-source-lang"
              className="block text-xs font-semibold text-foreground"
            >
              Ngôn ngữ nguồn mặc định
            </label>
            <select
              id="pref-source-lang"
              value={defaultSourceLang}
              onChange={(e) => setDefaultSourceLang(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            >
              {SUPPORTED_LANGUAGE_OPTIONS.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="pref-vad"
              className="block text-xs font-semibold text-foreground"
            >
              Độ nhạy nhận diện giọng nói (VAD)
            </label>
            <select
              id="pref-vad"
              value={vadSensitivity}
              onChange={(e) =>
                setVadSensitivity(
                  e.target.value as NonNullable<
                    UserPreferencesSettings["vadSensitivity"]
                  >
                )
              }
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            >
              <option value="low">Thấp (lọc nhiễu mạnh)</option>
              <option value="medium">Trung bình (khuyên dùng)</option>
              <option value="high">Cao (bắt giọng nhỏ)</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="pref-subtitle-mode"
              className="block text-xs font-semibold text-foreground"
            >
              Hiển thị phụ đề
            </label>
            <select
              id="pref-subtitle-mode"
              value={subtitleMode}
              onChange={(e) =>
                setSubtitleMode(
                  e.target.value as NonNullable<
                    UserPreferencesSettings["subtitleMode"]
                  >
                )
              }
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            >
              <option value="bilingual">Song ngữ (gốc + dịch)</option>
              <option value="target_only">Đơn ngữ (chỉ bản dịch)</option>
            </select>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-foreground">
              Ngôn ngữ đích mặc định
            </span>
            <span className="text-xs text-muted-foreground">
              Đã chọn {defaultTargetLangs.length}/10
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {SUPPORTED_LANGUAGE_OPTIONS.map((lang) => {
              const selected = defaultTargetLangs.includes(lang.code);
              return (
                <button
                  key={lang.code}
                  type="button"
                  aria-pressed={selected}
                  onClick={() => toggleTargetLang(lang.code)}
                  className={cn(
                    "rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                    selected
                      ? "border-indigo-600 bg-indigo-600 text-white"
                      : "border-border bg-background text-foreground hover:bg-muted"
                  )}
                >
                  {lang.label}
                </button>
              );
            })}
          </div>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-xl bg-destructive/10 px-3.5 py-2.5 text-xs font-medium text-destructive"
          >
            {error}
          </p>
        )}
        {success && (
          <p
            role="status"
            className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 px-3.5 py-2.5 text-xs font-medium text-emerald-700"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{success}</span>
          </p>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSaving}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang lưu...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Lưu cài đặt dịch</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
