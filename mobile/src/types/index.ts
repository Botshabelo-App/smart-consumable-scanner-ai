// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

export type UserRole =
  | 'government_inspector'
  | 'municipal_health_inspector'
  | 'school_food_inspector'
  | 'restaurant_manager'
  | 'warehouse_inspector'
  | 'manufacturer_quality_inspector'
  | 'supermarket_manager'
  | 'wholesaler'
  | 'administrator'
  | 'company_admin'
  | 'inspector'
  | 'consumer';

export type ProductCategory =
  | 'food'
  | 'meat'
  | 'dairy'
  | 'seafood'
  | 'produce'
  | 'beverage'
  | 'packaged'
  | 'frozen'
  | 'dry'
  | 'other';

export type Condition = 'fresh' | 'near_expiry' | 'suspicious' | 'expired';

export interface Product {
  id: string;
  name: string;
  category?: ProductCategory;
  packaging_type?: string;
  manufacturer?: string;
}

export interface BarcodeInfo {
  id: string;
  code: string;
  product?: Product;
  batch_number?: string;
  production_date?: string;
  expiry_date?: string;
}

export interface ScanResult {
  id: string;
  product_id?: string;
  barcode_id?: string;
  company_id?: string;
  branch_id?: string;
  device_id?: string;
  product_name?: string;
  brand?: string;
  category?: ProductCategory;
  condition: Condition;
  confidence: number;
  packaging_type?: string;
  packaging_condition?: string;
  overall_result?: string;
  overall_reason?: string;
  label_confidence?: number;
  detected_fields?: string[];
  findings?: string[];
  expiry_risk?: string;
  barcode_code?: string;
  batch_number?: string;
  production_date?: string;
  expiry_date?: string;
  ai_vs_label_discrepancy?: boolean;
  discrepancy_reason?: string;
  image_path?: string;
  inspector_name?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
  inspector_accepted?: boolean | null;
  override_condition?: Condition;
  override_reason?: string;
  override_notes?: string;
  inspector_email?: string;
  inspector_id?: string;
  company_name?: string;
  branch_name?: string;
  ocr_raw_text?: string;
  date_details?: DateCandidate[];
  field_status?: Record<string, FieldStatus>;
  date_flags?: string[];
  review_status?: string;
  final_result?: string;
  final_decision?: string;
  signed_off_at?: string;
  signed_off_by_name?: string;
}

export type FieldStatus = 'detected' | 'needs_verification' | 'entered' | 'corrected';

export interface DateCandidate {
  type: 'expiry' | 'best_before' | 'production' | 'packaging' | 'unlabelled';
  original_text: string;
  matched_text: string;
  format: string;
  interpreted: string;
  status: 'detected' | 'needs_verification';
  note?: string;
}

export interface ScanCorrection {
  id: string;
  field: string;
  original_value?: string;
  new_value?: string;
  reason: string;
  user_id: string;
  user_name?: string;
  created_at: string;
}

export interface Signoff {
  id: string;
  full_name: string;
  typed_name: string;
  email: string;
  role: string;
  decision: 'confirm' | 'override' | 'escalate';
  system_result?: string;
  final_result?: string;
  comments?: string;
  override_reason?: string;
  acknowledgement_text: string;
  created_at: string;
}

export interface ScanDetail extends ScanResult {
  corrections: ScanCorrection[];
  signoffs: Signoff[];
  reviews: ReviewRequest[];
}

export interface InspectionFilters {
  date_from?: string;
  date_to?: string;
  branch_id?: string;
  inspector_id?: string;
  product?: string;
  result?: string;
  review_status?: string;
}

export interface SummaryCounts { total: number; pass: number; warning: number; review: number }

export interface DashboardSummary {
  total: number;
  today: number;
  pass_count: number;
  warning: number;
  review: number;
  insufficient_data: number;
  expired_products: number;
  awaiting_review: number;
  signed_off: number;
  recent: { id: string; product_name?: string; brand?: string; overall_result?: string; review_status?: string; inspector?: string; site?: string; created_at?: string }[];
  by_site: (SummaryCounts & { branch_id?: string; site: string })[];
  by_inspector: (SummaryCounts & { inspector_id?: string; inspector: string })[];
  trend: (SummaryCounts & { date: string })[];
}

export interface UserAccount {
  id: string;
  email: string;
  full_name: string;
  role: UserRole | 'inspector';
  organization?: string;
  company_id?: string;
  branch_id?: string;
  is_active: boolean;
}

export interface DashboardStats {
  total_scanned: number;
  fresh: number;
  near_expiry: number;
  expired: number;
  suspicious: number;
  reports_generated: number;
  average_confidence: number;
}

export interface AnalyticsResult {
  stats: DashboardStats;
  category_expiry: { category: ProductCategory; expired: number; near_expiry: number; suspicious: number; fresh: number }[];
  manufacturer_trends: { manufacturer_name: string; scan_count: number; expired_count: number; suspicious_count: number }[];
  time_series: { bucket: string; count: number; average_confidence: number }[];
  geographic_distribution: { latitude: number; longitude: number; count: number }[];
}

export interface Report {
  id: string;
  scan_id?: string;
  report_type?: string;
  format?: string;
  report_id: string;
  notes?: string;
  file_url?: string;
  generated_at: string;
}

export interface ReviewRequest {
  id: string;
  scan_id: string;
  suggested_condition?: Condition;
  reviewer_notes?: string;
  status: 'pending' | 'approved' | 'rejected' | 'escalated';
  user_id?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  requester_name?: string;
  reviewer_name?: string;
  created_at?: string;
}

export interface Company {
  id: string;
  name: string;
}

export interface Branch {
  id: string;
  company_id: string;
  name: string;
}
