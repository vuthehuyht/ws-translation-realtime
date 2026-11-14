"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, Loader2, MailCheck, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api-client";
import {
  confirmRegistration,
  resendOtp,
  type ConfirmOtpResponse,
} from "@/lib/auth-api";
import { OtpInput6 } from "./otp-input-6";

interface VerifyOtpFormProps {
  email: string;
  onVerified?: (response: ConfirmOtpResponse) => void;
  className?: string;
}

const INITIAL_COOLDOWN_SECONDS = 60;

export function VerifyOtpForm({
  email,
  onVerified,
  className,
}: VerifyOtpFormProps) {
  const [otpCode, setOtpCode] = useState("");
  const [countdown, setCountdown] = useState(INITIAL_COOLDOWN_SECONDS);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [verifiedResponse, setVerifiedResponse] = useState<ConfirmOtpResponse | null>(null);

  // Prevent duplicate auto-submit calls when OtpInput6 triggers onComplete
  const lastSubmittedOtpRef = useRef<string | null>(null);
  const isCoolingDown = countdown > 0;

  useEffect(() => {
    if (!isCoolingDown) {
      return;
    }
    const timer = window.setInterval(() => {
      setCountdown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [isCoolingDown]);

  const submitOtp = async (code: string) => {
    if (!email || code.length !== 6 || isVerifying || verifiedResponse) {
      return;
    }
    if (lastSubmittedOtpRef.current === code) {
      return;
    }
    lastSubmittedOtpRef.current = code;
    setErrorMessage(null);
    setInfoMessage(null);
    setIsVerifying(true);

    try {
      const response = await confirmRegistration({ email, otpCode: code });
      setVerifiedResponse(response);
      if (onVerified) {
        onVerified(response);
      }
    } catch (error) {
      // Keep lastSubmittedOtpRef set so failed OTP is not auto-resubmitted on re-render
      if (error instanceof ApiError) {
        if (error.status === 422) {
          setErrorMessage("Mã OTP không chính xác hoặc đã hết hạn. Vui lòng kiểm tra lại.");
        } else if (error.status === 404) {
          setErrorMessage("Không tìm thấy tài khoản với email này.");
        } else {
          setErrorMessage(error.message);
        }
      } else {
        setErrorMessage("Không thể kết nối tới máy chủ. Vui lòng thử lại.");
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      setErrorMessage("Vui lòng nhập đủ 6 chữ số OTP.");
      return;
    }
    lastSubmittedOtpRef.current = null;
    await submitOtp(otpCode);
  };

  const handleResend = async () => {
    if (!email || countdown > 0 || isResending) {
      return;
    }
    setErrorMessage(null);
    setInfoMessage(null);
    setIsResending(true);

    try {
      const res = await resendOtp({ email });
      setCountdown(res.retryAfter ?? INITIAL_COOLDOWN_SECONDS);
      setOtpCode("");
      lastSubmittedOtpRef.current = null;
      setInfoMessage("Đã gửi lại mã OTP mới. Vui lòng kiểm tra hộp thư của bạn.");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 429) {
          const details = error.details as { retryAfter?: unknown } | undefined;
          const retryAfter =
            typeof details?.retryAfter === "number"
              ? details.retryAfter
              : INITIAL_COOLDOWN_SECONDS;
          setCountdown(retryAfter);
          setErrorMessage(`Vui lòng đợi ${retryAfter} giây trước khi gửi lại mã.`);
        } else if (error.status === 409) {
          setErrorMessage("Tài khoản này đã được kích hoạt trước đó. Bạn có thể đăng nhập ngay.");
        } else if (error.status === 404) {
          setErrorMessage("Email chưa được đăng ký trên hệ thống.");
        } else {
          setErrorMessage(error.message);
        }
      } else {
        setErrorMessage("Không thể kết nối tới máy chủ. Vui lòng thử lại.");
      }
    } finally {
      setIsResending(false);
    }
  };

  if (verifiedResponse) {
    return (
      <div className={cn("w-full max-w-[440px] mx-auto space-y-5 text-center", className)}>
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-600">
          <CheckCircle2 className="h-8 w-8" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold tracking-tight text-foreground">
            Kích hoạt tài khoản thành công!
          </h2>
          <p className="text-sm text-muted-foreground">
            Ví Host của bạn đã được khởi tạo với{" "}
            <span className="font-semibold text-emerald-600">
              ${Number(verifiedResponse.walletBalance).toFixed(2)} {verifiedResponse.currency}
            </span>{" "}
            Welcome Bonus. Đang chuyển sang trang đăng nhập...
          </p>
        </div>
        <Link
          href={`/login?verified=1&email=${encodeURIComponent(email)}`}
          className="inline-flex h-11 w-full items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 hover:opacity-95"
        >
          Đăng nhập ngay
        </Link>
      </div>
    );
  }

  return (
    <div className={cn("w-full max-w-[440px] mx-auto space-y-6", className)}>
      <div className="space-y-2 text-left">
        <div className="inline-flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <MailCheck className="h-5 w-5" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Xác thực email của bạn
        </h2>
        <p className="text-sm text-muted-foreground">
          Chúng tôi đã gửi mã OTP gồm 6 chữ số tới{" "}
          <span className="font-semibold text-foreground">{email || "email của bạn"}</span>.
        </p>
      </div>

      <form onSubmit={handleManualSubmit} className="space-y-5" noValidate>
        {!email && (
          <div
            role="alert"
            className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3.5 py-2.5 text-xs font-medium text-amber-700 dark:text-amber-400"
          >
            Thiếu địa chỉ email xác thực. Vui lòng quay lại trang đăng ký để bắt đầu lại.
          </div>
        )}
        <div className="space-y-2">
          <OtpInput6
            value={otpCode}
            onChange={(val) => {
              setOtpCode(val);
              lastSubmittedOtpRef.current = null;
              if (errorMessage) setErrorMessage(null);
            }}
            onComplete={(val) => {
              void submitOtp(val);
            }}
            disabled={isVerifying}
            hasError={Boolean(errorMessage)}
          />
          {errorMessage && (
            <p role="alert" className="text-xs font-medium text-destructive">
              {errorMessage}
            </p>
          )}
          {infoMessage && (
            <p role="status" className="text-xs font-medium text-emerald-600">
              {infoMessage}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isVerifying || otpCode.length !== 6 || !email}
          className="flex h-11 w-full items-center justify-center rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition-all hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isVerifying ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Xác nhận OTP"
          )}
        </button>
      </form>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Chưa nhận được mã?</span>
        <button
          type="button"
          onClick={handleResend}
          disabled={countdown > 0 || isResending || !email}
          className="inline-flex items-center gap-1.5 font-semibold text-primary hover:underline disabled:cursor-not-allowed disabled:text-muted-foreground disabled:no-underline"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", isResending && "animate-spin")} />
          {countdown > 0
            ? `Gửi lại mã sau ${countdown}s`
            : "Gửi lại mã OTP"}
        </button>
      </div>

      <div className="pt-2 text-center">
        <Link
          href="/register"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Quay lại trang đăng ký
        </Link>
      </div>
    </div>
  );
}
