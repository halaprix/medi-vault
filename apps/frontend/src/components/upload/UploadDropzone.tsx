"use client";
import { useCallback, useState } from "react";
export function UploadDropzone({ onUpload }: { onUpload: (file: File) => void }) {
  const [drag, setDrag] = useState(false);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDrag(false);
    const file = e.dataTransfer.files[0];
    if (file) onUpload(file);
  }, [onUpload]);
  return (
    <div
      className={`rounded-xl border-2 border-dashed p-8 text-center transition-colors ${drag ? "border-primary bg-primary/5" : "border-muted-foreground/25"}`}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
    >
      <p className="text-muted-foreground">Drop PDF here or click to upload</p>
      <input type="file" accept=".pdf" className="mt-2 text-sm" onChange={e => e.target.files?.[0] && onUpload(e.target.files[0])} />
    </div>
  );
}
