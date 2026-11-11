"use client";

import React, { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SecurityBrandHero } from "@/components/auth/security-brand-hero";
import { ResetPasswordForm } from "@/components/auth/reset-password-form";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "host@company.com";

  const handleResetSuccess = () => {
    // Pure frontend flow: navigate to login with success indicator
    router.push("/login?reset=success");
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[520px]">
      {/* Left Column: Email Verification Info */}
      <SecurityBrandHero
        icon="✉️"
        title="Kiểm tra Hòm thư của bạn"
        description={
          <span>
            Chúng tôi đã gửi mã xác thực 6 số đến địa chỉ email{" "}
            <strong className="text-white">{email}</strong>. Vui lòng kiểm tra cả
            mục Spam nếu chưa thấy.
          </span>
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
        <ResetPasswordForm onSubmitSuccess={handleResetSuccess} />
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
