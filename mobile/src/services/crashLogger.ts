// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import * as Application from 'expo-application';
import { Platform } from 'react-native';

import api from './api';

function getDeviceId(): string {
  try {
    if (Platform.OS === 'android') {
      return Application.getAndroidId?.() || 'unknown';
    }
    return 'unknown';
  } catch {
    return 'unknown';
  }
}

export async function logCrash(error: Error, context?: Record<string, any>): Promise<void> {
  try {
    await api.post('/monitoring/crashes', {
      device_id: getDeviceId(),
      platform: Platform.OS,
      platform_version: Platform.Version,
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString(),
    });
  } catch {
    // Silently ignore network failures while reporting crashes.
  }
}

export function setupGlobalErrorHandler(): void {
  const originalHandler = ErrorUtils.getGlobalHandler?.();
  ErrorUtils.setGlobalHandler((error: any, isFatal?: boolean) => {
    logCrash(error instanceof Error ? error : new Error(String(error)), { isFatal, source: 'global' }).catch(() => {});
    if (originalHandler) {
      originalHandler(error, isFatal);
    }
  });
}
