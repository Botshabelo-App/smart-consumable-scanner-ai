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

export interface ScanResult {
  id: string;
  product_name?: string;
  category?: ProductCategory;
  condition: Condition;
  confidence: number;
  packaging_type?: string;
  findings?: string[];
  expiry_risk?: string;
  image_path?: string;
  inspector_name?: string;
  latitude?: number;
  longitude?: number;
  created_at: string;
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

export interface Report {
  id: string;
  scan_id: string;
  report_id: string;
  notes?: string;
  file_url?: string;
  generated_at: string;
}
