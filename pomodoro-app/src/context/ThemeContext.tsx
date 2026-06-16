// src/context/ThemeContext.tsx
// React Context provider for persistent dark/light mode.
// Uses Appearance API + AsyncStorage for cross-session persistence.

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
} from 'react';
import { useColorScheme } from 'react-native';
import { loadTheme, saveTheme } from '../lib/storage';
import type { ThemeMode } from '../pomodoro/types';
type ResolvedTheme = 'light' | 'dark';

interface ThemeContextValue {
  mode: ThemeMode;
  resolved: ResolvedTheme;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
  colors: typeof lightColors;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

// ── Color Tokens ──

export const lightColors = {
  bgPrimary: '#ffffff',
  bgSecondary: '#f5f5f5',
  bgTertiary: '#e8e8e8',
  bgInverse: '#1a1a1a',
  textPrimary: '#1a1a1a',
  textSecondary: '#666666',
  textTertiary: '#999999',
  textInverse: '#ffffff',
  textLink: '#2563eb',
  borderPrimary: '#d4d4d4',
  borderSecondary: '#e8e8e8',
  accent: '#2563eb',
  accentHover: '#1d4ed8',
  success: '#16a34a',
  warning: '#d97706',
  error: '#dc2626',
  errorBg: '#fef2f2',
  shadow: 'rgba(0,0,0,0.1)',
  disabled: '#a3a3a3',
  workColor: '#ef4444',
  breakColor: '#22c55e',
  cardBg: '#ffffff',
  progressTrack: '#e8e8e8',
} as const;

export const darkColors: typeof lightColors = {
  bgPrimary: '#1a1a1a',
  bgSecondary: '#262626',
  bgTertiary: '#333333',
  bgInverse: '#ffffff',
  textPrimary: '#f5f5f5',
  textSecondary: '#a3a3a3',
  textTertiary: '#737373',
  textInverse: '#1a1a1a',
  textLink: '#60a5fa',
  borderPrimary: '#404040',
  borderSecondary: '#333333',
  accent: '#3b82f6',
  accentHover: '#60a5fa',
  success: '#22c55e',
  warning: '#f59e0b',
  error: '#ef4444',
  errorBg: '#450a0a',
  shadow: 'rgba(0,0,0,0.4)',
  disabled: '#525252',
  workColor: '#f87171',
  breakColor: '#4ade80',
  cardBg: '#262626',
  progressTrack: '#333333',
} as const;

function resolveTheme(mode: ThemeMode, systemScheme: 'light' | 'dark'): ResolvedTheme {
  if (mode === 'system') return systemScheme;
  return mode;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const systemScheme = useColorScheme() ?? 'light';
  const [mode, setModeState] = useState<ThemeMode>('system');

  // Hydrate saved theme on mount
  useEffect(() => {
    loadTheme().then((saved) => {
      if (saved) setModeState(saved);
    });
  }, []);

  const resolved = resolveTheme(mode, systemScheme);
  const colors = resolved === 'dark' ? darkColors : lightColors;

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    saveTheme(newMode);
  }, []);

  const toggle = useCallback(() => {
    setModeState((prev) => {
      const current = resolveTheme(prev, systemScheme);
      const next: ThemeMode = current === 'dark' ? 'light' : 'dark';
      saveTheme(next);
      return next;
    });
  }, [systemScheme]);

  return (
    <ThemeContext.Provider value={{ mode, resolved, setMode, toggle, colors }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return ctx;
}
