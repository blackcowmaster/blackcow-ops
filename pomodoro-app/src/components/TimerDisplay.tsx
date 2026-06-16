// src/components/TimerDisplay.tsx
// Large MM:SS countdown display with circular progress ring.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { CircularProgress } from './CircularProgress';
import { formatTimeMMSS } from '../pomodoro/sessionStats';
import type { TimerStatus } from '../pomodoro/types';

interface TimerDisplayProps {
  timeRemaining: number;
  totalDuration: number;
  status: TimerStatus;
  color: string;
  trackColor: string;
}

export function TimerDisplay({
  timeRemaining,
  totalDuration,
  status,
  color,
  trackColor,
}: TimerDisplayProps) {
  const progress =
    totalDuration > 0 ? timeRemaining / totalDuration : 0;
  const isIdle = status === 'idle';

  return (
    <View style={styles.container}>
      <CircularProgress
        progress={isIdle ? 1 : progress}
        size={260}
        strokeWidth={12}
        color={isIdle ? trackColor : color}
        trackColor={trackColor}
      />
      <View style={styles.timeOverlay}>
        <Text style={[styles.timeText, { color }]}>
          {formatTimeMMSS(timeRemaining)}
        </Text>
        <Text style={[styles.statusLabel, { color }]}>
          {status === 'running' ? 'FOCUS' : status.toUpperCase()}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  timeOverlay: {
    position: 'absolute',
    alignItems: 'center',
  },
  timeText: {
    fontSize: 56,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
    letterSpacing: -2,
  },
  statusLabel: {
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 4,
    marginTop: 4,
  },
});
