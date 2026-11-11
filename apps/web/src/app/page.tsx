import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      <div className="max-w-md space-y-4">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-xl font-bold text-white shadow-lg shadow-indigo-500/30">
          W
        </div>
        <h1 className="text-3xl font-bold tracking-tight">WS Translation</h1>
        <p className="text-sm text-muted-foreground">
          Realtime Speech-to-Speech & Speech-to-Text Translation System.
        </p>
        <div className="flex justify-center gap-3 pt-4">
          <Link
            href="/login"
            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow hover:opacity-90"
          >
            Đăng nhập
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-border bg-card px-5 py-2.5 text-sm font-semibold text-foreground hover:bg-muted"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
