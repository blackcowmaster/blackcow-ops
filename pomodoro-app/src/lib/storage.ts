// src/lib/storage.ts
// AsyncStorage persistence layer for tasks and theme preference.

import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Task, SessionRecord, ThemeMode } from '../pomodoro/types';

const KEYS = {
  TASKS: 'pomodoro-tasks',
  THEME: 'pomodoro-theme',
  SESSION_HISTORY: 'pomodoro-session-history',
} as const;

// ── Tasks ──

export async function loadTasks(): Promise<Task[]> {
  try {
    const json = await AsyncStorage.getItem(KEYS.TASKS);
    if (!json) return [];
    const parsed = JSON.parse(json);
    if (!Array.isArray(parsed)) return [];
    return parsed as Task[];
  } catch {
    return [];
  }
}

export async function saveTasks(tasks: Task[]): Promise<void> {
  try {
    await AsyncStorage.setItem(KEYS.TASKS, JSON.stringify(tasks));
  } catch {
    // Storage full or unavailable — silently fail
  }
}

// ── Theme ──

export async function loadTheme(): Promise<ThemeMode | null> {
  try {
    const val = await AsyncStorage.getItem(KEYS.THEME);
    if (val === 'light' || val === 'dark' || val === 'system') return val;
    return null;
  } catch {
    return null;
  }
}

export async function saveTheme(mode: ThemeMode): Promise<void> {
  try {
    await AsyncStorage.setItem(KEYS.THEME, mode);
  } catch {
    // Silently fail
  }
}

// ── Session History ──

export async function loadSessionHistory(): Promise<SessionRecord[]> {
  try {
    const json = await AsyncStorage.getItem(KEYS.SESSION_HISTORY);
    if (!json) return [];
    const parsed = JSON.parse(json);
    if (!Array.isArray(parsed)) return [];
    return parsed as SessionRecord[];
  } catch {
    return [];
  }
}

export async function saveSessionHistory(history: SessionRecord[]): Promise<void> {
  try {
    // Keep last 90 days only
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 90);
    const cutoffStr = cutoff.toISOString();
    const recent = history.filter((r) => r.completedAt >= cutoffStr);
    await AsyncStorage.setItem(KEYS.SESSION_HISTORY, JSON.stringify(recent));
  } catch {
    // Silently fail
  }
}

export async function appendSessionRecord(record: SessionRecord): Promise<void> {
  const history = await loadSessionHistory();
  history.push(record);
  await saveSessionHistory(history);
}
