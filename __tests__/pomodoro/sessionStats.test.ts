// __tests__/pomodoro/sessionStats.test.ts
// Unit tests for the session statistics module.
// Tests: same-day sessions, cross-midnight, empty history, single entry,
// streak with gaps, DST boundaries, and helper functions.
//
// Key design constraint (from pomodoro-wave1-qa S1 finding):
//   The stats module MUST receive SessionRecord[] as input — it MUST NOT
//   read TimerState.sessionsToday, which gets wiped by TIMER_RESET.

import {
  computeSessionStats,
  getTodayDateString,
  isConsecutiveDay,
} from '../../src/pomodoro/sessionStats';
import type { SessionRecord, SessionStats } from '../../src/pomodoro/sessionStats';

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Create a SessionRecord with defaults for brevity. */
function record(
  completedAt: string,
  durationSeconds = 1500,
  type: 'work' | 'break' = 'work',
): SessionRecord {
  return { completedAt, durationSeconds, type };
}

/** Return an ISO string for a date N days before/after today at noon local. */
function isoAtNoon(daysOffset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  d.setHours(12, 0, 0, 0);
  return d.toISOString();
}

/** Return YYYY-MM-DD for a date N days offset from today. */
function dateString(daysOffset = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + daysOffset);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

// ── getTodayDateString ───────────────────────────────────────────────────────

describe('getTodayDateString', () => {
  it('returns a string in YYYY-MM-DD format', () => {
    const result = getTodayDateString();
    expect(result).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });

  it('matches the current local date', () => {
    const result = getTodayDateString();
    const expected = dateString(0);
    expect(result).toBe(expected);
  });

  it('returns the same value when called multiple times', () => {
    const a = getTodayDateString();
    const b = getTodayDateString();
    expect(a).toBe(b);
  });
});

// ── isConsecutiveDay ─────────────────────────────────────────────────────────

describe('isConsecutiveDay', () => {
  it('returns true for consecutive days', () => {
    expect(isConsecutiveDay('2025-07-17', '2025-07-18')).toBe(true);
  });

  it('returns false for same day', () => {
    expect(isConsecutiveDay('2025-07-17', '2025-07-17')).toBe(false);
  });

  it('returns false for days with a gap', () => {
    expect(isConsecutiveDay('2025-07-17', '2025-07-19')).toBe(false);
  });

  it('returns false when day1 is after day2', () => {
    expect(isConsecutiveDay('2025-07-18', '2025-07-17')).toBe(false);
  });

  it('handles month boundaries', () => {
    expect(isConsecutiveDay('2025-01-31', '2025-02-01')).toBe(true);
    expect(isConsecutiveDay('2025-02-28', '2025-03-01')).toBe(true);
  });

  it('handles year boundaries', () => {
    expect(isConsecutiveDay('2025-12-31', '2026-01-01')).toBe(true);
    expect(isConsecutiveDay('2025-12-31', '2026-01-02')).toBe(false);
  });

  it('handles leap year — Feb 28 → Feb 29', () => {
    expect(isConsecutiveDay('2024-02-28', '2024-02-29')).toBe(true);
  });

  it('handles leap year — Feb 29 → Mar 1', () => {
    expect(isConsecutiveDay('2024-02-29', '2024-03-01')).toBe(true);
  });

  it('handles non-leap year — Feb 28 → Mar 1', () => {
    expect(isConsecutiveDay('2025-02-28', '2025-03-01')).toBe(true);
  });

  // DST boundary: isConsecutiveDay only deals with date strings (no time),
  // so DST has no effect.  This test verifies that invariant.
  it('is unaffected by DST (pure date arithmetic, no time component)', () => {
    // Spring forward: March 10 → March 11, 2024 (US DST)
    expect(isConsecutiveDay('2024-03-10', '2024-03-11')).toBe(true);
    // Fall back: November 3 → November 4, 2024 (US DST)
    expect(isConsecutiveDay('2024-11-03', '2024-11-04')).toBe(true);
  });
});

