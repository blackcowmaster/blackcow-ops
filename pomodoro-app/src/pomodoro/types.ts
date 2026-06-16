// src/pomodoro/types.ts
// Core types for the Pomodoro timer state machine.
// Framework-agnostic — zero dependencies.

export type TimerStatus = 'idle' | 'running' | 'paused';
export type SessionType = 'work' | 'break';

export interface TimerState {
  status: TimerStatus;
  sessionType: SessionType;
  timeRemaining: number;
  totalDuration: number;
  sessionsToday: number;
}

export type TimerAction =
  | { type: 'TIMER_START' }
  | { type: 'TIMER_PAUSE' }
  | { type: 'TIMER_RESET' }
  | { type: 'TIMER_TICK' }
  | { type: 'TIMER_COMPLETE'; nextSession: SessionType }
  | { type: 'SESSION_INCREMENT' };

export interface TimerEngineCallbacks {
  onTick: (driftMs: number) => void;
  onComplete: () => void;
}

export interface TimerEngine {
  start(): void;
  pause(): void;
  reset(): void;
  getElapsedMs(): number;
  isRunning(): boolean;
}

// ── Task Domain ──

export interface Task {
  id: string;
  title: string;
  completed: boolean;
  createdAt: string;
}

export type TaskAction =
  | { type: 'TASK_ADD'; payload: { title: string } }
  | { type: 'TASK_TOGGLE'; payload: { id: string } }
  | { type: 'TASK_DELETE'; payload: { id: string } }
  | { type: 'TASKS_HYDRATE'; payload: { tasks: Task[] } };

// ── Unified App State ──

export type AppAction = TimerAction | TaskAction;

export interface AppState {
  timer: TimerState;
  tasks: Task[];
}

// ── Session Stats ──

export interface SessionRecord {
  completedAt: string;
  durationSeconds: number;
  type: 'work' | 'break';
}

export interface SessionStats {
  sessionsToday: number;
  totalFocusMinutes: number;
  currentStreak: number;
}

export interface DailySummary {
  date: string;
  sessionsCompleted: number;
  focusMinutes: number;
  streak: number;
}

// ── Theme ──

export type ThemeMode = 'light' | 'dark' | 'system';
