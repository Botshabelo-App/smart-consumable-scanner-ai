// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { BarcodeScanningResult, CameraView, useCameraPermissions } from 'expo-camera';
import * as FileSystem from 'expo-file-system';
import * as Location from 'expo-location';
import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Button,
  FlatList,
  Image,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { analyzeImage, lookupBarcode, ScanPayload, submitScanFeedback } from '../services/api';
import { Condition, ScanResult } from '../types';

const conditionColor: Record<Condition, string> = {
  fresh: '#2e7d32',
  near_expiry: '#f9a825',
  suspicious: '#ef6c00',
  expired: '#c62828',
};

export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [captures, setCaptures] = useState<string[]>([]);
  const [productName, setProductName] = useState('');
  const [barcode, setBarcode] = useState('');
  const [batchNumber, setBatchNumber] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [scanBarcode, setScanBarcode] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [feedbackLoading, setFeedbackLoading] = useState(false);
  const [continuous, setContinuous] = useState(false);
  const [qualityNote, setQualityNote] = useState<string | null>(null);
  const [showOverride, setShowOverride] = useState(false);
  const [overrideCondition, setOverrideCondition] = useState<Condition>('fresh');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideNotes, setOverrideNotes] = useState('');

  useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, [permission]);

  useEffect(() => {
    if (!continuous || loading) return;
    const interval = setInterval(() => {
      takePicture();
    }, 3000);
    return () => clearInterval(interval);
  }, [continuous, loading, photo]);

  const validateImageQuality = async (uri: string): Promise<boolean> => {
    try {
      const info = await FileSystem.getInfoAsync(uri);
      if (!info.exists || info.size < 1024) {
        setQualityNote('Image too small or not saved.');
        return false;
      }
      const mb = info.size / (1024 * 1024);
      if (mb > 10) {
        setQualityNote('Image is large; it may upload slowly.');
      } else {
        setQualityNote(null);
      }
      return true;
    } catch (e) {
      setQualityNote('Could not verify image quality.');
      return false;
    }
  };

  const handleBarcodeScanned = async (scanningResult: BarcodeScanningResult) => {
    if (!scanBarcode || loading) return;
    const code = scanningResult.data;
    if (code === barcode) return;
    setBarcode(code);
    setScanBarcode(false);
    try {
      const info = await lookupBarcode(code);
      if (info.product) {
        setProductName(info.product.name);
      } else {
        setProductName('');
      }
      if (info.batch_number) setBatchNumber(info.batch_number);
      if (info.expiry_date) setExpiryDate(info.expiry_date.split('T')[0]);
      Alert.alert('Barcode scanned', `Code: ${code}\nProduct: ${info.product?.name || 'Unknown'}`);
    } catch (e: any) {
      Alert.alert('Barcode lookup failed', e?.response?.data?.detail || e.message);
    }
  };

  const takePicture = async () => {
    if (!cameraRef.current) return;
    try {
      const picture = await cameraRef.current.takePictureAsync({ quality: 0.8 });
      if (picture?.uri) {
        setPhoto(picture.uri);
        setCaptures((prev) => [picture.uri, ...prev].slice(0, 5));
        setResult(null);
      }
    } catch (e: any) {
      Alert.alert('Capture error', e.message);
    }
  };

  const analyze = async (uri: string = photo || '') => {
    if (!uri) return;
    const ok = await validateImageQuality(uri);
    if (!ok) return;

    setLoading(true);
    setResult(null);
    try {
      let location;
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status === 'granted') {
        const pos = await Location.getCurrentPositionAsync({});
        location = {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        };
      }
      const payload: ScanPayload = {
        uri,
        productName,
        barcodeCode: barcode || undefined,
        batchNumber: batchNumber || undefined,
        expiryDate: expiryDate || undefined,
        location,
      };
      const data = await analyzeImage(payload);
      setResult(data);
    } catch (e: any) {
      Alert.alert('Analysis error', e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setPhoto(null);
    setCaptures([]);
    setProductName('');
    setBarcode('');
    setBatchNumber('');
    setExpiryDate('');
    setResult(null);
    setQualityNote(null);
    setShowOverride(false);
    setOverrideReason('');
    setOverrideNotes('');
  };

  const handleAccept = async () => {
    if (!result || !result.id) return;
    setFeedbackLoading(true);
    try {
      const updated = await submitScanFeedback(result.id, true);
      setResult(updated);
      Alert.alert('Feedback recorded', 'You accepted the AI assessment.');
    } catch (e: any) {
      Alert.alert('Feedback error', e?.response?.data?.detail || e.message);
    } finally {
      setFeedbackLoading(false);
    }
  };

  const handleOverride = async () => {
    if (!result || !result.id) return;
    if (!overrideReason.trim()) {
      Alert.alert('Reason required', 'Please provide a reason for overriding the AI.');
      return;
    }
    setFeedbackLoading(true);
    try {
      const updated = await submitScanFeedback(result.id, false, overrideCondition, overrideReason, overrideNotes);
      setResult(updated);
      setShowOverride(false);
      Alert.alert('Feedback recorded', `Overridden to ${overrideCondition}.`);
    } catch (e: any) {
      Alert.alert('Feedback error', e?.response?.data?.detail || e.message);
    } finally {
      setFeedbackLoading(false);
    }
  };

  if (!permission?.granted) {
    return (
      <View style={styles.centered}>
        <Text>Camera permission required.</Text>
        <Button title="Grant permission" onPress={requestPermission} />
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.heading}>Scan a consumable product</Text>
      <CameraView
        ref={cameraRef}
        style={styles.camera}
        facing="back"
        barcodeScannerSettings={scanBarcode ? { barcodeTypes: ['qr', 'ean13', 'ean8', 'upc_a', 'code128'] } : undefined}
        onBarcodeScanned={scanBarcode ? handleBarcodeScanned : undefined}
      />
      <View style={styles.row}>
        <Button title="Capture" onPress={takePicture} />
        <View style={styles.continuousRow}>
          <Text>Continuous</Text>
          <Switch value={continuous} onValueChange={setContinuous} />
        </View>
        <View style={styles.continuousRow}>
          <Text>Scan barcode</Text>
          <Switch value={scanBarcode} onValueChange={setScanBarcode} />
        </View>
      </View>
      {photo && <Image source={{ uri: photo }} style={styles.preview} />}
      {captures.length > 1 && (
        <View style={styles.angles}>
          <Text style={styles.subheading}>Scan angles</Text>
          <FlatList
            horizontal
            data={captures}
            keyExtractor={(item, idx) => `${item}-${idx}`}
            renderItem={({ item }) => <Image source={{ uri: item }} style={styles.thumb} />}
          />
        </View>
      )}
      <TextInput
        style={styles.input}
        placeholder="Product name (optional)"
        value={productName}
        onChangeText={setProductName}
      />
      <TextInput
        style={styles.input}
        placeholder="Barcode (optional)"
        value={barcode}
        onChangeText={setBarcode}
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Batch number (optional)"
        value={batchNumber}
        onChangeText={setBatchNumber}
        autoCapitalize="none"
      />
      <TextInput
        style={styles.input}
        placeholder="Printed expiry date YYYY-MM-DD (optional)"
        value={expiryDate}
        onChangeText={setExpiryDate}
        autoCapitalize="none"
      />
      {qualityNote && <Text style={styles.qualityNote}>{qualityNote}</Text>}
      {photo && (
        <View style={styles.row}>
          <Button title={loading ? 'Analyzing...' : 'Analyze with AI'} onPress={() => analyze(photo)} disabled={loading} />
          <View style={{ width: 8 }} />
          <Button title="Reset" onPress={reset} />
        </View>
      )}
      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}
      {result && (
        <View style={[styles.result, { borderColor: conditionColor[result.condition], borderWidth: 2 }]}>
          <Text style={[styles.resultTitle, { color: conditionColor[result.condition] }]}>
            {result.condition.toUpperCase()}
          </Text>
          <Text style={styles.detail}>Product: {result.product_name || 'Unknown'}</Text>
          <Text style={styles.detail}>Category: {result.category || 'Unknown'}</Text>
          <Text style={styles.detail}>Packaging: {result.packaging_type || 'Unknown'}</Text>
          <Text style={styles.detail}>Confidence: {(result.confidence * 100).toFixed(1)}%</Text>
          {result.ai_vs_label_discrepancy && (
            <Text style={styles.discrepancy}>Flagged: {result.discrepancy_reason}</Text>
          )}
          <Text style={styles.subheading}>Why the AI decided this:</Text>
          {(result.findings || []).map((finding, idx) => (
            <Text key={idx} style={styles.finding}>
              • {finding}
            </Text>
          ))}
          {result.expiry_risk && (
            <Text style={styles.detail}>Expiry risk: {result.expiry_risk}</Text>
          )}
          <Text style={styles.detail}>Date: {new Date(result.created_at).toLocaleString()}</Text>

          {result.inspector_accepted === true && (
            <Text style={styles.accepted}>Inspector accepted this assessment.</Text>
          )}
          {result.inspector_accepted === false && (
            <Text style={styles.overridden}>
              Inspector overrode to {result.override_condition}: {result.override_reason}
            </Text>
          )}

          {result.inspector_accepted === null || result.inspector_accepted === undefined ? (
            <View style={styles.row}>
              <Button title="Accept AI" onPress={handleAccept} disabled={feedbackLoading} />
              <View style={{ width: 8 }} />
              <Button title="Override AI" onPress={() => setShowOverride(true)} disabled={feedbackLoading} />
            </View>
          ) : null}

          {showOverride && (
            <View style={styles.overrideForm}>
              <Text style={styles.subheading}>Override to:</Text>
              <View style={styles.row}>
                {(['fresh', 'near_expiry', 'suspicious', 'expired'] as Condition[]).map((c) => (
                  <View key={c} style={styles.conditionChip}>
                    <Button
                      title={c}
                      onPress={() => setOverrideCondition(c)}
                      color={overrideCondition === c ? conditionColor[c] : '#888'}
                    />
                  </View>
                ))}
              </View>
              <TextInput
                style={styles.input}
                placeholder="Reason for override (required)"
                value={overrideReason}
                onChangeText={setOverrideReason}
              />
              <TextInput
                style={styles.input}
                placeholder="Additional notes (optional)"
                value={overrideNotes}
                onChangeText={setOverrideNotes}
                multiline
              />
              <View style={styles.row}>
                <Button title="Submit override" onPress={handleOverride} disabled={feedbackLoading} />
                <View style={{ width: 8 }} />
                <Button title="Cancel" onPress={() => setShowOverride(false)} disabled={feedbackLoading} />
              </View>
            </View>
          )}
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#fff',
  },
  heading: {
    fontSize: 20,
    fontWeight: 'bold',
    marginVertical: 12,
    textAlign: 'center',
  },
  subheading: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 4,
  },
  camera: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 12,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 12,
    flexWrap: 'wrap',
  },
  continuousRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginLeft: 16,
  },
  preview: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 12,
    marginVertical: 12,
  },
  angles: {
    marginVertical: 8,
  },
  thumb: {
    width: 80,
    height: 80,
    borderRadius: 8,
    marginRight: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  qualityNote: {
    color: '#ef6c00',
    marginBottom: 8,
    textAlign: 'center',
  },
  result: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
  },
  resultTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  detail: {
    fontSize: 15,
    marginBottom: 4,
  },
  finding: {
    fontSize: 14,
    color: '#333',
    marginBottom: 2,
  },
  discrepancy: {
    fontSize: 14,
    color: '#c62828',
    fontWeight: '600',
    marginVertical: 6,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  accepted: {
    color: '#2e7d32',
    fontWeight: '600',
    marginTop: 10,
  },
  overridden: {
    color: '#c62828',
    fontWeight: '600',
    marginTop: 10,
  },
  overrideForm: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#ddd',
  },
  conditionChip: {
    marginHorizontal: 2,
  },
});
