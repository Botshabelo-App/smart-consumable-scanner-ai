// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import AsyncStorage from '@react-native-async-storage/async-storage';

import { brand } from '../config/brand';
import api from './api';
import { fetchRemoteBackendUrl } from './remoteConfig';

declare const __DEV__: boolean;

const API_URL_KEY = '@SmartScanner:apiBaseUrl';

const PRODUCTION_DEFAULT = brand.defaultBackendUrl;
const DEVELOPMENT_DEFAULT = 'http://10.0.2.2:8000';

export const getApiBaseUrl = async (): Promise<string> => {
  const stored = await AsyncStorage.getItem(API_URL_KEY);
  if (stored) return stored;
  return __DEV__ ? DEVELOPMENT_DEFAULT : PRODUCTION_DEFAULT;
};

export const setApiBaseUrl = async (url: string): Promise<void> => {
  const trimmed = url.trim();
  const normalized = trimmed.endsWith('/') ? trimmed.slice(0, -1) : trimmed;
  await AsyncStorage.setItem(API_URL_KEY, normalized);
  api.defaults.baseURL = normalized;
};

export const configureApiBaseUrl = async (): Promise<string> => {
  const candidates: (string | null)[] = [
    // 1. Try the current remote config URL first so the backend can move
    //    without a new APK.
    await fetchRemoteBackendUrl(),
    // 2. Fall back to the last known working URL.
    await getApiBaseUrl(),
    // 3. Fall back to the built-in default.
    PRODUCTION_DEFAULT,
  ];

  for (const candidate of candidates) {
    if (!candidate || candidate.includes('example.com')) continue;
    const normalized = candidate.trim().replace(/\/$/, '');
    try {
      api.defaults.baseURL = normalized;
      await api.get('/health');
      await AsyncStorage.setItem(API_URL_KEY, normalized);
      return normalized;
    } catch {
      // Try the next candidate.
    }
  }

  // If nothing works, keep the built-in default so the user can change it manually.
  await setApiBaseUrl(PRODUCTION_DEFAULT);
  return PRODUCTION_DEFAULT;
};

export const isDefaultPlaceholderUrl = (url: string): boolean => {
  return url.includes('example.com');
};
