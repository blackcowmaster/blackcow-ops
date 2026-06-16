// __tests__/pomodoro/timerEngine.test.ts
// Unit tests for the drift-compensating timer engine.
// Tests: lifecycle (start/pause/reset), tick firing, drift reporting,
// completion detection, and edge cases (double-start, pause-when-idle, etc.).

import { createTimerEngine } from '../../src/pomodoro/timerEngine';
import type { TimerEngine } from '../../src/pomodoro/types';

// ── Helpers ──────────────────────────────────────────────────────────────────

interface CallbackLog {
  ticks: number[]; // drift values received
  completes: number;
}

function createLoggingCallbacks(): {
  log: CallbackLog;
  onTick: (drift: number) => void;
  onComplete: () => void;
} {
  const log: CallbackLog = { ticks: [], completes: 0 };
  return {
    log,
    onTick: (drift) => log.ticks.push(drift),
    onComplete: () => log.completes++,
  };
}

// ── Lifecycle: start / pause / reset ─────────────────────────────────────────

describe('lifecycle', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('isRunning is false before start', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    expect(engine.isRunning()).toBe(false);
  });

  it('isRunning is true after start', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    engine.start();
    expect(engine.isRunning()).toBe(true);
  });

  it('isRunning is false after pause', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    engine.start();
    engine.pause();
    expect(engine.isRunning()).toBe(false);
  });

  it('isRunning is false after reset', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    engine.start();
    engine.reset();
    expect(engine.isRunning()).toBe(false);
  });

  it('start is idempotent (double start does not crash)', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    engine.start();
    engine.start(); // second call — should be no-op
    expect(engine.isRunning()).toBe(true);
  });

  it('pause is idempotent (double pause does not crash)', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    engine.start();
    engine.pause();
    engine.pause(); // second call — should be no-op
    expect(engine.isRunning()).toBe(false);
  });
});

// ── Tick firing ──────────────────────────────────────────────────────────────

describe('tick firing', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('fires onTick at the specified interval', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();

    // Advance 1 tick
    jest.advanceTimersByTime(1000);
    expect(log.ticks.length).toBe(1);

    // Advance another tick
    jest.advanceTimersByTime(1000);
    expect(log.ticks.length).toBe(2);

    // Advance 3 more ticks
    jest.advanceTimersByTime(3000);
    expect(log.ticks.length).toBe(5);
  });

  it('does NOT fire ticks after pause', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000); // 3 ticks
    expect(log.ticks.length).toBe(3);

    engine.pause();
    jest.advanceTimersByTime(5000); // should NOT fire any ticks
    expect(log.ticks.length).toBe(3);
  });

  it('resumes firing ticks after pause + start', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(2000); // 2 ticks
    expect(log.ticks.length).toBe(2);

    engine.pause();
    jest.advanceTimersByTime(1000); // paused — no ticks

    engine.start(); // resume
    jest.advanceTimersByTime(2000); // 2 more ticks
    expect(log.ticks.length).toBe(4);
  });

  it('does NOT fire ticks after reset', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000); // 3 ticks
    expect(log.ticks.length).toBe(3);

    engine.reset();
    jest.advanceTimersByTime(5000); // should NOT fire any ticks
    expect(log.ticks.length).toBe(3);
  });
});

// ── Drift reporting ──────────────────────────────────────────────────────────

describe('drift reporting', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('reports near-zero drift under fake timers (ideal conditions)', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();

    // With fake timers, Date.now() advances in sync with advanceTimersByTime
    jest.advanceTimersByTime(1000);
    expect(log.ticks[0]).toBeCloseTo(0, -1); // drift ≈ 0ms (±10ms)

    jest.advanceTimersByTime(1000);
    expect(log.ticks[1]).toBeCloseTo(0, -1);

    jest.advanceTimersByTime(1000);
    expect(log.ticks[2]).toBeCloseTo(0, -1);
  });

  it('drift stays within ±500ms over extended period', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 30 * 60 * 1000, 1000); // 30 min

    engine.start();

    // Simulate 30 minutes of ticks
    for (let i = 0; i < 30 * 60; i++) {
      jest.advanceTimersByTime(1000);
    }

    // All drift values should be within ±500ms
    // Under fake timers, they'll be near-zero.  The assertion is a safety bound.
    for (const drift of log.ticks) {
      expect(Math.abs(drift)).toBeLessThan(500);
    }
  });

  it('reports drift values as milliseconds', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(1000);

    // Drift should be a number (milliseconds), not NaN or undefined
    expect(typeof log.ticks[0]).toBe('number');
    expect(Number.isFinite(log.ticks[0])).toBe(true);
  });
});

// ── Completion detection ─────────────────────────────────────────────────────

