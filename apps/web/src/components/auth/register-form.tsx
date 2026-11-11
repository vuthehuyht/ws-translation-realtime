"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { PasswordMeter } from "./password-meter";
import { SocialSsoButtons } from "./social-sso-buttons";

export interface RegisterFormData {
  fullName: string;
  email: string;
  password: string;
}

interface RegisterFormProps {
  onSubmitSuccess?: (data: RegisterFormData) => void;
  className?: string;
}

export function RegisterForm({ onSubmitSuccess, className }: RegisterFormProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [agreeTerms, setAgreeTerms] = useState(true);

  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Validation error states
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    agreeTerms?: string;
  }>({});

  const validate = (): boolean => {
    const newErrors: typeof errors = {};

    if (!fullName.trim()) {
      newErrors.fullName = "Vui lòng nhập họ và tên của bạn";
    }

    if (!email.trim()) {
      newErrors.email = "Vui lòng nhập địa chỉ email";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      newErrors.email = "Địa chỉ email không hợp lệ (ví dụ: host@company.com)";
    }

    if (!password) {
      newErrors.password = "Vui lòng nhập mật khẩu";
    } else if (password.length < 8) {
      newErrors.password = "Mật khẩu phải có ít nhất 8 ký tự";
    }

    if (!agreeTerms) {
      newErrors.agreeTerms = "Bạn cần đồng ý với Điều khoản Dịch vụ để tiếp tục";
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
      // Simulate client-side registration call (or trigger Cognito callback)
      if (onSubmitSuccess) {
        onSubmitSuccess({
          fullName: fullName.trim(),
          email: email.trim(),
          password,
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
          Tạo tài khoản mới
        </h2>
        <p className="text-sm text-muted-foreground">
          Đăng ký nhanh với mạng xã hội hoặc email
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
        <span className="absolute bg-card px-3 text-xs text-muted-foreground">
          Hoặc tạo tài khoản email
        </span>
      </div>

      {/* Form Fields */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        {/* Full Name */}
        <div className="space-y-1.5 text-left">
          <label
            htmlFor="fullName"
            className="block text-xs font-semibold text-foreground"
          >
            Họ và tên diễn giả / Host
          </label>
          <input
            id="fullName"
            name="fullName"
            type="text"
            placeholder="Nguyễn Văn A"
            value={fullName}
            onChange={(e) => {
              setFullName(e.target.value);
              if (errors.fullName) setErrors((prev) => ({ ...prev, fullName: undefined }));
            }}
            className={cn(
              "flex h-10 w-full rounded-lg border bg-background px-3.5 py-2 text-sm text-foreground shadow-sm transition-colors",
              "placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2",
              errors.fullName
                ? "border-destructive focus-visible:ring-destructive/20"
                : "border-border focus-visible:border-primary focus-visible:ring-primary/20"
            )}
          />
          {errors.fullName && (
            <p className="text-xs font-medium text-destructive">{errors.fullName}</p>
          )}
        </div>

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
          <label
            htmlFor="password"
            className="block text-xs font-semibold text-foreground"
          >
            Mật khẩu
          </label>
          <div className="relative">
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              placeholder="Tối thiểu 8 ký tự..."
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
          {/* Password strength meter */}
          <PasswordMeter password={password} className="pt-1" />
        </div>

        {/* Terms Agreement Checkbox */}
        <div className="space-y-1 text-left pt-1">
          <label className="flex items-start gap-2.5 cursor-pointer text-xs text-muted-foreground">
            <input
              type="checkbox"
              id="agreeTerms"
              checked={agreeTerms}
              onChange={(e) => {
                setAgreeTerms(e.target.checked);
                if (errors.agreeTerms) setErrors((prev) => ({ ...prev, agreeTerms: undefined }));
              }}
              className="mt-0.5 h-4 w-4 rounded border-border text-primary focus:ring-primary/20"
            />
            <span>
              Tôi đồng ý với{" "}
              <Link href="/terms" className="font-semibold text-primary underline underline-offset-2">
                Điều khoản Dịch vụ
              </Link>{" "}
              và{" "}
              <Link href="/privacy" className="font-semibold text-primary underline underline-offset-2">
                Chính sách Bảo mật
              </Link>{" "}
              của WS Translation.
            </span>
          </label>
          {errors.agreeTerms && (
            <p className="text-xs font-medium text-destructive">{errors.agreeTerms}</p>
          )}
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
            "Tạo tài khoản"
          )}
        </button>
      </form>

      {/* Redirect to Login */}
      <div className="text-center text-sm text-muted-foreground">
        Đã có tài khoản?{" "}
        <Link
          href="/login"
          className="font-semibold text-primary hover:underline underline-offset-2"
        >
          Đăng nhập ngay
        </Link>
      </div>
    </div>
  );
}
