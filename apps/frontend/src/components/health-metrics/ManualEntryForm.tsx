"use client";
export function ManualEntryForm() {
  return (
    <form className="space-y-3">
      <select className="w-full rounded-lg border px-3 py-2 text-sm"><option>Select metric...</option></select>
      <input type="number" placeholder="Value" className="w-full rounded-lg border px-3 py-2 text-sm" />
      <input type="date" className="w-full rounded-lg border px-3 py-2 text-sm" />
      <button type="submit" className="w-full rounded-lg bg-primary text-primary-foreground px-4 py-2 text-sm">Add Entry</button>
    </form>
  );
}
