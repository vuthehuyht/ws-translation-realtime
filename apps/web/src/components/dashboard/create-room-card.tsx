"use client";

import React, { useState } from "react";
import { Check, Play } from "lucide-react";
import { cn } from "@/lib/utils";

export type RoomMode = "BROADCAST" | "1_ON_1";

export interface CreateRoomFormPayload {
  title: string;
  mode: RoomMode;
  sourceLang: string;
  targetLangs: string[];
  allowTranscriptDownload: boolean;
}

interface CreateRoomCardProps {
  initialSourceLang?: string | null;
  initialTargetLangs?: string[];
  onCreateRoom: (payload: CreateRoomFormPayload) => void;
}

const SOURCE_LANGUAGES = [
  { code: "vi-VN", label: "Tiếng Việt (vi-VN)" },
  { code: "en-US", label: "English - US (en-US)" },
  { code: "ja-JP", label: "日本語 - Japanese (ja-JP)" },
  { code: "ko-KR", label: "한국어 - Korean (ko-KR)" },
  { code: "zh-CN", label: "中文 - Chinese (zh-CN)" },
];

const TARGET_LANGUAGES = [
  { code: "en-US", label: "English (US)" },
  { code: "ja-JP", label: "Japanese" },
  { code: "ko-KR", label: "Korean" },
  { code: "zh-CN", label: "Chinese" },
  { code: "fr-FR", label: "French" },
  { code: "de-DE", label: "German" },
  { code: "es-ES", label: "Spanish" },
  { code: "th-TH", label: "Thai" },
  { code: "id-ID", label: "Indonesian" },
  { code: "pt-BR", label: "Portuguese" },
  { code: "ru-RU", label: "Russian" },
  { code: "ar-SA", label: "Arabic" },
];

const MAX_TARGET_LANGUAGES = 10;

