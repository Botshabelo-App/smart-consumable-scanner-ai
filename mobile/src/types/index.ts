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
  scan_id: string;
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
  status: 'pending' | 'approved' | 'rejected';
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
