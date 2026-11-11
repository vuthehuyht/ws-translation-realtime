"use client";

import React, { useState, useEffect } from "react";
import { Eye, EyeOff, Loader2, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { OtpInput6 } from "./otp-input-6";
import { PasswordMeter } from "./password-meter";

export interface ResetPasswordFormData {
  otp: string;
  password: string;
}

interface ResetPasswordFormProps {
  onSubmitSuccess?: (data: ResetPasswordFormData) => void;
  onResendOtp?: () => void;
  className?: string;
}

export function ResetPasswordForm({
  onSubmitSuccess,
  onResendOtp,
  className,
}: ResetPasswordFormProps) {
  const [otp, setOtp] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Resend countdown timer (starts at 45s)
  const [countdown, setCountdown] = useState(45);
  const [isLoading, setIsLoading] = useState(false);

  const [errors, setErrors] = useState<{
    otp?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  useEffect(() => {
    if (countdown <= 0) return;
    const interval = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [countdown]);

  const handleResend = () => {
    if (countdown > 0) return;
    setCountdown(45);
    if (onResendOtp) {
      onResendOtp();
    }
  };

  const validate = (): boolean => {
    const newErrors: typeof errors = {};

    if (!otp || otp.length < 6) {
      newErrors.otp = "Vui lòng nhập đầy đủ mã OTP 6 số";
    }

    if (!password) {
      newErrors.password = "Vui lòng nhập mật khẩu mới";
    } else if (password.length < 8) {
      newErrors.password = "Mật khẩu phải có ít nhất 8 ký tự";
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Vui lòng nhập lại mật khẩu mới";
    } else if (confirmPassword !== password) {
      newErrors.confirmPassword = "Mật khẩu xác nhận không khớp";
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
          otp,
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
          Đặt lại Mật khẩu mới
        </h2>
        <p className="text-sm text-muted-foreground">
          Nhập mã OTP 6 số và thiết lập mật khẩu bảo vệ mới
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5" noValidate>
        {/* OTP Input Field */}
        <div className="space-y-2 text-left">
          <label className="block text-xs font-semibold text-foreground">
            Mã xác thực OTP (6 số)
          </label>
          <OtpInput6
            value={otp}
            onChange={(val) => {
              setOtp(val);
              if (errors.otp) setErrors((prev) => ({ ...prev, otp: undefined }));
            }}
            hasError={Boolean(errors.otp)}
          />
          {errors.otp && (
            <p className="text-xs font-medium text-destructive">{errors.otp}</p>
          )}

          {/* Resend Countdown Link */}
          <div className="flex items-center justify-between pt-1 text-xs">
            <span className="text-muted-foreground">Chưa nhận được mã?</span>
            {countdown > 0 ? (
              <span className="font-semibold text-primary">
                Gửi lại mã (sau {countdown}s)
              </span>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                className="font-semibold text-primary hover:underline underline-offset-2"
              >
                Gửi lại mã ngay
              </button>
            )}
          </div>
        </div>

        {/* New Password */}
        <div className="space-y-1.5 text-left">
          <label
            htmlFor="new-password"
            className="block text-xs font-semibold text-foreground"
          >
            Mật khẩu mới
          </label>
          <div className="relative">
            <input
              id="new-password"
              name="new-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
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
              aria-label={showPassword ? "Ẩn mật khẩu mới" : "Hiện mật khẩu mới"}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.password && (
            <p className="text-xs font-medium text-destructive">{errors.password}</p>
          )}
          <PasswordMeter password={password} className="pt-1" />
        </div>

        {/* Confirm Password */}
        <div className="space-y-1.5 text-left">
          <label
            htmlFor="confirm-password"
            className="block text-xs font-semibold text-foreground"
          >
            Xác nhận lại mật khẩu mới
          </label>
          <div className="relative">
            <input
              id="confirm-password"
              name="confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              placeholder="Nhập lại mật khẩu..."
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (errors.confirmPassword) {
                  setErrors((prev) => ({ ...prev, confirmPassword: undefined }));
                }
              }}
              className={cn(
                "flex h-10 w-full rounded-lg border bg-background px-3.5 pr-10 py-2 text-sm text-foreground shadow-sm transition-colors",
                "placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2",
                errors.confirmPassword
                  ? "border-destructive focus-visible:ring-destructive/20"
                  : "border-border focus-visible:border-primary focus-visible:ring-primary/20"
              )}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label={showConfirmPassword ? "Ẩn mật khẩu xác nhận" : "Hiện mật khẩu xác nhận"}
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {errors.confirmPassword && (
            <p className="text-xs font-medium text-destructive">{errors.confirmPassword}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-700 px-4 text-sm font-semibold text-white shadow-md shadow-emerald-600/25 transition-all hover:opacity-95 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Check className="h-4 w-4" />
              <span>Lưu Mật khẩu &amp; Đăng nhập ngay</span>
            </>
          )}
        </button>
      </form>
    </div>
  );
}
