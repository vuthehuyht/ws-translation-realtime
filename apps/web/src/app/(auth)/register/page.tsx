"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { AudioTechHero } from "@/components/auth/audio-tech-hero";
import { RegisterForm, type RegisterFormData } from "@/components/auth/register-form";
import { ApiError } from "@/lib/api-client";
import { registerHost } from "@/lib/auth-api";

export default function RegisterPage() {
  const router = useRouter();
  const [serverError, setServerError] = useState<string | null>(null);

  const handleRegisterSuccess = async (data: RegisterFormData) => {
    setServerError(null);
    try {
      const response = await registerHost({
        fullName: data.fullName,
        email: data.email,
        password: data.password,
        role: "HOST",
      });
      const searchParams = new URLSearchParams({ email: response.email });
      router.push(`/verify-otp?${searchParams.toString()}`);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 409) {
          setServerError("Email này đã được đăng ký. Vui lòng đăng nhập hoặc dùng email khác.");
          return;
        }
        setServerError(error.message);
        return;
      }
      setServerError("Không thể kết nối tới máy chủ. Vui lòng thử lại sau.");
    }
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
        <RegisterForm
          onSubmitSuccess={handleRegisterSuccess}
          serverError={serverError}
        />
      </div>
    </div>
  );
}
