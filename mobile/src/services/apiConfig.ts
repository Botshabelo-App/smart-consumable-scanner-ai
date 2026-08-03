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
  let url: string | null = null;

  // 1. Try to fetch the current backend URL from the remote config file.
  //    This allows the pilot backend to move (e.g. new Cloudflare tunnel)
  //    without requiring a new APK.
  url = await fetchRemoteBackendUrl();
  if (url) {
    await setApiBaseUrl(url);
    return url;
  }

  // 2. Fall back to the last known URL.
  url = await getApiBaseUrl();
  await setApiBaseUrl(url);
  return url;
};

export const isDefaultPlaceholderUrl = (url: string): boolean => {
  return url.includes('example.com');
};
