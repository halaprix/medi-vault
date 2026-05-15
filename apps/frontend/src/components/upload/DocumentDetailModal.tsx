"use client";
export function DocumentDetailModal({ docId, onClose }: { docId?: string; onClose: () => void }) {
  if (!docId) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="bg-background rounded-xl p-6 max-w-lg w-full mx-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-lg font-semibold">Document Details</h2>
        <p className="text-sm text-muted-foreground mt-2">ID: {docId}</p>
        <button onClick={onClose} className="mt-4 px-4 py-2 rounded-lg bg-secondary text-sm">Close</button>
      </div>
    </div>
  );
}
