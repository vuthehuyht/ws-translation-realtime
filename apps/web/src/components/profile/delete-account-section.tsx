"use client";

import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, Loader2, Trash2, X } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import { cancelPendingRefreshes } from "@/lib/auth-refresh";
import { deleteAccount } from "@/lib/user-api";

interface DeleteAccountSectionProps {
  email: string;
  walletBalance?: string | null;
  onAccountDeleted: () => void;
}

const REQUIRED_CONFIRMATION = "DELETE";

export function DeleteAccountSection({
  email,
  walletBalance,
  onAccountDeleted,
}: DeleteAccountSectionProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [confirmationText, setConfirmationText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // A ref closes the same-tick double-submit window that React state alone leaves open.
  const submittingRef = useRef(false);
  const triggerButtonRef = useRef<HTMLButtonElement>(null);
  const confirmationInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isModalOpen) {
      return;
    }
    confirmationInputRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !submittingRef.current) {
        setIsModalOpen(false);
        setError(null);
        triggerButtonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  const openModal = () => {
    setConfirmationText("");
    setError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    if (submittingRef.current) {
      return;
    }
    setIsModalOpen(false);
    setError(null);
    triggerButtonRef.current?.focus();
  };

  const isConfirmed = confirmationText.trim() === REQUIRED_CONFIRMATION;

  const handleConfirmDelete = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    if (!isConfirmed || submittingRef.current) {
      return;
    }

    submittingRef.current = true;
    setError(null);
    setIsSubmitting(true);
    // Cancel any in-flight proactive refresh so it cannot race and overwrite the post-delete redirect.
    cancelPendingRefreshes();
    try {
      await deleteAccount({ confirmation: REQUIRED_CONFIRMATION });
      setIsModalOpen(false);
      onAccountDeleted();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          setError(
            "Không thể xóa tài khoản khi bạn đang có phòng dịch hoạt động. Vui lòng kết thúc tất cả phòng đang mở trước."
          );
        } else {
          setError(err.message);
        }
      } else {
        setError("Không thể xóa tài khoản lúc này. Vui lòng thử lại sau.");
      }
    } finally {
      submittingRef.current = false;
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <section className="rounded-2xl border border-destructive/30 bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div className="space-y-1">
              <h2 className="text-base font-semibold text-destructive">
                Vùng nguy hiểm — Xóa tài khoản (GDPR/PDPA)
              </h2>
              <p className="text-xs leading-relaxed text-muted-foreground">
                Xóa vĩnh viễn tài khoản{" "}
                <span className="font-semibold text-foreground">{email}</span>,
                thu hồi toàn bộ phiên đăng nhập và ẩn danh dữ liệu cá nhân. Sổ
                cái kế toán giao dịch được lưu ẩn danh theo quy định thuế.
              </p>
              <ul className="list-disc space-y-1 pl-4 pt-1 text-xs text-muted-foreground">
                <li>
                  Hành động này{" "}
                  <span className="font-semibold text-foreground">
                    không thể hoàn tác
                  </span>
                  {walletBalance
                    ? ` và số dư ví hiện tại (${walletBalance}) sẽ không thể tiếp tục sử dụng.`
                    : "."}
                </li>
                <li>
                  Sau khi xóa, bạn cần chờ{" "}
                  <span className="font-semibold text-foreground">7 ngày</span>{" "}
                  mới có thể tạo lại tài khoản mới bằng email này.
                </li>
                <li>
                  Tài khoản đăng ký lại bằng email cũ sẽ{" "}
                  <span className="font-semibold text-foreground">
                    không nhận các quyền lợi/ưu đãi chào mừng dành cho tài khoản
                    mới
                  </span>
                  .
                </li>
              </ul>
            </div>
          </div>

          <button
            ref={triggerButtonRef}
            type="button"
            onClick={openModal}
            className="inline-flex shrink-0 items-center justify-center gap-2 self-start rounded-xl border border-destructive/40 bg-destructive/10 px-4 py-2.5 text-xs font-semibold text-destructive transition-colors hover:bg-destructive hover:text-white"
          >
            <Trash2 className="h-4 w-4" />
            <span>Xóa tài khoản</span>
          </button>
        </div>
      </section>

      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-account-modal-title"
          aria-describedby="delete-account-modal-description"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              closeModal();
            }
          }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm"
        >
          <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl">
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-destructive/10 text-destructive">
                  <AlertTriangle className="h-5 w-5" />
                </div>
                <h3
                  id="delete-account-modal-title"
                  className="text-base font-bold text-foreground"
                >
                  Xác nhận xóa tài khoản vĩnh viễn
                </h3>
              </div>
              <button
                type="button"
                aria-label="Đóng hộp thoại xóa tài khoản"
                onClick={closeModal}
                disabled={isSubmitting}
                className="rounded-lg p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:opacity-50"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div
              id="delete-account-modal-description"
              className="mt-4 space-y-2 rounded-xl border border-destructive/20 bg-destructive/5 p-3.5 text-xs leading-relaxed text-muted-foreground"
            >
              <p>
                Tài khoản{" "}
                <span className="font-semibold text-foreground">{email}</span>{" "}
                sẽ bị xóa khỏi hệ thống xác thực và ẩn danh hoàn toàn dữ liệu cá
                nhân.
              </p>
              <p>
                Bạn phải chờ <strong className="text-foreground">7 ngày</strong>{" "}
                mới có thể đăng ký lại từ email này, và tài khoản mới sẽ{" "}
                <strong className="text-foreground">
                  không nhận quyền lợi/khuyến mãi tài khoản mới
                </strong>
                .
              </p>
            </div>

            <form
              onSubmit={(e) => void handleConfirmDelete(e)}
              className="mt-4 space-y-4"
            >
              <div className="space-y-1.5">
                <label
                  htmlFor="delete-account-confirmation"
                  className="block text-xs font-semibold text-foreground"
                >
                  Nhập{" "}
                  <span className="rounded bg-muted px-1.5 py-0.5 font-mono text-destructive">
                    {REQUIRED_CONFIRMATION}
                  </span>{" "}
                  để xác nhận xóa tài khoản
                </label>
                <input
                  ref={confirmationInputRef}
                  id="delete-account-confirmation"
                  type="text"
                  autoComplete="off"
                  placeholder={REQUIRED_CONFIRMATION}
                  value={confirmationText}
                  onChange={(e) => setConfirmationText(e.target.value)}
                  disabled={isSubmitting}
                  className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-destructive focus:ring-2 focus:ring-destructive/15"
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

              <div className="flex items-center justify-end gap-2.5 pt-1">
                <button
                  type="button"
                  onClick={closeModal}
                  disabled={isSubmitting}
                  className="rounded-xl border border-border bg-background px-4 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted disabled:opacity-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={!isConfirmed || isSubmitting}
                  className="inline-flex items-center gap-2 rounded-xl bg-destructive px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Đang xóa tài khoản...</span>
                    </>
                  ) : (
                    <>
                      <Trash2 className="h-3.5 w-3.5" />
                      <span>Xóa vĩnh viễn tài khoản</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
