"use client";
const steps = ["Uploading", "OCR Processing", "LLM Extraction", "Normalization", "Complete"];
export function ProcessingStatusTracker({ currentStep = 0 }: { currentStep?: number }) {
  return (
    <div className="space-y-2">
      {steps.map((step, i) => (
        <div key={step} className={`flex items-center gap-2 text-sm ${i <= currentStep ? "text-primary" : "text-muted-foreground"}`}>
          <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${i <= currentStep ? "bg-primary text-primary-foreground" : "bg-muted"}`}>{i <= currentStep ? "✓" : i + 1}</span>
          {step}
        </div>
      ))}
    </div>
  );
}
