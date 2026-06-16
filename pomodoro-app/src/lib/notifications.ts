// src/lib/notifications.ts
// Cross-platform notification scheduling for Pomodoro session completion.
// Uses expo-notifications for iOS, Android, and Web.

import * as Notifications from 'expo-notifications';
import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';
import type { SessionType } from '../pomodoro/types';

// ── Setup ──

export function setupNotificationHandler(): void {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

export async function requestNotificationPermissions(): Promise<boolean> {
  try {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') return false;

    // Android requires explicit channel creation
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('pomodoro-alerts', {
        name: 'Pomodoro Alerts',
        importance: Notifications.AndroidImportance.HIGH,
        sound: 'default',
      });
    }

    return true;
  } catch {
    return false;
  }
}

// ── Scheduling ──

export async function sendSessionCompleteNotification(
  sessionType: SessionType,
): Promise<void> {
  // Cancel any pending to avoid notification pile-up
  await Notifications.cancelAllScheduledNotificationsAsync();

  const isWork = sessionType === 'work';

  await Notifications.scheduleNotificationAsync({
    content: {
      title: isWork ? 'Work Session Complete!' : 'Break Over!',
      body: isWork
        ? 'Great job! Take a 5-minute break.'
        : 'Break finished. Ready to focus?',
      sound: true,
    },
    trigger: null, // immediate
  });

  // Haptic feedback (mobile only)
  if (Platform.OS !== 'web') {
    try {
      await Haptics.notificationAsync(
        isWork
          ? Haptics.NotificationFeedbackType.Success
          : Haptics.NotificationFeedbackType.Warning,
      );
    } catch {
      // Haptics unavailable — silently skip
    }
  }
}
