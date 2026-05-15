// ===== Shared API types for medi-vault frontend =====

// User / Auth
export interface UserProfile {
  id: string;
  display_name: string;
  created_at: string;
  is_setup: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserProfile;
}

export interface SetupResponse {
  access_token: string;
  token_type: string;
}

// Biomarkers
export interface Biomarker {
  id: string;
  loinc_code: string;
  display_name: string;
  category: string;
  standard_unit: string;
  reference_range_low: number | null;
  reference_range_high: number | null;
}

export type BiomarkerCategory =
  | "Complete Blood Count"
  | "Metabolic Panel"
  | "Lipid Panel"
  | "Thyroid Panel"
  | "Vitamins & Minerals"
  | "Hormones"
  | "Cardiac Markers"
  | "Coagulation"
  | "Urinalysis"
  | "Other";

// Documents
export type DocumentStatus =
  | "pending"
  | "processing"
  | "ocr_complete"
  | "llm_complete"
  | "normalized"
  | "complete"
  | "failed";

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  lab_name: string | null;
  collection_date: string | null;
  result_count: number;
  created_at: string;
  updated_at: string;
  error_message?: string | null;
}

export interface DocumentDetail extends Document {
  ocr_text: string | null;
  llm_json: Record<string, unknown> | null;
  results: TestResult[];
}

// Test Results
export interface TestResult {
  id: string;
  document_id: string;
  biomarker_id: string;
  biomarker_display_name: string;
  category: string;
  value: number;
  standard_unit: string;
  reference_range_low: number | null;
  reference_range_high: number | null;
  is_out_of_range: boolean;
  out_of_range_direction: "low" | "high" | null;
  result_date: string;
  notes: string | null;
  created_at: string;
}

export interface TestResultSummary {
  biomarker_id: string;
  display_name: string;
  category: string;
  latest_value: number;
  unit: string;
  is_out_of_range: boolean;
  direction: "low" | "high" | null;
  result_count: number;
  first_date: string;
  last_date: string;
}

export interface TestResultTrend {
  biomarker_id: string;
  display_name: string;
  unit: string;
  points: TrendPoint[];
  reference_low: number | null;
  reference_high: number | null;
}

export interface TrendPoint {
  result_date: string;
  value: number;
  document_id: string;
  is_out_of_range: boolean;
}

// Health Metrics
export type HealthMetricType = "weight_kg" | "steps" | "sleep_hours" | "resting_hr";

export interface HealthMetric {
  id: string;
  metric_type: HealthMetricType;
  value: number;
  unit: string;
  recorded_at: string;
  source: "manual" | "google_fit";
  created_at: string;
}

export interface HealthMetricSummary {
  metric_type: HealthMetricType;
  unit: string;
  latest_value: number;
  previous_value: number | null;
  change: number | null;
  change_pct: number | null;
  avg_7d: number;
  avg_30d: number;
  min_30d: number;
  max_30d: number;
}

// Google Fit
export interface GoogleFitStatus {
  connected: boolean;
  email: string | null;
  last_sync: string | null;
  next_sync: string | null;
  sync_status: "idle" | "syncing" | "error";
  sync_error: string | null;
}

export interface SyncJob {
  id: string;
  status: "pending" | "running" | "complete" | "failed";
  started_at: string | null;
  completed_at: string | null;
  metrics_synced: number;
  error_message: string | null;
}

// Recommendations
export interface Recommendation {
  id: string;
  biomarker_id: string;
  biomarker_display_name: string;
  result_value: number;
  direction: "low" | "high";
  content: string;
  sources: RecommendationSource[];
  dismissed: boolean;
  created_at: string;
}

export interface RecommendationSource {
  title: string;
  url: string | null;
  snippet: string;
}

// Settings
export interface UserSettings {
  display_name: string;
  unit_system: "metric" | "imperial";
  theme: "light" | "dark" | "system";
  google_fit_connected: boolean;
  google_fit_email: string | null;
}

export interface OllamaStatus {
  running: boolean;
  model: string;
  version: string | null;
}

// API responses
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  error_code?: string;
}
