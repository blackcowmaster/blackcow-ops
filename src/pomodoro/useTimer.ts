// src/pomodoro/useTimer.ts
// React hook adapter for the Pomodoro timer.
//
// This file is a REFERENCE ADAPTER — it requires 'react' as a peer
// dependency.  It is NOT compiled or tested in this Express/Node.js
// project.  Copy this file into a React / React Native project to use.
//
// Usage in a React component:
//
//   import { useTimer } from './useTimer';
//
//   function TimerScreen() {
//     const { state, dispatch, engine } = useTimer();
//     // state.timer.status, state.timer.timeRemaining, etc.
//   }

import { useReducer, useEffect, useRef, useCallback } from 'react';
import {
  timerReducer,
  initialTimerState,
  WORK_DURATION,
  BREAK_DURATION,
} from './timerReducer';
import { createTimerEngine } from './timerEngine';
import type { TimerState, TimerAction, SessionType } from './types';

// Re-export types for convenience
export type { TimerState, TimerAction, TimerStatus, SessionType } from './types';

export interface UseTimerReturn {
  state: TimerState;
  dispatch: React.Dispatch<TimerAction>;
  /** Start the timer (from idle or paused). */
  start: () => void;
  /** Pause the running timer. */
  pause: () => void;
  /** Reset to idle work state. */
  reset: () => void;
}

/**
 * React hook that wires the timerReducer + timerEngine together.
 *
 * - `useReducer` manages the state machine
 * - `createTimerEngine` handles drift-compensated setInterval
 * - `useEffect` bridges the engine callbacks to dispatch
 */
export function useTimer(): UseTimerReturn {
  const [state, dispatch] = useReducer(timerReducer, initialTimerState);

  // Stable callback refs to avoid re-creating the engine on every render
  const onTickRef = useRef<() => void>(() => {});
  const onCompleteRef = useRef<() => void>(() => {});

  // Keep refs in sync with current state
  const stateRef = useRef(state);
  stateRef.current = state;

  onTickRef.current = () => {
    dispatch({ type: 'TIMER_TICK' });
  };

  onCompleteRef.current = () => {
    const current = stateRef.current;
    const nextSession: SessionType =
      current.sessionType === 'work' ? 'break' : 'work';

    if (current.sessionType === 'work') {
      dispatch({ type: 'SESSION_INCREMENT' });
    }

    dispatch({ type: 'TIMER_COMPLETE', nextSession });
  };

  // Create engine on mount, destroy on unmount
  const engineRef = useRef<ReturnType<typeof createTimerEngine> | null>(null);

  useEffect(() => {
    const durationMs =
      (state.sessionType === 'work' ? WORK_DURATION : BREAK_DURATION) * 1000;

    engineRef.current = createTimerEngine(
      {
        onTick: () => onTickRef.current(),
        onComplete: () => onCompleteRef.current(),
      },
      durationMs,
      1000,
    );

    return () => {
      engineRef.current?.reset();
    };
    // Only re-create engine when session type changes (work ↔ break)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.sessionType]);

  // Sync engine with timer status
  useEffect(() => {
    const engine = engineRef.current;
    if (!engine) return;

    if (state.status === 'running' && !engine.isRunning()) {
      engine.start();
    } else if (state.status !== 'running' && engine.isRunning()) {
      engine.pause();
    }
  }, [state.status]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      engineRef.current?.reset();
    };
  }, []);

  const start = useCallback(() => dispatch({ type: 'TIMER_START' }), []);
  const pause = useCallback(() => dispatch({ type: 'TIMER_PAUSE' }), []);
  const reset = useCallback(() => {
    engineRef.current?.reset();
    dispatch({ type: 'TIMER_RESET' });
  }, []);

  return { state, dispatch, start, pause, reset };
}
