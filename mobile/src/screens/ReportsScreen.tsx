// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useState } from 'react';
import { ActivityIndicator, Button, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { downloadReport } from '../services/reports';

const RESULTS = [
  { key: '', label: 'All results' },
  { key: 'PASS_NO_VISIBLE_ANOMALY', label: 'Pass' },
  { key: 'WARNING', label: 'Warning' },
  { key: 'REVIEW', label: 'Review' },
  { key: 'INSUFFICIENT_DATA', label: 'Insufficient' },
];

export default function ReportsScreen() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [product, setProduct] = useState('');
  const [result, setResult] = useState('');
  const [notes, setNotes] = useState('');
  const [busy, setBusy] = useState(false);
  const [last, setLast] = useState('');

  const run = async (format: 'pdf' | 'csv' | 'excel') => {
    const uri = await downloadReport(format, { filters: { date_from: dateFrom, date_to: dateTo, product, result }, notes }, setBusy);
    if (uri) setLast(`${format.toUpperCase()} saved: ${uri.split('/').pop()}`);
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Inspection Reports</Text>
      <Text style={styles.small}>Reports are generated on the server from your organisation's saved inspections and downloaded to this phone.</Text>
      <View style={styles.row}>
        <TextInput style={[styles.input, styles.half]} placeholder="From YYYY-MM-DD" value={dateFrom} onChangeText={setDateFrom} />
        <TextInput style={[styles.input, styles.half]} placeholder="To YYYY-MM-DD" value={dateTo} onChangeText={setDateTo} />
      </View>
      <TextInput style={styles.input} placeholder="Product / brand / barcode (optional)" value={product} onChangeText={setProduct} />
      <View style={styles.chips}>
        {RESULTS.map((r) => (
          <TouchableOpacity key={r.key} onPress={() => setResult(r.key)} style={[styles.chip, result === r.key && styles.chipOn]}>
            <Text style={result === r.key ? { color: '#fff' } : undefined}>{r.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <TextInput style={styles.input} placeholder="Notes to include (optional)" value={notes} onChangeText={setNotes} multiline />
      <View style={styles.buttons}>
        <Button title="Download PDF" disabled={busy} onPress={() => run('pdf')} />
        <Button title="Download CSV" disabled={busy} onPress={() => run('csv')} />
        <Button title="Download Excel" disabled={busy} onPress={() => run('excel')} />
      </View>
      {busy && <ActivityIndicator style={{ marginTop: 12 }} />}
      {last ? <Text style={styles.ok}>{last}</Text> : null}
      <Text style={styles.small}>Single-inspection reports: open an inspection in History and use the report buttons at the bottom.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 6 },
  small: { fontSize: 12, color: '#555', marginVertical: 6 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 8, marginBottom: 6 },
  row: { flexDirection: 'row', justifyContent: 'space-between' },
  half: { width: '49%' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 6 },
  chip: { borderWidth: 1, borderColor: '#1565c0', borderRadius: 14, paddingHorizontal: 10, paddingVertical: 4, margin: 2 },
  chipOn: { backgroundColor: '#1565c0' },
  buttons: { gap: 8, marginVertical: 8 },
  ok: { color: '#2e7d32', marginTop: 8 },
});
