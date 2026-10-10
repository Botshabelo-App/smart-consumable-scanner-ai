// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosInstance } from 'axios';

import { deleteToken, getToken, saveToken } from '../context/AuthContext';
import {
  AnalyticsResult, BarcodeInfo, Branch, Company, DashboardSummary, InspectionFilters, Report, ReviewRequest,
  ScanDetail, ScanResult, UserAccount,
} from '../types';

declare const __DEV__: boolean;

const API_BASE_URL = __DEV__ ? 'http://10.0.2.2:8000' : 'https://api.smartscanner.example.com';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SmartScanner) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36',
  },
});

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let onSessionExpired: (() => void) | null = null;

/** Called once by AuthProvider: an expired/invalid login sends the user back to the login screen. */
export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler;
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const url: string = error?.config?.url || '';
    const isAuthCall = url.includes('/auth/login') || url.includes('/auth/register');
    const status = error?.response?.status;
    const deactivated = status === 403 && error?.response?.data?.detail === 'Account deactivated';
    if ((status === 401 || deactivated) && !isAuthCall && (await getToken())) {
      await deleteToken();
      onSessionExpired?.();
      error.message = deactivated ? 'This account has been deactivated.' : 'Your session has expired. Please log in again.';
    }
    return Promise.reject(error);
  }
);

/** Readable message from an API error (FastAPI detail strings or validation lists). */
export function errorMessage(e: any): string {
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d: any) => `${(d.loc || []).slice(-1)[0] || ''}: ${d.msg}`).join('\n');
  return e?.message || 'Unknown error';
}

const OFFLINE_QUEUE_KEY = 'offline_scan_queue';

export async function login(email: string, password: string): Promise<string> {
  const { data } = await api.post('/auth/login', { email, password });
  await saveToken(data.access_token);
  return data.access_token;
}

export async function register(payload: {
  email: string;
  full_name: string;
  password: string;
  role: string;
  organization?: string;
  company_id?: string;
  branch_id?: string;
}): Promise<void> {
  await api.post('/auth/register', payload);
}

export async function logout(): Promise<void> {
  await deleteToken();
}

export interface ScanPayload {
  uri: string;
  productName?: string;
  brand?: string;
  barcodeCode?: string;
  batchNumber?: string;
  productionDate?: string;
  expiryDate?: string;
  location?: { latitude: number; longitude: number };
  companyId?: string;
  branchId?: string;
  deviceId?: string;
}

export async function analyzeImage(payload: ScanPayload): Promise<ScanResult> {
  try {
    return await uploadScan(payload);
  } catch (e) {
    await queueOfflineScan(payload);
    throw e;
  }
}

async function uploadScan(payload: ScanPayload): Promise<ScanResult> {
  const { uri, productName, brand, barcodeCode, batchNumber, productionDate, expiryDate, location, companyId, branchId, deviceId } = payload;
  const formData = new FormData();
  const filename = uri.split('/').pop() || 'scan.jpg';
  const match = /\.\w+$/.exec(filename);
  const type = match ? `image/${match[0].replace('.', '')}` : 'image/jpeg';

  formData.append('image', { uri, name: filename, type } as any);
  if (productName) formData.append('product_name', productName);
  if (brand) formData.append('brand', brand);
  if (barcodeCode) formData.append('barcode_code', barcodeCode);
  if (batchNumber) formData.append('batch_number', batchNumber);
  if (productionDate) formData.append('production_date', productionDate);
  if (expiryDate) formData.append('expiry_date', expiryDate);
  if (location) {
    formData.append('latitude', String(location.latitude));
    formData.append('longitude', String(location.longitude));
  }
  if (companyId) formData.append('company_id', companyId);
  if (branchId) formData.append('branch_id', branchId);
  if (deviceId) formData.append('device_id', deviceId);

  const { data } = await api.post('/scans/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return data;
}

function cleanFilters(f?: InspectionFilters) {
  const out: Record<string, string> = {};
  Object.entries(f || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && String(v).trim() !== '') out[k] = String(v).trim();
  });
  return out;
}

export async function getScans(filters?: InspectionFilters, limit = 100): Promise<ScanResult[]> {
  const { data } = await api.get('/scans/', { params: { ...cleanFilters(filters), limit } });
  return data;
}

export async function getScanDetail(scanId: string): Promise<ScanDetail> {
  const { data } = await api.get(`/scans/${scanId}/detail`);
  return data;
}

export async function correctScanField(scanId: string, field: string, value: string, reason: string): Promise<ScanDetail> {
  const { data } = await api.post(`/scans/${scanId}/corrections`, { field, value, reason });
  return data;
}

export async function signOffScan(
  scanId: string,
  payload: { decision: 'confirm' | 'override' | 'escalate'; final_result?: string; typed_name: string; acknowledged: boolean; comments?: string; override_reason?: string }
): Promise<ScanDetail> {
  const { data } = await api.post(`/scans/${scanId}/signoff`, payload);
  return data;
}

export async function getDashboardSummary(filters?: InspectionFilters): Promise<DashboardSummary> {
  const { data } = await api.get('/dashboard/summary', { params: cleanFilters(filters) });
  return data;
}

