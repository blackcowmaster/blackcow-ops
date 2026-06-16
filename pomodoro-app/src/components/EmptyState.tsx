// src/components/EmptyState.tsx
// Placeholder shown when the task list is empty.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface EmptyStateProps {
  message: string;
  textColor: string;
  secondaryColor: string;
}

export function EmptyState({
  message,
  textColor,
  secondaryColor,
}: EmptyStateProps) {
  return (
    <View style={styles.container}>
      <Text style={[styles.icon, { color: secondaryColor }]}>{'\u2611'}</Text>
      <Text style={[styles.message, { color: secondaryColor }]}>
        {message}
      </Text>
      <Text style={[styles.hint, { color: secondaryColor }]}>
        Add tasks to stay organized during your focus sessions.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  icon: {
    fontSize: 48,
    marginBottom: 16,
    opacity: 0.5,
  },
  message: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 8,
  },
  hint: {
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 18,
    opacity: 0.7,
  },
});
