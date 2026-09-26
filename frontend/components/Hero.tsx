import Link from "next/link";
import { ShieldCheck, Search, ClipboardList } from "lucide-react";

export default function Hero() {
  return (
    <section className="relative overflow-hidden px-4 pt-24 pb-24">
      <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-(--color-border) bg-black/40 px-3 py-1.5 text-sm text-(--color-accent) backdrop-blur">
            <ShieldCheck className="h-4 w-4" />
            Reference index · 12,480 entries
          </div>

          <h1 className="max-w-lg text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl">
            Know exactly what is inside the strip.
          </h1>

          <p className="mt-6 max-w-md text-lg leading-8 text-zinc-400">
            RxGuard reads a medicine name and strength, matches it against a
            pharmacology reference index, and grades how sure it is —
            including when it isn&apos;t.
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              href="/verify"
              className="inline-flex items-center gap-2 rounded-full bg-(--color-accent) px-6 py-3 font-medium text-black transition-colors hover:bg-(--color-accent-dim)"
            >
              <Search className="h-4 w-4" />
              Verify a medicine
            </Link>
            <Link
              href="#method"
              className="inline-flex items-center gap-2 rounded-full border border-(--color-border) bg-black/30 px-6 py-3 font-medium text-zinc-200 backdrop-blur transition-colors hover:bg-(--color-surface-raised)"
            >
              <ClipboardList className="h-4 w-4" />
              How grading works
            </Link>
          </div>
        </div>

        <div className="rounded-2xl border border-(--color-border) bg-(--color-surface-raised)/95 p-6 backdrop-blur">
          <div className="mb-5 flex items-center justify-between">
            <span className="font-mono text-xs text-zinc-500">live check</span>
            <span className="h-2 w-2 rounded-full bg-(--color-accent)" />
          </div>

          <div className="mb-5 flex items-center gap-4">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-800 font-mono text-lg">
              A
            </div>
            <div>
              <p className="font-mono text-lg">Atorvastatin</p>
              <p className="text-sm text-zinc-500">20 mg · film-coated tablet</p>
            </div>
          </div>

          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-emerald-800 bg-emerald-950/40 px-3 py-1.5 text-sm text-emerald-400">
            <ShieldCheck className="h-4 w-4" />
            High confidence <span className="font-mono">94.1%</span>
          </div>

          <dl className="divide-y divide-(--color-border) border-t border-(--color-border)">
            <div className="flex items-center justify-between py-3">
              <dt className="text-sm text-zinc-500">Salt match</dt>
              <dd className="font-mono text-sm">Atorvastatin calcium</dd>
            </div>
            <div className="flex items-center justify-between py-3">
              <dt className="text-sm text-zinc-500">Equivalents</dt>
              <dd className="font-mono text-sm">3 found</dd>
            </div>
            <div className="flex items-center justify-between py-3">
              <dt className="text-sm text-zinc-500">Interactions flagged</dt>
              <dd className="font-mono text-sm">1 major</dd>
            </div>
          </dl>
        </div>
      </div>
    </section>
  );
}