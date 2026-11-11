"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { AudioTechHero } from "@/components/auth/audio-tech-hero";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  const router = useRouter();

  const handleLoginSuccess = () => {
    // Pure frontend flow: navigate to dashboard
    router.push("/dashboard");
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[560px]">
      {/* Left Column: Audio Technology Brand Hero with Live Waveform & Metrics */}
      <AudioTechHero variant="login" className="w-full" />

      {/* Right Column: Clean SaaS Login Form */}
      <div className="flex items-center justify-center p-6 sm:p-10 bg-card">
        <LoginForm onSubmitSuccess={handleLoginSuccess} />
      </div>
    </div>
  );
}
