"use client";

import { useState } from "react";
import { Link2, Search, Loader2 } from "lucide-react";
import { Results } from "@/components/Results";
import { verifyDrugs, type VerifyResponse } from "@/lib/api";

const SAMPLE_STRIP = "Paracetamol\nAmoxicillin";

export default function VerificationBench() {
  const [value, setValue] = useState("");
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runCheck() {
    const names = value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);

    if (names.length === 0) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await verifyDrugs(names);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setLoading(false);
    }
  }

  function loadSample() {
    setValue(SAMPLE_STRIP);
  }

  return (
    <section id="verify" className="px-4 py-24 bg-[#0B0D11]">
      <div className="mx-auto max-w-6xl">
        <p className="mb-4 font-mono text-sm text-(--color-accent)">
          Verification bench
        </p>
        <h2 className="mb-10 max-w-2xl text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
          Enter what the packaging says. Read back what the index knows.
        </h2>

        <div className="mb-10 rounded-2xl border border-(--color-border) bg-(--color-surface-raised) p-6">
          <div className="mb-4 flex items-center gap-2 text-sm text-zinc-500">
            <Link2 className="h-4 w-4" />
            One medicine per line
          </div>

          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={"Paracetamol\nAmoxicillin"}
            rows={4}
            spellCheck={false}
            className="mb-6 w-full resize-none rounded-xl border border-(--color-border) bg-black/40 p-4 font-mono text-base text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-(--color-accent)"
          />

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={runCheck}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-full bg-(--color-accent) px-6 py-3 font-medium text-black transition-colors hover:bg-(--color-accent-dim) disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
              {loading ? "Verifying…" : "Verify entries"}
            </button>
            <button
              onClick={loadSample}
              disabled={loading}
              className="font-mono text-sm text-zinc-500 transition-colors hover:text-zinc-300"
            >
              use sample strip
            </button>
          </div>
        </div>

        {loading && (
          <div className="flex flex-col gap-6">
            {[0, 1].map((i) => (
              <div
                key={i}
                className="h-32 animate-pulse rounded-2xl border border-(--color-border) bg-(--color-surface-raised)"
              />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-900/50 bg-red-950/20 p-5 text-sm text-red-400">
            {error}
          </div>
        )}

        {result && !loading && (
          <Results drugs={result.drugs} interactions={result.interactions} />
        )}
      </div>
    </section>
  );
}