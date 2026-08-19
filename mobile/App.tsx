// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import React, { useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { AuthProvider } from './src/context/AuthContext';
import { ConnectivityProvider } from './src/context/ConnectivityContext';
import { ErrorBoundary } from './src/components/ErrorBoundary';
import AppNavigator from './src/navigation/AppNavigator';
import { configureApiBaseUrl } from './src/services/apiConfig';
import { syncOfflineScans } from './src/services/api';
import { setupGlobalErrorHandler } from './src/services/crashLogger';

setupGlobalErrorHandler();

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    configureApiBaseUrl()
      .catch(() => {})
      .finally(() => syncOfflineScans())
      .finally(() => setReady(true));
  }, []);

  if (!ready) {
    return <View style={styles.container} />;
  }

  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaProvider>
        <ErrorBoundary>
          <ConnectivityProvider>
            <AuthProvider>
              <StatusBar style="auto" />
              <AppNavigator />
            </AuthProvider>
          </ConnectivityProvider>
        </ErrorBoundary>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
