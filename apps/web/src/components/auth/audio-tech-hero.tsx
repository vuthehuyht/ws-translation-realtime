import React from "react";
import { Mic, Zap, Users, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";

interface AudioTechHeroProps {
  variant?: "register" | "login";
  badgeText?: string;
  title?: string;
  description?: string;
  showTrialCard?: boolean;
  className?: string;
}

export function AudioTechHero({
  variant = "login",
  badgeText,
  title,
  description,
  showTrialCard,
  className,
}: AudioTechHeroProps) {
  const isRegister = variant === "register" || showTrialCard;

  const resolvedBadge =
    badgeText ?? (isRegister ? "Tài khoản Host Miễn Phí" : "AWS Realtime Speech Pipeline");

  const resolvedTitle =
    title ??
    (isRegister
      ? "Bắt đầu tổ chức phiên dịch trong 30 giây"
      : "Xóa bỏ rào cản ngôn ngữ với tốc độ dưới 500ms");

  const resolvedDescription =
    description ??
    (isRegister
      ? "Tạo tài khoản để sở hữu phòng dịch riêng, hỗ trợ dịch song song 10 ngôn ngữ và nhận biên bản tóm tắt AI tự động từ Bedrock."
      : "Nền tảng truyền phát âm thanh nhị phân 16kHz kết hợp Amazon Transcribe, Translate và Polly Neural cho hội nghị quốc tế và webinar quy mô 1.000 người nghe.");

  return (
    <div
      className={cn(
        "relative flex flex-col justify-between overflow-hidden bg-[radial-gradient(circle_at_20%_30%,_#1e1b4b_0%,_#0f172a_60%,_#020617_100%)] p-8 sm:p-10 lg:p-12 text-white",
        className
      )}
    >
      {/* Ambient background glows matching mockup */}
      <div
        className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-indigo-500/25 blur-[80px]"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none absolute -bottom-20 -right-20 h-72 w-72 rounded-full bg-cyan-500/20 blur-[80px]"
        aria-hidden="true"
      />

      {/* Top Header & Brand Introduction */}
      <div className="relative z-10 space-y-4">
        <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/8 px-3.5 py-1 text-xs font-semibold backdrop-blur-md">
          {isRegister ? (
            <span className="text-[#38bdf8]">{resolvedBadge}</span>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]" />
              <span>{resolvedBadge}</span>
            </>
          )}
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl lg:text-[1.85rem] leading-[1.25]">
          {resolvedTitle}
        </h1>

        <p className="max-w-md text-sm text-[#94a3b8] leading-relaxed">
          {resolvedDescription}
        </p>
      </div>

      {/* Center: Register Trial Card OR Login Waveform Card */}
      <div className="relative z-10 my-8">
        {isRegister ? (
          <div className="rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-md shadow-lg">
            <div className="flex items-center gap-2.5 text-sm font-semibold text-[#34d399] mb-2.5">
              <span className="text-base" role="img" aria-label="gift">🎁</span>
              <span>Tặng 10 phút dịch thử nghiệm miễn phí</span>
            </div>
            <ul className="space-y-1.5 text-xs text-[#cbd5e1] pl-5 list-disc leading-relaxed">
              <li>Truyền phát âm thanh chuẩn PCM 16kHz</li>
              <li>Hỗ trợ tối đa 1.000 người nghe cùng lúc</li>
              <li>Không yêu cầu nhập thẻ tín dụng trước</li>
            </ul>
          </div>
        ) : (
          <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-md shadow-2xl space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="flex h-6 w-6 items-center justify-center rounded-md bg-indigo-500/30 text-indigo-300">
                  <Mic className="h-3.5 w-3.5" />
                </div>
                <span className="text-xs font-semibold text-slate-200">
                  Host Studio Audio Stream
                </span>
              </div>
              <span className="inline-flex items-center rounded border border-emerald-500/30 bg-emerald-500/20 px-2 py-0.5 text-[10px] font-semibold text-emerald-300">
                VAD: SPEAKING
              </span>
            </div>

            <div className="flex h-9 items-center justify-between gap-1 px-1" aria-hidden="true">
              {[14, 26, 34, 20, 30, 36, 28, 18, 32, 22, 12].map((height, i) => (
                <span
                  key={i}
                  className="w-1.5 rounded-full bg-gradient-to-t from-indigo-500 to-cyan-400"
                  style={{ height: `${height}px` }}
                />
              ))}
            </div>

            <div className="space-y-1 border-t border-white/10 pt-2.5 text-xs">
              <div className="flex items-center gap-2 text-slate-200">
                <span className="font-mono text-[11px] text-slate-400">[vi-VN]</span>
                <span>&quot;Chào mừng mọi người đến với phiên dịch tự động...&quot;</span>
              </div>
              <div className="flex items-center gap-2 text-cyan-300">
                <span className="font-mono text-[11px] text-cyan-500">[ja-JP]</span>
                <span>「リアルタイム翻訳セッションへようこそ...」</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Metrics (for login) or Support Note (for register) */}
      <div className="relative z-10 border-t border-white/8 pt-4">
        {isRegister ? (
          <div className="flex items-center justify-between text-xs text-[#64748b]">
            <span>Được hỗ trợ bởi AWS Transcribe &amp; Bedrock</span>
            <span className="text-[#94a3b8]">24/7 Support</span>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <div className="flex items-center justify-center gap-1 text-base font-bold text-white">
                <Zap className="h-3.5 w-3.5 text-cyan-400" />
                <span>&lt; 500ms</span>
              </div>
              <div className="text-[11px] text-slate-400">Độ trễ đầu cuối</div>
            </div>
            <div className="border-x border-white/10">
              <div className="flex items-center justify-center gap-1 text-base font-bold text-white">
                <Users className="h-3.5 w-3.5 text-indigo-400" />
                <span>1,000+</span>
              </div>
              <div className="text-[11px] text-slate-400">Người nghe/phòng</div>
            </div>
            <div>
              <div className="flex items-center justify-center gap-1 text-base font-bold text-emerald-400">
                <DollarSign className="h-3.5 w-3.5" />
                <span>$0 Idle</span>
              </div>
              <div className="text-[11px] text-slate-400">Không tốn phí khi chờ</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
