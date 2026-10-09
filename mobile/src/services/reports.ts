// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { Alert } from 'react-native';

import { getToken } from '../context/AuthContext';
import { apiBaseUrl, errorMessage, generateBatchReport, generateReport } from './api';
import { InspectionFilters } from '../types';

const MIME: Record<string, string> = {
  pdf: 'application/pdf',
  csv: 'text/csv',
  excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
};

/** Generate a report on the server, download it to the phone and open the share/open dialog. */
export async function downloadReport(
  format: 'pdf' | 'csv' | 'excel',
  target: { scanId?: string; filters?: InspectionFilters; notes?: string },
  setBusy?: (b: boolean) => void
): Promise<string | null> {
  setBusy?.(true);
  try {
    const report = target.scanId
      ? await generateReport(target.scanId, format, target.notes)
      : await generateBatchReport(format, target.filters, target.notes);
    const ext = format === 'excel' ? 'xlsx' : format;
    const dest = `${FileSystem.documentDirectory}${report.report_id}.${ext}`;
    const token = await getToken();
    const res = await FileSystem.downloadAsync(`${apiBaseUrl()}/reports/${report.id}/download`, dest, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status !== 200) throw new Error(`Download failed (HTTP ${res.status})`);
    if (await Sharing.isAvailableAsync()) {
      await Sharing.shareAsync(res.uri, { mimeType: MIME[format], dialogTitle: `Report ${report.report_id}` });
    } else {
      Alert.alert('Report saved', res.uri);
    }
    return res.uri;
  } catch (e) {
    Alert.alert('Report error', errorMessage(e));
    return null;
  } finally {
    setBusy?.(false);
  }
}
