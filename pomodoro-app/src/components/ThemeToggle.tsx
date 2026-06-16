// src/components/ThemeToggle.tsx
// Dark/light/system mode toggle button.

import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useTheme } from '../context/ThemeContext';
import type { ThemeMode } from '../pomodoro/types';

const MODE_ICONS: Record<ThemeMode, string> = {
  light: '\u2600',  // sun
  dark: '\u263E',   // moon
  system: '\u2699', // gear
};

const MODE_LABELS: Record<ThemeMode, string> = {
  light: 'Light',
  dark: 'Dark',
  system: 'System',
};

export function ThemeToggle() {
  const { mode, setMode, colors } = useTheme();

  const cycle = () => {
    const modes: ThemeMode[] = ['light', 'dark', 'system'];
    const idx = modes.indexOf(mode);
    const next = modes[(idx + 1) % modes.length];
    setMode(next);
  };

  return (
    <TouchableOpacity
      onPress={cycle}
      style={[styles.button, { backgroundColor: colors.bgTertiary }]}
      accessibilityLabel={`Theme: ${MODE_LABELS[mode]}. Tap to change.`}
      accessibilityRole="button"
    >
      <Text style={styles.icon}>{MODE_ICONS[mode]}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: 20,
  },
});
