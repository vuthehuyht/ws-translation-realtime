import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "WS Translation - Realtime AI Speech-to-Speech Translation",
  description: "Sub-500ms real-time speech translation powered by AWS Transcribe, Translate, and Polly Neural",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi" suppressHydrationWarning>
      <body className="antialiased min-h-screen bg-background text-foreground font-sans">
        {children}
      </body>
    </html>
  );
}
