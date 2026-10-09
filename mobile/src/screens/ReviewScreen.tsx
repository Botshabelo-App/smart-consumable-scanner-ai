// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { useFocusEffect } from '@react-navigation/native';
import React, { useCallback, useState } from 'react';
import { Alert, Button, RefreshControl, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

import { RESULT_COLOR, RESULT_LABEL } from '../components/InspectionFields';
import { errorMessage, getMe, getReviewRequests, getScans, updateReview } from '../services/api';
import { ReviewRequest, ScanResult, UserAccount } from '../types';

export default function ReviewScreen({ navigation }: any) {
  const [awaiting, setAwaiting] = useState<ScanResult[]>([]);
  const [reviews, setReviews] = useState<ReviewRequest[]>([]);
  const [me, setMe] = useState<UserAccount | null>(null);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [scans, revs, u] = await Promise.all([getScans({ review_status: 'awaiting_review' }, 200), getReviewRequests(), getMe()]);
      const escalated = await getScans({ review_status: 'escalated' }, 200);
      const seen = new Set<string>();
      setAwaiting([...escalated, ...scans].filter((s) => (seen.has(s.id) ? false : (seen.add(s.id), true))));
      setReviews(revs);
      setMe(u);
    } catch (e) {
      Alert.alert('Error', errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(useCallback(() => { load(); }, [load]));

  const isAdmin = me?.role === 'company_admin' || me?.role === 'administrator';

  const decide = async (r: ReviewRequest, status: 'approved' | 'rejected' | 'escalated') => {
    const n = (notes[r.id] || '').trim();
    if (n.length < 3) return Alert.alert('Reason required', 'Write the reason for this decision.');
    try {
      await updateReview(r.id, status, n);
      await load();
    } catch (e) {
      Alert.alert('Not saved', errorMessage(e));
    }
  };

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}>
      <Text style={styles.title}>Review</Text>
      <Text style={styles.subtitle}>Inspections needing review or sign-off ({awaiting.length})</Text>
      {awaiting.length === 0 && <Text style={styles.small}>Nothing is waiting for review.</Text>}
      {awaiting.map((s) => (
        <TouchableOpacity key={s.id} style={styles.item} onPress={() => navigation.navigate('ScanDetail', { scanId: s.id })}>
          <Text style={[styles.name, { color: RESULT_COLOR[s.overall_result || ''] || '#333' }]}>
            {s.product_name || 'Product not detected'} – {RESULT_LABEL[s.overall_result || ''] || s.overall_result}
          </Text>
          <Text style={styles.small}>Status: {s.review_status}  •  {new Date(s.created_at).toLocaleString()}  •  {s.inspector_name}</Text>
          <Text style={styles.small}>Tap to view evidence, correct fields and sign off</Text>
        </TouchableOpacity>
      ))}

      <Text style={styles.subtitle}>Review requests</Text>
      {reviews.length === 0 && <Text style={styles.small}>No review requests.</Text>}
      {reviews.map((r) => (
        <View key={r.id} style={styles.item}>
          <TouchableOpacity onPress={() => navigation.navigate('ScanDetail', { scanId: r.scan_id })}>
            <Text style={styles.name}>Request {r.status.toUpperCase()} – open inspection</Text>
          </TouchableOpacity>
          <Text style={styles.small}>
            Requested by {r.requester_name || 'unknown'}{r.created_at ? ` on ${new Date(r.created_at).toLocaleString()}` : ''}
          </Text>
          {r.reviewer_notes ? <Text style={styles.small}>Notes: {r.reviewer_notes}</Text> : null}
          {r.reviewer_name ? <Text style={styles.small}>Handled by {r.reviewer_name}</Text> : null}
          {isAdmin && (r.status === 'pending' || r.status === 'escalated') && (
            <View>
              <TextInput style={styles.input} placeholder="Decision reason (required)" value={notes[r.id] || ''} onChangeText={(t) => setNotes({ ...notes, [r.id]: t })} />
              <View style={styles.row}>
                <Button title="Approve" onPress={() => decide(r, 'approved')} />
                <Button title="Reject" color="#c62828" onPress={() => decide(r, 'rejected')} />
                {r.status !== 'escalated' && <Button title="Escalate" color="#ef6c00" onPress={() => decide(r, 'escalated')} />}
              </View>
            </View>
          )}
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  title: { fontSize: 22, fontWeight: 'bold' },
  subtitle: { fontSize: 16, fontWeight: '600', marginTop: 16, marginBottom: 6 },
  item: { paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#eee' },
  name: { fontWeight: '600' },
  small: { fontSize: 12, color: '#555' },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 8, marginVertical: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-around' },
});
