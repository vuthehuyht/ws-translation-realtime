"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowLeft, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ForgotPasswordFormProps {
  onSubmitSuccess?: (email: string) => void;
  className?: string;
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

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      if (onSubmitSuccess) {
        onSubmitSuccess(email.trim());
      }
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
            <p className="text-xs font-medium text-destructive">{error}</p>
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
