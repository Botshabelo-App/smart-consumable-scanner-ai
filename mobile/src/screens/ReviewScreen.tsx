// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Button, FlatList, StyleSheet, Text, TextInput, View } from 'react-native';

import { createReviewRequest, getReviewRequests, getScans } from '../services/api';
import { ReviewRequest, ScanResult } from '../types';

const conditions: Array<ScanResult['condition']> = ['fresh', 'near_expiry', 'suspicious', 'expired'];

export default function ReviewScreen() {
  const [scans, setScans] = useState<ScanResult[]>([]);
  const [requests, setRequests] = useState<ReviewRequest[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [suggested, setSuggested] = useState<ScanResult['condition']>('fresh');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const [s, r] = await Promise.all([getScans(), getReviewRequests()]);
      setScans(s);
      setRequests(r);
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e.message);
    }
  };

  const submit = async () => {
    if (!selected) return;
    setLoading(true);
    try {
      await createReviewRequest(selected, suggested, notes);
      Alert.alert('Review requested', 'An authorized reviewer will examine this scan.');
      setSelected(null);
      setNotes('');
      load();
    } catch (e: any) {
      Alert.alert('Error', e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const renderScan = ({ item }: { item: ScanResult }) => (
    <View style={[styles.card, selected === item.id && styles.selected]}>
      <Text style={styles.name}>{item.product_name || 'Unknown product'}</Text>
      <Text>AI: {item.condition}</Text>
      <Text>{new Date(item.created_at).toLocaleString()}</Text>
      <Button title={selected === item.id ? 'Selected' : 'Request review'} onPress={() => setSelected(item.id)} />
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>AI Review Workflow</Text>
      <FlatList
        data={scans}
        keyExtractor={(item) => item.id}
        renderItem={renderScan}
        ListEmptyComponent={<ActivityIndicator />}
      />
      {selected && (
        <View style={styles.form}>
          <Text>Suggest correct condition:</Text>
          <View style={styles.row}>
            {conditions.map((c) => (
              <View key={c} style={styles.btn}>
                <Button title={c} onPress={() => setSuggested(c)} color={suggested === c ? '#1976d2' : undefined} />
              </View>
            ))}
          </View>
          <TextInput style={styles.input} placeholder="Notes" value={notes} onChangeText={setNotes} />
          {loading ? <ActivityIndicator /> : <Button title="Submit review request" onPress={submit} />}
        </View>
      )}
      <Text style={styles.subtitle}>Pending reviews ({requests.filter((r) => r.status === 'pending').length})</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 12 },
  subtitle: { fontSize: 16, fontWeight: '600', marginTop: 12 },
  card: { padding: 12, backgroundColor: '#f5f5f5', borderRadius: 8, marginBottom: 8 },
  selected: { backgroundColor: '#d0eaff' },
  name: { fontSize: 16, fontWeight: 'bold' },
  form: { marginTop: 12 },
  row: { flexDirection: 'row', flexWrap: 'wrap', marginVertical: 8 },
  btn: { margin: 2 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginVertical: 8 },
});
