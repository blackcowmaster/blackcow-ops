// app/_layout.tsx
// Root layout — wraps entire app with Context providers + Stack navigator.

import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { TimerProvider } from '../src/context/TimerContext';
import { TaskProvider } from '../src/context/TaskContext';
import { ThemeProvider, useTheme } from '../src/context/ThemeContext';
import { ErrorBoundary } from '../src/components/ErrorBoundary';
import { setupNotificationHandler } from '../src/lib/notifications';

function AppContent() {
  const { resolved, colors } = useTheme();
  const isDark = resolved === 'dark';

  // Setup notification handler once
  useEffect(() => {
    setupNotificationHandler();
  }, []);

  return (
    <ErrorBoundary
      bgColor={colors.bgPrimary}
      textColor={colors.textPrimary}
      errorColor={colors.error}
      accentColor={colors.accent}
    >
      <StatusBar style={isDark ? 'light' : 'dark'} />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.bgPrimary },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen
          name="tasks"
          options={{
            presentation: 'modal',
            headerShown: true,
            headerTitle: 'Tasks',
            headerStyle: { backgroundColor: colors.bgSecondary },
            headerTintColor: colors.textPrimary,
          }}
        />
      </Stack>
    </ErrorBoundary>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider>
      <TaskProvider>
        <TimerProvider>
          <AppContent />
        </TimerProvider>
      </TaskProvider>
    </ThemeProvider>
  );
}
