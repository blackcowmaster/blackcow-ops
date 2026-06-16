// src/components/SessionTypeIndicator.tsx
// Visual indicator showing WORK (red) or BREAK (green) session type.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import type { SessionType } from '../pomodoro/types';

interface SessionTypeIndicatorProps {
  sessionType: SessionType;
  workColor: string;
  breakColor: string;
}

export function SessionTypeIndicator({
  sessionType,
  workColor,
  breakColor,
}: SessionTypeIndicatorProps) {
  const isWork = sessionType === 'work';
  const color = isWork ? workColor : breakColor;
  const label = isWork ? 'WORK' : 'BREAK';
  const dot = isWork ? '\u25CF' : '\u25CB'; // filled / hollow circle

  return (
    <View style={[styles.container, { borderColor: color }]}>
      <Text style={[styles.dot, { color }]}>{dot}</Text>
      <Text style={[styles.label, { color }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1.5,
    alignSelf: 'center',
  },
  dot: {
    fontSize: 10,
    marginRight: 6,
  },
  label: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 3,
  },
});
