"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2, RefreshCw, Wallet } from "lucide-react";
import { AvatarUploader } from "@/components/profile/avatar-uploader";
import { BillingInfoForm } from "@/components/profile/billing-info-form";
import { ChangePasswordForm } from "@/components/profile/change-password-form";
import { ProfileBasicForm } from "@/components/profile/profile-basic-form";
import { ApiError } from "@/lib/api-client";
import { patchAuthSessionUser } from "@/lib/auth-refresh";
import { type UserMe, getMe } from "@/lib/user-api";

export default function ProfilePage() {
  const [user, setUser] = useState<UserMe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchProfile = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getMe();
      setUser(data);
      patchAuthSessionUser({
        fullName: data.fullName,
        avatarUrl: data.avatarUrl,
        defaultSourceLang: data.defaultSourceLang,
        defaultTargetLangs: data.defaultTargetLangs,
        timezone: data.timezone,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setLoadError(err.message);
      } else {
        setLoadError("Không thể tải thông tin hồ sơ cá nhân.");
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchProfile();
  }, [fetchProfile]);

  const handleUserUpdated = (nextUser: UserMe) => {
    setUser(nextUser);
    patchAuthSessionUser({
      fullName: nextUser.fullName,
      avatarUrl: nextUser.avatarUrl,
      defaultSourceLang: nextUser.defaultSourceLang,
      defaultTargetLangs: nextUser.defaultTargetLangs,
      timezone: nextUser.timezone,
    });
  };

  const handleAvatarUpdated = (nextAvatarUrl: string) => {
    setUser((prev) => (prev ? { ...prev, avatarUrl: nextAvatarUrl } : prev));
    patchAuthSessionUser({ avatarUrl: nextAvatarUrl });
  };

  const formattedBalance = user?.wallet
    ? `$${Number(user.wallet.balance).toFixed(2)}`
    : null;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Quay lại Host Studio</span>
          </Link>
          <h1 className="mt-1.5 text-2xl font-bold tracking-tight text-foreground">
            Hồ sơ cá nhân
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Quản lý ảnh đại diện, thông tin cá nhân, thông tin hóa đơn VAT và
            mật khẩu tài khoản.
          </p>
        </div>

        {formattedBalance && (
          <div className="inline-flex items-center gap-2.5 self-start rounded-2xl border border-indigo-200 bg-indigo-50/70 px-4 py-2.5 sm:self-auto">
            <Wallet className="h-4 w-4 text-indigo-600" />
            <div className="leading-tight">
              <p className="text-[11px] font-medium text-indigo-700/80">
                Số dư ví hiện tại
              </p>
              <p className="text-sm font-bold text-indigo-950">
                {formattedBalance}{" "}
                <span className="text-xs font-medium text-indigo-700">
                  {user?.wallet?.currency}
                </span>
              </p>
            </div>
          </div>
        )}
      </div>

      {isLoading && (
        <div
          data-testid="profile-loading"
          className="flex items-center justify-center gap-2 rounded-2xl border border-border bg-card py-16 text-sm text-muted-foreground"
        >
          <Loader2 className="h-5 w-5 animate-spin text-indigo-600" />
          <span>Đang tải hồ sơ cá nhân...</span>
        </div>
      )}

      {!isLoading && loadError && (
        <div
          role="alert"
          className="flex flex-col items-start justify-between gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 p-6 sm:flex-row sm:items-center"
        >
          <div>
            <p className="text-sm font-semibold text-destructive">
              Không thể tải dữ liệu hồ sơ
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">{loadError}</p>
          </div>
          <button
            type="button"
            onClick={() => void fetchProfile()}
            className="inline-flex items-center gap-1.5 rounded-xl border border-border bg-background px-3.5 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            <span>Thử lại</span>
          </button>
        </div>
      )}

      {!isLoading && user && (
        <div className="space-y-6">
          <AvatarUploader
            fullName={user.fullName}
            email={user.email}
            avatarUrl={user.avatarUrl}
            onAvatarUpdated={handleAvatarUpdated}
          />
          <ProfileBasicForm user={user} onUpdated={handleUserUpdated} />
          <BillingInfoForm user={user} onUpdated={handleUserUpdated} />
          <ChangePasswordForm />
        </div>
      )}
    </div>
  );
}
