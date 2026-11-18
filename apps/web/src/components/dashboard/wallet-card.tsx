"use client";

import React, { useEffect, useRef, useState } from "react";
import { AlertTriangle, Plus, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface WalletCardProps {
  balance: number;
  autoTopUp: boolean;
  onToggleAutoTopUp: (nextValue: boolean) => void;
  onTopUpConfirm: (amountUsd: number, method: "stripe" | "vietqr") => void;
  onViewBilling?: () => void;
}

const TOP_UP_PACKAGES = [5, 10, 25, 50];
const USD_TO_VND_RATE = 25500;

export function WalletCard({
  balance,
  autoTopUp,
  onToggleAutoTopUp,
  onTopUpConfirm,
  onViewBilling,
}: WalletCardProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [paymentTab, setPaymentTab] = useState<"stripe" | "vietqr">("stripe");
  const [selectedAmount, setSelectedAmount] = useState<number>(10);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const triggerButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (!isModalOpen) {
      return;
    }

    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsModalOpen(false);
        triggerButtonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  const closeModal = () => {
    setIsModalOpen(false);
    triggerButtonRef.current?.focus();
  };

  const estimatedMinutes = Math.max(0, Math.floor(balance / 0.15));
  const isLowBalance = balance < 1.0;

  const handleConfirm = () => {
    onTopUpConfirm(selectedAmount, paymentTab);
    closeModal();
  };

  return (
    <>
      <section className="flex flex-col justify-between overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        <div>
          <div className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-slate-900 p-5 text-white">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-indigo-200">
                Số dư ví khả dụng
              </span>
              <span className="rounded-md bg-white/10 px-2 py-0.5 text-[11px] font-medium text-indigo-100">
                USD Wallet
              </span>
            </div>

            <div className="mt-3 flex items-baseline gap-2">
              <span
                data-testid="wallet-balance"
                className="text-3xl font-bold tracking-tight tabular-nums"
              >
                ${balance.toFixed(2)}
              </span>
              <span className="text-xs font-medium text-indigo-200">USD</span>
            </div>

            <p className="mt-1.5 text-xs text-indigo-100/90">
              Ước tính ~{estimatedMinutes} phút Broadcast (100 người nghe)
            </p>
          </div>

          <div className="space-y-4 p-5">
            {isLowBalance && (
              <div
                role="alert"
                className="flex items-start gap-2.5 rounded-lg border border-amber-500/30 bg-amber-50 p-3 text-xs text-amber-800"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                <div>
                  <p className="font-semibold">Số dư dưới $1.00</p>
                  <p className="mt-0.5 text-amber-700">
                    Vui lòng nạp thêm để tránh gián đoạn khi đang phát trực tiếp.
                  </p>
                </div>
              </div>
            )}

            <button
              ref={triggerButtonRef}
              type="button"
              onClick={() => setIsModalOpen(true)}
              className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-4 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition-all hover:opacity-95"
            >
              <Plus className="h-4 w-4" />
              <span>Nạp tiền nhanh (Stripe / VietQR)</span>
            </button>

            <div className="flex items-center justify-between gap-4 border-t border-border/60 pt-4">
              <div>
                <p className="text-xs font-semibold text-foreground">Auto Top-up</p>
                <p className="text-[11px] text-muted-foreground">
                  Tự động nạp $10.00 khi số dư &lt; $1.00
                </p>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={autoTopUp}
                aria-label="Auto Top-up"
                onClick={() => onToggleAutoTopUp(!autoTopUp)}
                className={cn(
                  "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors",
                  autoTopUp ? "bg-indigo-600" : "bg-slate-200"
                )}
              >
                <span
                  className={cn(
                    "pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition",
                    autoTopUp ? "translate-x-5" : "translate-x-0"
                  )}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-border/60 bg-muted/40 px-5 py-3 text-xs">
          <span className="text-muted-foreground">Cập nhật theo chu kỳ 10s</span>
          <button
            type="button"
            onClick={onViewBilling}
            className="font-semibold text-primary hover:underline"
          >
            Lịch sử giao dịch →
          </button>
        </div>
      </section>

      {isModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Nạp tiền vào Ví Host"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              closeModal();
            }
          }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
        >
          <div className="w-full max-w-md overflow-hidden rounded-2xl border border-border bg-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-border/70 px-5 py-4">
              <h3 className="text-sm font-bold text-foreground">
                Nạp tiền vào Ví Host
              </h3>
              <button
                ref={closeButtonRef}
                type="button"
                aria-label="Đóng modal nạp tiền"
                onClick={closeModal}
                className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-4 p-5">
              <div className="grid grid-cols-2 gap-2 rounded-lg bg-muted p-1">
                <button
                  type="button"
                  onClick={() => setPaymentTab("stripe")}
                  className={cn(
                    "rounded-md py-1.5 text-xs font-semibold transition-all",
                    paymentTab === "stripe"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  Thẻ quốc tế (Stripe)
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentTab("vietqr")}
                  className={cn(
                    "rounded-md py-1.5 text-xs font-semibold transition-all",
                    paymentTab === "vietqr"
                      ? "bg-card text-foreground shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  Chuyển khoản VietQR
                </button>
              </div>

              <div>
                <p className="mb-2 text-xs font-semibold text-foreground">
                  Chọn gói nạp (USD)
                </p>
                <div className="grid grid-cols-4 gap-2">
                  {TOP_UP_PACKAGES.map((amount) => (
                    <button
                      key={amount}
                      type="button"
                      onClick={() => setSelectedAmount(amount)}
                      className={cn(
                        "rounded-lg py-2 text-xs font-bold transition-all",
                        selectedAmount === amount
                          ? "border-2 border-indigo-600 bg-indigo-50 text-indigo-700"
                          : "border border-border text-foreground hover:border-indigo-400"
                      )}
                    >
                      ${amount}
                    </button>
                  ))}
                </div>
              </div>

              {paymentTab === "stripe" ? (
                <div className="space-y-1 rounded-xl border border-border bg-muted/50 p-3.5 text-xs text-muted-foreground">
                  <p className="font-semibold text-foreground">
                    Thanh toán bảo mật qua Stripe Checkout
                  </p>
                  <p>
                    Số tiền{" "}
                    <span className="font-bold text-primary">
                      ${selectedAmount.toFixed(2)} USD
                    </span>{" "}
                    sẽ được cộng vào ví ngay sau khi xác nhận.
                  </p>
                </div>
              ) : (
                <div className="space-y-2 rounded-xl border border-border bg-muted/50 p-4 text-center">
                  <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-lg border border-dashed border-indigo-300 bg-card font-mono text-[11px] text-indigo-600">
                    [ VietQR Preview ]
                  </div>
                  <p className="text-xs font-semibold text-foreground">
                    Quy đổi:{" "}
                    <span className="text-primary">
                      {(selectedAmount * USD_TO_VND_RATE).toLocaleString("en-US")}{" "}
                      VND
                    </span>
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Quét mã bằng app ngân hàng, ví tự động cộng tiền sau 3–5 giây.
                  </p>
                </div>
              )}

              <button
                type="button"
                onClick={handleConfirm}
                className="h-11 w-full rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition-all hover:opacity-95"
              >
                Xác nhận nạp ${selectedAmount.toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