export async function getMe(): Promise<UserAccount> {
  const { data } = await api.get('/auth/me');
  return data;
}

export async function getUsers(): Promise<UserAccount[]> {
  const { data } = await api.get('/admin/inspectors');
  return data;
}

export async function createInspector(payload: {
  email: string; full_name: string; password: string; role: string; company_id?: string; branch_id?: string;
}): Promise<UserAccount> {
  const { data } = await api.post('/admin/inspectors', payload);
  return data;
}

export async function setUserActive(userId: string, active: boolean): Promise<UserAccount> {
  const { data } = await api.patch(`/admin/users/${userId}/activation`, { is_active: active });
  return data;
}

export async function resetUserPassword(userId: string, newPassword: string): Promise<UserAccount> {
  const { data } = await api.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword });
  return data;
}

export async function createBranch(companyId: string, name: string): Promise<Branch> {
  const { data } = await api.post('/admin/branches', { company_id: companyId, name });
  return data;
}

export async function generateBatchReport(format: 'pdf' | 'csv' | 'excel', filters?: InspectionFilters, notes?: string): Promise<Report> {
  const { data } = await api.post(`/reports/batch?format=${format}`, { ...cleanFilters(filters), notes });
  return data;
}

export async function updateReview(reviewId: string, status: 'approved' | 'rejected' | 'escalated', reviewerNotes: string): Promise<ReviewRequest> {
  const { data } = await api.patch(`/reviews/${reviewId}`, { status, reviewer_notes: reviewerNotes });
  return data;
}

export function apiBaseUrl(): string {
  return api.defaults.baseURL || '';
}

export async function getDashboardStats() {
  const { data } = await api.get('/dashboard/stats');
  return data;
}

export async function getAnalytics(): Promise<AnalyticsResult> {
  const { data } = await api.get('/analytics/');
  return data;
}

export async function lookupBarcode(code: string): Promise<BarcodeInfo> {
  const { data } = await api.get(`/products/barcodes/${encodeURIComponent(code)}`);
  return data;
}

export async function generateReport(
  scanId: string,
  format: 'pdf' | 'csv' | 'excel' = 'pdf',
  notes?: string
): Promise<Report> {
  const { data } = await api.post(`/reports/?format=${format}`, { scan_id: scanId, notes });
  return data;
}

export async function submitScanFeedback(
  scanId: string,
  accepted: boolean,
  overrideCondition?: string,
  reason?: string,
  additionalNotes?: string
): Promise<ScanResult> {
  const { data } = await api.post(`/scans/${scanId}/feedback`, {
    accepted,
    override_condition: overrideCondition,
    reason,
    additional_notes: additionalNotes,
  });
  return data;
}

export async function createReviewRequest(scanId: string, suggestedCondition: string, reviewerNotes?: string): Promise<ReviewRequest> {
  const { data } = await api.post('/reviews/', { scan_id: scanId, suggested_condition: suggestedCondition, reviewer_notes: reviewerNotes });
  return data;
}

export async function getReviewRequests(): Promise<ReviewRequest[]> {
  const { data } = await api.get('/reviews/');
  return data;
}

export async function getCompanies(): Promise<Company[]> {
  const { data } = await api.get('/admin/companies');
  return data;
}

export async function getBranches(companyId?: string): Promise<Branch[]> {
  const { data } = await api.get('/admin/branches', { params: { company_id: companyId } });
  return data;
}

interface QueuedScan extends ScanPayload {
  createdAt: string;
}

async function queueOfflineScan(scan: ScanPayload) {
  const existing: QueuedScan[] = JSON.parse((await AsyncStorage.getItem(OFFLINE_QUEUE_KEY)) || '[]');
  existing.push({ ...scan, createdAt: new Date().toISOString() });
  await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(existing));
}

export async function getOfflineScans(): Promise<QueuedScan[]> {
  return JSON.parse((await AsyncStorage.getItem(OFFLINE_QUEUE_KEY)) || '[]');
}

export async function clearOfflineScans(): Promise<void> {
  await AsyncStorage.removeItem(OFFLINE_QUEUE_KEY);
}

export async function syncOfflineScans(
  onProgress?: (completed: number, total: number) => void
): Promise<{ uploaded: number; failed: number }> {
  const queued: QueuedScan[] = JSON.parse((await AsyncStorage.getItem(OFFLINE_QUEUE_KEY)) || '[]');
  if (!queued.length) return { uploaded: 0, failed: 0 };

  let uploaded = 0;
  let failed = 0;
  const remaining: QueuedScan[] = [];

  for (let i = 0; i < queued.length; i++) {
    const scan = queued[i];
    try {
      await uploadScan(scan);
      uploaded += 1;
      onProgress?.(uploaded + failed, queued.length);
    } catch (e: any) {
      // Keep the scan in the queue if the failure looks like a network error.
      if (e.message?.includes('Network') || e.code === 'ECONNABORTED' || !e.response) {
        remaining.push(scan);
      } else {
        // Non-retryable server error; count as failed but still remove.
        failed += 1;
      }
    }
  }

  await AsyncStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(remaining));
  return { uploaded, failed };
}

export default api;
