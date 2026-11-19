import React from "react";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft, AudioWaveform, FileText, ShieldCheck } from "lucide-react";

export const metadata: Metadata = {
  title: "Điều khoản sử dụng | VoiceBridge AI",
  description:
    "Điều khoản dịch vụ, quy tắc gói cước Credit, tính cước theo giây và chính sách sử dụng hợp lệ của VoiceBridge AI.",
};

const SECTIONS = [
  {
    title: "1. Phạm vi dịch vụ & Tài khoản",
    points: [
      "VoiceBridge AI cung cấp nền tảng dịch thuật giọng nói và phụ đề thời gian thực (Speech-to-Speech & Speech-to-Text) cho chế độ 1-on-1 và hội thảo Broadcast đa ngôn ngữ.",
      "Chủ phòng (Host) chịu trách nhiệm bảo mật thông tin đăng nhập, nội dung phát biểu trong phòng và thông báo cho người tham gia rằng phiên đang được phiên dịch và lưu biên bản bằng AI.",
      "Người nghe (Listener) tham gia qua đường dẫn hoặc mã phòng không bị tính phí cá nhân và chỉ có quyền nhận phụ đề/âm thanh theo cấu hình của Host.",
    ],
  },
  {
    title: "2. Gói dịch vụ, Ví Credit 3 ngăn & Thanh toán",
    points: [
      "Đơn vị sử dụng dịch vụ là Credit (1 USD = 100 Credits). Hệ thống cung cấp 4 gói thuê bao cố định theo tháng (FREE, PRO, BUSINESS, ENTERPRISE) cùng 3 gói nạp lẻ cố định (PACK_S, PACK_M, PACK_L).",
      "Mỗi ví duy trì 3 ngăn Credit và ưu tiên khấu trừ theo thứ tự: Promo Credits (có hạn dùng) -> Plan Credits (reset cuối chu kỳ gói tháng) -> Top-up Credits (không hết hạn, bảo toàn kể cả khi hạ gói).",
      "Khi nâng gói (Upgrade), chu kỳ 30 ngày mới và toàn bộ quyền lợi gói mới được kích hoạt ngay sau khi thanh toán thành công qua Stripe hoặc VietQR. Khi hủy gia hạn, quyền lợi gói hiện tại được giữ nguyên đến hết ngày cuối chu kỳ đã thanh toán.",
    ],
  },
  {
    title: "3. Cơ chế Tính cước Theo Từng Giây & Bảo vệ Chi phí",
    points: [
      "Chi phí phòng dịch được đo và khấu trừ chính xác theo từng giây sử dụng thực tế (Per-Second Billing) dựa trên thời lượng tiếng nói (sau lọc khoảng lặng VAD), số ký tự dịch, số ký tự tổng hợp giọng đọc khi có người bật loa và tổng người-giây kết nối.",
      "Mọi khung âm thanh hoặc ký tự phát sinh lỗi 5xx từ phía nhà cung cấp AI sẽ không bị trừ Credit (0 Cr).",
      "Phiên dịch sẽ tự động hạ cấp mềm tắt giọng đọc (nếu được bật) khi còn dưới 1 phút Credit ước tính và đóng phiên an toàn khi số dư chạm 0 Credit.",
    ],
  },
  {
    title: "4. Chính sách Sử dụng Hợp lệ & Chống Lạm dụng",
    points: [
      "Nghiêm cấm sử dụng dịch vụ để truyền bá nội dung vi phạm pháp luật, xâm phạm bản quyền hoặc tạo hàng loạt tài khoản bằng email dùng một lần nhằm trục lợi Credit dùng thử (Welcome Bonus).",
      "VoiceBridge AI có quyền tạm khóa tài khoản hoặc đóng khẩn cấp phòng đang hoạt động nếu phát hiện hành vi gian lận thanh toán hoặc vi phạm nghiêm trọng điều khoản này.",
    ],
  },
  {
    title: "5. Hoàn tiền & Liên hệ",
    points: [
      "Yêu cầu hoàn tiền đối với giao dịch lỗi kỹ thuật hoặc thanh toán nhầm được tiếp nhận trong vòng 7 ngày qua email support@voicebridge.ai kèm mã giao dịch.",
      "Khi có thay đổi trọng yếu đối với Điều khoản sử dụng, chúng tôi sẽ thông báo trước ít nhất 14 ngày qua email đăng ký tài khoản.",
    ],
  },
];

export default function TermsPage() {
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
              href="/privacy"
              className="text-muted-foreground transition-colors hover:text-foreground"
            >
              Chính sách bảo mật
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
            <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-500/25 bg-indigo-500/10 px-3 py-1 text-xs font-semibold text-indigo-700">
              <FileText className="h-3.5 w-3.5" />
              <span>Tài liệu pháp lý</span>
            </span>
            <span className="text-xs text-muted-foreground">
              Cập nhật lần cuối: 19/11/2026
            </span>
          </div>

          <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Điều khoản sử dụng
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            Bằng việc đăng ký tài khoản hoặc sử dụng dịch vụ dịch thuật thời gian
            thực VoiceBridge AI, bạn đồng ý tuân thủ các điều khoản dưới đây.
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
              <span>Cần giải đáp thêm về điều khoản hoặc hợp đồng Enterprise?</span>
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
