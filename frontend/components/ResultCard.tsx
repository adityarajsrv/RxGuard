"use client";

import { useState } from "react";
import {
  ShieldCheck,
  TriangleAlert,
  CircleHelp,
  ChevronDown,
  Send,
  Loader2,
} from "lucide-react";
import type { DrugCardResult, InteractionResult } from "@/lib/api";
import { askAboutDrug } from "@/lib/api";

const confidenceStyles = {
  high: {
    icon: ShieldCheck,
    classes: "border-emerald-800 bg-emerald-950/40 text-emerald-400",
    label: "High confidence",
  },
  medium: {
    icon: TriangleAlert,
    classes: "border-amber-800 bg-amber-950/40 text-amber-400",
    label: "Medium confidence",
  },
  unverified: {
    icon: CircleHelp,
    classes: "border-[var(--color-border)] bg-black/30 text-zinc-400",
    label: "Unverified",
  },
} as const;

function formatStrength(strengthMg: Record<string, number>): string {
  const entries = Object.entries(strengthMg);
  if (entries.length === 0) return "";
  return entries.map(([name, mg]) => `${name} ${mg}mg`).join(" + ");
}

type Tab = "equivalents" | "interactions" | "ask";
const TAB_LABELS: Record<Tab, string> = {
  equivalents: "Equivalents",
  interactions: "Interactions",
  ask: "Ask",
};

