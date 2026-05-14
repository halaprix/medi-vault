"use client";

import { useState } from "react";
import api from "@/lib/api";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const { data } = await api.post("/documents/upload", form);
      setResult(`Uploaded: ${data.document_id} (${data.status})`);
    } catch (e: any) {
      setResult(`Error: ${e.response?.data?.detail || e.message}`);
    }
    setUploading(false);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="text-2xl font-bold">Upload Lab Results</h1>
      <div className="rounded-lg border-2 border-dashed p-8 text-center">
        <input
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,.tiff,.webp"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="mb-4"
        />
        <p className="text-sm text-gray-500">PDF, JPG, PNG, TIFF, WEBP — max 50MB</p>
      </div>
      <button
        disabled={!file || uploading}
        onClick={handleUpload}
        className="w-full rounded bg-primary px-4 py-3 text-white disabled:opacity-50"
      >
        {uploading ? "Uploading..." : "Upload & Process"}
      </button>
      {result && <p className="text-sm">{result}</p>}
    </div>
  );
}
