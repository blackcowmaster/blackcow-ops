// src/pomodoro/timerReducer.ts
// Pure reducer function for the Pomodoro timer state machine.
// Zero dependencies — framework-agnostic.

import type { TimerState, TimerAction, SessionType } from './types';

export const WORK_DURATION = 25 * 60;
export const BREAK_DURATION = 5 * 60;

export function createInitialTimerState(): TimerState {
  return {
    status: 'idle',
    sessionType: 'work',
    timeRemaining: WORK_DURATION,
    totalDuration: WORK_DURATION,
    sessionsToday: 0,
  };
}

export const initialTimerState: TimerState = createInitialTimerState();

export function durationFor(sessionType: SessionType): number {
  return sessionType === 'work' ? WORK_DURATION : BREAK_DURATION;
}

export function toggleSession(sessionType: SessionType): SessionType {
  return sessionType === 'work' ? 'break' : 'work';
}

export function timerReducer(
  state: TimerState,
  action: TimerAction,
): TimerState {
  switch (action.type) {
    case 'TIMER_START': {
      if (state.status === 'idle') {
        return {
          ...state,
          status: 'running',
          sessionType: 'work',
          timeRemaining: WORK_DURATION,
          totalDuration: WORK_DURATION,
        };
      }
      if (state.status === 'paused') {
        return { ...state, status: 'running' };
      }
      return state;
    }
    case 'TIMER_PAUSE': {
      if (state.status !== 'running') return state;
      return { ...state, status: 'paused' };
    }
    case 'TIMER_RESET': {
      return createInitialTimerState();
    }
    case 'TIMER_TICK': {
      if (state.status !== 'running') return state;
      if (state.timeRemaining <= 0) return state;
      return { ...state, timeRemaining: state.timeRemaining - 1 };
    }
    case 'TIMER_COMPLETE': {
      const nextDuration = durationFor(action.nextSession);
      return {
        ...state,
        status: 'idle',
        sessionType: action.nextSession,
        timeRemaining: nextDuration,
        totalDuration: nextDuration,
      };
    }
    case 'SESSION_INCREMENT': {
      return { ...state, sessionsToday: state.sessionsToday + 1 };
    }
    default: {
      const _exhaustive: never = action;
      void _exhaustive;
      return state;
    }
  }
}
