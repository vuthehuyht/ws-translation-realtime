import type { Metadata } from "next";
import { SiteFooter } from "@/components/layout/site-footer";
import "./globals.css";

export const metadata: Metadata = {
  title: "VoiceBridge AI - Realtime AI Speech-to-Speech Translation",
  description: "Sub-500ms real-time speech translation powered by AWS Transcribe, Translate, and Polly Neural",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body
        className="flex min-h-screen flex-col bg-background font-sans text-foreground antialiased"
        suppressHydrationWarning
      >
        <div className="flex flex-1 flex-col">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
