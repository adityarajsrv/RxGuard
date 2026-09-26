import {
  ShieldCheck,
  TriangleAlert,
  CircleHelp,
  ChevronDown,
} from "lucide-react";

type Confidence = "high" | "medium" | "unverified";

interface ResultCardProps {
  initial: string;
  name: string;
  meta: string;
  salt: string;
  confidence: Confidence;
  score: string;
  note?: string;
  batchRef: string;
}

const confidenceStyles: Record<
  Confidence,
  { icon: typeof ShieldCheck; classes: string; label: string }
> = {
  high: {
    icon: ShieldCheck,
    classes:
      "border-emerald-800 bg-emerald-950/40 text-emerald-400",
    label: "High confidence",
  },
  medium: {
    icon: TriangleAlert,
    classes:
      "border-amber-800 bg-amber-950/40 text-amber-400",
    label: "Medium confidence",
  },
  unverified: {
    icon: CircleHelp,
    classes:
      "border-[var(--color-border)] bg-black/30 text-zinc-400",
    label: "Unverified",
  },
};

export default function ResultCard({
  initial,
  name,
  meta,
  salt,
  confidence,
  score,
  note,
  batchRef,
}: ResultCardProps) {
  const { icon: Icon, classes, label } = confidenceStyles[confidence];

  return (
    <div className="rounded-2xl border border-(--color-border) bg-(--color-surface-raised) p-6 sm:p-8">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-zinc-800 font-mono text-lg">
            {initial}
          </div>

          <div>
            <p className="font-mono text-lg">{name}</p>
            <p className="text-sm text-zinc-500">{meta}</p>
            <p className="mt-1 text-sm text-zinc-400">{salt}</p>
          </div>
        </div>

        <span
          className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-sm ${classes}`}
        >
          <Icon className="h-4 w-4" />
          {label} <span className="font-mono">{score}</span>
        </span>
      </div>

      {note && (
        <div className="mb-5 rounded-xl border border-(--color-border) bg-black/30 p-4 text-sm text-zinc-400">
          {note}
        </div>
      )}

      <div className="flex items-center justify-between border-t border-(--color-border) pt-4">
        <span className="font-mono text-sm text-zinc-500">
          Batch ref {batchRef}
        </span>

        <button className="inline-flex items-center gap-2 rounded-full border border-(--color-border) px-4 py-2 text-sm font-medium text-zinc-200 transition-colors hover:bg-black/40">
          Equivalents &amp; interactions
          <ChevronDown className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}