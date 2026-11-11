"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AudioTechHero } from "@/components/auth/audio-tech-hero";
import { RegisterForm, type RegisterFormData } from "@/components/auth/register-form";

export default function RegisterPage() {
  const router = useRouter();

  const handleRegisterSuccess = (data: RegisterFormData) => {
    // Pure frontend flow: pass email to verify-otp page
    const searchParams = new URLSearchParams({ email: data.email });
    router.push(`/verify-otp?${searchParams.toString()}`);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[580px]">
      {/* Left Column: Audio Technology Brand Hero */}
      <AudioTechHero
        variant="register"
        showTrialCard={true}
        className="w-full"
      />

      {/* Right Column: Interactive Registration Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-card">
        <RegisterForm onSubmitSuccess={handleRegisterSuccess} />
      </div>
    </div>
  );
}
