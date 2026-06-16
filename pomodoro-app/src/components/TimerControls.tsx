// src/components/TimerControls.tsx
// Start / Pause / Reset button row with contextual enabled states.

import React from 'react';
import { View, TouchableOpacity, Text, StyleSheet } from 'react-native';
import type { TimerStatus } from '../pomodoro/types';

interface TimerControlsProps {
  status: TimerStatus;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  accentColor: string;
  textColor: string;
  bgColor: string;
  borderColor: string;
}

export function TimerControls({
  status,
  onStart,
  onPause,
  onReset,
  accentColor,
  textColor,
  bgColor,
  borderColor,
}: TimerControlsProps) {
  const isRunning = status === 'running';
  const isIdle = status === 'idle';
  const isPaused = status === 'paused';

  return (
    <View style={styles.container}>
      {/* Reset — always available */}
      <TouchableOpacity
        onPress={onReset}
        style={[
          styles.secondaryButton,
          { borderColor, backgroundColor: bgColor },
        ]}
        accessibilityLabel="Reset timer"
        accessibilityRole="button"
      >
        <Text style={[styles.secondaryLabel, { color: textColor }]}>
          Reset
        </Text>
      </TouchableOpacity>

      {/* Start / Pause — context-dependent */}
      <TouchableOpacity
        onPress={isRunning ? onPause : onStart}
        disabled={false}
        style={[
          styles.primaryButton,
          { backgroundColor: accentColor },
        ]}
        accessibilityLabel={
          isRunning ? 'Pause timer' : 'Start timer'
        }
        accessibilityRole="button"
      >
        <Text style={styles.primaryLabel}>
          {isRunning ? 'Pause' : isPaused ? 'Resume' : 'Start'}
        </Text>
      </TouchableOpacity>

      {/* Spacer for symmetric layout */}
      <View style={styles.secondaryButton} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  primaryButton: {
    width: 120,
    height: 52,
    borderRadius: 26,
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryLabel: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  secondaryButton: {
    width: 80,
    height: 44,
    borderRadius: 22,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryLabel: {
    fontSize: 15,
    fontWeight: '600',
  },
});
