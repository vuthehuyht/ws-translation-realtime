import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  AudioWaveform,
  BookOpen,
  CheckCircle2,
  Coins,
  FileText,
  Globe2,
  Mic,
  QrCode,
  Radio,
  ShieldCheck,
  Sparkles,
  Volume2,
} from "lucide-react";

export const metadata: Metadata = {
  title: "VoiceBridge AI — Dịch giọng nói thời gian thực đa ngôn ngữ",
  description:
    "Nền tảng dịch giọng nói Speech-to-Speech & Speech-to-Text dưới 500ms cho 1-on-1 và hội thảo Broadcast lên đến 1.000 người nghe, tính cước minh bạch theo từng giây.",
};

const CAPABILITIES = [
  {
    href: "/products/realtime-translation",
    icon: Radio,
    badge: "Phiên dịch trực tiếp",
    title: "Hội thoại 1-on-1 & Hội thảo 1.000 người",
    desc: "Dịch song song 10 ngôn ngữ với Amazon Transcribe, Translate, Polly Neural và giọng Tiếng Việt Azure Neural.",
  },
  {
    href: "/pricing",
    icon: Coins,
    badge: "Bảng giá & Gói cước",
    title: "4 Gói cố định, trừ Credit theo từng giây",
    desc: "Quy đổi minh bạch 1 USD = 100 Credits, trừ theo thứ tự Promo -> Gói tháng -> Top-up không hết hạn.",
  },
  {
    href: "/products/transcripts-ai-summary",
    icon: FileText,
    badge: "Biên bản & Tóm tắt AI",
    title: "Xuất phụ đề đa định dạng & Tóm tắt thông minh",
    desc: "Tự động đóng gói .TXT, .SRT, .VTT, .CSV lên S3 và tạo bản tóm tắt đa ngôn ngữ kèm mốc thời gian.",
  },
  {
    href: "/products/custom-vocabularies",
    icon: BookOpen,
    badge: "Từ điển thuật ngữ",
    title: "Chuẩn hóa tên thương hiệu & từ chuyên ngành",
    desc: "Đồng bộ danh sách thuật ngữ kỹ thuật, y khoa, tài chính trực tiếp sang Transcribe & Translate.",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    icon: Mic,
    title: "Tạo phòng & Mic Check (0 Cr)",
    desc: "Chọn chế độ 1-on-1 hoặc Broadcast, ngôn ngữ nguồn/đích và kiểm tra sóng âm micro trước khi bấm bắt đầu.",
  },
  {
    step: "02",
    icon: QrCode,
    title: "Chiếu mã QR cho người nghe",
    desc: "Thính giả quét QR bằng điện thoại, không cần đăng nhập, tự chọn ngôn ngữ phụ đề và bật/tắt giọng đọc AI.",
  },
  {
    step: "03",
    icon: Sparkles,
    title: "Dịch trực tiếp & Tóm tắt AI",
    desc: "Phụ đề chạy mượt < 500ms; kết thúc phòng tự động xuất biên bản S3 và tạo bản tóm tắt AI đa ngôn ngữ.",
  },
];

const PLAN_HIGHLIGHTS = [
  { name: "Free", price: "$0", credits: "200 Cr dùng thử", note: "1-on-1 · 1 ngôn ngữ · 2 người" },
  { name: "Pro", price: "$19/th", credits: "1.800 Cr/tháng", note: "Broadcast · 3 ngôn ngữ · 100 người", popular: true },
  { name: "Business", price: "$59/th", credits: "6.000 Cr/tháng", note: "6 ngôn ngữ · 300 người · Auto Top-up" },
  { name: "Enterprise", price: "$199/th", credits: "21.000 Cr/tháng", note: "10 ngôn ngữ · 1.000 người · White-label" },
];