describe('completion', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('fires onComplete exactly when totalMs is reached', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 3000, 1000);

    engine.start();

    // After 2 ticks (2000ms), not yet complete
    jest.advanceTimersByTime(2000);
    expect(log.completes).toBe(0);
    expect(log.ticks.length).toBe(2);

    // After 3rd tick (3000ms), complete fires
    jest.advanceTimersByTime(1000);
    expect(log.completes).toBe(1);
  });

  it('stops ticking after completion', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 3000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000); // completion fires here

    const tickCountAtCompletion = log.ticks.length;
    expect(log.completes).toBe(1);

    // Advance well past the duration
    jest.advanceTimersByTime(10000);
    expect(log.ticks.length).toBe(tickCountAtCompletion);
    expect(log.completes).toBe(1); // only once
  });

  it('isRunning is false after completion', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 2000, 1000);

    engine.start();
    jest.advanceTimersByTime(2000);

    expect(engine.isRunning()).toBe(false);
  });

  it('completion fires on exact boundary (not late)', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000, 1000);

    engine.start();

    // Advance exactly to 5000ms
    jest.advanceTimersByTime(5000);
    expect(log.completes).toBe(1);
  });

  it('does not fire onComplete if reset before completion', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000); // 3 ticks in, 2s remaining
    expect(log.completes).toBe(0);

    engine.reset();

    // Advance past what would have been completion
    jest.advanceTimersByTime(5000);
    expect(log.completes).toBe(0);
  });

  it('does not fire onComplete after pause without reaching total', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000, 1000);

    engine.start();
    jest.advanceTimersByTime(2000); // 2 ticks
    engine.pause();

    // Time passes while paused — should not trigger completion
    jest.advanceTimersByTime(10000);
    expect(log.completes).toBe(0);
  });
});

// ── getElapsedMs ─────────────────────────────────────────────────────────────

describe('getElapsedMs', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('returns 0 before start', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 5000);
    expect(engine.getElapsedMs()).toBe(0);
  });

  it('returns elapsed time while running', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();

    jest.advanceTimersByTime(3500);
    // After 3.5s with 1s ticks, 3 ticks have fired
    // getElapsedMs uses Date.now() which is advanced by fake timers
    const elapsed = engine.getElapsedMs();
    expect(elapsed).toBeGreaterThanOrEqual(3000);
    expect(elapsed).toBeLessThan(4000);
  });

  it('returns 0 after reset', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000);

    engine.reset();
    expect(engine.getElapsedMs()).toBe(0);
  });

  it('does not advance while paused', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000);
    engine.pause();

    const elapsedAtPause = engine.getElapsedMs();

    // Time passes while paused
    jest.advanceTimersByTime(5000);

    // getElapsedMs should still be close to what it was at pause
    // (using tick-based calculation since paused)
    const elapsedAfterPause = engine.getElapsedMs();
    expect(elapsedAfterPause).toBe(elapsedAtPause);
  });
});

// ── Edge cases ───────────────────────────────────────────────────────────────

describe('edge cases', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('zero totalMs — completes immediately on start', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 0, 1000);

    engine.start();

    // First tick sees elapsed ≥ 0 → complete
    jest.advanceTimersByTime(1000);
    expect(log.completes).toBe(1);
    expect(log.ticks.length).toBe(0); // completes before tick callback
  });

  it('negative totalMs — treated same as zero (completes immediately)', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, -500, 1000);

    engine.start();
    jest.advanceTimersByTime(1000);
    expect(log.completes).toBe(1);
  });

  it('custom interval (e.g., 100ms ticks)', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 500, 100);

    engine.start();

    // Should fire every 100ms
    jest.advanceTimersByTime(100);
    expect(log.ticks.length).toBe(1);

    jest.advanceTimersByTime(100);
    expect(log.ticks.length).toBe(2);

    jest.advanceTimersByTime(100);
    expect(log.ticks.length).toBe(3);

    jest.advanceTimersByTime(100);
    expect(log.ticks.length).toBe(4);

    // 5th tick at 500ms → completion
    jest.advanceTimersByTime(100);
    expect(log.completes).toBe(1);
  });

  it('cannot start after completion without reset', () => {
    const { onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 2000, 1000);

    engine.start();
    jest.advanceTimersByTime(2000);
    expect(engine.isRunning()).toBe(false);

    // Try to start again without reset
    engine.start();
    expect(engine.isRunning()).toBe(false); // should not start
  });

  it('can start again after reset following completion', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 2000, 1000);

    // First run
    engine.start();
    jest.advanceTimersByTime(2000);
    expect(log.completes).toBe(1);

    // Reset and run again
    engine.reset();
    engine.start();
    jest.advanceTimersByTime(2000);
    expect(log.completes).toBe(2);
  });

  it('multiple pause/resume cycles do not accumulate drift', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();

    // Run 2s, pause 1s, run 2s, pause 1s, run 2s
    jest.advanceTimersByTime(2000);
    engine.pause();
    jest.advanceTimersByTime(1000);
    engine.start();

    jest.advanceTimersByTime(2000);
    engine.pause();
    jest.advanceTimersByTime(1000);
    engine.start();

    jest.advanceTimersByTime(2000);
    // Total active time: 6s → 6 ticks

    expect(log.ticks.length).toBe(6);

    // Drift should still be near-zero (pause time was correctly excluded)
    for (const drift of log.ticks) {
      expect(Math.abs(drift)).toBeLessThan(500);
    }
  });
});

// ── Cleanup (no leaks) ───────────────────────────────────────────────────────

describe('cleanup', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('reset clears the interval (no ticks after reset)', () => {
    const { log, onTick, onComplete } = createLoggingCallbacks();
    const engine = createTimerEngine({ onTick, onComplete }, 10000, 1000);

    engine.start();
    jest.advanceTimersByTime(3000);
    expect(log.ticks.length).toBe(3);

    engine.reset();

    // Clear any pending timers and advance
    jest.clearAllTimers();
    jest.advanceTimersByTime(10000);
    expect(log.ticks.length).toBe(3); // no new ticks
  });
});
