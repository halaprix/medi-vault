"use client";
export function GoogleFitSyncPanel() {
  return (
    <div className="rounded-xl border bg-card p-4">
      <h3 className="font-semibold">Google Fit</h3>
      <p className="text-sm text-muted-foreground mt-1">Connect to sync health data.</p>
      <button className="mt-2 px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm">Connect Google Fit</button>
    </div>
  );
}
