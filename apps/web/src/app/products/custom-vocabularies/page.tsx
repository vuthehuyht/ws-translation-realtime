"use client";

import React, { useState } from "react";
import { BookOpen, CheckCircle2, Sparkles, Upload } from "lucide-react";
import { ProductPageShell } from "@/components/products/product-page-shell";
import { cn } from "@/lib/utils";

type DomainKey = "cloud" | "medical" | "finance";

const DOMAIN_EXAMPLES: Record<
  DomainKey,
  {
    name: string;
    terms: string[];
    before: string;
    after: string;
  }
> = {
  cloud: {
    name: "Công nghệ Cloud & AWS",
    terms: ["ElastiCache", "AppSync Events", "Fargate", "uvloop", "VoiceBridge AI"],
    before:
      "Hệ thống dùng Elastic Cash và App Sink trên pha ghết để truyền âm thanh qua Voice Brick.",
    after:
      "Hệ thống dùng ElastiCache và AppSync Events trên Fargate để truyền âm thanh qua VoiceBridge AI.",
  },
  medical: {
    name: "Y khoa & Dược phẩm",
    terms: ["Metformin", "Atorvastatin", "Echocardiography", "HbA1c", "MRI 3 Tesla"],
    before:
      "Bệnh nhân cần đo chỉ số hát bê a một xê và làm siêu âm tim ê cô trước khi dùng mét pho min.",
    after:
      "Bệnh nhân cần đo chỉ số HbA1c và làm siêu âm tim Echocardiography trước khi dùng Metformin.",
  },
  finance: {
    name: "Tài chính & Ngân hàng",
    terms: ["NAPAS EMVCo", "VietQR", "EBITDA", "PCI-DSS", "Off-session Charge"],
    before:
      "Cổng thanh toán tuân thủ pi xi ai đi ét ét và sinh mã việc quy rờ theo chuẩn na phát.",
    after:
      "Cổng thanh toán tuân thủ PCI-DSS và sinh mã VietQR theo chuẩn NAPAS EMVCo.",
  },
};

export default function CustomVocabulariesProductPage() {
  const [domain, setDomain] = useState<DomainKey>("cloud");
  const active = DOMAIN_EXAMPLES[domain];

  return (
    <ProductPageShell
      badge="Từ điển thuật ngữ"
      title="Chuẩn hóa tên thương hiệu & thuật ngữ chuyên ngành"
      subtitle="Nâng cao độ chính xác nhận diện tên thương hiệu, thuật ngữ kỹ thuật, y khoa, tài chính và giữ nguyên bản dịch chuẩn cho toàn bộ sự kiện."
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { plan: "PRO", quota: "2 bộ từ điển · 50 từ/bộ", note: "Phù hợp nhóm dự án nhỏ" },
          { plan: "BUSINESS", quota: "10 bộ từ điển · 256 từ/bộ", note: "Hội thảo & doanh nghiệp" },
          { plan: "ENTERPRISE", quota: "Không giới hạn + Import CSV", note: "Đồng bộ tự động AWS" },
        ].map((tier) => (
          <div
            key={tier.plan}
            className="rounded-2xl border border-border bg-card p-5 shadow-sm"
          >
            <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700">
              {tier.plan}
            </span>
            <p className="mt-2 text-sm font-bold text-foreground">{tier.quota}</p>
            <p className="mt-1 text-xs text-muted-foreground">{tier.note}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
          <div className="flex flex-wrap items-center gap-2">
            {(Object.keys(DOMAIN_EXAMPLES) as DomainKey[]).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setDomain(key)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors",
                  domain === key
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                    : "border-border bg-background text-muted-foreground hover:text-foreground"
                )}
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span>{DOMAIN_EXAMPLES[key].name}</span>
              </button>
            ))}
          </div>

          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-700">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>AWS Sync Status: READY</span>
          </span>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground">
            Từ khóa trong bộ &ldquo;{active.name}&rdquo;:
          </p>
          <div className="flex flex-wrap gap-2">
            {active.terms.map((term) => (
              <span
                key={term}
                className="rounded-lg border border-indigo-200 bg-indigo-50/70 px-2.5 py-1 text-xs font-semibold text-indigo-700"
              >
                {term}
              </span>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4">
            <p className="text-[11px] font-bold uppercase tracking-wider text-rose-700">
              Trước khi gắn Từ điển (STT mặc định)
            </p>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">
              {active.before}
            </p>
          </div>

          <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
            <p className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-emerald-700">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Sau khi đồng bộ Custom Vocabulary</span>
            </p>
            <p className="mt-2 text-sm font-medium leading-relaxed text-foreground">
              {active.after}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-4 py-3 text-xs text-muted-foreground">
          <Upload className="h-4 w-4 shrink-0 text-indigo-600" />
          <span>
            Hỗ trợ tải lên file <strong>.CSV / .TXT</strong> (tối đa 256 thuật ngữ/bộ)
            và chọn nhanh ngay khi khởi tạo phòng dịch.
          </span>
        </div>
      </div>
    </ProductPageShell>
  );
}
