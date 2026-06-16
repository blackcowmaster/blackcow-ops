// src/pomodoro/timerEngine.ts
// Drift-compensating timer engine.
// Framework-agnostic — zero dependencies.

import type { TimerEngine, TimerEngineCallbacks } from './types';

export function createTimerEngine(
  callbacks: TimerEngineCallbacks,
  totalMs: number,
  intervalMs: number = 1000,
): TimerEngine {
  const { onTick, onComplete } = callbacks;

  let intervalId: ReturnType<typeof setInterval> | null = null;
  let startTime = 0;
  let tickCount = 0;
  let accumulatedPauseMs = 0;
  let pauseStartTime = 0;
  let running = false;
  let completed = false;

  function clearTimer(): void {
    if (intervalId !== null) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }

  const engine: TimerEngine = {
    start(): void {
      if (running) return;
      if (completed) return;

      if (intervalId !== null) {
        accumulatedPauseMs += Date.now() - pauseStartTime;
      } else {
        startTime = Date.now();
        tickCount = 0;
        accumulatedPauseMs = 0;
        completed = false;
      }

      running = true;

      intervalId = setInterval(() => {
        tickCount++;
        const now = Date.now();
        const elapsed = now - startTime - accumulatedPauseMs;
        const expected = tickCount * intervalMs;
        const drift = elapsed - expected;

        if (elapsed >= totalMs) {
          clearTimer();
          running = false;
          completed = true;
          onComplete();
          return;
        }

        onTick(drift);
      }, intervalMs);
    },

    pause(): void {
      if (!running) return;
      clearTimer();
      running = false;
      pauseStartTime = Date.now();
    },

    reset(): void {
      clearTimer();
      running = false;
      completed = false;
      tickCount = 0;
      startTime = 0;
      accumulatedPauseMs = 0;
      pauseStartTime = 0;
    },

    getElapsedMs(): number {
      if (startTime === 0) return 0;
      if (!running) return tickCount * intervalMs;
      return Date.now() - startTime - accumulatedPauseMs;
    },

    isRunning(): boolean {
      return running;
    },
  };

  return engine;
}
