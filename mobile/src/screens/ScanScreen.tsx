import { CameraView, useCameraPermissions } from 'expo-camera';
import * as Location from 'expo-location';
import React, { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Button,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Condition, ScanResult } from '../types';
import { analyzeImage } from '../services/api';

const conditionEmoji: Record<Condition, string> = {
  fresh: '🟢',
  near_expiry: '🟡',
  suspicious: '🟠',
  expired: '🔴',
};

export default function ScanScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [productName, setProductName] = useState('');
  const [result, setResult] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!permission?.granted) {
      requestPermission();
    }
  }, [permission]);

  const takePicture = async () => {
    if (!cameraRef.current) return;
    const picture = await cameraRef.current.takePictureAsync();
    if (picture?.uri) {
      setPhoto(picture.uri);
      setResult(null);
    }
  };

  const analyze = async () => {
    if (!photo) return;
    setLoading(true);
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
      const data = await analyzeImage(photo, productName, location);
      setResult(data);
    } catch (e: any) {
      Alert.alert('Analysis error', e?.response?.data?.detail || e.message);
    } finally {
      setLoading(false);
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
      <CameraView ref={cameraRef} style={styles.camera} facing="back" />
      <View style={styles.row}>
        <Button title="Capture" onPress={takePicture} />
      </View>
      {photo && <Image source={{ uri: photo }} style={styles.preview} />}
      <TextInput
        style={styles.input}
        placeholder="Product name (optional)"
        value={productName}
        onChangeText={setProductName}
      />
      {photo && (
        <Button title={loading ? 'Analyzing...' : 'Analyze with AI'} onPress={analyze} disabled={loading} />
      )}
      {loading && <ActivityIndicator style={{ marginTop: 12 }} />}
      {result && (
        <View style={styles.result}>
          <Text style={styles.resultTitle}>{conditionEmoji[result.condition]} {result.condition.toUpperCase()}</Text>
          <Text>Product: {result.product_name || 'Unknown'}</Text>
          <Text>Category: {result.category || 'Unknown'}</Text>
          <Text>Confidence: {(result.confidence * 100).toFixed(1)}%</Text>
          <Text>Date: {new Date(result.created_at).toLocaleString()}</Text>
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
  camera: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 12,
  },
  row: {
    marginVertical: 12,
  },
  preview: {
    width: '100%',
    aspectRatio: 3 / 4,
    borderRadius: 12,
    marginVertical: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    marginBottom: 12,
  },
  result: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
