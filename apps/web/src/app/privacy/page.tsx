import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, AudioWaveform, Lock, ShieldCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "Chính sách bảo mật | VoiceBridge AI",
  description:
    "Cách VoiceBridge AI thu thập, xử lý, mã hóa, lưu trữ và bảo vệ dữ liệu giọng nói, biên bản dịch và thông tin thanh toán.",
};

const SECTIONS = [
  {
    title: "1. Dữ liệu chúng tôi thu thập",
    points: [
      "Thông tin tài khoản Host: họ tên, địa chỉ email, ngôn ngữ mặc định, múi giờ và thông tin xuất hóa đơn VAT (nếu bạn chủ động cung cấp).",
      "Dữ liệu phiên dịch: luồng âm thanh đầu vào khi bạn bật micro, văn bản nhận diện/bản dịch và thông số kỹ thuật phục vụ đối soát Credit (số giây nói, số ký tự, số lượng người nghe).",
      "Thông tin thanh toán: chúng tôi chỉ lưu mã giao dịch và mã tham chiếu từ Stripe/VietQR, tuyệt đối không lưu số thẻ tín dụng thô (PAN) hay mã CVV trên hệ thống.",
    ],
  },
  {
    title: "2. Cách xử lý âm thanh & Nhà cung cấp AI",
    points: [
      "Luồng âm thanh được mã hóa truyền tải qua HTTPS/WSS (TLS) và chỉ đệm tạm thời tối đa 10 giây trên Redis nội bộ vùng Singapore (AWS ap-southeast-1) nhằm đảm bảo không mất chữ khi chuyển đổi máy chủ.",
      "Dữ liệu giọng nói và văn bản được xử lý thời gian thực qua Amazon Transcribe, Amazon Translate, Amazon Polly, Amazon Bedrock và Azure AI Speech (vùng Singapore southeastasia cho tiếng Việt) để trả kết quả dịch trực tiếp.",
    ],
  },
  {
    title: "3. Thời gian lưu trữ & Tự động xóa dữ liệu",
    points: [
      "File âm thanh giọng đọc AI (TTS .mp3): chỉ phục vụ phát trực tiếp trong phiên và tự động xóa vĩnh viễn khỏi Amazon S3 sau 24 giờ.",
      "Biên bản bản dịch & Tóm tắt AI trên S3: được lưu theo thời hạn gói dịch vụ tại thời điểm kết thúc phòng (FREE: 7 ngày, PRO: 30 ngày, BUSINESS: 90 ngày, ENTERPRISE: 365 ngày) và tự động xóa khi hết hạn.",
      "Listener chỉ được tải biên bản nếu Host chủ động bật tùy chọn cho phép tải xuống cho phòng đó.",
    ],
  },
  {
    title: "4. Bảo mật phiên đăng nhập & Kiểm toán",
    points: [
      "Xác thực Host sử dụng Amazon Cognito (JWT RS256 qua JWKS). Refresh Token chỉ lưu trong HttpOnly Cookie để bảo vệ trước tấn công XSS và hỗ trợ thu hồi tức thì trên mọi thiết bị.",
      "Mọi thao tác can thiệp quản trị hệ thống đều được ghi nhận trong nhật ký kiểm toán bất biến (Audit Logs).",
    ],
  },
  {
    title: "5. Quyền riêng tư & Xóa dữ liệu (GDPR / PDPA)",
    points: [
      "Màn hình Người nghe luôn hiển thị thông báo minh bạch rằng phiên họp đang được dịch thuật và lưu biên bản bằng AI.",
      "Host có toàn quyền chủ động xóa biên bản của từng phòng bất kỳ lúc nào hoặc yêu cầu xóa tài khoản và dữ liệu cá nhân thông qua cài đặt tài khoản hoặc liên hệ support@voicebridge.ai.",
    ],
  },
];

export default function PrivacyPage() {
  return (
    <div className="flex-1 bg-slate-50/70">
      <div className="border-b border-border bg-card/90">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="inline-flex items-center gap-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-sm">
              <AudioWaveform className="h-4 w-4" />
            </span>
            <span className="text-sm font-bold tracking-tight text-foreground">
              VoiceBridge AI
            </span>
          </Link>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <Link
              href="/terms"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Điều khoản sử dụng
            </Link>
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-foreground transition-colors hover:bg-muted"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              <span>Quay lại</span>
            </Link>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-700">
              <Lock className="h-3.5 w-3.5" />
              <span>Bảo mật &amp; Quyền riêng tư</span>
            </span>
            <span className="text-xs text-muted-foreground">
              Cập nhật lần cuối: 19/11/2026
            </span>
          </div>

          <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Chính sách bảo mật
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            VoiceBridge AI cam kết bảo vệ dữ liệu giọng nói, biên bản hội thảo và
            thông tin tài khoản của bạn theo các tiêu chuẩn bảo mật hiện đại.
          </p>

          <div className="mt-8 space-y-8">
            {SECTIONS.map((section) => (
              <section key={section.title} className="space-y-3">
                <h2 className="text-base font-semibold text-foreground">
                  {section.title}
                </h2>
                <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-muted-foreground">
                  {section.points.map((point) => (
                    <li key={point}>{point}</li>
                  ))}
                </ul>
              </section>
            ))}
          </div>

          <div className="mt-10 flex flex-col gap-3 rounded-xl border border-border bg-muted/40 p-4 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
            <div className="inline-flex items-center gap-2 font-medium text-foreground">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              <span>Yêu cầu hỗ trợ bảo mật hoặc xóa dữ liệu cá nhân:</span>
            </div>
            <a
              href="mailto:support@voicebridge.ai"
              className="font-semibold text-indigo-600 hover:underline"
            >
              support@voicebridge.ai
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
