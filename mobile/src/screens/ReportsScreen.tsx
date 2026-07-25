// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Button, FlatList, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { generateReport, getScans } from '../services/api';
import { ScanResult } from '../types';

export default function ReportsScreen() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const [format, setFormat] = useState<'pdf' | 'csv' | 'excel'>('pdf');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getScans().then(setScans);
  }, []);

  const createReport = async () => {
    if (!selected) {
      Alert.alert('Select a scan');
      return;
    }
    setLoading(true);
    try {
      const report = await generateReport(selected, format, notes);
      Alert.alert('Report generated', `ID: ${report.report_id}`);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  if (!scans.length) return <ActivityIndicator style={{ flex: 1 }} />;

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Generate Report</Text>
      <FlatList
        data={scans}
        keyExtractor={(item) => item.id}
        scrollEnabled={false}
        renderItem={({ item }) => (
          <View style={[styles.card, selected === item.id && styles.selected]}>
            <Text>{item.product_name || 'Unknown product'}</Text>
            <Text>{item.condition}</Text>
            <Button
              title={selected === item.id ? 'Selected' : 'Select'}
              onPress={() => setSelected(item.id)}
            />
          </View>
        )}
      />
      <TextInput
        style={styles.input}
        placeholder="Notes"
        value={notes}
        onChangeText={setNotes}
      />
      <View style={styles.formatRow}>
        {(['pdf', 'csv', 'excel'] as const).map((f) => (
          <View key={f} style={styles.formatButton}>
            <Button title={f.toUpperCase()} onPress={() => setFormat(f)} />
          </View>
        ))}
      </View>
      {loading ? <ActivityIndicator /> : <Button title="Generate Report" onPress={createReport} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  card: {
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginBottom: 8,
  },
  selected: {
    backgroundColor: '#d0eaff',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    marginVertical: 12,
  },
  formatRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  formatButton: {
    flex: 1,
    marginHorizontal: 4,
  },
});
