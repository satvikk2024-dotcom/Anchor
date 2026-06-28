import { matchScoreTier, type MatchScoreTier } from "@/lib/format";

const TIER_CLASSES: Record<MatchScoreTier, string> = {
  high: "bg-success/10 text-success",
  medium: "bg-warning/10 text-warning",
  low: "bg-danger/10 text-danger",
  unknown: "bg-fg-muted/10 text-fg-muted",
};

export default function MatchScoreBadge({ score }: { score: number | null }) {
  const tier = matchScoreTier(score);
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-micro font-semibold ${TIER_CLASSES[tier]}`}
    >
      {score == null ? "—" : score}
    </span>
  );
}
