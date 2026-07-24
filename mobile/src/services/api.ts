import axios, { AxiosInstance } from 'axios';

import { DashboardStats, Report, ScanResult } from '../types';
import { getToken, saveToken, deleteToken } from '../context/AuthContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

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
}): Promise<void> {
  await api.post('/auth/register', payload);
}

export async function logout(): Promise<void> {
  await deleteToken();
}

export async function analyzeImage(
  uri: string,
  productName?: string,
  location?: { latitude: number; longitude: number }
): Promise<ScanResult> {
  try {
    return await uploadScan(uri, productName, location);
  } catch (e) {
    // Network failure: queue for later sync if offline mode is needed
    await queueOfflineScan({ uri, productName, location });
    throw e;
  }
}

async function uploadScan(
  uri: string,
  productName?: string,
  location?: { latitude: number; longitude: number }
): Promise<ScanResult> {
  const formData = new FormData();
  const filename = uri.split('/').pop() || 'scan.jpg';
  const match = /\.\w+$/.exec(filename);
  const type = match ? `image/${match[0].replace('.', '')}` : 'image/jpeg';

  formData.append('image', { uri, name: filename, type } as any);
  if (productName) formData.append('product_name', productName);
  if (location) {
    formData.append('latitude', String(location.latitude));
    formData.append('longitude', String(location.longitude));
  }

  const { data } = await api.post('/scans/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getScans(): Promise<ScanResult[]> {
  const { data } = await api.get('/scans/');
  return data;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await api.get('/dashboard/stats');
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

interface QueuedScan {
  uri: string;
  productName?: string;
  location?: { latitude: number; longitude: number };
  createdAt: string;
}

async function queueOfflineScan(scan: Omit<QueuedScan, 'createdAt'>) {
  const existing = JSON.parse((await AsyncStorage.getItem(OFFLINE_QUEUE_KEY)) || '[]');
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
