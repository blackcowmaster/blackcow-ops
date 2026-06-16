// src/pomodoro/useTimer.ts
// React hook adapter for the Pomodoro timer.
// Bridges timerReducer + timerEngine for React Native components.

import { useReducer, useEffect, useRef, useCallback } from 'react';
import {
  timerReducer,
  initialTimerState,
  WORK_DURATION,
  BREAK_DURATION,
} from './timerReducer';
import { createTimerEngine } from './timerEngine';
import type { TimerState, TimerAction, SessionType } from './types';

export type { TimerState, TimerAction, TimerStatus, SessionType } from './types';

export interface UseTimerReturn {
  state: TimerState;
  dispatch: React.Dispatch<TimerAction>;
  start: () => void;
  pause: () => void;
  reset: () => void;
}

export function useTimer(
  onSessionComplete?: (sessionType: SessionType) => void,
): UseTimerReturn {
  const [state, dispatch] = useReducer(timerReducer, initialTimerState);

  const onTickRef = useRef<() => void>(() => {});
  const onCompleteRef = useRef<() => void>(() => {});
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
    onSessionComplete?.(current.sessionType);
  };

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.sessionType]);

  useEffect(() => {
    const engine = engineRef.current;
    if (!engine) return;

    if (state.status === 'running' && !engine.isRunning()) {
      engine.start();
    } else if (state.status !== 'running' && engine.isRunning()) {
      engine.pause();
    }
  }, [state.status]);

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
