"use client";
export function DocumentsTable() {
  return (
    <div className="rounded-xl border">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/50"><tr><th className="p-3 text-left">Name</th><th className="p-3 text-left">Date</th><th className="p-3 text-left">Status</th><th className="p-3"></th></tr></thead>
        <tbody><tr><td colSpan={4} className="p-3 text-center text-muted-foreground">No documents yet.</td></tr></tbody>
      </table>
    </div>
  );
}
