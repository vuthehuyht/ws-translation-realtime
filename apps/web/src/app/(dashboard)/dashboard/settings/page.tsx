"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, RefreshCw } from "lucide-react";
import { TranslationPreferencesForm } from "@/components/profile/translation-preferences-form";
import { ApiError } from "@/lib/api-client";
import { patchAuthSessionUser } from "@/lib/auth-refresh";
import { type UserMe, getMe } from "@/lib/user-api";

export default function SettingsPage() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getMe();
      setUser(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setLoadError(err.message);
      } else {
        setLoadError("Không thể tải cấu hình cài đặt.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSettings();
  }, [fetchSettings]);

  const handleUserUpdated = (nextUser: UserMe) => {
    setUser(nextUser);
    patchAuthSessionUser({
      defaultSourceLang: nextUser.defaultSourceLang,
      defaultTargetLangs: nextUser.defaultTargetLangs,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Quay lại Host Studio</span>
        </Link>
        <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-foreground">
          Cài đặt
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Thiết lập ngôn ngữ dịch thuật mặc định, độ nhạy nhận diện giọng nói và
          cách hiển thị phụ đề cho các phòng họp mới.
        </p>
      </div>

      {isLoading && (
        <div
          data-testid="settings-loading"
          className="flex items-center justify-center gap-2 rounded-2xl border border-border bg-card py-16 text-sm text-muted-foreground"
        >
          <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
          <span>Đang tải cài đặt...</span>
        </div>
      )}

      {!isLoading && loadError && (
        <div
          role="alert"
          className="flex flex-col items-start justify-between gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 sm:flex-row sm:items-center"
        >
          <div>
            <p className="text-sm font-semibold text-destructive">
              Không thể tải dữ liệu cài đặt
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">{loadError}</p>
          </div>
          <button
            type="button"
            onClick={() => void fetchSettings()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-background px-3.5 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Thử lại</span>
          </button>
        </div>
      )}

      {!isLoading && user && (
        <TranslationPreferencesForm
          user={user}
          onUpdated={handleUserUpdated}
        />
      )}
    </div>
  );
}
