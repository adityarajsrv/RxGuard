import ResultCard from "@/components/ResultCard";
import type { DrugCardResult, InteractionResult } from "@/lib/api";

export function Results({
  drugs,
  interactions,
}: {
  drugs: DrugCardResult[];
  interactions: InteractionResult[];
}) {
  return (
    <div className="flex flex-col gap-6">
      {drugs.map((drug) => {
        const relevantInteractions = interactions.filter(
          (i) =>
            i.drug_a === drug.composition.drug_name_input ||
            i.drug_b === drug.composition.drug_name_input
        );
        return (
          <ResultCard
            key={drug.composition.drug_name_input}
            drug={drug}
            interactions={relevantInteractions}
          />
        );
      })}
    </div>
  );
}