// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { createContext, useContext, useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import api from '../services/api';
import { configureApiBaseUrl } from '../services/apiConfig';

type ConnectivityState = {
  isOnline: boolean;
  isChecking: boolean;
  serverUrl: string;
  retry: () => Promise<void>;
};

const ConnectivityContext = createContext<ConnectivityState>({
  isOnline: false,
  isChecking: true,
  serverUrl: '',
  retry: async () => {},
});

export const useConnectivity = () => useContext(ConnectivityContext);

const CHECK_INTERVAL_MS = 5000;

export function ConnectivityProvider({ children }: { children: React.ReactNode }) {
  const [isOnline, setIsOnline] = useState(false);
  const [isChecking, setIsChecking] = useState(true);
  const [serverUrl, setServerUrl] = useState('');

  const checkHealth = async (): Promise<boolean> => {
    try {
      await api.get('/health');
      return true;
    } catch {
      return false;
    }
  };

  const refresh = async () => {
    setIsChecking(true);
    // Pull the latest backend URL from remote config before checking.
    const url = await configureApiBaseUrl().catch(() => '');
    setServerUrl(url || '');
    const ok = await checkHealth();
    setIsOnline(ok);
    setIsChecking(false);
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(() => {
      // Always try to fetch the latest backend URL from remote config first,
      // so the app can reconnect automatically when the backend tunnel changes.
      configureApiBaseUrl()
        .then((url) => {
          setServerUrl(url);
          return checkHealth();
        })
        .then((ok) => setIsOnline(ok));
    }, CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, []);

  if (isChecking) {
    return (
      <View style={styles.overlay} pointerEvents="auto">
        <ActivityIndicator size="large" color="#0d5aa3" />
        <Text style={styles.text}>Connecting to server...</Text>
        {!!serverUrl && <Text style={styles.url}>{serverUrl}</Text>}
      </View>
    );
  }

  return (
    <ConnectivityContext.Provider value={{ isOnline, isChecking, serverUrl, retry: refresh }}>
      {children}
      {!isOnline && (
        <View style={styles.overlay} pointerEvents="auto">
          <ActivityIndicator size="large" color="#0d5aa3" />
          <Text style={styles.text}>Server unavailable. Reconnecting...</Text>
          {!!serverUrl && <Text style={styles.url}>{serverUrl}</Text>}
        </View>
      )}
    </ConnectivityContext.Provider>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(255,255,255,0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    zIndex: 100,
  },
  text: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
    color: '#0d5aa3',
    textAlign: 'center',
  },
  url: {
    marginTop: 8,
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
  },
});
