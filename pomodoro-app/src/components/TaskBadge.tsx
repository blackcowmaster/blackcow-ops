// src/components/TaskBadge.tsx
// Small badge showing count of pending (incomplete) tasks.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface TaskBadgeProps {
  count: number;
  accentColor: string;
  textColor: string;
}

export function TaskBadge({ count, accentColor, textColor }: TaskBadgeProps) {
  if (count === 0) return null;

  return (
    <View style={[styles.badge, { backgroundColor: accentColor }]}>
      <Text style={[styles.text, { color: textColor }]}>{count}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    minWidth: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 6,
  },
  text: {
    fontSize: 12,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
});
