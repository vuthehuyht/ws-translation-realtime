"use client";

import React, { useState } from "react";
import { CheckCircle2, Clock, Download, FileText, Sparkles } from "lucide-react";
import { ProductPageShell } from "@/components/products/product-page-shell";
import { cn } from "@/lib/utils";

const TRANSCRIPT_LINES = [
  {
    id: "seg-1",
    time: "02:15",
    speaker: "Dr. Alex",
    source: "We adopted PostgreSQL 16 ACID transactions for our 3-bucket credit wallet.",
    vi: "Chúng tôi áp dụng transaction ACID trên PostgreSQL 16 cho ví Credit 3 ngăn.",
  },
  {
    id: "seg-2",
    time: "08:40",
    speaker: "Dr. Alex",
    source: "Azure AI Speech in Singapore handles Vietnamese Neural TTS with under 5ms network overhead.",
    vi: "Azure AI Speech tại Singapore xử lý giọng đọc Tiếng Việt Neural với độ trễ mạng dưới 5ms.",
  },
  {
    id: "seg-3",
    time: "18:10",
    speaker: "Minh Tran",
    source: "Let us finalize the Enterprise rollout checklist and load-test 1,000 listeners next week.",
    vi: "Hãy chốt checklist triển khai Enterprise và kiểm thử tải 1.000 người nghe vào tuần tới.",
  },
];

const TAKEAWAYS = [
  {
    segId: "seg-1",
    time: "02:15",
    topic: "Toàn vẹn tài chính với Ví Credit 3 ngăn",
    detail: "Trừ nguyên tử theo thứ tự Promo -> Plan -> Top-up trên PostgreSQL 16.",
  },
  {
    segId: "seg-2",
    time: "08:40",
    topic: "Multi-Provider TTS hỗ trợ Tiếng Việt",
    detail: "Kết hợp Amazon Polly Neural và Azure AI Speech (southeastasia) cho vi-VN.",
  },
  {
    segId: "seg-3",
    time: "18:10",
    topic: "Kế hoạch kiểm thử tải 1.000 người nghe",
    detail: "Xác nhận độ trễ fan-out AppSync Events < 50ms trước khi mở bán Enterprise.",
  },
];

const EXPORT_FORMATS = [
  { ext: ".TXT / .MD", plan: "PRO+", desc: "Biên bản họp đơn ngữ & song ngữ" },
  { ext: ".SRT / .VTT", plan: "BUSINESS+", desc: "Phụ đề video chuẩn mili-giây" },
  { ext: ".CSV", plan: "BUSINESS+", desc: "Bảng đối chiếu đa ngôn ngữ (UTF-8 BOM)" },
];

export default function TranscriptsAiSummaryProductPage() {
  const [activeTab, setActiveTab] = useState<"transcript" | "summary">("summary");
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  const handleJumpToSegment = (segId: string) => {
    setHighlightedId(segId);
    setActiveTab("transcript");
  };

  return (
    <ProductPageShell
      badge="Biên bản & Tóm tắt AI"
      title="Biên bản đa định dạng & Tóm tắt cuộc họp bằng AI"
      subtitle="Tự động đóng gói toàn bộ phiên dịch lên Amazon S3 (lưu 7/30/90/365 ngày theo gói) và tạo bản tóm tắt đa ngôn ngữ bằng Amazon Bedrock với cơ chế cache 0 Cr cho mọi lần xem lại."
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {EXPORT_FORMATS.map((fmt) => (
          <div
            key={fmt.ext}
            className="flex items-start justify-between rounded-2xl border border-border bg-card p-5 shadow-sm"
          >
            <div>
              <p className="text-sm font-bold text-foreground">{fmt.ext}</p>
              <p className="mt-1 text-xs text-muted-foreground">{fmt.desc}</p>
            </div>
            <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700">
              {fmt.plan}
            </span>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
          <div className="inline-flex rounded-xl border border-border bg-muted/50 p-1">
            <button
              type="button"
              onClick={() => setActiveTab("summary")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors",
                activeTab === "summary"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Sparkles className="h-3.5 w-3.5 text-indigo-600" />
              <span>Tóm tắt AI (Amazon Bedrock)</span>
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("transcript")}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors",
                activeTab === "transcript"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <FileText className="h-3.5 w-3.5 text-indigo-600" />
              <span>Toàn bộ Biên bản</span>
            </button>
          </div>

          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold text-emerald-700">
            <Download className="h-3.5 w-3.5" />
            <span>Tạo 1 lần (15–25 Cr) · Xem lại 0 Cr từ S3 Cache</span>
          </span>
        </div>

        {activeTab === "summary" ? (
          <div className="mt-5 space-y-5">
            <div className="rounded-xl bg-indigo-50/60 p-4">
              <p className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                Tổng quan cốt lõi (Executive Overview)
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-foreground">
                Phiên họp chốt kiến trúc ví Credit 3 ngăn trên PostgreSQL 16, tích hợp
                Azure AI Speech Singapore cho giọng Tiếng Việt Neural và kế hoạch kiểm
                thử tải 1.000 người nghe cho gói Enterprise.
              </p>
            </div>

            <div className="space-y-2.5">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Các luận điểm chính (bấm mốc thời gian để nhảy tới câu gốc)
              </p>
              {TAKEAWAYS.map((item) => (
                <div
                  key={item.segId}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-background p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    <p className="text-sm font-semibold text-foreground">{item.topic}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{item.detail}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleJumpToSegment(item.segId)}
                    className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-bold text-indigo-700 transition-colors hover:bg-indigo-100"
                  >
                    <Clock className="h-3.5 w-3.5" />
                    <span>[{item.time}] Xem câu gốc</span>
                  </button>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                Việc cần làm (Action Items)
              </p>
              <ul className="space-y-1.5 text-xs text-foreground">
                <li className="inline-flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span>Hoàn thiện checklist triển khai Enterprise và chạy load test 1.000 listeners.</span>
                </li>
              </ul>
            </div>
          </div>
        ) : (
          <div className="mt-5 space-y-3">
            {TRANSCRIPT_LINES.map((line) => (
              <div
                key={line.id}
                className={cn(
                  "rounded-xl border p-4 transition-colors",
                  highlightedId === line.id
                    ? "border-indigo-500 bg-indigo-50/60"
                    : "border-border bg-background"
                )}
              >
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span className="font-semibold text-foreground">{line.speaker}</span>
                  <span>[{line.time}]</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{line.source}</p>
                <p className="mt-1 text-sm font-semibold text-foreground">{line.vi}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </ProductPageShell>
  );
}
