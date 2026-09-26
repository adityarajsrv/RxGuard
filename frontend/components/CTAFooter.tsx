import { RotateCw, Stethoscope } from "lucide-react";

export default function CtaFooter() {
  return (
    <section className="border-t border-(--color-border) px-4 py-24">
      <div className="mx-auto max-w-6xl">
        <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <h2 className="mb-3 text-4xl font-semibold tracking-tight sm:text-5xl">
              Run another strip through the check.
            </h2>
            <p className="max-w-md text-zinc-400">
              Every result carries its own confidence grade, so you always
              know how much weight it can hold.
            </p>
          </div>
        <a
            href="/verify"
            className="inline-flex shrink-0 items-center gap-2 rounded-full bg-(--color-accent) px-6 py-3 font-medium text-black transition-colors hover:bg-(--color-accent-dim)"
          >
            <RotateCw className="h-4 w-4" />
            Verify again
          </a>
        </div>

        <div className="mt-12 flex items-center gap-3 rounded-xl border border-(--color-border) bg-(--color-surface-raised) p-5 text-sm text-zinc-400">
          <Stethoscope className="h-5 w-5 shrink-0 text-zinc-500" />
          Prototype tool, not a certified medical device. Consult a
          pharmacist or doctor.
        </div>

        <p className="mt-12 font-mono text-sm text-zinc-600">
          RxGuard · reference index build 2026.09
        </p>
      </div>
    </section>
  );
}