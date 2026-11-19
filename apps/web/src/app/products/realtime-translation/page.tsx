"use client";

import React, { useState } from "react";
import { Mic, Radio, Users, Volume2, VolumeX } from "lucide-react";
import { ProductPageShell } from "@/components/products/product-page-shell";
import { cn } from "@/lib/utils";

type ModeKey = "BROADCAST" | "1_ON_1";
type TargetLang = "vi-VN" | "en-US" | "ja-JP" | "ko-KR";

const LANG_OPTIONS: { code: TargetLang; label: string; ttsProvider: string }[] = [
  { code: "vi-VN", label: "Tiếng Việt (VI)", ttsProvider: "Azure Neural (HoaiMy)" },
  { code: "en-US", label: "English (EN)", ttsProvider: "Amazon Polly Neural" },
  { code: "ja-JP", label: "日本語 (JA)", ttsProvider: "Amazon Polly Neural" },
  { code: "ko-KR", label: "한국어 (KO)", ttsProvider: "Amazon Polly Neural" },
];

const SAMPLE_SEGMENTS: Record<
  ModeKey,
  { speaker: string; time: string; source: string; translations: Record<TargetLang, string> }[]
> = {
  BROADCAST: [
    {
      speaker: "Dr. Alex (Keynote)",
      time: "00:12",
      source: "Welcome everyone to our 2026 APAC Cloud Architecture Summit.",
      translations: {
        "vi-VN": "Chào mừng mọi người đến với Hội nghị Kiến trúc Đám mây APAC 2026.",
        "en-US": "Welcome everyone to our 2026 APAC Cloud Architecture Summit.",
        "ja-JP": "2026年APACクラウドアーキテクチャサミットへようこそ。",
        "ko-KR": "2026 APAC 클라우드 아키텍처 서밋에 오신 것을 환영합니다.",
      },
    },
    {
      speaker: "Dr. Alex (Keynote)",
      time: "00:19",
      source: "Our single-AZ Redis ring buffer guarantees zero dropped words during failover.",
      translations: {
        "vi-VN": "Bộ đệm vòng Redis Single-AZ đảm bảo không mất từ nào khi chuyển đổi dự phòng.",
        "en-US": "Our single-AZ Redis ring buffer guarantees zero dropped words during failover.",
        "ja-JP": "シングルAZのRedisリングバッファにより、フェイルオーバー時も単語の欠落を防ぎます。",
        "ko-KR": "싱글 AZ Redis 링 버퍼는 장애 조치 중 단어 손실이 없음을 보장합니다.",
      },
    },
  ],
  "1_ON_1": [
    {
      speaker: "Host (Tiếng Việt)",
      time: "00:05",
      source: "Chào anh Tanaka, chúng ta cùng chốt tiến độ giao hàng quý 4 nhé.",
      translations: {
        "vi-VN": "Chào anh Tanaka, chúng ta cùng chốt tiến độ giao hàng quý 4 nhé.",
        "en-US": "Hello Mr. Tanaka, let's finalize our Q4 delivery timeline together.",
        "ja-JP": "田中さん、こんにちは。第4四半期の納品スケジュールを確定しましょう。",
        "ko-KR": "다나카 씨, 안녕하세요. 4분기 납품 일정을 함께 확정합시다.",
      },
    },
    {
      speaker: "Mr. Tanaka (日本語)",
      time: "00:11",
      source: "承知しました。来週の火曜日までに最終仕様書をお送りします。",
      translations: {
        "vi-VN": "Tôi đã rõ. Chúng tôi sẽ gửi tài liệu đặc tả cuối cùng trước thứ Ba tuần tới.",
        "en-US": "Understood. We will send the final specification document by next Tuesday.",
        "ja-JP": "承知しました。来週の火曜日までに最終仕様書をお送りします。",
        "ko-KR": "알겠습니다. 다음 주 화요일까지 최종 사양서를 보내드리겠습니다.",
      },
    },
  ],
};

