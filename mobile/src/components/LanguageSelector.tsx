// Copyright 2026 Moeketsi Daniel and contributors.
// All rights reserved.
// This file is part of the Smart Consumable Scanner AI project.
// Use is subject to the project licence terms.

import React from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import { brand, supportedLanguages } from '../config/brand';

interface LanguageSelectorProps {
  selected: string;
  onSelect: (code: string) => void;
}

export function LanguageSelector({ selected, onSelect }: LanguageSelectorProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>Voice language</Text>
      <View style={styles.row}>
        {supportedLanguages.map((lang) => (
          <TouchableOpacity
            key={lang.code}
            style={[
              styles.chip,
              selected === lang.code && { backgroundColor: brand.primaryColor },
            ]}
            onPress={() => onSelect(lang.code)}
          >
            <Text
              style={[
                styles.chipText,
                selected === lang.code && { color: '#fff' },
              ]}
            >
              {lang.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginVertical: 8 },
  label: { fontSize: 12, color: '#555', marginBottom: 4 },
  row: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 16,
    backgroundColor: '#e1e8ed',
    marginRight: 6,
    marginBottom: 6,
  },
  chipText: { fontSize: 12, color: '#333' },
});