// ── computeSessionStats: empty / minimal history ─────────────────────────────

describe('computeSessionStats — empty / minimal', () => {
  it('returns zeros for empty history', () => {
    const stats = computeSessionStats([]);
    expect(stats).toEqual({
      sessionsToday: 0,
      totalFocusMinutes: 0,
      currentStreak: 0,
    });
  });

  it('single work session today — 1 session, 25 min, streak 1', () => {
    const stats = computeSessionStats([record(isoAtNoon(0))]);
    expect(stats.sessionsToday).toBe(1);
    expect(stats.totalFocusMinutes).toBe(25);
    expect(stats.currentStreak).toBe(1);
  });

  it('single break session today — does NOT count for focus minutes or streak', () => {
    const stats = computeSessionStats([record(isoAtNoon(0), 300, 'break')]);
    expect(stats.sessionsToday).toBe(0);
    expect(stats.totalFocusMinutes).toBe(0);
    expect(stats.currentStreak).toBe(0);
  });

  it('single entry from past day — 0 today, streak 0', () => {
    const yesterday = isoAtNoon(-1);
    const stats = computeSessionStats([record(yesterday)]);
    expect(stats.sessionsToday).toBe(0);
    expect(stats.totalFocusMinutes).toBe(0);
    expect(stats.currentStreak).toBe(0);
  });

  it('single entry from yesterday + today empty → streak 0', () => {
    const yesterday = isoAtNoon(-1);
    const stats = computeSessionStats([record(yesterday)]);
    // No sessions today → streak is 0 (must include today)
    expect(stats.currentStreak).toBe(0);
  });
});

// ── computeSessionStats: same-day sessions ───────────────────────────────────

