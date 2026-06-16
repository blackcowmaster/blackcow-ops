// src/pomodoro/types.ts
// Core types for the Pomodoro timer state machine.
// Framework-agnostic — usable in React (useReducer), Vue, or vanilla TS.

/** The high-level status of the timer. */
export type TimerStatus = 'idle' | 'running' | 'paused';

/** Which type of session is active or will start next. */
export type SessionType = 'work' | 'break';

/**
 * Complete timer state — the single source of truth for the timer domain.
 * This is what the reducer manages.
 */
export interface TimerState {
  /** Current timer status */
  status: TimerStatus;
  /** Active session type (work = 25 min, break = 5 min) */
  sessionType: SessionType;
  /** Remaining seconds in the current session (counts down) */
  timeRemaining: number;
  /** Total seconds for the current session (fixed per session type) */
  totalDuration: number;
  /** Number of completed work sessions today */
  sessionsToday: number;
}

/**
 * Discriminated union of all timer actions.
 * The reducer handles every variant — no default fallthrough.
 */
export type TimerAction =
  | { type: 'TIMER_START' }
  | { type: 'TIMER_PAUSE' }
  | { type: 'TIMER_RESET' }
  | { type: 'TIMER_TICK' }
  | { type: 'TIMER_COMPLETE'; nextSession: SessionType }
  | { type: 'SESSION_INCREMENT' };

/** Callback signatures for the timer engine. */
export interface TimerEngineCallbacks {
  /** Called every tick with the current drift in ms (actual - expected elapsed) */
  onTick: (driftMs: number) => void;
  /** Called when the timer reaches zero */
  onComplete: () => void;
}

/** Public interface of the drift-compensating timer engine. */
export interface TimerEngine {
  /** Start (or resume) the timer. Idempotent if already running. */
  start(): void;
  /** Pause the timer. No-op if not running. */
  pause(): void;
  /** Stop and fully reset the engine. Must call start() to begin again. */
  reset(): void;
  /** Milliseconds since last start/resume (accounting for pauses). */
  getElapsedMs(): number;
  /** Whether the engine interval is currently active. */
  isRunning(): boolean;
}
