"use client";

import React, { Suspense, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AudioTechHero } from "@/components/auth/audio-tech-hero";
import { VerifyOtpForm } from "@/components/auth/verify-otp-form";

function VerifyOtpContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") ?? "";
  const redirectTimerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current !== null) {
        window.clearTimeout(redirectTimerRef.current);
      }
    };
  }, []);

  const handleVerified = () => {
    const params = new URLSearchParams({ verified: "1" });
    if (email) {
      params.set("email", email);
    }
    redirectTimerRef.current = window.setTimeout(() => {
      router.push(`/login?${params.toString()}`);
    }, 1200);
  };

  return <VerifyOtpForm email={email} onVerified={handleVerified} />;
}

export default function VerifyOtpPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[580px]">
      <AudioTechHero
        variant="register"
        showTrialCard={true}
        className="w-full"
      />

      <div className="flex items-center justify-center p-6 sm:p-10 bg-card">
        <Suspense
          fallback={
            <div className="text-sm text-muted-foreground">Đang tải biểu mẫu xác thực...</div>
          }
        >
          <VerifyOtpContent />
        </Suspense>
      </div>
    </div>
  );
}
