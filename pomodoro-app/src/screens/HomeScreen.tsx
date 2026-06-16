// src/screens/HomeScreen.tsx
// Main Pomodoro timer screen — timer display, controls, session counter, stats.

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  AppState,
  AppStateStatus,
  TouchableOpacity,
  Text,
} from 'react-native';
import { Link } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTimerContext } from '../context/TimerContext';
import { useTaskContext } from '../context/TaskContext';
import { useTheme } from '../context/ThemeContext';
import { TimerDisplay } from '../components/TimerDisplay';
import { SessionTypeIndicator } from '../components/SessionTypeIndicator';
import { TimerControls } from '../components/TimerControls';
import { SessionCounter } from '../components/SessionCounter';
import { SessionStatsCard } from '../components/SessionStatsCard';
import { TaskBadge } from '../components/TaskBadge';
import { ThemeToggle } from '../components/ThemeToggle';
import { loadSessionHistory } from '../lib/storage';
import { requestNotificationPermissions } from '../lib/notifications';
import { computeSessionStats } from '../pomodoro/sessionStats';
import type { SessionStats } from '../pomodoro/types';

export function HomeScreen() {
  const { state, start, pause, reset } = useTimerContext();
  const { pendingCount } = useTaskContext();
  const { colors } = useTheme();

  const [stats, setStats] = useState<SessionStats>({
    sessionsToday: 0,
    totalFocusMinutes: 0,
    currentStreak: 0,
  });

  const reloadStats = useCallback(async () => {
    const history = await loadSessionHistory();
    setStats(computeSessionStats(history));
  }, []);

  // Reload stats on mount + when sessionsToday changes
  useEffect(() => {
    reloadStats();
  }, [state.sessionsToday, reloadStats]);

  // Request notification permissions on mount
  useEffect(() => {
    requestNotificationPermissions();
  }, []);

  // Daily reset: detect date change on app foreground
  const lastDateRef = useRef<string>('');
  useEffect(() => {
    const handleAppState = (nextState: AppStateStatus) => {
      if (nextState === 'active') {
        const today = new Date().toDateString();
        if (lastDateRef.current && lastDateRef.current !== today) {
          reloadStats();
        }
        lastDateRef.current = today;
      }
    };

    lastDateRef.current = new Date().toDateString();
    const sub = AppState.addEventListener('change', handleAppState);
    return () => sub.remove();
  }, [reloadStats]);

  const color =
    state.sessionType === 'work' ? colors.workColor : colors.breakColor;

  return (
    <SafeAreaView
      style={[styles.safeArea, { backgroundColor: colors.bgPrimary }]}
      edges={['top']}
    >
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Header row: theme toggle + tasks link + task badge */}
        <View style={styles.header}>
          <ThemeToggle />
          <View style={styles.headerSpacer} />
          <Link href="/tasks" asChild>
            <TouchableOpacity
              style={[styles.tasksButton, { backgroundColor: colors.bgSecondary, borderColor: colors.borderPrimary }]}
              accessibilityLabel="Open tasks"
              accessibilityRole="button"
            >
              <Text style={[styles.tasksLabel, { color: colors.textPrimary }]}>
                Tasks
              </Text>
              <TaskBadge
                count={pendingCount}
                accentColor={colors.accent}
                textColor="#ffffff"
              />
            </TouchableOpacity>
          </Link>
        </View>

        {/* Session type pill */}
        <SessionTypeIndicator
          sessionType={state.sessionType}
          workColor={colors.workColor}
          breakColor={colors.breakColor}
        />

        {/* Timer display with progress ring */}
        <View style={styles.timerSection}>
          <TimerDisplay
            timeRemaining={state.timeRemaining}
            totalDuration={state.totalDuration}
            status={state.status}
            color={color}
            trackColor={colors.progressTrack}
          />
        </View>

        {/* Start / Pause / Reset */}
        <TimerControls
          status={state.status}
          onStart={start}
          onPause={pause}
          onReset={reset}
          accentColor={colors.accent}
          textColor={colors.textPrimary}
          bgColor={colors.bgSecondary}
          borderColor={colors.borderPrimary}
        />

        {/* Sessions + Streak counter */}
        <SessionCounter
          sessions={stats.sessionsToday}
          streak={stats.currentStreak}
          textColor={colors.textPrimary}
          secondaryColor={colors.textSecondary}
        />

        {/* Detailed stats card */}
        <SessionStatsCard
          sessionsToday={stats.sessionsToday}
          totalFocusMinutes={stats.totalFocusMinutes}
          currentStreak={stats.currentStreak}
          bgColor={colors.cardBg}
          textColor={colors.textPrimary}
          secondaryColor={colors.textSecondary}
          accentColor={colors.accent}
          borderColor={colors.borderPrimary}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
    gap: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  headerSpacer: {
    flex: 1,
  },
  tasksButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1,
  },
  tasksLabel: {
    fontSize: 15,
    fontWeight: '600',
  },
  timerSection: {
    alignItems: 'center',
    paddingVertical: 8,
  },
});
