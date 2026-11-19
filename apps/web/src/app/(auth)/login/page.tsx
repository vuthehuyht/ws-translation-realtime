"use client";

import React, { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AudioTechHero } from "@/components/auth/audio-tech-hero";
import { LoginForm, type LoginFormData } from "@/components/auth/login-form";
import { ApiError } from "@/lib/api-client";
import { loginHost } from "@/lib/auth-api";
import { saveAuthSession } from "@/lib/auth-storage";

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [serverError, setServerError] = useState<string | null>(null);
  const [unconfirmedEmail, setUnconfirmedEmail] = useState<string | null>(null);

  const isVerified = searchParams.get("verified") === "1";
  const isPasswordReset = searchParams.get("reset") === "success";
  const initialEmail = searchParams.get("email") ?? "";
  const infoBanner = isVerified
    ? "Tài khoản của bạn đã được xác thực thành công. Vui lòng đăng nhập để tiếp tục."
    : isPasswordReset
      ? "Mật khẩu đã được đặt lại thành công. Vui lòng đăng nhập bằng mật khẩu mới."
      : null;

  const handleLoginSuccess = async (data: LoginFormData) => {
    setServerError(null);
    setUnconfirmedEmail(null);

    try {
      const response = await loginHost({
        email: data.email,
        password: data.password,
        rememberMe: Boolean(data.rememberMe),
      });

      saveAuthSession(
        {
          tokens: response.tokens,
          user: response.user,
        },
        Boolean(data.rememberMe)
      );

      router.push("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          if (/not confirmed/i.test(error.message)) {
            setUnconfirmedEmail(data.email);
            setServerError(
              "Tài khoản chưa được xác thực OTP. Vui lòng nhập mã OTP để kích hoạt tài khoản."
            );
            return;
          }
          setServerError("Email hoặc mật khẩu không chính xác.");
          return;
        }
        if (error.status === 403) {
          setServerError(
            "Tài khoản của bạn đã bị tạm khóa. Vui lòng liên hệ bộ phận hỗ trợ."
          );
          return;
        }
        if (error.status === 422) {
          setServerError("Thông tin đăng nhập chưa hợp lệ. Vui lòng kiểm tra lại.");
          return;
        }
        setServerError(error.message || "Đăng nhập thất bại. Vui lòng thử lại.");
        return;
      }

      setServerError(
        "Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại kết nối mạng."
      );
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[560px]">
      {/* Left Column: Audio Technology Brand Hero with Live Waveform & Metrics */}
      <AudioTechHero variant="login" className="w-full" />

      {/* Right Column: Clean SaaS Login Form */}
      <div className="flex items-center justify-center bg-card px-6 pt-12 pb-6 sm:px-10 sm:pt-16 sm:pb-8">
        <LoginForm
          onSubmitSuccess={handleLoginSuccess}
          serverError={serverError}
          serverErrorAction={
            unconfirmedEmail ? (
              <Link
                href={`/verify-otp?email=${encodeURIComponent(unconfirmedEmail)}`}
                className="inline-block font-semibold underline underline-offset-2 hover:opacity-80"
              >
                Xác thực OTP ngay →
              </Link>
            ) : undefined
          }
          infoBanner={infoBanner}
          initialEmail={initialEmail}
        />
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[560px]">
          <AudioTechHero variant="login" className="w-full" />
          <div className="flex items-center justify-center p-6 sm:p-10 bg-card text-sm text-muted-foreground">
            Đang tải...
          </div>
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}