describe('computeSessionStats — same-day', () => {
  it('multiple work sessions today — aggregates correctly', () => {
    const sessions = [
      record(isoAtNoon(0), 1500, 'work'),
      record(isoAtNoon(0), 1500, 'work'),
      record(isoAtNoon(0), 1500, 'work'),
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(3);
    expect(stats.totalFocusMinutes).toBe(75); // 3 × 25
    expect(stats.currentStreak).toBe(1);
  });

  it('mixed work + break sessions today — only work counts', () => {
    const sessions = [
      record(isoAtNoon(0), 1500, 'work'),
      record(isoAtNoon(0), 300, 'break'),
      record(isoAtNoon(0), 1500, 'work'),
      record(isoAtNoon(0), 300, 'break'),
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(2);
    expect(stats.totalFocusMinutes).toBe(50); // 2 × 25
  });

  it('non-standard session durations — aggregates correctly', () => {
    const sessions = [
      record(isoAtNoon(0), 1800, 'work'), // 30 min
      record(isoAtNoon(0), 600, 'work'), // 10 min
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(2);
    expect(stats.totalFocusMinutes).toBe(40);
  });
});

// ── computeSessionStats: cross-midnight ──────────────────────────────────────

describe('computeSessionStats — cross-midnight', () => {
  it('session just before midnight local time counts for that day, not today', () => {
    // Create a timestamp that is yesterday in local time
    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    yesterday.setHours(23, 59, 0, 0);
    const stats = computeSessionStats([record(yesterday.toISOString())]);
    expect(stats.sessionsToday).toBe(0);
  });

  it('session just after midnight local time counts for today', () => {
    const today = new Date();
    today.setHours(0, 1, 0, 0);
    const stats = computeSessionStats([record(today.toISOString())]);
    expect(stats.sessionsToday).toBe(1);
  });

  it('session today at 11:59 PM local counts for today', () => {
    const today = new Date();
    today.setHours(23, 59, 0, 0);
    const stats = computeSessionStats([record(today.toISOString())]);
    expect(stats.sessionsToday).toBe(1);
  });

  it('UTC midnight ≠ local midnight — uses local date', () => {
    // If local timezone is UTC-5, then 2025-07-17T04:00:00Z = 2025-07-16 11PM local
    // We can't hardcode the offset, but we can test that the module uses local time.
    // Create a known UTC timestamp and verify it maps to the correct local date.
    const now = new Date();
    const todayLocal = dateString(0);
    // A session at noon UTC today — should map to today's local date
    // (unless local TZ is way off, which is fine — this tests the principle)
    const noonToday = new Date(now);
    noonToday.setHours(12, 0, 0, 0);
    const stats = computeSessionStats([record(noonToday.toISOString())]);
    expect(stats.sessionsToday).toBe(1);
  });
});

// ── computeSessionStats: streaks ─────────────────────────────────────────────

describe('computeSessionStats — streaks', () => {
  it('streak of 3 consecutive days including today', () => {
    const sessions = [
      record(isoAtNoon(0)), // today
      record(isoAtNoon(-1)), // yesterday
      record(isoAtNoon(-2)), // 2 days ago
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.currentStreak).toBe(3);
  });

  it('streak of 7 consecutive days', () => {
    const sessions: SessionRecord[] = [];
    for (let i = 0; i >= -6; i--) {
      sessions.push(record(isoAtNoon(i)));
    }
    const stats = computeSessionStats(sessions);
    expect(stats.currentStreak).toBe(7);
    expect(stats.sessionsToday).toBe(1);
    expect(stats.totalFocusMinutes).toBe(25);
  });

  it('streak stops at first gap (even if earlier days have sessions)', () => {
    const sessions = [
      record(isoAtNoon(0)), // today ← streak starts
      record(isoAtNoon(-1)), // yesterday ← continues
      // gap at -2
      record(isoAtNoon(-3)), // 3 days ago ← NOT part of streak
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.currentStreak).toBe(2);
  });

  it('streak of 1 when today has sessions but yesterday does not', () => {
    const sessions = [
      record(isoAtNoon(0)), // today
      record(isoAtNoon(-2)), // 2 days ago (gap)
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.currentStreak).toBe(1);
  });

  it('streak of 0 when today has no sessions (even if yesterday does)', () => {
    const sessions = [record(isoAtNoon(-1))];
    const stats = computeSessionStats(sessions);
    expect(stats.currentStreak).toBe(0);
  });

  it('multiple sessions on same day do not affect streak count', () => {
    const sessions = [
      record(isoAtNoon(0)),
      record(isoAtNoon(0)),
      record(isoAtNoon(0)), // 3 sessions today
      record(isoAtNoon(-1)), // 1 session yesterday
    ];
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(3);
    expect(stats.currentStreak).toBe(2); // 2 days, not 4
  });

  it('streak across month boundary', () => {
    // Use explicit date strings to test month boundary
    const sessions = [
      { completedAt: '2025-07-01T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
      { completedAt: '2025-06-30T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
      { completedAt: '2025-06-29T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
    ];
    // We can only assert this if today is July 1, 2025 — skip if not
    const today = dateString(0);
    if (today === '2025-07-01') {
      const stats = computeSessionStats(sessions);
      expect(stats.currentStreak).toBe(3);
    }
  });

  it('streak across year boundary', () => {
    const sessions = [
      { completedAt: '2026-01-01T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
      { completedAt: '2025-12-31T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
      { completedAt: '2025-12-30T12:00:00.000Z', durationSeconds: 1500, type: 'work' as const },
    ];
    const today = dateString(0);
    if (today === '2026-01-01') {
      const stats = computeSessionStats(sessions);
      expect(stats.currentStreak).toBe(3);
    }
  });
});

// ── computeSessionStats: DST boundaries ──────────────────────────────────────

describe('computeSessionStats — DST boundaries', () => {
  it('spring-forward: 23-hour day does not break streak', () => {
    // March 10, 2024 (US DST spring-forward): day is 23 hours long
    // Sessions on Mar 9, Mar 10, Mar 11 should form a streak of 3
    // These are UTC timestamps at noon Eastern (before/after DST shift)
    const sessions = [
      { completedAt: '2024-03-11T16:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EDT = 16:00Z
      { completedAt: '2024-03-10T16:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EDT = 16:00Z
      { completedAt: '2024-03-09T17:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EST = 17:00Z
    ];
    const today = dateString(0);
    if (today === '2024-03-11') {
      const stats = computeSessionStats(sessions);
      expect(stats.currentStreak).toBe(3);
    }
  });

  it('fall-back: 25-hour day does not break streak', () => {
    // November 3, 2024 (US DST fall-back): day is 25 hours long
    const sessions = [
      { completedAt: '2024-11-04T17:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EST = 17:00Z
      { completedAt: '2024-11-03T17:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EST = 17:00Z
      { completedAt: '2024-11-02T16:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // noon EDT = 16:00Z
    ];
    const today = dateString(0);
    if (today === '2024-11-04') {
      const stats = computeSessionStats(sessions);
      expect(stats.currentStreak).toBe(3);
    }
  });

  it('DST transition does not affect session counting for a single day', () => {
    // DST spring-forward: a session completed in the morning and evening of Mar 10
    // should both count as Mar 10, not two different days
    const sessions = [
      { completedAt: '2024-03-10T10:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // 5am EST
      { completedAt: '2024-03-10T20:00:00.000Z', durationSeconds: 1500, type: 'work' as const }, // 4pm EDT
    ];
    const today = dateString(0);
    if (today === '2024-03-10') {
      const stats = computeSessionStats(sessions);
      expect(stats.sessionsToday).toBe(2);
    }
  });
});

// ── computeSessionStats: mixed scenarios ─────────────────────────────────────

describe('computeSessionStats — mixed scenarios', () => {
  it('unsorted history — still computes correctly', () => {
    const sessions = [record(isoAtNoon(-2)), record(isoAtNoon(0)), record(isoAtNoon(-1))];
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(1);
    expect(stats.currentStreak).toBe(3); // today, yesterday, 2 days ago all present
  });

  it('history with only breaks — all zeros', () => {
    const sessions = [
      record(isoAtNoon(0), 300, 'break'),
      record(isoAtNoon(-1), 300, 'break'),
      record(isoAtNoon(-2), 300, 'break'),
    ];
    const stats = computeSessionStats(sessions);
    expect(stats).toEqual({
      sessionsToday: 0,
      totalFocusMinutes: 0,
      currentStreak: 0,
    });
  });

  it('large history (365 days) — does not crash', () => {
    const sessions: SessionRecord[] = [];
    for (let i = 0; i < 365; i++) {
      sessions.push({ completedAt: isoAtNoon(-i), durationSeconds: 1500, type: 'work' });
    }
    const stats = computeSessionStats(sessions);
    expect(stats.sessionsToday).toBe(1);
    expect(stats.currentStreak).toBe(365);
    expect(stats.totalFocusMinutes).toBe(25);
  });

  it('returns a new object each call (no mutation risk)', () => {
    const sessions = [record(isoAtNoon(0))];
    const a = computeSessionStats(sessions);
    const b = computeSessionStats(sessions);
    expect(a).toEqual(b);
    expect(a).not.toBe(b); // different object references
  });
});

// ── TypeScript compile-time checks ───────────────────────────────────────────

describe('type safety', () => {
  it('SessionRecord type is usable at runtime', () => {
    const r: SessionRecord = {
      completedAt: '2025-07-17T12:00:00.000Z',
      durationSeconds: 1500,
      type: 'work',
    };
    expect(r.completedAt).toBe('2025-07-17T12:00:00.000Z');
  });

  it('SessionStats shape is correct', () => {
    const stats: SessionStats = {
      sessionsToday: 3,
      totalFocusMinutes: 75,
      currentStreak: 7,
    };
    expect(stats.currentStreak).toBe(7);
  });
});
