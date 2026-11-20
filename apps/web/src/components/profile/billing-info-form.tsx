"use client";

import React, { useState } from "react";
import { Building2, CheckCircle2, Loader2, Save } from "lucide-react";
import { ApiError } from "@/lib/api-client";
import { type UserMe, updateBillingInfo } from "@/lib/user-api";

interface BillingInfoFormProps {
  user: UserMe;
  onUpdated: (nextUser: UserMe) => void;
}

const TAX_CODE_REGEX = /^(?:\d{10}|\d{13}|\d{10}-\d{3})$/;

export function BillingInfoForm({ user, onUpdated }: BillingInfoFormProps) {
  const [companyName, setCompanyName] = useState(user.companyName ?? "");
  const [taxCode, setTaxCode] = useState(user.taxCode ?? "");
  const [companyAddress, setCompanyAddress] = useState(
    user.companyAddress ?? ""
  );
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);

    const trimmedTaxCode = taxCode.trim();
    if (trimmedTaxCode && !TAX_CODE_REGEX.test(trimmedTaxCode)) {
      setError(
        "Mã số thuế phải gồm 10 hoặc 13 chữ số (ví dụ: 0101234567 hoặc 0101234567-001)."
      );
      return;
    }

    setIsSaving(true);
    try {
      const updated = await updateBillingInfo({
        companyName: companyName.trim() || null,
        taxCode: trimmedTaxCode || null,
        companyAddress: companyAddress.trim() || null,
      });
      onUpdated(updated);
      setSuccess("Đã lưu thông tin xuất hóa đơn VAT.");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Không thể lưu thông tin hóa đơn VAT. Vui lòng thử lại.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2.5 border-b border-border/80 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-600">
          <Building2 className="h-4 w-4" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-foreground">
            Thông tin doanh nghiệp &amp; Hóa đơn VAT
          </h2>
          <p className="text-xs text-muted-foreground">
            Tự động gắn vào biên lai thanh toán PDF khi nạp tiền hoặc gia hạn gói.
          </p>
        </div>
      </div>

      <form onSubmit={(e) => void handleSubmit(e)} className="mt-5 space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor="billing-company-name"
              className="block text-xs font-semibold text-foreground"
            >
              Tên công ty / Tổ chức
            </label>
            <input
              id="billing-company-name"
              type="text"
              maxLength={255}
              placeholder="Công ty Cổ phần VoiceBridge Việt Nam"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="billing-tax-code"
              className="block text-xs font-semibold text-foreground"
            >
              Mã số thuế
            </label>
            <input
              id="billing-tax-code"
              type="text"
              maxLength={64}
              placeholder="0101234567 hoặc 0101234567-001"
              value={taxCode}
              onChange={(e) => setTaxCode(e.target.value)}
              className="w-full rounded-xl border border-border bg-background px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors focus:border-indigo-600 focus:ring-2 focus:ring-indigo-600/15"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <label
            htmlFor="billing-company-address"
            className="block text-xs font-semibold text-foreground"
          >
            Địa chỉ xuất hóa đơn
          </label>
          <input
            id="billing-company-address"
            type="text"
            maxLength={512}
            placeholder="Số 123 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh"
            value={companyAddress}
            onChange={(e) => setCompanyAddress(e.target.value)}
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
                <span>Lưu thông tin VAT</span>
              </>
            )}
          </button>
        </div>
      </form>
    </section>
  );
}
