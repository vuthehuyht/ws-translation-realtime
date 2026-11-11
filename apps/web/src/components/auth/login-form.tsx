"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SocialSsoButtons } from "./social-sso-buttons";

export interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

interface LoginFormProps {
  onSubmitSuccess?: (data: LoginFormData) => void;
  className?: string;
}

export function LoginForm({ onSubmitSuccess, className }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Validation error states
  const [errors, setErrors] = useState<{
    email?: string;
    password?: string;
  }>({});

  const validate = (): boolean => {
    const newErrors: typeof errors = {};

    if (!email.trim()) {
      newErrors.email = "Vui lòng nhập địa chỉ email";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      newErrors.email = "Địa chỉ email không hợp lệ (ví dụ: host@company.com)";
    }

    if (!password) {
      newErrors.password = "Vui lòng nhập mật khẩu";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      if (onSubmitSuccess) {
        onSubmitSuccess({
          email: email.trim(),
          password,
          rememberMe,
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={cn("w-full max-w-[440px] mx-auto space-y-6", className)}>
      <div className="space-y-1 text-left">
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Chào mừng trở lại
        </h2>
        <p className="text-sm text-muted-foreground">
          Đăng nhập để quản lý phòng dịch và số dư ví
        </p>
      </div>

      {/* Social SSO Authentication */}
      <SocialSsoButtons
        onGoogleClick={() => {
          // Placeholder for Cognito Google federated sign-in
        }}
        onAppleClick={() => {
          // Placeholder for Cognito Apple federated sign-in
        }}
      />

      {/* Elegant Divider */}
      <div className="relative flex items-center justify-center">
        <div className="w-full border-t border-border" />
        <span className="absolute bg-card px-3 text-xs uppercase tracking-wider text-muted-foreground">
          Hoặc đăng nhập với Email
        </span>
      </div>

      {/* Form Fields */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Email */}
        <div className="space-y-1.5 text-left">
          <label
            htmlFor="email"
            className="block text-xs font-semibold text-foreground"
          >
            Địa chỉ Email
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
              if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }));
            }}
            className={cn(
              "flex h-10 w-full rounded-lg border bg-background px-3.5 py-2 text-sm text-foreground shadow-sm transition-colors",
              "placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2",
              errors.email
                ? "border-destructive focus-visible:ring-destructive/20"
                : "border-border focus-visible:border-primary focus-visible:ring-primary/20"
            )}
          />
          {errors.email && (
            <p className="text-xs font-medium text-destructive">{errors.email}</p>
          )}
        </div>

        {/* Password */}
        <div className="space-y-1.5 text-left">
          <div className="flex items-center justify-between">
            <label
              htmlFor="password"
              className="block text-xs font-semibold text-foreground"
            >
              Mật khẩu
            </label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-primary hover:underline underline-offset-2"
            >
              Quên mật khẩu?
            </Link>
          </div>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (errors.password) setErrors((prev) => ({ ...prev, password: undefined }));
              }}
              className={cn(
                "flex h-10 w-full rounded-lg border bg-background px-3.5 pr-10 py-2 text-sm text-foreground shadow-sm transition-colors",
                "placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2",
                errors.password
                  ? "border-destructive focus-visible:ring-destructive/20"
                  : "border-border focus-visible:border-primary focus-visible:ring-primary/20"
              )}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showPassword ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-xs font-medium text-destructive">{errors.password}</p>
          )}
        </div>

        {/* Remember Me Option */}
        <div className="flex items-center justify-between pt-0.5">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <input
              type="checkbox"
              id="rememberMe"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary/20"
            />
            <label htmlFor="rememberMe" className="cursor-pointer">
              Ghi nhớ đăng nhập
            </label>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="flex h-11 w-full items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition-all hover:opacity-95 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Đăng nhập vào Hệ thống"
          )}
        </button>
      </form>

      {/* Redirect to Register */}
      <div className="text-center text-sm text-muted-foreground">
        Chưa có tài khoản Host?{" "}
        <Link
          href="/register"
          className="font-semibold text-primary hover:underline underline-offset-2"
        >
          Đăng ký miễn phí
        </Link>
      </div>
    </div>
  );
}
