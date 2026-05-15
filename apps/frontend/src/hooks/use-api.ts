import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import type {
  Document,
  DocumentDetail,
  TestResultSummary,
  TestResultTrend,
  HealthMetric,
  HealthMetricSummary,
  GoogleFitStatus,
  SyncJob,
  Recommendation,
  UserSettings,
  OllamaStatus,
  PaginatedResponse,
  LoginResponse,
} from "@/types";

// ===== Auth =====
export function useLogin() {
  return useMutation({
    mutationFn: (pin: string) =>
      api.post<LoginResponse>("/auth/login", { pin }).then((r) => r.data),
  });
}

export function useSetup() {
  return useMutation({
    mutationFn: (pin: string) =>
      api.post<LoginResponse>("/auth/setup", { pin }).then((r) => r.data),
  });
}

// ===== Dashboard =====
export function useResultsSummary() {
  return useQuery<TestResultSummary[]>({
    queryKey: ["results", "summary"],
    queryFn: () => api.get("/results/summary").then((r) => r.data),
  });
}

export function useOutOfRange() {
  return useQuery<TestResultSummary[]>({
    queryKey: ["results", "out-of-range"],
    queryFn: () => api.get("/results/out-of-range").then((r) => r.data),
  });
}

// ===== Documents =====
export function useDocuments() {
  return useQuery<PaginatedResponse<Document>>({
    queryKey: ["documents"],
    queryFn: () => api.get("/documents/?per_page=50").then((r) => r.data),
  });
}

export function useDocument(id: string) {
  return useQuery<DocumentDetail>({
    queryKey: ["documents", id],
    queryFn: () => api.get(`/documents/${id}`).then((r) => r.data),
    enabled: !!id,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return api.post("/documents/upload", form).then((r) => r.data);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useReprocessDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/documents/${id}/reprocess`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

// ===== Results =====
export function useResults(params?: Record<string, string>) {
  return useQuery<PaginatedResponse<TestResultSummary>>({
    queryKey: ["results", params],
    queryFn: () =>
      api.get("/results/", { params }).then((r) => r.data),
  });
}

export function useResultTrend(biomarkerId: string) {
  return useQuery<TestResultTrend>({
    queryKey: ["results", "trend", biomarkerId],
    queryFn: () =>
      api.get(`/results/${biomarkerId}/trend`).then((r) => r.data),
    enabled: !!biomarkerId,
  });
}

// ===== Health Metrics =====
export function useHealthMetrics(params?: Record<string, string>) {
  return useQuery<PaginatedResponse<HealthMetric>>({
    queryKey: ["metrics", params],
    queryFn: () =>
      api.get("/metrics/", { params }).then((r) => r.data),
  });
}

export function useHealthMetricsSummary() {
  return useQuery<HealthMetricSummary[]>({
    queryKey: ["metrics", "summary"],
    queryFn: () => api.get("/metrics/summary").then((r) => r.data),
  });
}

export function useManualEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: {
      metric_type: string;
      value: number;
      recorded_at: string;
    }) => api.post("/metrics/", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

// ===== Google Fit =====
export function useGoogleFitStatus() {
  return useQuery<GoogleFitStatus>({
    queryKey: ["google-fit", "status"],
    queryFn: () => api.get("/google-fit/status").then((r) => r.data),
  });
}

export function useGoogleFitSync() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      api.post("/google-fit/sync").then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["google-fit"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

export function useSyncHistory() {
  return useQuery<SyncJob[]>({
    queryKey: ["google-fit", "history"],
    queryFn: () =>
      api.get("/google-fit/sync-history").then((r) => r.data),
  });
}

// ===== Recommendations =====
export function useRecommendations(biomarkerId?: string) {
  return useQuery<Recommendation[]>({
    queryKey: ["recommendations", biomarkerId],
    queryFn: () =>
      api
        .get("/recommendations/", {
          params: biomarkerId ? { biomarker_id: biomarkerId } : {},
        })
        .then((r) => r.data),
  });
}

export function useGenerateRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (biomarkerId: string) =>
      api
        .post("/recommendations/generate", { biomarker_id: biomarkerId })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

export function useDismissRecommendation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      api.post(`/recommendations/${id}/dismiss`).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["recommendations"] });
    },
  });
}

// ===== Settings =====
export function useSettings() {
  return useQuery<UserSettings>({
    queryKey: ["settings"],
    queryFn: () => api.get("/settings").then((r) => r.data),
  });
}

export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<UserSettings>) =>
      api.put("/settings", data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["settings"] });
    },
  });
}

export function useOllamaStatus() {
  return useQuery<OllamaStatus>({
    queryKey: ["ollama", "status"],
    queryFn: () => api.get("/ollama/status").then((r) => r.data),
    refetchInterval: 30_000,
  });
}

// ===== Biomarkers Reference =====
export function useBiomarkers(params?: { search?: string; category?: string }) {
  return useQuery({
    queryKey: ["biomarkers", params],
    queryFn: () =>
      api.get("/biomarkers/", { params }).then((r) => r.data),
  });
}
