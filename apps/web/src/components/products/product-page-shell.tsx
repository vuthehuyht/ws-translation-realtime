import React from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, AudioWaveform } from "lucide-react";

interface ProductPageShellProps {
  badge: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export function ProductPageShell({
  badge,
  title,
  subtitle,
  children,
}: ProductPageShellProps) {
  return (
    <div className="flex-1 bg-slate-50/70">
      <div className="sticky top-0 z-30 border-b border-border bg-card/95 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex shrink-0 items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm">
              <AudioWaveform className="h-4 w-4" />
            </span>
            <span className="text-sm font-bold tracking-tight text-foreground">
              VoiceBridge AI
            </span>
          </Link>

          <Link
            href="/dashboard"
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-muted"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>Dashboard</span>
          </Link>
        </div>
      </div>

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-10 sm:px-6 lg:px-8">
        <div className="space-y-3">
          <span className="inline-flex items-center rounded-full border border-indigo-500/25 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-700">
            {badge}
          </span>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            {title}
          </h1>
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {subtitle}
          </p>
        </div>

        {children}

        <div className="flex flex-col items-start justify-between gap-4 rounded-2xl border border-indigo-500/20 bg-gradient-to-r from-indigo-600 to-indigo-700 p-6 text-white shadow-md sm:flex-row sm:items-center">
          <div className="space-y-1">
            <p className="text-base font-bold">
              Trải nghiệm ngay với 200 Credits miễn phí
            </p>
            <p className="text-xs text-indigo-100">
              Khởi tạo phòng dịch 1-on-1 hoặc Broadcast trong chưa đầy 30 giây,
              tính cước minh bạch theo từng giây thực tế.
            </p>
          </div>
          <Link
            href="/register"
            className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-bold text-indigo-700 shadow-sm transition-opacity hover:opacity-95"
          >
            <span>Dùng thử miễn phí</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </main>
    </div>
  );
}
