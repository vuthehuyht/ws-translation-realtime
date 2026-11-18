import React from "react";
import Link from "next/link";
import { AudioWaveform } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-card/90">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div className="max-w-sm space-y-2">
            <Link href="/" className="inline-flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm">
                <AudioWaveform className="h-4 w-4" />
              </span>
              <span className="text-sm font-bold tracking-tight text-foreground">
                VoiceBridge AI
              </span>
            </Link>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Nền tảng dịch giọng nói thời gian thực đa ngôn ngữ dưới 500ms với
              Amazon Transcribe, Translate và Polly Neural.
            </p>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              <span>AWS ap-southeast-1 · Realtime Pipeline</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:gap-12">
            <div className="space-y-2.5">
              <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Nền tảng
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li>
                  <Link
                    href="/dashboard"
                    className="transition-colors hover:text-foreground"
                  >
                    Host Dashboard
                  </Link>
                </li>
                <li>
                  <Link
                    href="/login"
                    className="transition-colors hover:text-foreground"
                  >
                    Đăng nhập
                  </Link>
                </li>
                <li>
                  <Link
                    href="/register"
                    className="transition-colors hover:text-foreground"
                  >
                    Đăng ký miễn phí
                  </Link>
                </li>
              </ul>
            </div>

            <div className="space-y-2.5">
              <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
                Pháp lý &amp; Hỗ trợ
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li>
                  <span
                    aria-disabled="true"
                    title="Tài liệu pháp lý đang được hoàn thiện"
                    className="cursor-not-allowed text-muted-foreground/70"
                  >
                    Điều khoản sử dụng (Sắp ra mắt)
                  </span>
                </li>
                <li>
                  <span
                    aria-disabled="true"
                    title="Tài liệu pháp lý đang được hoàn thiện"
                    className="cursor-not-allowed text-muted-foreground/70"
                  >
                    Chính sách bảo mật (Sắp ra mắt)
                  </span>
                </li>
                <li>
                  <Link
                    href="/forgot-password"
                    className="transition-colors hover:text-foreground"
                  >
                    Khôi phục mật khẩu
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-2 border-t border-border/70 pt-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 VoiceBridge AI. All rights reserved.</p>
          <p>Hỗ trợ Speech-to-Speech &amp; Speech-to-Text lên đến 1.000 người nghe/phòng.</p>
        </div>
      </div>
    </footer>
  );
}
