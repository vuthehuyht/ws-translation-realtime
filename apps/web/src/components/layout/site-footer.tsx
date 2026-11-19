import React from "react";
import Link from "next/link";
import { AudioWaveform, Globe2, Mail, ShieldCheck } from "lucide-react";

const PRODUCT_FEATURES = [
  { href: "/products/realtime-translation", label: "Phiên dịch trực tiếp" },
  { href: "/pricing", label: "Bảng giá & Gói cước" },
  { href: "/products/transcripts-ai-summary", label: "Biên bản & Tóm tắt AI" },
  { href: "/products/custom-vocabularies", label: "Từ điển thuật ngữ" },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-card/90">
      <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="space-y-3 lg:col-span-5">
            <Link href="/" className="inline-flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm shadow-indigo-600/20">
                <AudioWaveform className="h-4 w-4" />
              </span>
              <span className="text-sm font-bold tracking-tight text-foreground">
                VoiceBridge AI
              </span>
            </Link>
            <p className="max-w-sm text-xs leading-relaxed text-muted-foreground">
              Nền tảng dịch giọng nói thời gian thực đa ngôn ngữ dưới 500ms với
              Amazon Transcribe, Translate, Polly &amp; Azure Neural TTS.
            </p>
            <div className="flex flex-wrap items-center gap-2 pt-0.5">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span>AWS ap-southeast-1 · Realtime</span>
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                <Globe2 className="h-3 w-3 text-indigo-600" />
                <span>10 ngôn ngữ · 1.000 người nghe</span>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:col-span-7">
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Sản phẩm
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                {PRODUCT_FEATURES.map((feature) => (
                  <li key={feature.href} className="leading-relaxed">
                    <Link
                      href={feature.href}
                      className="transition-colors hover:text-foreground"
                    >
                      {feature.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Hỗ trợ
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li>
                  <a
                    href="mailto:support@voicebridge.ai"
                    className="inline-flex items-center gap-1.5 transition-colors hover:text-foreground"
                  >
                    <Mail className="h-3.5 w-3.5" />
                    <span>support@voicebridge.ai</span>
                  </a>
                </li>
                <li>
                  <span
                    aria-disabled="true"
                    title="Trung tâm trợ giúp đang được hoàn thiện"
                    className="cursor-not-allowed text-muted-foreground/70"
                  >
                    Trung tâm trợ giúp (Sắp ra mắt)
                  </span>
                </li>
              </ul>
            </div>

            <div className="col-span-2 space-y-3 sm:col-span-1">
              <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Pháp lý &amp; Bảo mật
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li>
                  <Link
                    href="/terms"
                    className="transition-colors hover:text-foreground"
                  >
                    Điều khoản sử dụng
                  </Link>
                </li>
                <li>
                  <Link
                    href="/privacy"
                    className="transition-colors hover:text-foreground"
                  >
                    Chính sách bảo mật
                  </Link>
                </li>
                <li className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-700">
                  <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
                  <span>Mã hóa TLS &amp; Tuân thủ GDPR</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-2 border-t border-border/70 pt-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 VoiceBridge AI. All rights reserved.</p>
          <p>
            Hỗ trợ Speech-to-Speech &amp; Speech-to-Text · Tính cước minh bạch theo từng giây.
          </p>
        </div>
      </div>
    </footer>
  );
}
