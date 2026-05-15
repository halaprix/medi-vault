"use client";
export function PINManagement() {
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">PIN Management</h3>
      <input type="password" placeholder="New PIN" className="w-full rounded-lg border px-3 py-2 text-sm" />
      <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm">Update PIN</button>
    </div>
  );
}
