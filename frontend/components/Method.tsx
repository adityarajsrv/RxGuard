import { Pill, FlaskConical, ClipboardList, ShieldCheck, CircleHelp } from "lucide-react";

export default function Method() {
  return (
    <section id="method" className="px-4 py-36 mt-12">
      <div className="mx-auto max-w-6xl">
        <h2 className="mb-12 text-4xl font-semibold tracking-tight sm:text-5xl">
          Three checks run on every entry.
        </h2>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
          <div
            className="relative overflow-hidden rounded-2xl border border-(--color-border) bg-cover bg-center p-8"
            style={{
              backgroundImage:
                "url('https://images.unsplash.com/photo-1587854692152-cbe660dbde88?q=80&w=1600&auto=format&fit=crop')",
            }}
          >
            <div className="absolute inset-0 bg-black/70" />

            <div className="relative">
              <Pill className="mb-6 h-6 w-6 text-(--color-accent)" />
              <h3 className="mb-3 text-2xl font-semibold">
                Identity match, graded not guessed
              </h3>
              <p className="mb-8 max-w-md text-zinc-300">
                Brand names, salts and strengths are resolved separately, so
                a partial match never gets reported as a full one.
              </p>

              <div className="flex flex-wrap gap-3">
                <span className="inline-flex items-center gap-2 rounded-full border border-emerald-800 bg-emerald-950/50 px-3 py-1.5 text-sm text-emerald-400">
                  <ShieldCheck className="h-4 w-4" />
                  High confidence
                </span>
                <span className="inline-flex items-center gap-2 rounded-full border border-(--color-border) bg-black/40 px-3 py-1.5 text-sm text-zinc-300">
                  <CircleHelp className="h-4 w-4" />
                  Unverified
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="rounded-2xl border border-(--color-border) bg-(--color-surface-raised) p-8">
              <FlaskConical className="mb-5 h-6 w-6 text-(--color-accent)" />
              <h3 className="mb-2 text-xl font-semibold">Equivalents</h3>
              <p className="text-zinc-400">
                Same-salt alternatives listed with strengths in mono, so a
                650 mg swap never hides behind a 500 mg name.
              </p>
            </div>

            <div className="rounded-2xl border border-(--color-border) bg-(--color-surface-raised) p-8">
              <ClipboardList className="mb-5 h-6 w-6 text-(--color-accent)" />
              <h3 className="mb-2 text-xl font-semibold">Interaction screen</h3>
              <p className="mb-3 font-mono text-sm text-zinc-500">
                Live FDA label lookup + curated fallback
              </p>
              <p className="text-zinc-400">
                Severity and the clinical reason, never just a warning
                colour.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}