export default function ResultCard({
  drug,
  interactions,
}: {
  drug: DrugCardResult;
  interactions: InteractionResult[];
}) {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("equivalents");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<string | null>(null);
  const [verified, setVerified] = useState<boolean | null>(null);
  const [asking, setAsking] = useState(false);

  const { composition, equivalents } = drug;
  const { icon: Icon, classes, label } = confidenceStyles[composition.confidence];
  const initial = composition.drug_name_input.charAt(0).toUpperCase();
  const strengthLabel = formatStrength(composition.strength_mg);
  const saltLabel =
    composition.active_ingredients.length > 0
      ? composition.active_ingredients.join(", ")
      : "No ingredients confirmed";
  const sourcesLabel = `${composition.sources_checked.length} source${
    composition.sources_checked.length === 1 ? "" : "s"
  } checked`;

  async function handleAsk() {
    if (!question.trim()) return;
    setAsking(true);
    setAnswer(null);
    setVerified(null);
    try {
      const res = await askAboutDrug(composition.drug_name_input, question, composition.confidence);
      setAnswer(res.answer);
      setVerified(res.verified ?? null);
    } catch {
      setAnswer("Could not get an answer right now.");
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="rounded-2xl border border-(--color-border) bg-(--color-surface-raised) p-6 sm:p-8">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-zinc-800 font-mono text-lg">
            {initial}
          </div>
          <div>
            <p className="font-mono text-lg">{composition.drug_name_input}</p>
            <p className="text-sm text-zinc-500">
              {strengthLabel || "Strength not confirmed"} · {sourcesLabel}
            </p>
            <p className="mt-1 text-sm text-zinc-400">{saltLabel}</p>
          </div>
        </div>

        <span className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${classes}`}>
          <Icon className="h-4 w-4" />
          {label}
        </span>
      </div>

      {composition.disagreement_reason && (
        <div className="mb-5 rounded-xl border border-(--color-border) bg-black/30 p-4 text-sm text-zinc-400">
          {composition.disagreement_reason}
        </div>
      )}

      {composition.usage_context && (
        <div className="mb-5 rounded-xl border border-(--color-border) bg-black/20 p-4 text-sm text-zinc-300">
          <p className="mb-1 font-medium text-zinc-400">Typically used for</p>
          <p>{composition.usage_context}</p>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-(--color-border) pt-4">
        <span className="font-mono text-xs text-zinc-500">
          {composition.sources_checked.map((s) => s.source_name).join(" · ") || "no sources"}
        </span>

        <button
          onClick={() => setExpanded((v) => !v)}
          className="inline-flex items-center gap-2 rounded-full border border-(--color-border) px-4 py-2 text-sm font-medium text-zinc-200 transition-colors duration-200 ease-out hover:bg-black/40"
        >
          Details
          <ChevronDown
            className="h-4 w-4 transition-transform duration-200 ease-out"
            style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
          />
        </button>
      </div>

      <div
        className="grid transition-[grid-template-rows] duration-250 ease-out"
        style={{ gridTemplateRows: expanded ? "1fr" : "0fr" }}
      >
        <div className="overflow-hidden">
          <div className="mt-5 border-t border-(--color-border) pt-5">
            <div className="mb-4 inline-flex gap-1 rounded-full border border-(--color-border) p-1">
              {(Object.keys(TAB_LABELS) as Tab[]).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors duration-150 ease-out ${
                    activeTab === tab
                      ? "bg-(--color-accent) text-black"
                      : "text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {TAB_LABELS[tab]}
                </button>
              ))}
            </div>

            {activeTab === "equivalents" && (
              <div>
                {equivalents.length === 0 ? (
                  <p className="text-sm text-zinc-500">
                    {composition.confidence === "high"
                      ? "No equivalents found."
                      : "Equivalents unavailable at this confidence level."}
                  </p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {equivalents.map((eq) => (
                      <a
                        key={eq.brand_name}
                        href={eq.source_url || undefined}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between rounded-lg border border-(--color-border) px-4 py-2.5 text-sm transition-colors duration-150 ease-out hover:bg-black/30"
                      >
                        <span>{eq.brand_name}</span>
                        <span className="font-mono text-zinc-400">
                          {eq.price_inr != null ? `₹${eq.price_inr}` : "—"}
                          {eq.seller ? ` · ${eq.seller}` : ""}
                        </span>
                      </a>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "interactions" && (
              <div>
                {interactions.length === 0 ? (
                  <p className="text-sm text-zinc-500">No other drugs to check against.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {interactions.map((i, idx) => (
                      <div key={idx} className="rounded-lg border border-(--color-border) px-4 py-3 text-sm">
                        <div className="mb-1 flex items-center justify-between gap-3">
                          <span className="font-mono text-zinc-300">{i.drug_a} + {i.drug_b}</span>
                          <span className={
                            i.verdict === "known_interaction" ? "text-amber-400"
                            : i.verdict === "cannot_verify" ? "text-zinc-500"
                            : "text-emerald-400"
                          }>
                            {i.verdict.replace(/_/g, " ")}
                          </span>
                        </div>
                        {i.description && <p className="text-zinc-500">{i.description}</p>}
                        {i.source && <p className="mt-1 font-mono text-xs text-zinc-600">source: {i.source}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === "ask" && (
              <div>
                <div className="mb-3 flex gap-2">
                  <input
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAsk()}
                    placeholder={`Ask about ${composition.drug_name_input}…`}
                    className="flex-1 rounded-lg border border-(--color-border) bg-black/40 px-3 py-2 text-sm outline-none placeholder:text-zinc-600 transition-colors duration-150 ease-out focus:border-(--color-accent)"
                  />
                  <button
                    onClick={handleAsk}
                    disabled={asking || !question.trim()}
                    className="flex items-center justify-center rounded-lg bg-(--color-accent) px-3 text-black transition-colors duration-150 ease-out disabled:opacity-50"
                  >
                    {asking ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </button>
                </div>

                {answer && (
                  <div className="rounded-lg border border-(--color-border) bg-black/20 p-3 text-sm text-zinc-300 animate-[fadeIn_200ms_var(--ease-out)]">
                    <p>{answer}</p>
                    {verified === true && (
                      <p className="mt-2 flex items-center gap-1 text-xs text-emerald-400">
                        <ShieldCheck className="h-3 w-3" /> Checked against source — no unsupported claims found
                      </p>
                    )}
                    {verified === false && (
                      <p className="mt-2 flex items-center gap-1 text-xs text-amber-400">
                        <TriangleAlert className="h-3 w-3" /> Could not fully confirm this against the source — verify independently
                      </p>
                    )}
                  </div>
                )}

                {!answer && !asking && (
                  <p className="text-xs text-zinc-600">
                    Answers are grounded in the FDA label only — it will say so if it can&apos;t find a reliable answer.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}