export default function RealtimeTranslationProductPage() {
  const [mode, setMode] = useState<ModeKey>("BROADCAST");
  const [selectedLang, setSelectedLang] = useState<TargetLang>("vi-VN");
  const [ttsEnabled, setTtsEnabled] = useState(true);

  const activeLangMeta =
    LANG_OPTIONS.find((item) => item.code === selectedLang) ?? LANG_OPTIONS[0];
  const segments = SAMPLE_SEGMENTS[mode];

  return (
    <ProductPageShell
      badge="Phiên dịch trực tiếp"
      title="Phiên dịch hội thoại 1-on-1 & Hội thảo đa ngôn ngữ"
      subtitle="Chuyển đổi mượt mà giữa đàm thoại song công 2 chiều (1-on-1) và phát sóng hội trường lên đến 1.000 người nghe đồng thời với độ trễ phụ đề dưới 500ms."
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { label: "Phụ đề tạm thời (Partial)", value: "< 500ms", desc: "Chạy chữ trực tiếp theo nhịp nói" },
          { label: "Dịch song song 10 ngôn ngữ", value: "< 150ms", desc: "Amazon Translate asyncio.gather" },
          { label: "Giọng đọc Neural TTS", value: "< 1.2s", desc: "Polly Neural + Azure Speech (vi-VN)" },
        ].map((metric) => (
          <div
            key={metric.label}
            className="rounded-2xl border border-border bg-card p-5 shadow-sm"
          >
            <p className="text-xs font-medium text-muted-foreground">{metric.label}</p>
            <p className="mt-1 text-2xl font-bold text-indigo-600">{metric.value}</p>
            <p className="mt-1 text-xs text-muted-foreground">{metric.desc}</p>
          </div>
        ))}
      </div>

      <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="inline-flex rounded-xl border border-border bg-muted/50 p-1">
            <button
              type="button"
              onClick={() => setMode("BROADCAST")}
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors",
                mode === "BROADCAST"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Radio className="h-3.5 w-3.5 text-indigo-600" />
              <span>Broadcast (1-to-1.000)</span>
            </button>
            <button
              type="button"
              onClick={() => setMode("1_ON_1")}
              className={cn(
                "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors",
                mode === "1_ON_1"
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <Users className="h-3.5 w-3.5 text-indigo-600" />
              <span>1-on-1 Song công</span>
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {LANG_OPTIONS.map((lang) => (
              <button
                key={lang.code}
                type="button"
                onClick={() => setSelectedLang(lang.code)}
                className={cn(
                  "rounded-lg border px-2.5 py-1.5 text-xs font-semibold transition-colors",
                  selectedLang === lang.code
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                    : "border-border bg-background text-muted-foreground hover:text-foreground"
                )}
              >
                {lang.label}
              </button>
            ))}

            <button
              type="button"
              onClick={() => setTtsEnabled((prev) => !prev)}
              className={cn(
                "inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors",
                ttsEnabled
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-700"
                  : "border-border bg-background text-muted-foreground"
              )}
            >
              {ttsEnabled ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
              <span>{ttsEnabled ? "Loa TTS: BẬT" : "Chỉ phụ đề (0 Cr TTS)"}</span>
            </button>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-4 py-2.5 text-xs">
            <span className="inline-flex items-center gap-2 font-semibold text-emerald-700">
              <Mic className="h-3.5 w-3.5" />
              <span>Silero VAD đang hoạt động · Tự động lọc khoảng lặng</span>
            </span>
            <span className="text-muted-foreground">
              {ttsEnabled
                ? `Kênh âm thanh: ${activeLangMeta.ttsProvider}`
                : "Demand-Driven TTS tắt -> Tiết kiệm 100% chi phí giọng đọc"}
            </span>
          </div>

          {segments.map((seg) => (
            <div
              key={seg.time}
              className="rounded-xl border border-border/80 bg-background p-4 space-y-1.5"
            >
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span className="font-semibold text-foreground">{seg.speaker}</span>
                <span>[{seg.time}] · Final</span>
              </div>
              <p className="text-xs text-muted-foreground">{seg.source}</p>
              <p className="text-sm font-semibold text-indigo-700">
                {seg.translations[selectedLang]}
              </p>
            </div>
          ))}
        </div>
      </div>
    </ProductPageShell>
  );
}
