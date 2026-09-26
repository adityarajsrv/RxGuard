import Link from "next/link";
import { ShieldCheck } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 px-4 pt-4">
      <div className="mx-auto flex max-w-6xl items-center justify-between rounded-full border border-(--color-border) bg-(--color-surface-raised)/90 px-6 py-3 backdrop-blur">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <ShieldCheck className="h-5 w-5 text-(--color-accent)" strokeWidth={2} />
          RxGuard
        </Link>

        <nav className="hidden items-center gap-8 text-sm text-zinc-400 sm:flex">
          <Link href="/#method" className="transition-colors hover:text-zinc-50">
            Method
          </Link>
          <Link href="/verify" className="transition-colors hover:text-zinc-50">
            Verification
          </Link>
        </nav>

        <Link
          href="/verify"
          className="rounded-full bg-(--color-accent) px-5 py-2 text-sm font-medium text-black transition-colors hover:bg-(--color-accent-dim)"
        >
          Check a medicine
        </Link>
      </div>
    </header>
  );
}