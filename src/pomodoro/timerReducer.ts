// src/pomodoro/timerReducer.ts
// Pure reducer function for the Pomodoro timer state machine.
// Designed to be passed directly to React's useReducer.
// Framework-agnostic — zero dependencies.

import type { TimerState, TimerAction, SessionType } from './types';

// ── Constants ────────────────────────────────────────────────────────────────

/** Work session duration in seconds (25 minutes). */
export const WORK_DURATION = 25 * 60; // 1500s

/** Break session duration in seconds (5 minutes). */
export const BREAK_DURATION = 5 * 60; // 300s

// ── Initial State ────────────────────────────────────────────────────────────

/**
 * Factory for the initial timer state.
 * Always starts idle, set for a work session.
 */
export function createInitialTimerState(): TimerState {
  return {
    status: 'idle',
    sessionType: 'work',
    timeRemaining: WORK_DURATION,
    totalDuration: WORK_DURATION,
    sessionsToday: 0,
  };
}

/**
 * Singleton initial state — safe to use directly since the reducer
 * always returns new objects.
 */
export const initialTimerState: TimerState = createInitialTimerState();

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Return the duration in seconds for a given session type. */
export function durationFor(sessionType: SessionType): number {
  return sessionType === 'work' ? WORK_DURATION : BREAK_DURATION;
}

/** Flip the session type. */
export function toggleSession(sessionType: SessionType): SessionType {
  return sessionType === 'work' ? 'break' : 'work';
}

// ── Reducer ──────────────────────────────────────────────────────────────────

/**
 * Pure reducer for the Pomodoro timer state machine.
 *
 * State transitions:
 * ```
 * IDLE    --TIMER_START-->  RUNNING  (session = work, time = 1500)
 * PAUSED  --TIMER_START-->  RUNNING  (resume, preserves time)
 * RUNNING --TIMER_PAUSE-->  PAUSED
 * ANY     --TIMER_RESET-->  IDLE     (session = work, time = 1500)
 * RUNNING --TIMER_TICK----> RUNNING  (time--,  no-op at 0)
 * IDLE    --TIMER_COMPLETE→ IDLE    (nextSession applied)
 * *       --SESSION_INCREMENT→ *     (sessionsToday++)
 * ```
 *
 * All unknown action types return the current state unchanged.
 */
export function timerReducer(
  state: TimerState,
  action: TimerAction,
): TimerState {
  switch (action.type) {
    // ── START ────────────────────────────────────────────────────────
    case 'TIMER_START': {
      // From idle: begin a new work session
      if (state.status === 'idle') {
        return {
          ...state,
          status: 'running',
          sessionType: 'work',
          timeRemaining: WORK_DURATION,
          totalDuration: WORK_DURATION,
        };
      }
      // From paused: resume with current time
      if (state.status === 'paused') {
        return { ...state, status: 'running' };
      }
      // Already running — no-op
      return state;
    }

    // ── PAUSE ────────────────────────────────────────────────────────
    case 'TIMER_PAUSE': {
      // Only pause if currently running
      if (state.status !== 'running') return state;
      return { ...state, status: 'paused' };
    }

    // ── RESET ────────────────────────────────────────────────────────
    case 'TIMER_RESET': {
      // Return to initial idle state regardless of current state
      return createInitialTimerState();
    }

    // ── TICK ─────────────────────────────────────────────────────────
    case 'TIMER_TICK': {
      // Only tick if running and time remains
      if (state.status !== 'running') return state;
      if (state.timeRemaining <= 0) return state;
      return { ...state, timeRemaining: state.timeRemaining - 1 };
    }

    // ── COMPLETE ─────────────────────────────────────────────────────
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

    // ── SESSION INCREMENT ────────────────────────────────────────────
    case 'SESSION_INCREMENT': {
      return { ...state, sessionsToday: state.sessionsToday + 1 };
    }

    // ── Unknown action ───────────────────────────────────────────────
    default: {
      // Exhaustiveness check: at compile time this ensures all
      // TimerAction variants are handled above.
      const _exhaustive: never = action;
      void _exhaustive;
      return state;
    }
  }
}
