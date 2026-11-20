"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { SecurityBrandHero } from "@/components/auth/security-brand-hero";
import {
  ResetPasswordForm,
  type ResetPasswordFormData,
} from "@/components/auth/reset-password-form";
import { ApiError } from "@/lib/api-client";
import { forgotPassword, resetPassword } from "@/lib/auth-api";

function getResetErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 422) {
      return "Mã OTP không đúng, đã hết hạn, hoặc mật khẩu mới chưa đạt chuẩn bảo mật.";
    }
    if (err.status === 429) {
      return "Bạn đã thử quá số lần cho phép. Vui lòng chờ ít phút rồi thử lại.";
    }
    if (err.status >= 500) {
      return "Hệ thống tạm thời bận. Vui lòng thử lại sau ít phút.";
    }
    return err.message;
  }
  return "Không thể kết nối tới máy chủ. Vui lòng thử lại.";
}

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = (searchParams.get("email") ?? "").trim().toLowerCase();
  const [serverError, setServerError] = useState<string | null>(null);
  const [infoBanner, setInfoBanner] = useState<string | null>(null);

  const handleResetSubmit = async (data: ResetPasswordFormData) => {
    if (!email) {
      setServerError("Thiếu địa chỉ email. Vui lòng yêu cầu lại mã OTP.");
      return;
    }

    setServerError(null);
    setInfoBanner(null);

    try {
      await resetPassword({
        email,
        otpCode: data.otp,
        newPassword: data.password,
      });
      const params = new URLSearchParams({ reset: "success", email });
      router.push(`/login?${params.toString()}`);
    } catch (err) {
      setServerError(getResetErrorMessage(err));
    }
  };

  const handleResendOtp = async (): Promise<number | void> => {
    if (!email) {
      setServerError("Thiếu địa chỉ email. Vui lòng yêu cầu lại mã OTP.");
      return;
    }

    setServerError(null);
    setInfoBanner(null);

    try {
      await forgotPassword({ email });
      setInfoBanner("Mã xác thực OTP mới đã được gửi đến hòm thư của bạn.");
      return 60;
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const details = err.details as { retryAfter?: unknown } | undefined;
        const retryAfter =
          typeof details?.retryAfter === "number" && details.retryAfter > 0
            ? Math.ceil(details.retryAfter)
            : 60;
        setServerError(
          `Bạn đã yêu cầu quá số lần cho phép. Vui lòng thử lại sau ${retryAfter} giây.`
        );
        return retryAfter;
      }
      setServerError(getResetErrorMessage(err));
      // Send failed: do not make the user wait 60s before they can retry.
      return 0;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[520px]">
      {/* Left Column: Email Verification Info */}
      <SecurityBrandHero
        icon="✉️"
        title="Kiểm tra hòm thư của bạn"
        description={
          email ? (
            <span>
              Chúng tôi đã gửi mã xác thực 6 số đến địa chỉ email{" "}
              <strong className="text-white">{email}</strong>. Vui lòng kiểm tra
              cả mục Spam nếu chưa thấy.
            </span>
          ) : (
            <span>
              Vui lòng nhập email tại trang Quên mật khẩu để nhận mã xác thực 6
              số trước khi đặt lại mật khẩu mới.
            </span>
          )
        }
        footerText={
          <span>
            Mã xác thực có hiệu lực trong vòng{" "}
            <strong className="text-slate-300">15 phút</strong>.
          </span>
        }
        className="w-full"
      />

      {/* Right Column: Reset Password with OTP Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-card">
        {email ? (
          <ResetPasswordForm
            onSubmitSuccess={handleResetSubmit}
            onResendOtp={handleResendOtp}
            serverError={serverError}
            infoBanner={infoBanner}
          />
        ) : (
          <div className="w-full max-w-[440px] mx-auto space-y-4 text-left">
            <h2 className="text-2xl font-bold tracking-tight text-foreground">
              Thiếu thông tin email
            </h2>
            <p className="text-sm text-muted-foreground">
              Liên kết đặt lại mật khẩu không hợp lệ hoặc thiếu địa chỉ email.
              Vui lòng bắt đầu lại từ bước Quên mật khẩu.
            </p>
            <Link
              href="/forgot-password"
              className="inline-flex h-10 items-center justify-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground shadow-sm hover:opacity-95"
            >
              Quay lại Quên mật khẩu
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[520px] flex items-center justify-center bg-card text-muted-foreground text-sm">
          Đang tải trang xác thực...
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
