// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import AsyncStorage from '@react-native-async-storage/async-storage';
import axios, { AxiosInstance } from 'axios';

import { deleteToken, getToken, saveToken } from '../context/AuthContext';
import { AnalyticsResult, BarcodeInfo, Branch, Company, Report, ReviewRequest, ScanResult } from '../types';

declare const __DEV__: boolean;

const API_BASE_URL = __DEV__ ? 'http://10.0.2.2:8000' : 'https://api.smartscanner.example.com';

const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

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
  const { uri, productName, barcodeCode, batchNumber, productionDate, expiryDate, location, companyId, branchId, deviceId } = payload;
  const formData = new FormData();
  const filename = uri.split('/').pop() || 'scan.jpg';
  const match = /\.\w+$/.exec(filename);
  const type = match ? `image/${match[0].replace('.', '')}` : 'image/jpeg';

  formData.append('image', { uri, name: filename, type } as any);
  if (productName) formData.append('product_name', productName);
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

export async function getScans(): Promise<ScanResult[]> {
  const { data } = await api.get('/scans/');
  return data;
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

export default api;
