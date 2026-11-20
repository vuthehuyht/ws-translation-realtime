"use client";

import React, { useMemo, useState } from "react";
import { CheckCircle2, Loader2, Save, User as UserIcon } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import {
  type UserMe,
  getAllTimezoneOptions,
  updateProfile,
} from "@/lib/user-api";

interface ProfileBasicFormProps {
  user: UserMe;
  onUpdated: (nextUser: UserMe) => void;
}

const E164_REGEX = /^\+[1-9]\d{6,14}$/;

export function ProfileBasicForm({ user, onUpdated }: ProfileBasicFormProps) {
  const [fullName, setFullName] = useState(user.fullName);
  const [phoneNumber, setPhoneNumber] = useState(user.phoneNumber ?? "");
  const [timezone, setTimezone] = useState(user.timezone);
  const [bio, setBio] = useState(user.bio ?? "");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const timezoneOptions = useMemo(() => {
    const all = getAllTimezoneOptions();
    return all.some((opt) => opt.value === timezone)
      ? all
      : [{ value: timezone, label: timezone }, ...all];
  }, [timezone]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const trimmedName = fullName.trim();
    if (trimmedName.length < 2) {
      setError("Họ và tên phải có ít nhất 2 ký tự.");
      return;
    }

    const normalizedPhone = phoneNumber.replace(/[\s\-().]/g, "").trim();
    if (normalizedPhone && !E164_REGEX.test(normalizedPhone)) {
      setError(
        "Số điện thoại phải theo chuẩn quốc tế E.164 (ví dụ: +84901234567)."
      );
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updateProfile({
        fullName: trimmedName,
        phoneNumber: normalizedPhone || null,
        timezone,
        bio: bio.trim() || null,
      });
      onUpdated(updated);
      setSuccess("Đã lưu thông tin cá nhân.");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể cập nhật thông tin cá nhân. Vui lòng thử lại.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2.5 border-b border-border/80 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-600">
          <UserIcon className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Thông tin cá nhân
          </h2>
          <p className="text-xs text-muted-foreground">
            Tên hiển thị, số điện thoại liên hệ và múi giờ làm việc mặc định.
          </p>
        </div>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor="profile-full-name"
              className="block text-xs font-semibold text-foreground"
            >
              Họ và tên
            </label>
            <input
              id="profile-full-name"
              type="text"
              required
              minLength={2}
              maxLength={100}
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="profile-phone"
              className="block text-xs font-semibold text-foreground"
            >
              Số điện thoại (E.164)
            </label>
            <input
              id="profile-phone"
              type="tel"
              placeholder="+84901234567"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="profile-timezone"
            className="block text-xs font-semibold text-foreground"
          >
            Múi giờ
          </label>
          <select
            id="profile-timezone"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
          >
            {timezoneOptions.map((tz) => (
              <option key={tz.value} value={tz.value}>
                {tz.label}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="profile-bio"
            className="block text-xs font-semibold text-foreground"
          >
            Giới thiệu ngắn
          </label>
          <textarea
            id="profile-bio"
            rows={3}
            maxLength={500}
            placeholder="Ví dụ: Điều phối viên hội thảo công nghệ quốc tế..."
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
          />
        </div>

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
            disabled={isSaving}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSaving ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang lưu...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Lưu thông tin</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
