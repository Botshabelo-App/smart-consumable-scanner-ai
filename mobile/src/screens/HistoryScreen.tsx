// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import { ActivityIndicator, Button, FlatList, RefreshControl, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { RESULT_COLOR, RESULT_LABEL, dateOnly } from '../components/InspectionFields';
import { errorMessage, getScans } from '../services/api';
import { InspectionFilters, ScanResult } from '../types';

const RESULT_FILTERS: { key: string; label: string }[] = [
  { key: '', label: 'All' },
  { key: 'PASS_NO_VISIBLE_ANOMALY', label: 'Pass' },
  { key: 'WARNING', label: 'Warning' },
  { key: 'REVIEW', label: 'Review' },
  { key: 'INSUFFICIENT_DATA', label: 'Insufficient' },
];

export default function HistoryScreen({ navigation }: any) {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [product, setProduct] = useState('');
  const [result, setResult] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const load = useCallback(async (filters: InspectionFilters) => {
    setLoading(true);
    setError('');
    try {
      setScans(await getScans(filters, 200));
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const filters = { product, result, date_from: dateFrom, date_to: dateTo };

  useFocusEffect(
    useCallback(() => {
      load(filters);
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [result])
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Scan History</Text>
      <TextInput style={styles.input} placeholder="Search product, brand, barcode or batch" value={product} onChangeText={setProduct} onSubmitEditing={() => load(filters)} returnKeyType="search" />
      <View style={styles.rowInputs}>
        <TextInput style={[styles.input, styles.half]} placeholder="From YYYY-MM-DD" value={dateFrom} onChangeText={setDateFrom} />
        <TextInput style={[styles.input, styles.half]} placeholder="To YYYY-MM-DD" value={dateTo} onChangeText={setDateTo} />
      </View>
      <View style={styles.chips}>
        {RESULT_FILTERS.map((f) => (
          <TouchableOpacity key={f.key} onPress={() => setResult(f.key)} style={[styles.chip, result === f.key && styles.chipOn]}>
            <Text style={result === f.key ? styles.chipTextOn : undefined}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Button title="Search" onPress={() => load(filters)} />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {loading && scans.length === 0 ? (
        <ActivityIndicator style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={scans}
          keyExtractor={(item) => item.id}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={() => load(filters)} />}
          ListEmptyComponent={<Text style={styles.empty}>No inspections match these filters.</Text>}
          renderItem={({ item }) => {
            const r = item.final_result || item.overall_result || '';
            return (
              <TouchableOpacity style={styles.item} onPress={() => navigation.navigate('ScanDetail', { scanId: item.id })}>
                <View style={[styles.dot, { backgroundColor: RESULT_COLOR[r] || '#9e9e9e' }]} />
                <View style={{ flex: 1 }}>
                  <Text style={styles.name}>{item.product_name || 'Product not detected'}{item.brand ? ` – ${item.brand}` : ''}</Text>
                  <Text style={styles.meta}>{RESULT_LABEL[r] || r || 'No result'}{item.signed_off_at ? '  •  signed off' : ''}{item.review_status && item.review_status !== 'not_required' ? `  •  review ${item.review_status}` : ''}</Text>
                  <Text style={styles.meta}>Expiry: {dateOnly(item.expiry_date) || 'Not detected'}  •  Batch: {item.batch_number || 'Not detected'}</Text>
                  <Text style={styles.meta}>{new Date(item.created_at).toLocaleString()}  •  {item.inspector_name || ''}{item.branch_name ? ` @ ${item.branch_name}` : ''}</Text>
                </View>
              </TouchableOpacity>
            );
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 12, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 8 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 8, marginBottom: 6 },
  rowInputs: { flexDirection: 'row', justifyContent: 'space-between' },
  half: { width: '49%' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 6 },
  chip: { borderWidth: 1, borderColor: '#1565c0', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 4, margin: 2 },
  chipOn: { backgroundColor: '#1565c0' },
  chipTextOn: { color: '#fff' },
  item: { flexDirection: 'row', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: '#eee' },
  dot: { width: 12, height: 12, borderRadius: 6, marginTop: 5, marginRight: 10 },
  name: { fontWeight: '600', fontSize: 15 },
  meta: { color: '#555', fontSize: 12 },
  error: { color: '#c62828', marginVertical: 6 },
  empty: { textAlign: 'center', color: '#777', marginTop: 20 },
});
