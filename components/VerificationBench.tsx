"use client";

import { useState } from "react";
import { Link2, Search, Upload } from "lucide-react";
import { Results, type ResultEntry } from "@/components/Results";

const SAMPLE_STRIP = "Paracetamol 500\nAmoxicillin 250\nZyntrexil";

const SAMPLE_RESULTS: ResultEntry[] = [
  {
    initial: "P",
    name: "Paracetamol",
    meta: "500 mg · Film-coated tablet",
    salt: "Acetaminophen",
    confidence: "high",
    score: "98.4%",
    batchRef: "PCM-4471-B",
  },
  {
    initial: "A",
    name: "Amoxicillin",
    meta: "250 mg · Capsule",
    salt: "Amoxicillin trihydrate",
    confidence: "medium",
    score: "81.2%",
    note: "Strength inferred from packaging text — confirm against the printed strip.",
    batchRef: "AMX-7318-C",
  },
  {
    initial: "Z",
    name: "Zyntrexil",
    meta: "Not resolved · Unknown form",
    salt: "No salt match in reference index",
    confidence: "unverified",
    score: "31.6%",
    note: "No entry matched this name closely enough to report. Check the spelling on the strip, or confirm with a pharmacist.",
    batchRef: "—",
  },
];

export default function VerificationBench() {
  const [value, setValue] = useState("");
  const [results, setResults] = useState<ResultEntry[] | null>(null);

  function runCheck() {
    if (!value.trim()) return;
    setResults(SAMPLE_RESULTS);
  }

  function loadSample() {
    setValue(SAMPLE_STRIP);
    setResults(SAMPLE_RESULTS);
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
            One medicine per line — name and strength
          </div>

          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={"Paracetamol 500\nAmoxicillin 250"}
            rows={4}
            spellCheck={false}
            className="mb-6 w-full resize-none rounded-xl border border-(--color-border) bg-black/40 p-4 font-mono text-base text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-(--color-accent)"
          />

          <div className="flex flex-wrap items-center gap-4">
            <button
              onClick={runCheck}
              className="inline-flex items-center gap-2 rounded-full bg-(--color-accent) px-6 py-3 font-medium text-black transition-colors hover:bg-(--color-accent-dim)"
            >
              <Search className="h-4 w-4" />
              Verify entries
            </button>
            <button className="inline-flex items-center gap-2 rounded-full border border-(--color-border) px-6 py-3 font-medium text-zinc-200 transition-colors hover:bg-black/40">
              <Upload className="h-4 w-4" />
              Upload a list
            </button>
            <button
              onClick={loadSample}
              className="font-mono text-sm text-zinc-500 transition-colors hover:text-zinc-300"
            >
              use sample strip
            </button>
          </div>
        </div>

        {results && <Results entries={results} />}
      </div>
    </section>
  );
}