// src/pomodoro/sessionStats.ts
// Pure-computation session statistics module.
// Computes sessions today, total focus minutes, and consecutive-day streak.

import type { SessionStats, DailySummary, SessionRecord } from './types';

function toLocalDate(isoString: string): string {
  const d = new Date(isoString);
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, '0');
  const dd = String(d.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

function previousDay(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number);
  const prev = new Date(Date.UTC(y, m - 1, d - 1));
  const py = prev.getUTCFullYear();
  const pm = String(prev.getUTCMonth() + 1).padStart(2, '0');
  const pd = String(prev.getUTCDate()).padStart(2, '0');
  return `${py}-${pm}-${pd}`;
}

export function getTodayDateString(): string {
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, '0');
  const dd = String(today.getDate()).padStart(2, '0');
  return `${yyyy}-${mm}-${dd}`;
}

export function isConsecutiveDay(day1: string, day2: string): boolean {
  const [y1, m1, d1] = day1.split('-').map(Number);
  const next = new Date(Date.UTC(y1, m1 - 1, d1 + 1));
  const ny = next.getUTCFullYear();
  const nm = String(next.getUTCMonth() + 1).padStart(2, '0');
  const nd = String(next.getUTCDate()).padStart(2, '0');
  const expected = `${ny}-${nm}-${nd}`;
  return day2 === expected;
}

export function computeSessionStats(history: SessionRecord[]): SessionStats {
  const today = getTodayDateString();
  const workSessions = history.filter((s) => s.type === 'work');

  let sessionsToday = 0;
  let totalFocusSeconds = 0;
  const activeDays = new Set<string>();

  for (const session of workSessions) {
    const localDate = toLocalDate(session.completedAt);
    if (localDate === today) {
      sessionsToday++;
      totalFocusSeconds += session.durationSeconds;
    }
    activeDays.add(localDate);
  }

  const totalFocusMinutes = Math.round(totalFocusSeconds / 60);

  let currentStreak = 0;
  if (activeDays.has(today)) {
    currentStreak = 1;
    let cursor = today;
    // eslint-disable-next-line no-constant-condition
    while (true) {
      cursor = previousDay(cursor);
      if (activeDays.has(cursor)) {
        currentStreak++;
      } else {
        break;
      }
    }
  }

  return { sessionsToday, totalFocusMinutes, currentStreak };
}

export function generateDailySummary(history: SessionRecord[]): DailySummary {
  const stats = computeSessionStats(history);
  return {
    date: getTodayDateString(),
    sessionsCompleted: stats.sessionsToday,
    focusMinutes: stats.totalFocusMinutes,
    streak: stats.currentStreak,
  };
}

export function formatDuration(seconds: number): string {
  if (seconds <= 0) return '0s';
  const totalSeconds = Math.floor(seconds);
  if (totalSeconds < 60) return `${totalSeconds}s`;

  const minutes = Math.floor(totalSeconds / 60);
  if (totalSeconds < 3600) return `${minutes}m`;

  const hours = Math.floor(totalSeconds / 3600);
  const remainingMinutes = minutes % 60;
  if (remainingMinutes === 0) return `${hours}h`;
  return `${hours}h ${remainingMinutes}m`;
}

export function formatTimeMMSS(seconds: number): string {
  const clamped = Math.max(0, Math.floor(seconds));
  const mins = Math.floor(clamped / 60);
  const secs = clamped % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}