export function CreateRoomCard({
  initialSourceLang,
  initialTargetLangs,
  onCreateRoom,
}: CreateRoomCardProps) {
  const [title, setTitle] = useState("");
  const [mode, setMode] = useState<RoomMode>("BROADCAST");
  const [sourceLang, setSourceLang] = useState(
    initialSourceLang && SOURCE_LANGUAGES.some((l) => l.code === initialSourceLang)
      ? initialSourceLang
      : "vi-VN"
  );
  const [targetLangs, setTargetLangs] = useState<string[]>(() => {
    const resolvedSource =
      initialSourceLang && SOURCE_LANGUAGES.some((l) => l.code === initialSourceLang)
        ? initialSourceLang
        : "vi-VN";
    const validDefaults = (initialTargetLangs ?? []).filter(
      (code) =>
        code !== resolvedSource &&
        TARGET_LANGUAGES.some((lang) => lang.code === code)
    );
    if (validDefaults.length > 0) {
      return validDefaults.slice(0, MAX_TARGET_LANGUAGES);
    }
    return ["en-US", "ja-JP", "ko-KR"].filter((code) => code !== resolvedSource);
  });
  const [allowTranscriptDownload, setAllowTranscriptDownload] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const availableTargetLanguages = TARGET_LANGUAGES.filter(
    (lang) => lang.code !== sourceLang
  );
  const isLimitReached = targetLangs.length >= MAX_TARGET_LANGUAGES;

  const handleSourceLangChange = (nextSource: string) => {
    setSourceLang(nextSource);
    setTargetLangs((prev) => prev.filter((code) => code !== nextSource));
  };

  const toggleTargetLang = (code: string) => {
    setErrorMessage(null);
    setTargetLangs((prev) => {
      if (prev.includes(code)) {
        return prev.filter((item) => item !== code);
      }
      if (prev.length >= MAX_TARGET_LANGUAGES) {
        return prev;
      }
      return [...prev, code];
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (targetLangs.length === 0) {
      setErrorMessage("Vui lòng chọn ít nhất 1 ngôn ngữ đích.");
      return;
    }

    onCreateRoom({
      title: title.trim(),
      mode,
      sourceLang,
      targetLangs,
      allowTranscriptDownload,
    });
    setTitle("");
  };

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm sm:p-6">
      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-bold text-foreground">
              Tạo phòng dịch mới
            </h2>
            <p className="text-xs text-muted-foreground">
              Chọn chế độ, ngôn ngữ nguồn và tối đa 10 ngôn ngữ đích cho người nghe.
            </p>
          </div>
          <span className="inline-flex items-center self-start rounded-full bg-indigo-50 px-2.5 py-1 text-xs font-semibold text-indigo-700 tabular-nums">
            Đã chọn {targetLangs.length}/{MAX_TARGET_LANGUAGES} ngôn ngữ đích
          </span>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <label
              htmlFor="room-title"
              className="block text-xs font-semibold text-foreground"
            >
              Tên phòng họp (tùy chọn)
            </label>
            <input
              id="room-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ví dụ: Hội nghị đối tác Q4 - Tokyo"
              className="flex h-10 w-full rounded-lg border border-border bg-background px-3.5 text-sm text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="source-lang"
              className="block text-xs font-semibold text-foreground"
            >
              Ngôn ngữ nguồn (Speaker)
            </label>
            <select
              id="source-lang"
              value={sourceLang}
              onChange={(e) => handleSourceLangChange(e.target.value)}
              className="flex h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
            >
              {SOURCE_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-2">
          <span className="block text-xs font-semibold text-foreground">
            Chế độ phòng
          </span>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setMode("BROADCAST")}
              aria-pressed={mode === "BROADCAST"}
              className={cn(
                "flex items-start gap-3 rounded-xl p-3.5 text-left transition-all",
                mode === "BROADCAST"
                  ? "border-2 border-indigo-600 bg-indigo-50/50"
                  : "border border-border bg-background hover:border-slate-300"
              )}
            >
              <span
                className={cn(
                  "mt-0.5 flex h-4 w-4 shrink-0 rounded-full bg-white",
                  mode === "BROADCAST"
                    ? "border-4 border-indigo-600"
                    : "border border-slate-300"
                )}
              />
              <div>
                <p className="text-xs font-bold text-foreground">
                  Broadcast (Hội trường / Webinar)
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  1 Host nói · Tối đa 1.000 người nghe qua QR · ~15 Cr/phút
                </p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setMode("1_ON_1")}
              aria-pressed={mode === "1_ON_1"}
              className={cn(
                "flex items-start gap-3 rounded-xl p-3.5 text-left transition-all",
                mode === "1_ON_1"
                  ? "border-2 border-indigo-600 bg-indigo-50/50"
                  : "border border-border bg-background hover:border-slate-300"
              )}
            >
              <span
                className={cn(
                  "mt-0.5 flex h-4 w-4 shrink-0 rounded-full bg-white",
                  mode === "1_ON_1"
                    ? "border-4 border-indigo-600"
                    : "border border-slate-300"
                )}
              />
              <div>
                <p className="text-xs font-bold text-foreground">
                  1-on-1 (Hội thoại 2 chiều)
                </p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  Phiên dịch song phương 2 người · ~7,5 Cr/phút
                </p>
              </div>
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <span className="block text-xs font-semibold text-foreground">
            Ngôn ngữ đích (chọn ít nhất 1, tối đa 10)
          </span>
          <div className="flex flex-wrap gap-2">
            {availableTargetLanguages.map((lang) => {
              const isSelected = targetLangs.includes(lang.code);
              const isDisabled = !isSelected && isLimitReached;

              return (
                <button
                  key={lang.code}
                  type="button"
                  disabled={isDisabled}
                  aria-pressed={isSelected}
                  onClick={() => toggleTargetLang(lang.code)}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-full px-3 py-1.5 text-xs transition-all",
                    isSelected
                      ? "border border-indigo-600 bg-indigo-600 font-semibold text-white shadow-sm"
                      : isDisabled
                        ? "cursor-not-allowed border border-border bg-muted font-medium text-muted-foreground/50"
                        : "border border-border bg-background font-medium text-foreground hover:border-indigo-400 hover:text-indigo-600"
                  )}
                >
                  {isSelected && <Check className="h-3 w-3" />}
                  <span>{lang.label}</span>
                </button>
              );
            })}
          </div>
          {errorMessage && (
            <p role="alert" className="text-xs font-medium text-destructive">
              {errorMessage}
            </p>
          )}
        </div>

        <div className="flex flex-col gap-4 border-t border-border/60 pt-4 sm:flex-row sm:items-center sm:justify-between">
          <label className="flex cursor-pointer items-center gap-2.5 text-xs text-muted-foreground">
            <input
              type="checkbox"
              checked={allowTranscriptDownload}
              onChange={(e) => setAllowTranscriptDownload(e.target.checked)}
              className="h-4 w-4 rounded border-border text-primary focus:ring-primary/20"
            />
            <span>Cho phép người nghe tải biên bản dịch (.TXT / .SRT)</span>
          </label>

          <button
            type="submit"
            className="inline-flex h-11 items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-600 to-indigo-700 px-5 text-sm font-semibold text-white shadow-md shadow-indigo-600/20 transition-all hover:opacity-95"
          >
            <Play className="h-4 w-4 fill-current" />
            <span>Tạo &amp; mở phòng dịch ngay</span>
          </button>
        </div>
      </form>
    </section>
  );
}