export default function HomePage() {
  return (
    <div className="flex-1 bg-slate-50/70">
      {/* Top Navigation */}
      <header className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm shadow-indigo-600/25">
              <AudioWaveform className="h-5 w-5" />
            </span>
            <span className="text-sm font-bold tracking-tight text-foreground">
              VoiceBridge AI
            </span>
          </Link>

          <div className="flex items-center gap-2">
            <Link
              href="/login"
              className="rounded-lg px-3.5 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-muted"
            >
              Đăng nhập
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm shadow-indigo-600/25 transition-colors hover:bg-indigo-700"
            >
              <span>Dùng thử miễn phí</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </header>

      <main>
        {/* Hero Section */}
        <section className="mx-auto max-w-7xl px-4 pb-16 pt-12 sm:px-6 sm:pt-16 lg:px-8">
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12">
            <div className="space-y-6 lg:col-span-6">
              <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3.5 py-1.5 text-xs font-semibold text-emerald-700">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
                <span>AWS ap-southeast-1 · Độ trễ phụ đề &lt; 500ms</span>
              </div>

              <h1 className="text-3xl font-extrabold tracking-tight text-foreground sm:text-5xl sm:leading-[1.12]">
                Dịch giọng nói thời gian thực cho mọi{" "}
                <span className="bg-gradient-to-r from-indigo-600 to-cyan-600 bg-clip-text text-transparent">
                  cuộc họp &amp; hội thảo toàn cầu
                </span>
              </h1>

              <p className="max-w-xl text-sm leading-relaxed text-muted-foreground sm:text-base">
                Phát biểu bằng ngôn ngữ mẹ đẻ và truyền tải đồng thời phụ đề cùng
                giọng đọc AI tự nhiên sang tối đa 10 ngôn ngữ cho 1.000 người nghe.
                Tối ưu chi phí với VAD lọc khoảng lặng và tính cước chính xác theo
                từng giây.
              </p>

              <div className="flex flex-wrap items-center gap-3 pt-1">
                <Link
                  href="/register"
                  className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-700 px-5 py-3 text-sm font-semibold text-white shadow-md shadow-indigo-600/25 transition-opacity hover:opacity-95"
                >
                  <span>Bắt đầu miễn phí · Tặng 200 Cr</span>
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex items-center gap-2 rounded-xl border border-border bg-card px-5 py-3 text-sm font-semibold text-foreground shadow-sm transition-colors hover:bg-muted"
                >
                  <span>Xem bảng giá</span>
                </Link>
              </div>

              <div className="grid grid-cols-3 gap-4 border-t border-border/80 pt-6">
                <div>
                  <p className="text-xl font-bold text-foreground">&lt; 500ms</p>
                  <p className="text-xs text-muted-foreground">Độ trễ phụ đề Partial</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-foreground">1.000</p>
                  <p className="text-xs text-muted-foreground">Người nghe / phòng</p>
                </div>
                <div>
                  <p className="text-xl font-bold text-foreground">10 ngôn ngữ</p>
                  <p className="text-xs text-muted-foreground">Dịch song song tức thì</p>
                </div>
              </div>
            </div>

            {/* Interactive-looking Live Session Preview Card */}
            <div className="lg:col-span-6">
              <div className="rounded-2xl border border-border bg-card p-5 shadow-xl shadow-slate-900/5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-4">
                  <div className="flex items-center gap-2.5">
                    <span className="inline-flex h-2.5 w-2.5 animate-pulse rounded-full bg-rose-500" />
                    <span className="text-xs font-bold text-foreground">
                      LIVE · APAC Tech Summit 2026
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] font-semibold">
                    <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-indigo-700">
                      342 người nghe
                    </span>
                    <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-emerald-700">
                      14.2 Cr / phút
                    </span>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="rounded-xl border border-border/70 bg-slate-50/90 p-3.5">
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                      <span className="inline-flex items-center gap-1.5 font-semibold text-foreground">
                        <Mic className="h-3.5 w-3.5 text-emerald-600" />
                        Speaker (EN-US)
                      </span>
                      <span>VAD Active · 00:18:40</span>
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-slate-700">
                      &ldquo;Our single-AZ Redis ring buffer guarantees zero dropped words
                      even during container rolling updates.&rdquo;
                    </p>
                  </div>

                  <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                    <div className="rounded-xl border border-indigo-200 bg-indigo-50/50 p-3.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-indigo-700">Tiếng Việt (VI)</span>
                        <span className="inline-flex items-center gap-1 text-emerald-700">
                          <Volume2 className="h-3 w-3" /> Azure Neural
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs font-medium leading-relaxed text-foreground">
                        Bộ đệm vòng Redis Single-AZ đảm bảo không mất từ nào kể cả khi
                        cập nhật hệ thống.
                      </p>
                    </div>

                    <div className="rounded-xl border border-border bg-background p-3.5">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="font-bold text-foreground">日本語 (JA)</span>
                        <span className="inline-flex items-center gap-1 text-indigo-600">
                          <Volume2 className="h-3 w-3" /> Polly Neural
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs font-medium leading-relaxed text-foreground">
                        シングルAZのRedisリングバッファにより、更新時も単語の欠落を防ぎます。
                      </p>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-muted/50 px-3.5 py-2.5 text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1.5 font-medium text-foreground">
                    <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                    Demand-Driven TTS · 0 Cr cho ngôn ngữ không bật loa
                  </span>
                  <Link
                    href="/products/realtime-translation"
                    className="font-semibold text-indigo-600 hover:underline"
                  >
                    Xem bản demo →
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Core Capabilities */}
        <section className="border-t border-border/80 bg-card/60 py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="max-w-2xl space-y-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                Tính năng cốt lõi
              </span>
              <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Thiết kế trọn gói từ phòng họp 1-on-1 đến hội thảo nghìn người
              </h2>
            </div>

            <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {CAPABILITIES.map((cap) => {
                const Icon = cap.icon;
                return (
                  <Link
                    key={cap.href}
                    href={cap.href}
                    className="group flex flex-col justify-between rounded-2xl border border-border bg-card p-5 shadow-sm transition-all hover:border-indigo-400 hover:shadow-md"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 transition-colors group-hover:bg-indigo-600 group-hover:text-white">
                          <Icon className="h-5 w-5" />
                        </span>
                        <span className="rounded-full bg-muted px-2.5 py-0.5 text-[10px] font-semibold text-muted-foreground">
                          {cap.badge}
                        </span>
                      </div>
                      <h3 className="mt-4 text-sm font-bold text-foreground">
                        {cap.title}
                      </h3>
                      <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                        {cap.desc}
                      </p>
                    </div>
                    <span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 group-hover:underline">
                      <span>Tìm hiểu thêm</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
              Quy trình 3 bước
            </span>
            <h2 className="mt-2 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Lên sóng hội thảo đa ngôn ngữ chỉ trong 30 giây
            </h2>
          </div>

          <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
            {HOW_IT_WORKS.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="rounded-2xl border border-border bg-card p-6 shadow-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                      <Icon className="h-5 w-5" />
                    </span>
                    <span className="text-2xl font-extrabold text-slate-200">
                      {item.step}
                    </span>
                  </div>
                  <h3 className="mt-4 text-base font-bold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                    {item.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Quick Pricing Overview */}
        <section className="border-t border-border/80 bg-card/60 py-16">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
                  Bảng giá cố định &amp; Ví Credit
                </span>
                <h2 className="mt-1 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                  Chọn gói phù hợp, nạp thêm không lo hết hạn
                </h2>
              </div>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:underline"
              >
                <span>Xem bảng so sánh đầy đủ &amp; Ước tính chi phí</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {PLAN_HIGHLIGHTS.map((plan) => (
                <div
                  key={plan.name}
                  className={
                    plan.popular
                      ? "rounded-2xl border border-indigo-600 bg-card p-5 shadow-sm ring-1 ring-indigo-600/20"
                      : "rounded-2xl border border-border bg-card p-5 shadow-sm"
                  }
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-foreground">{plan.name}</span>
                    {plan.popular && (
                      <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-bold text-indigo-700">
                        Phổ biến
                      </span>
                    )}
                  </div>
                  <p className="mt-2 text-2xl font-bold text-foreground">{plan.price}</p>
                  <p className="mt-1 text-xs font-semibold text-indigo-600">
                    {plan.credits}
                  </p>
                  <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                    <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600" />
                    <span>{plan.note}</span>
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Bottom CTA */}
        <section className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
          <div className="flex flex-col items-start justify-between gap-6 rounded-2xl bg-gradient-to-r from-indigo-600 to-indigo-700 p-8 text-white shadow-lg shadow-indigo-600/20 sm:flex-row sm:items-center">
            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold">
                <Globe2 className="h-3.5 w-3.5" />
                <span>Sẵn sàng cho sự kiện đa ngôn ngữ tiếp theo</span>
              </span>
              <h2 className="text-xl font-bold sm:text-2xl">
                Nhận ngay 200 Credits miễn phí khi tạo tài khoản Host
              </h2>
              <p className="text-xs text-indigo-100">
                Không yêu cầu thẻ tín dụng. Hỗ trợ thanh toán Stripe &amp; VietQR nội địa.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/register"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-xs font-bold text-indigo-700 shadow-sm transition-opacity hover:opacity-95"
              >
                <span>Đăng ký miễn phí</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
              <Link
                href="/dashboard"
                className="rounded-xl border border-white/30 bg-white/10 px-5 py-3 text-xs font-bold text-white transition-colors hover:bg-white/20"
              >
                Vào Dashboard
              </Link>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
