"use client";
export function RecommendationCard({ title, body }: { title?: string; body?: string }) {
  return (
    <div className="rounded-xl border bg-card p-4">
      <h4 className="font-semibold text-sm">{title || "Recommendation"}</h4>
      <p className="text-sm text-muted-foreground mt-1">{body || "No details available."}</p>
      <button className="mt-2 text-xs px-3 py-1 rounded bg-secondary">Dismiss</button>
    </div>
  );
}
