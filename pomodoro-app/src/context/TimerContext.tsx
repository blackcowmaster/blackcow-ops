// src/context/TimerContext.tsx
// React Context provider wrapping the Pomodoro timer state machine.
// Internally handles session completion: notifications + history persistence.

import React, { createContext, useContext, useCallback } from 'react';
import { useTimer } from '../pomodoro/useTimer';
import type { TimerState, TimerAction, SessionType } from '../pomodoro/types';
import { WORK_DURATION } from '../pomodoro/timerReducer';
import {
  appendSessionRecord,
  loadSessionHistory,
} from '../lib/storage';
import { sendSessionCompleteNotification } from '../lib/notifications';

interface TimerContextValue {
  state: TimerState;
  dispatch: React.Dispatch<TimerAction>;
  start: () => void;
  pause: () => void;
  reset: () => void;
}

const TimerContext = createContext<TimerContextValue | undefined>(undefined);

export function TimerProvider({ children }: { children: React.ReactNode }) {
  const handleSessionComplete = useCallback(
    async (sessionType: SessionType) => {
      const record = {
        completedAt: new Date().toISOString(),
        durationSeconds: sessionType === 'work' ? WORK_DURATION : 300,
        type: sessionType,
      };
      // Fire-and-forget — don't block the timer state update
      appendSessionRecord(record).catch(() => {});
      sendSessionCompleteNotification(sessionType).catch(() => {});
    },
    [],
  );

  const timer = useTimer(handleSessionComplete);

  return (
    <TimerContext.Provider value={timer}>{children}</TimerContext.Provider>
  );
}

export function useTimerContext(): TimerContextValue {
  const ctx = useContext(TimerContext);
  if (!ctx) {
    throw new Error('useTimerContext must be used within a TimerProvider');
  }
  return ctx;
}
