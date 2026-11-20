"use client";

import React, { useRef, useState } from "react";
import { Camera, CheckCircle2, Loader2, Upload } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import {
  ALLOWED_AVATAR_TYPES,
  MAX_AVATAR_BYTES,
  confirmAvatarUpload,
  requestAvatarUploadUrl,
  uploadAvatarBinary,
} from "@/lib/user-api";

interface AvatarUploaderProps {
  fullName: string;
  email: string;
  avatarUrl: string | null;
  onAvatarUpdated: (nextAvatarUrl: string) => void;
}

export function AvatarUploader({
  fullName,
  email,
  avatarUrl,
  onAvatarUpdated,
}: AvatarUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const initial = (fullName.trim() || email || "H").charAt(0).toUpperCase();

  const handleFileChange = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = event.target.files?.[0];
    // Reset input value so selecting the same file again still triggers onChange.
    event.target.value = "";
    if (!file) {
      return;
    }

    setError(null);
    setSuccess(null);

    const allowedTypes: readonly string[] = ALLOWED_AVATAR_TYPES;
    if (!allowedTypes.includes(file.type)) {
      setError("Chỉ hỗ trợ ảnh định dạng JPG, PNG hoặc WebP.");
      return;
    }

    if (file.size <= 0 || file.size > MAX_AVATAR_BYTES) {
      setError("Dung lượng ảnh đại diện không được vượt quá 2MB.");
      return;
    }

    setIsUploading(true);
    try {
      const presigned = await requestAvatarUploadUrl({
        fileName: file.name,
        fileType: file.type as (typeof ALLOWED_AVATAR_TYPES)[number],
        fileSizeBytes: file.size,
      });
      await uploadAvatarBinary(presigned.uploadUrl, file);
      const confirmed = await confirmAvatarUpload(presigned.s3Key);
      onAvatarUpdated(confirmed.avatarUrl);
      setSuccess("Đã cập nhật ảnh đại diện thành công.");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể tải ảnh đại diện. Vui lòng thử lại.");
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <div className="relative h-20 w-20 shrink-0 overflow-hidden rounded-full border-2 border-indigo-600/20 bg-indigo-600/10">
            {avatarUrl ? (
              /* eslint-disable-next-line @next/next/no-img-element */
              <img
                src={avatarUrl}
                alt={fullName || email}
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="flex h-full w-full items-center justify-center text-2xl font-bold text-indigo-600">
                {initial}
              </span>
            )}
            <button
              type="button"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
              aria-label="Chọn ảnh đại diện mới"
              className="absolute inset-0 flex items-center justify-center bg-slate-900/45 text-white opacity-0 transition-opacity hover:opacity-100 focus-visible:opacity-100 disabled:cursor-not-allowed"
            >
              <Camera className="h-5 w-5" />
            </button>
          </div>

          <div>
            <h2 className="text-base font-semibold text-foreground">
              Ảnh đại diện
            </h2>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Hỗ trợ JPG, PNG, WebP. Dung lượng tối đa 2MB.
            </p>
            <p className="mt-1 text-xs font-medium text-muted-foreground">
              {email}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            data-testid="avatar-file-input"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => void handleFileChange(e)}
            className="hidden"
          />
          <button
            type="button"
            disabled={isUploading}
            onClick={() => fileInputRef.current?.click()}
            className="inline-flex items-center gap-2 rounded-xl border border-border bg-background px-4 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isUploading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Đang tải lên...</span>
              </>
            ) : (
              <>
                <Upload className="h-4 w-4" />
                <span>Tải ảnh mới</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <p
          role="alert"
          className="mt-4 rounded-xl bg-destructive/10 px-3.5 py-2.5 text-xs font-medium text-destructive"
        >
          {error}
        </p>
      )}
      {success && (
        <p
          role="status"
          className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 px-3.5 py-2.5 text-xs font-medium text-emerald-700"
        >
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{success}</span>
        </p>
      )}
    </section>
  );
}
