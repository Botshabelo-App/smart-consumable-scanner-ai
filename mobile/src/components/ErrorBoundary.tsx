// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React, { Component, ReactNode } from 'react';
import { Text, View } from 'react-native';

import { logCrash } from '../services/crashLogger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    logCrash(error, { source: 'ErrorBoundary' }).catch(() => {});
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 }}>
            <Text style={{ fontSize: 18, fontWeight: '600' }}>Something went wrong.</Text>
            <Text style={{ marginTop: 8, textAlign: 'center' }}>The error has been reported for diagnosis.</Text>
          </View>
        )
      );
    }
    return this.props.children;
  }
}
