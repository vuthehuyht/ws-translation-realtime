"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { SecurityBrandHero } from "@/components/auth/security-brand-hero";
import { ForgotPasswordForm } from "@/components/auth/forgot-password-form";

export default function ForgotPasswordPage() {
  const router = useRouter();

  const handleForgotPasswordSuccess = (email: string) => {
    const searchParams = new URLSearchParams({ email });
    router.push(`/reset-password?${searchParams.toString()}`);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[520px]">
      {/* Left Column: Security Information */}
      <SecurityBrandHero
        icon="🔐"
        title="Bảo mật Tài khoản Host"
        description="Hệ thống sử dụng dịch vụ xác thực chuẩn AWS Cognito. Mã bảo mật 6 số sẽ được gửi trực tiếp đến hòm thư đã đăng ký của bạn."
        footerText={
          <span>
            Cần trợ giúp khẩn cấp? Liên hệ:{" "}
            <span className="text-slate-300">support@wstranslation.ai</span>
          </span>
        }
        className="w-full"
      />

      {/* Right Column: Forgot Password Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-card">
        <ForgotPasswordForm onSubmitSuccess={handleForgotPasswordSuccess} />
      </div>
    </div>
  );
}
