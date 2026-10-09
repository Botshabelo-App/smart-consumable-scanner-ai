// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Alert, Button, Image, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';

import InspectionFields, { RESULT_LABEL, ResultBanner } from '../components/InspectionFields';
import { getToken } from '../context/AuthContext';
import {
  apiBaseUrl, correctScanField, createReviewRequest, errorMessage, getMe, getScanDetail, signOffScan,
} from '../services/api';
import { downloadReport } from '../services/reports';
import { ScanDetail, UserAccount } from '../types';

const FIELDS: { key: string; label: string }[] = [
  { key: 'product_name', label: 'Product' },
  { key: 'brand', label: 'Brand' },
  { key: 'barcode_code', label: 'Barcode' },
  { key: 'batch_number', label: 'Batch / lot' },
  { key: 'production_date', label: 'Production date' },
  { key: 'expiry_date', label: 'Expiry date' },
  { key: 'category', label: 'Category' },
  { key: 'packaging_type', label: 'Packaging' },
];
const RESULTS = ['PASS_NO_VISIBLE_ANOMALY', 'WARNING', 'REVIEW', 'INSUFFICIENT_DATA'];

export default function ScanDetailScreen({ route }: any) {
  const scanId: string = route.params.scanId;
  const [scan, setScan] = useState<ScanDetail | null>(null);
  const [me, setMe] = useState<UserAccount | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [field, setField] = useState('expiry_date');
  const [value, setValue] = useState('');
  const [reason, setReason] = useState('');
  const [decision, setDecision] = useState<'confirm' | 'override' | 'escalate'>('confirm');
  const [finalResult, setFinalResult] = useState('REVIEW');
  const [typedName, setTypedName] = useState('');
  const [ack, setAck] = useState(false);
  const [comments, setComments] = useState('');
  const [overrideReason, setOverrideReason] = useState('');
  const [showOcr, setShowOcr] = useState(false);

  const load = useCallback(async () => {
    try {
      const [d, u, t] = await Promise.all([getScanDetail(scanId), getMe(), getToken()]);
      setScan(d);
      setMe(u);
      setToken(t);
    } catch (e) {
      Alert.alert('Error', errorMessage(e));
    }
  }, [scanId]);

  useEffect(() => {
    load();
  }, [load]);

  const run = async (fn: () => Promise<any>, done: string) => {
    setBusy(true);
    try {
      const r = await fn();
      if (r && r.id === scanId) setScan(r);
      else await load();
      Alert.alert('Saved', done);
      return true;
    } catch (e) {
      Alert.alert('Not saved', errorMessage(e));
      return false;
    } finally {
      setBusy(false);
    }
  };

  if (!scan) return <ActivityIndicator style={{ flex: 1 }} />;
  const signedOff = !!scan.signed_off_at;
  const isAdmin = me?.role === 'company_admin' || me?.role === 'administrator';

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <ResultBanner scan={scan} />
      {token && (
        <Image
          source={{ uri: `${apiBaseUrl()}/scans/${scan.id}/image`, headers: { Authorization: `Bearer ${token}` } }}
          style={styles.photo}
          resizeMode="contain"
        />
      )}
      <InspectionFields scan={scan} />
      <Text style={styles.meta}>
        Review status: {scan.review_status || 'not recorded'}
        {signedOff ? `  •  Signed off by ${scan.signed_off_by_name} (${new Date(scan.signed_off_at!).toLocaleString()})` : '  •  Not signed off'}
      </Text>

      <Button title={showOcr ? 'Hide original OCR text' : 'Show original OCR text'} onPress={() => setShowOcr(!showOcr)} />
      {showOcr && <Text style={styles.ocr}>{scan.ocr_raw_text || 'No text was read from the label.'}</Text>}

      <Text style={styles.h}>Findings</Text>
      {(scan.findings || []).map((f, i) => <Text key={i} style={styles.small}>• {f}</Text>)}

      <Text style={styles.h}>Correct a field</Text>
      {signedOff && !isAdmin ? (
        <Text style={styles.small}>This inspection is signed off. Only an organisation admin can correct it.</Text>
      ) : (
        <View>
          <View style={styles.chips}>
            {FIELDS.map((f) => (
              <View key={f.key} style={styles.chip}>
                <Button title={f.label} color={field === f.key ? '#1565c0' : '#9e9e9e'} onPress={() => setField(f.key)} />
              </View>
            ))}
          </View>
          <TextInput style={styles.input} placeholder={field.endsWith('_date') ? 'New value (YYYY-MM-DD or DD/MM/YYYY)' : 'New value (empty = clear)'} value={value} onChangeText={setValue} autoCapitalize="none" />
          <TextInput style={styles.input} placeholder="Reason / observation (required)" value={reason} onChangeText={setReason} multiline />
          <Button
            title="Save correction"
            disabled={busy}
            onPress={async () => {
              if (reason.trim().length < 3) return Alert.alert('Reason required', 'Explain why this value is being corrected.');
              if (await run(() => correctScanField(scan.id, field, value, reason), 'Correction recorded. The original value is kept in the audit trail.')) {
                setValue('');
                setReason('');
              }
            }}
          />
        </View>
      )}

      {!signedOff && scan.review_status !== 'escalated' && (
        <View style={{ marginTop: 8 }}>
          <Button
            title="Request supervisor review"
            disabled={busy}
            onPress={() => run(() => createReviewRequest(scan.id, scan.condition, reason || 'Flagged by inspector'), 'Review requested.')}
          />
        </View>
      )}

      <Text style={styles.h}>Inspector sign-off</Text>
      {signedOff && !isAdmin ? (
        <Text style={styles.small}>Already signed off.</Text>
      ) : (
        <View>
          <Text style={styles.small}>System result: {RESULT_LABEL[scan.overall_result || ''] || scan.overall_result}</Text>
          <View style={styles.chips}>
            {(['confirm', 'override', 'escalate'] as const).map((d) => (
              <View key={d} style={styles.chip}>
                <Button title={d === 'confirm' ? 'Confirm result' : d === 'override' ? 'Override' : 'Escalate'} color={decision === d ? '#1565c0' : '#9e9e9e'} onPress={() => setDecision(d)} />
              </View>
            ))}
          </View>
          {decision === 'override' && (
            <View>
              <View style={styles.chips}>
                {RESULTS.filter((r) => r !== scan.overall_result).map((r) => (
                  <View key={r} style={styles.chip}>
                    <Button title={r.split('_')[0]} color={finalResult === r ? '#1565c0' : '#9e9e9e'} onPress={() => setFinalResult(r)} />
                  </View>
                ))}
              </View>
              <TextInput style={styles.input} placeholder="Override reason (required)" value={overrideReason} onChangeText={setOverrideReason} multiline />
            </View>
          )}
          <TextInput style={styles.input} placeholder="Comments / observations" value={comments} onChangeText={setComments} multiline />
          <Text style={styles.ack}>
            I confirm that I personally inspected this product and that this record, including any corrections, is accurate to the
            best of my knowledge. This is an electronic acknowledgement linked to my account and the time; it is not a certified
            digital signature.
          </Text>
          <View style={styles.ackRow}>
            <Switch value={ack} onValueChange={setAck} />
            <Text style={{ marginLeft: 8 }}>I agree</Text>
          </View>
          <TextInput style={styles.input} placeholder={`Type your full name (${me?.full_name || ''})`} value={typedName} onChangeText={setTypedName} />
          <Button
            title="Sign off"
            disabled={busy}
            onPress={() =>
              run(
                () => signOffScan(scan.id, {
                  decision,
                  final_result: decision === 'override' ? finalResult : undefined,
                  typed_name: typedName,
                  acknowledged: ack,
                  comments: comments || undefined,
                  override_reason: decision === 'override' ? overrideReason : undefined,
                }),
                'Sign-off recorded.'
              )
            }
          />
        </View>
      )}

      <Text style={styles.h}>Audit trail</Text>
      {scan.corrections.length === 0 && scan.reviews.length === 0 && scan.signoffs.length === 0 && <Text style={styles.small}>No changes recorded.</Text>}
      {scan.corrections.map((c) => (
        <Text key={c.id} style={styles.small}>
          ✎ {new Date(c.created_at).toLocaleString()} – {c.user_name}: {c.field} "{c.original_value ?? 'Not detected'}" → "{c.new_value ?? 'cleared'}" ({c.reason})
        </Text>
      ))}
      {scan.reviews.map((r) => (
        <Text key={r.id} style={styles.small}>
          ⚑ Review {r.status} – requested by {r.requester_name || 'unknown'}
          {r.reviewer_name ? `, handled by ${r.reviewer_name}` : ''}
          {r.reviewed_at ? ` at ${new Date(r.reviewed_at).toLocaleString()}` : ''}
          {r.reviewer_notes ? ` – ${r.reviewer_notes}` : ''}
        </Text>
      ))}
      {scan.signoffs.map((s) => (
        <Text key={s.id} style={styles.small}>
          ✔ {new Date(s.created_at).toLocaleString()} – {s.full_name} ({s.role}) {s.decision}: final {s.final_result || 'none (escalated)'}
          {s.override_reason ? ` – reason: ${s.override_reason}` : ''}
          {s.comments ? ` – ${s.comments}` : ''}
        </Text>
      ))}

      <Text style={styles.h}>Report for this inspection</Text>
      <View style={styles.chips}>
        {(['pdf', 'csv', 'excel'] as const).map((f) => (
          <View key={f} style={styles.chip}>
            <Button title={f.toUpperCase()} disabled={busy} onPress={() => downloadReport(f, { scanId: scan.id }, setBusy)} />
          </View>
        ))}
      </View>
      {busy && <ActivityIndicator />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, backgroundColor: '#fff' },
  photo: { width: '100%', height: 260, backgroundColor: '#eee', borderRadius: 8, marginVertical: 8 },
  meta: { marginVertical: 8, color: '#555' },
  ocr: { fontFamily: 'monospace', fontSize: 12, backgroundColor: '#f5f5f5', padding: 8, marginVertical: 6 },
  h: { fontSize: 17, fontWeight: 'bold', marginTop: 18, marginBottom: 6 },
  small: { fontSize: 13, color: '#333', marginBottom: 4 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginVertical: 4 },
  chip: { margin: 2 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10, marginVertical: 4 },
  ack: { fontSize: 13, backgroundColor: '#fff8e1', padding: 8, borderRadius: 6, marginVertical: 6 },
  ackRow: { flexDirection: 'row', alignItems: 'center', marginVertical: 4 },
});
