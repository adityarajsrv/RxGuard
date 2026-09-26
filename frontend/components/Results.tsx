import ResultCard from "@/components/ResultCard";

export type Confidence = "high" | "medium" | "unverified";

export interface ResultEntry {
  initial: string;
  name: string;
  meta: string;
  salt: string;
  confidence: Confidence;
  score: string;
  note?: string;
  batchRef: string;
}

export function Results({ entries }: { entries: ResultEntry[] }) {
  return (
    <div className="flex flex-col gap-6">
      {entries.map((entry) => (
        <ResultCard key={entry.name} {...entry} />
      ))}
    </div>
  );
}