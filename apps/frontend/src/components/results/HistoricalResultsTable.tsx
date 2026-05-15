"use client";
export function HistoricalResultsTable() {
  return (
    <div className="rounded-xl border overflow-auto">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/50"><tr><th className="p-3 text-left">Date</th><th className="p-3 text-left">Biomarker</th><th className="p-3 text-left">Value</th><th className="p-3 text-left">Range</th></tr></thead>
        <tbody><tr><td colSpan={4} className="p-3 text-center text-muted-foreground">No historical data.</td></tr></tbody>
      </table>
    </div>
  );
}
