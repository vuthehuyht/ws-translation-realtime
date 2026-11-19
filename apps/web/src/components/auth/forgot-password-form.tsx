"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import { forgotPassword } from "@/lib/auth-api";
import { cn } from "@/lib/utils";

interface ForgotPasswordFormProps {
  onSubmitSuccess?: (email: string) => void;
  className?: string;
}

function formatRetryAfter(seconds: number): string {
  const totalSeconds = Math.max(1, Math.ceil(seconds));
  if (totalSeconds < 60) {
    return `${totalSeconds} giây`;
  }
  const minutes = Math.floor(totalSeconds / 60);
  const remainingSeconds = totalSeconds % 60;
  if (remainingSeconds === 0) {
    return `${minutes} phút`;
  }
  return `${minutes} phút ${remainingSeconds} giây`;
}

function getApiErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 429) {
      const details = err.details as { retryAfter?: unknown } | undefined;
      if (typeof details?.retryAfter === "number" && details.retryAfter > 0) {
        return `Bạn đã yêu cầu quá số lần cho phép. Vui lòng thử lại sau ${formatRetryAfter(details.retryAfter)}.`;
      }
      return "Bạn đã yêu cầu quá số lần cho phép. Vui lòng thử lại sau ít phút.";
    }
    if (err.status === 422) {
      return "Địa chỉ email không hợp lệ (ví dụ: host@company.com)";
    }
    if (err.status >= 500) {
      return "Hệ thống tạm thời bận. Vui lòng thử lại sau ít phút.";
    }
    return err.message;
  }
  return "Không thể kết nối tới máy chủ. Vui lòng thử lại.";
}

export function ForgotPasswordForm({
  onSubmitSuccess,
  className,
}: ForgotPasswordFormProps) {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const validate = (): boolean => {
    if (!email.trim()) {
      setError("Vui lòng nhập địa chỉ email đã đăng ký");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Địa chỉ email không hợp lệ (ví dụ: host@company.com)");
      return false;
    }
    setError(undefined);
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isLoading || !validate()) {
      return;
    }

    const normalizedEmail = email.trim().toLowerCase();
    setIsLoading(true);
    setError(undefined);

    try {
      const response = await forgotPassword({ email: normalizedEmail });
      if (onSubmitSuccess) {
        onSubmitSuccess(response.email);
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("w-full max-w-[440px] mx-auto space-y-6", className)}>
      <div className="space-y-4 text-left">
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-muted-foreground transition-colors hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Quay lại Đăng nhập</span>
        </Link>

        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Quên mật khẩu?
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Đừng lo lắng! Hãy nhập địa chỉ email tài khoản của bạn, chúng tôi sẽ
            gửi mã xác thực 6 số để bạn đặt lại mật khẩu mới.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        <div className="space-y-1.5 text-left">
          <label
            htmlFor="email"
            className="block text-xs font-semibold text-foreground"
          >
            Địa chỉ Email đã đăng ký
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            placeholder="host@company.com"
            aria-invalid={Boolean(error)}
            aria-describedby={error ? "forgot-password-error" : undefined}
            value={email}
            onChange={(e) => {
              setEmail(e.target.value);
              if (error) setError(undefined);
            }}
            className={cn(
              "flex h-11 w-full rounded-lg border bg-background px-3.5 py-2 text-sm text-foreground shadow-sm transition-colors",
              "placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2",
              error
                ? "border-destructive focus-visible:ring-destructive/20"
                : "border-border focus-visible:border-primary focus-visible:ring-primary/20"
            )}
          />
          {error && (
            <p
              id="forgot-password-error"
              role="alert"
              className="text-xs font-medium text-destructive"
            >
              {error}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex h-11 w-full items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition-all hover:opacity-95 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Gửi mã xác thực qua Email →"
          )}
        </button>
      </form>
    </div>
  );
}
