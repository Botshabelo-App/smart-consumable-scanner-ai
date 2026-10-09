// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { ScanResult } from '../types';

export const RESULT_COLOR: Record<string, string> = {
  PASS_NO_VISIBLE_ANOMALY: '#2e7d32',
  WARNING: '#c62828',
  REVIEW: '#ef6c00',
  INSUFFICIENT_DATA: '#616161',
};

export const RESULT_LABEL: Record<string, string> = {
  PASS_NO_VISIBLE_ANOMALY: 'PASS – no visible anomaly',
  WARNING: 'WARNING',
  REVIEW: 'REVIEW needed',
  INSUFFICIENT_DATA: 'INSUFFICIENT DATA',
};

const DATE_TYPE_LABEL: Record<string, string> = {
  expiry: 'Expiry / use by',
  best_before: 'Best before',
  production: 'Production / manufactured',
  packaging: 'Packed',
  unlabelled: 'Unlabelled date',
};

const FLAG_LABEL: Record<string, string> = {
  expired: 'EXPIRED – printed date has passed',
  near_expiry: 'Near expiry (within 7 days)',
  production_after_expiry: 'Production date is after expiry date',
  production_in_future: 'Production date is in the future',
  expiry_more_than_5_years_ahead: 'Expiry date more than 5 years ahead – check',
  expiry_needs_verification: 'Expiry date needs verification',
};

export function dateOnly(iso?: string): string | undefined {
  return iso ? iso.split('T')[0] : undefined;
}

export function displayValue(scan: ScanResult, field: string, value?: string | null): { text: string; color: string } {
  const status = scan.field_status?.[field];
  if (value === undefined || value === null || value === '') return { text: 'Not detected', color: '#9e9e9e' };
  if (status === 'needs_verification') return { text: `${value}  (needs verification)`, color: '#ef6c00' };
  if (status === 'corrected') return { text: `${value}  (corrected)`, color: '#1565c0' };
  if (status === 'entered') return { text: `${value}  (entered by inspector)`, color: '#333' };
  return { text: value, color: '#333' };
}

function Row({ label, scan, field, value }: { label: string; scan: ScanResult; field: string; value?: string | null }) {
  const v = displayValue(scan, field, value);
  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <Text style={[styles.value, { color: v.color }]}>{v.text}</Text>
    </View>
  );
}

export function ResultBanner({ scan }: { scan: ScanResult }) {
  const r = scan.final_result || scan.overall_result;
  if (!r) return null;
  return (
    <View style={[styles.banner, { backgroundColor: RESULT_COLOR[r] || '#616161' }]}>
      <Text style={styles.bannerText}>{RESULT_LABEL[r] || r}</Text>
      {scan.final_result && scan.final_result !== scan.overall_result ? (
        <Text style={styles.bannerSub}>Inspector override (system said {RESULT_LABEL[scan.overall_result || ''] || scan.overall_result})</Text>
      ) : null}
      {scan.overall_reason ? <Text style={styles.bannerSub}>{scan.overall_reason}</Text> : null}
    </View>
  );
}

export default function InspectionFields({ scan }: { scan: ScanResult }) {
  return (
    <View>
      <Row label="Product" scan={scan} field="product_name" value={scan.product_name} />
      <Row label="Brand" scan={scan} field="brand" value={scan.brand} />
      <Row label="Barcode" scan={scan} field="barcode_code" value={scan.barcode_code} />
      <Row label="Batch / lot" scan={scan} field="batch_number" value={scan.batch_number} />
      <Row label="Production date" scan={scan} field="production_date" value={dateOnly(scan.production_date)} />
      <Row label="Expiry / best before" scan={scan} field="expiry_date" value={dateOnly(scan.expiry_date)} />
      <Row label="Category" scan={scan} field="category" value={scan.category} />
      <Row label="Packaging" scan={scan} field="packaging_type" value={[scan.packaging_type, scan.packaging_condition].filter(Boolean).join(' – ')} />
      <Row label="School / site" scan={scan} field="site" value={scan.branch_name || 'No site assigned'} />
      <Row label="Inspector" scan={scan} field="inspector" value={scan.inspector_name} />
      <Row label="Inspected at" scan={scan} field="created_at" value={new Date(scan.created_at).toLocaleString()} />
      {(scan.date_flags || []).map((f) => (
        <Text key={f} style={styles.flag}>⚠ {FLAG_LABEL[f] || f}</Text>
      ))}
      {(scan.date_details || []).length > 0 && (
        <View style={styles.box}>
          <Text style={styles.boxTitle}>Dates read from the label</Text>
          {(scan.date_details || []).map((d, i) => (
            <Text key={i} style={styles.small}>
              {DATE_TYPE_LABEL[d.type] || d.type}: "{d.matched_text}" → {d.interpreted}
              {d.status === 'needs_verification' ? ' (needs verification)' : ''}
              {d.note ? ` – ${d.note}` : ''}
            </Text>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', paddingVertical: 4, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#ddd' },
  label: { width: 140, color: '#555', fontWeight: '600' },
  value: { flex: 1 },
  banner: { padding: 12, borderRadius: 10, marginVertical: 8 },
  bannerText: { color: '#fff', fontSize: 20, fontWeight: 'bold' },
  bannerSub: { color: '#fff', marginTop: 4 },
  flag: { color: '#c62828', fontWeight: '600', marginTop: 6 },
  box: { marginTop: 8, padding: 8, backgroundColor: '#fafafa', borderRadius: 8 },
  boxTitle: { fontWeight: '600', marginBottom: 4 },
  small: { fontSize: 13, color: '#333', marginBottom: 2 },
});
