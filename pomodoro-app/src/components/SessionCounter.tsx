// src/components/SessionCounter.tsx
// Displays today's completed work session count + streak.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface SessionCounterProps {
  sessions: number;
  streak: number;
  textColor: string;
  secondaryColor: string;
}

export function SessionCounter({
  sessions,
  streak,
  textColor,
  secondaryColor,
}: SessionCounterProps) {
  return (
    <View style={styles.container}>
      <View style={styles.stat}>
        <Text style={[styles.value, { color: textColor }]}>{sessions}</Text>
        <Text style={[styles.label, { color: secondaryColor }]}>
          sessions today
        </Text>
      </View>
      <View style={[styles.divider, { backgroundColor: secondaryColor }]} />
      <View style={styles.stat}>
        <Text style={[styles.value, { color: textColor }]}>{streak}</Text>
        <Text style={[styles.label, { color: secondaryColor }]}>
          day streak
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 24,
  },
  stat: {
    alignItems: 'center',
  },
  value: {
    fontSize: 28,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  label: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  divider: {
    width: 1,
    height: 36,
    opacity: 0.3,
  },
});
