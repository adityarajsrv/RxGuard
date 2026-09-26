"use client";

import { useState } from "react";
import {
  ShieldCheck,
  TriangleAlert,
  CircleHelp,
  ChevronDown,
} from "lucide-react";
import type { DrugCardResult, InteractionResult } from "@/lib/api";

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

export default function ResultCard({
  drug,
  interactions,
}: {
  drug: DrugCardResult;
  interactions: InteractionResult[];
}) {
  const [expanded, setExpanded] = useState(false);
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

        <span
          className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${classes}`}
        >
          <Icon className="h-4 w-4" />
          {label}
        </span>
      </div>

      {composition.disagreement_reason && (
        <div className="mb-5 rounded-xl border border-(--color-border) bg-black/30 p-4 text-sm text-zinc-400">
          {composition.disagreement_reason}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-(--color-border) pt-4">
        <span className="font-mono text-xs text-zinc-500">
          {composition.sources_checked.map((s) => s.source_name).join(" · ") || "no sources"}
        </span>

        <button
          onClick={() => setExpanded((v) => !v)}
          className="inline-flex items-center gap-2 rounded-full border border-(--color-border) px-4 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-black/40"
        >
          Equivalents &amp; interactions
          <ChevronDown
            className={`h-4 w-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </button>
      </div>

      {expanded && (
        <div className="mt-5 flex flex-col gap-5 border-t border-(--color-border) pt-5">
          <div>
            <p className="mb-3 text-sm font-medium text-zinc-300">Equivalents</p>
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
                    className="flex items-center justify-between rounded-lg border border-(--color-border) px-4 py-2.5 text-sm hover:bg-black/30"
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

          <div>
            <p className="mb-3 text-sm font-medium text-zinc-300">Interactions</p>
            {interactions.length === 0 ? (
              <p className="text-sm text-zinc-500">No other drugs to check against.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {interactions.map((i, idx) => (
                  <div
                    key={idx}
                    className="rounded-lg border border-(--color-border) px-4 py-3 text-sm"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-mono text-zinc-300">
                        {i.drug_a} + {i.drug_b}
                      </span>
                      <span
                        className={
                          i.verdict === "known_interaction"
                            ? "text-amber-400"
                            : i.verdict === "cannot_verify"
                            ? "text-zinc-500"
                            : "text-emerald-400"
                        }
                      >
                        {i.verdict.replace(/_/g, " ")}
                      </span>
                    </div>
                    {i.description && (
                      <p className="text-zinc-500">{i.description}</p>
                    )}
                    {i.source && (
                      <p className="mt-1 font-mono text-xs text-zinc-600">
                        source: {i.source}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}