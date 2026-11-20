"use client";

import React, { useState } from "react";
import { CheckCircle2, Eye, EyeOff, KeyRound, Loader2 } from "lucide-react";
import { PasswordMeter } from "@/components/auth/password-meter";
import { ApiError } from "@/lib/api-client";
import { changePassword } from "@/lib/user-api";

export function ChangePasswordForm() {
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPasswords, setShowPasswords] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    if (!oldPassword) {
      setError("Vui lòng nhập mật khẩu hiện tại.");
      return;
    }
    if (newPassword !== newPassword.trim()) {
      setError("Mật khẩu mới không được chứa khoảng trắng ở đầu hoặc cuối.");
      return;
    }
    if (!/^[\x20-\x7E]+$/.test(newPassword)) {
      setError(
        "Mật khẩu mới chỉ được dùng ký tự không dấu (tắt bộ gõ tiếng Việt khi nhập)."
      );
      return;
    }
    if (newPassword.length < 8) {
      setError("Mật khẩu mới phải có tối thiểu 8 ký tự.");
      return;
    }
    if (
      !/[A-Z]/.test(newPassword) ||
      !/[a-z]/.test(newPassword) ||
      !/[0-9]/.test(newPassword) ||
      !/[!@#$%^&*(),.?":{}|<>\-_+=~`[\]\\;/']/.test(newPassword)
    ) {
      setError(
        "Mật khẩu mới cần có ít nhất 1 chữ hoa, 1 chữ thường, 1 chữ số và 1 ký tự đặc biệt."
      );
      return;
    }
    if (newPassword === oldPassword) {
      setError("Mật khẩu mới phải khác mật khẩu hiện tại.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("Xác nhận mật khẩu mới không khớp.");
      return;
    }

    setIsSubmitting(true);
    try {
      await changePassword({ oldPassword, newPassword });
      setOldPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setSuccess("Đã đổi mật khẩu thành công.");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400) {
          setError("Mật khẩu hiện tại không chính xác.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Không thể đổi mật khẩu lúc này. Vui lòng thử lại.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const inputType = showPasswords ? "text" : "password";

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-border/80 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-600">
            <KeyRound className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Đổi mật khẩu
            </h2>
            <p className="text-xs text-muted-foreground">
              Sử dụng mật khẩu mạnh để bảo vệ tài khoản Host và số dư ví.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowPasswords((prev) => !prev)}
          className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          {showPasswords ? (
            <>
              <EyeOff className="h-3.5 w-3.5" />
              <span>Ẩn mật khẩu</span>
            </>
          ) : (
            <>
              <Eye className="h-3.5 w-3.5" />
              <span>Hiện mật khẩu</span>
            </>
          )}
        </button>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-4">
        <div className="space-y-1.5">
          <label
            htmlFor="pw-old"
            className="block text-xs font-semibold text-foreground"
          >
            Mật khẩu hiện tại
          </label>
          <input
            id="pw-old"
            type={inputType}
            autoComplete="current-password"
            required
            value={oldPassword}
            onChange={(e) => setOldPassword(e.target.value)}
            className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
          />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor="pw-new"
              className="block text-xs font-semibold text-foreground"
            >
              Mật khẩu mới
            </label>
            <input
              id="pw-new"
              type={inputType}
              autoComplete="new-password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="pw-confirm"
              className="block text-xs font-semibold text-foreground"
            >
              Xác nhận mật khẩu mới
            </label>
            <input
              id="pw-confirm"
              type={inputType}
              autoComplete="new-password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>
        </div>

        {newPassword && <PasswordMeter password={newPassword} />}

        {error && (
          <p
            role="alert"
            className="rounded-xl bg-destructive/10 px-3.5 py-2.5 text-xs font-medium text-destructive"
          >
            {error}
          </p>
        )}
        {success && (
          <p
            role="status"
            className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 px-3.5 py-2.5 text-xs font-medium text-emerald-700"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{success}</span>
          </p>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang cập nhật...</span>
              </>
            ) : (
              <>
                <KeyRound className="h-4 w-4" />
                <span>Đổi mật khẩu</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
