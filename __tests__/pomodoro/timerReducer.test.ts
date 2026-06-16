// __tests__/pomodoro/timerReducer.test.ts
// Unit tests for the Pomodoro timer state machine.
// Tests every transition, edge case, and guard clause in timerReducer.

import {
  timerReducer,
  createInitialTimerState,
  WORK_DURATION,
  BREAK_DURATION,
  durationFor,
  toggleSession,
} from '../../src/pomodoro/timerReducer';
import type { TimerState, TimerAction } from '../../src/pomodoro/types';

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Create a fresh idle state for each test. */
function idle(): TimerState {
  return createInitialTimerState();
}

/** Create a running state (work session, 1200s remaining). */
function running(overrides: Partial<TimerState> = {}): TimerState {
  return {
    status: 'running',
    sessionType: 'work',
    timeRemaining: 1200,
    totalDuration: WORK_DURATION,
    sessionsToday: 0,
    ...overrides,
  };
}

/** Create a paused state (work session, 900s remaining). */
function paused(overrides: Partial<TimerState> = {}): TimerState {
  return {
    status: 'paused',
    sessionType: 'work',
    timeRemaining: 900,
    totalDuration: WORK_DURATION,
    sessionsToday: 0,
    ...overrides,
  };
}

// ── Constants ────────────────────────────────────────────────────────────────

describe('constants', () => {
  it('WORK_DURATION is 25 minutes (1500 seconds)', () => {
    expect(WORK_DURATION).toBe(1500);
  });

  it('BREAK_DURATION is 5 minutes (300 seconds)', () => {
    expect(BREAK_DURATION).toBe(300);
  });
});

// ── Helpers ──────────────────────────────────────────────────────────────────

describe('durationFor', () => {
  it('returns WORK_DURATION for "work"', () => {
    expect(durationFor('work')).toBe(WORK_DURATION);
  });

  it('returns BREAK_DURATION for "break"', () => {
    expect(durationFor('break')).toBe(BREAK_DURATION);
  });
});

describe('toggleSession', () => {
  it('toggles work → break', () => {
    expect(toggleSession('work')).toBe('break');
  });

  it('toggles break → work', () => {
    expect(toggleSession('break')).toBe('work');
  });
});

// ── Initial State ────────────────────────────────────────────────────────────

describe('initial state', () => {
  it('is idle', () => {
    expect(idle().status).toBe('idle');
  });

  it('is set for a work session', () => {
    expect(idle().sessionType).toBe('work');
  });

  it('has WORK_DURATION time remaining', () => {
    expect(idle().timeRemaining).toBe(WORK_DURATION);
  });

  it('has WORK_DURATION as total duration', () => {
    expect(idle().totalDuration).toBe(WORK_DURATION);
  });

  it('has zero sessions today', () => {
    expect(idle().sessionsToday).toBe(0);
  });

  it('createInitialTimerState returns a new object each call', () => {
    const a = createInitialTimerState();
    const b = createInitialTimerState();
    expect(a).not.toBe(b);
    expect(a).toEqual(b);
  });
});

// ── TIMER_START ──────────────────────────────────────────────────────────────

describe('TIMER_START', () => {
  const action: TimerAction = { type: 'TIMER_START' };

  describe('from idle', () => {
    it('transitions to running', () => {
      const next = timerReducer(idle(), action);
      expect(next.status).toBe('running');
    });

    it('sets sessionType to work', () => {
      const next = timerReducer(idle(), action);
      expect(next.sessionType).toBe('work');
    });

    it('sets timeRemaining to WORK_DURATION', () => {
      const next = timerReducer(idle(), action);
      expect(next.timeRemaining).toBe(WORK_DURATION);
    });

    it('sets totalDuration to WORK_DURATION', () => {
      const next = timerReducer(idle(), action);
      expect(next.totalDuration).toBe(WORK_DURATION);
    });

    it('preserves sessionsToday', () => {
      const state = { ...idle(), sessionsToday: 3 };
      const next = timerReducer(state, action);
      expect(next.sessionsToday).toBe(3);
    });

    it('returns a new object (immutability)', () => {
      const state = idle();
      const next = timerReducer(state, action);
      expect(next).not.toBe(state);
    });
  });

  describe('from paused', () => {
    it('transitions to running', () => {
      const next = timerReducer(paused(), action);
      expect(next.status).toBe('running');
    });

    it('preserves timeRemaining (resume, not restart)', () => {
      const next = timerReducer(paused({ timeRemaining: 900 }), action);
      expect(next.timeRemaining).toBe(900);
    });

    it('preserves sessionType', () => {
      const next = timerReducer(paused({ sessionType: 'break' }), action);
      expect(next.sessionType).toBe('break');
    });

    it('preserves sessionsToday', () => {
      const next = timerReducer(paused({ sessionsToday: 5 }), action);
      expect(next.sessionsToday).toBe(5);
    });
  });

  describe('from running (no-op)', () => {
    it('does not change state', () => {
      const state = running();
      const next = timerReducer(state, action);
      expect(next).toEqual(state);
    });

    it('returns the same reference-equivalent state', () => {
      const state = running();
      const next = timerReducer(state, action);
      expect(next.status).toBe('running');
      expect(next.timeRemaining).toBe(state.timeRemaining);
    });
  });
});

// ── TIMER_PAUSE ──────────────────────────────────────────────────────────────

describe('TIMER_PAUSE', () => {
  const action: TimerAction = { type: 'TIMER_PAUSE' };

  describe('from running', () => {
    it('transitions to paused', () => {
      const next = timerReducer(running(), action);
      expect(next.status).toBe('paused');
    });

    it('preserves timeRemaining', () => {
      const next = timerReducer(running({ timeRemaining: 777 }), action);
      expect(next.timeRemaining).toBe(777);
    });

    it('preserves sessionType', () => {
      const next = timerReducer(running({ sessionType: 'break' }), action);
      expect(next.sessionType).toBe('break');
    });

    it('preserves sessionsToday', () => {
      const next = timerReducer(running({ sessionsToday: 2 }), action);
      expect(next.sessionsToday).toBe(2);
    });
  });

  describe('from idle (no-op)', () => {
    it('does not change state', () => {
      const next = timerReducer(idle(), action);
      expect(next).toEqual(idle());
    });
  });

  describe('from paused (no-op)', () => {
    it('does not change state', () => {
      const state = paused();
      const next = timerReducer(state, action);
      expect(next).toEqual(state);
    });
  });
});

// ── TIMER_RESET ──────────────────────────────────────────────────────────────

describe('TIMER_RESET', () => {
  const action: TimerAction = { type: 'TIMER_RESET' };

  it('returns to idle from running', () => {
    const next = timerReducer(running({ sessionsToday: 4 }), action);
    expect(next.status).toBe('idle');
    expect(next.sessionType).toBe('work');
    expect(next.timeRemaining).toBe(WORK_DURATION);
    expect(next.totalDuration).toBe(WORK_DURATION);
    expect(next.sessionsToday).toBe(0); // resets everything
  });

  it('returns to idle from paused', () => {
    const next = timerReducer(paused({ sessionsToday: 7 }), action);
    expect(next.status).toBe('idle');
    expect(next.sessionsToday).toBe(0);
  });

  it('returns to idle from idle (idempotent)', () => {
    const next = timerReducer(idle(), action);
    expect(next).toEqual(idle());
  });

  it('always resets sessionsToday to 0', () => {
    const next = timerReducer(
      { ...idle(), sessionsToday: 99 },
      action,
    );
    expect(next.sessionsToday).toBe(0);
  });
});

// ── TIMER_TICK ───────────────────────────────────────────────────────────────

describe('TIMER_TICK', () => {
  const action: TimerAction = { type: 'TIMER_TICK' };

  describe('from running', () => {
    it('decrements timeRemaining by 1', () => {
      const next = timerReducer(running({ timeRemaining: 100 }), action);
      expect(next.timeRemaining).toBe(99);
    });

    it('stays in running status', () => {
      const next = timerReducer(running(), action);
      expect(next.status).toBe('running');
    });

    it('decrements from 1 to 0', () => {
      const next = timerReducer(running({ timeRemaining: 1 }), action);
      expect(next.timeRemaining).toBe(0);
    });

    it('does not go below 0 (clamped)', () => {
      const next = timerReducer(running({ timeRemaining: 0 }), action);
      expect(next.timeRemaining).toBe(0);
    });

    it('preserves sessionType', () => {
      const next = timerReducer(running({ sessionType: 'break' }), action);
      expect(next.sessionType).toBe('break');
    });
  });

  describe('from idle (no-op)', () => {
    it('does not decrement timeRemaining', () => {
      const next = timerReducer(idle(), action);
      expect(next.timeRemaining).toBe(WORK_DURATION);
    });

    it('stays idle', () => {
      const next = timerReducer(idle(), action);
      expect(next.status).toBe('idle');
    });
  });

  describe('from paused (no-op)', () => {
    it('does not decrement timeRemaining', () => {
      const state = paused({ timeRemaining: 500 });
      const next = timerReducer(state, action);
      expect(next.timeRemaining).toBe(500);
    });

    it('stays paused', () => {
      const next = timerReducer(paused(), action);
      expect(next.status).toBe('paused');
    });
  });

  describe('immutability', () => {
    it('returns new object on tick', () => {
      const state = running();
      const next = timerReducer(state, action);
      expect(next).not.toBe(state);
    });

    it('does not mutate original state', () => {
      const state = running({ timeRemaining: 50 });
      timerReducer(state, action);
      expect(state.timeRemaining).toBe(50); // unchanged
    });
  });
});

// ── TIMER_COMPLETE ───────────────────────────────────────────────────────────

describe('TIMER_COMPLETE', () => {
  describe('work → break transition', () => {
    const action: TimerAction = { type: 'TIMER_COMPLETE', nextSession: 'break' };

    it('transitions to idle', () => {
      const next = timerReducer(running(), action);
      expect(next.status).toBe('idle');
    });

    it('sets sessionType to break', () => {
      const next = timerReducer(running(), action);
      expect(next.sessionType).toBe('break');
    });

    it('sets timeRemaining to BREAK_DURATION', () => {
      const next = timerReducer(running(), action);
      expect(next.timeRemaining).toBe(BREAK_DURATION);
    });

    it('sets totalDuration to BREAK_DURATION', () => {
      const next = timerReducer(running(), action);
      expect(next.totalDuration).toBe(BREAK_DURATION);
    });

    it('preserves sessionsToday (increment is separate action)', () => {
      const next = timerReducer(running({ sessionsToday: 3 }), action);
      expect(next.sessionsToday).toBe(3);
    });
  });

  describe('break → work transition', () => {
    const action: TimerAction = { type: 'TIMER_COMPLETE', nextSession: 'work' };

    it('sets sessionType to work', () => {
      const next = timerReducer(
        running({ sessionType: 'break', timeRemaining: 10 }),
        action,
      );
      expect(next.sessionType).toBe('work');
    });

    it('sets timeRemaining to WORK_DURATION', () => {
      const next = timerReducer(
        running({ sessionType: 'break' }),
        action,
      );
      expect(next.timeRemaining).toBe(WORK_DURATION);
    });

    it('does NOT increment sessionsToday', () => {
      const next = timerReducer(
        running({ sessionType: 'break', sessionsToday: 5 }),
        action,
      );
      expect(next.sessionsToday).toBe(5);
    });
  });

  describe('from any state', () => {
    it('works from idle state', () => {
      const action: TimerAction = { type: 'TIMER_COMPLETE', nextSession: 'break' };
      const next = timerReducer(idle(), action);
      expect(next.status).toBe('idle');
      expect(next.sessionType).toBe('break');
    });

    it('works from paused state', () => {
      const action: TimerAction = { type: 'TIMER_COMPLETE', nextSession: 'work' };
      const next = timerReducer(paused(), action);
      expect(next.status).toBe('idle');
      expect(next.sessionType).toBe('work');
    });
  });
});

// ── SESSION_INCREMENT ────────────────────────────────────────────────────────

describe('SESSION_INCREMENT', () => {
  const action: TimerAction = { type: 'SESSION_INCREMENT' };

  it('increments sessionsToday by 1', () => {
    const next = timerReducer(idle(), action);
    expect(next.sessionsToday).toBe(1);
  });

  it('increments from existing count', () => {
    const state = { ...idle(), sessionsToday: 4 };
    const next = timerReducer(state, action);
    expect(next.sessionsToday).toBe(5);
  });

  it('does not change other fields', () => {
    const state = running({ sessionsToday: 2 });
    const next = timerReducer(state, action);
    expect(next.status).toBe('running');
    expect(next.timeRemaining).toBe(state.timeRemaining);
    expect(next.sessionType).toBe(state.sessionType);
  });

  it('works from paused', () => {
    const state = paused({ sessionsToday: 9 });
    const next = timerReducer(state, action);
    expect(next.sessionsToday).toBe(10);
    expect(next.status).toBe('paused');
  });
});

// ── Full workflow simulations ────────────────────────────────────────────────

describe('full workflows', () => {
  it('complete work session: idle → start → ticks → complete → break', () => {
    let state = idle();

    // Start
    state = timerReducer(state, { type: 'TIMER_START' });
    expect(state.status).toBe('running');
    expect(state.sessionType).toBe('work');
    expect(state.timeRemaining).toBe(WORK_DURATION);

    // Tick down to 1
    while (state.timeRemaining > 1) {
      state = timerReducer(state, { type: 'TIMER_TICK' });
    }
    expect(state.timeRemaining).toBe(1);

    // Final tick to 0
    state = timerReducer(state, { type: 'TIMER_TICK' });
    expect(state.timeRemaining).toBe(0);

    // Complete → break
    state = timerReducer(state, { type: 'TIMER_COMPLETE', nextSession: 'break' });
    expect(state.status).toBe('idle');
    expect(state.sessionType).toBe('break');
    expect(state.timeRemaining).toBe(BREAK_DURATION);
  });

  it('pause and resume mid-session', () => {
    let state = idle();

    // Start
    state = timerReducer(state, { type: 'TIMER_START' });
    expect(state.status).toBe('running');

    // Tick 10 times
    for (let i = 0; i < 10; i++) {
      state = timerReducer(state, { type: 'TIMER_TICK' });
    }
    const timeAfterTicks = state.timeRemaining;
    expect(timeAfterTicks).toBe(WORK_DURATION - 10);

    // Pause
    state = timerReducer(state, { type: 'TIMER_PAUSE' });
    expect(state.status).toBe('paused');
    expect(state.timeRemaining).toBe(timeAfterTicks); // preserved

    // Tick while paused — no-op
    state = timerReducer(state, { type: 'TIMER_TICK' });
    expect(state.timeRemaining).toBe(timeAfterTicks);

    // Resume
    state = timerReducer(state, { type: 'TIMER_START' });
    expect(state.status).toBe('running');
    expect(state.timeRemaining).toBe(timeAfterTicks); // still preserved

    // More ticks work
    state = timerReducer(state, { type: 'TIMER_TICK' });
    expect(state.timeRemaining).toBe(timeAfterTicks - 1);
  });

  it('full work→break→work cycle with session increment', () => {
    let state = idle();

    // Work session
    state = timerReducer(state, { type: 'TIMER_START' });
    while (state.timeRemaining > 0) {
      state = timerReducer(state, { type: 'TIMER_TICK' });
    }

    // Complete work → increment → break
    state = timerReducer(state, { type: 'SESSION_INCREMENT' });
    expect(state.sessionsToday).toBe(1);
    state = timerReducer(state, { type: 'TIMER_COMPLETE', nextSession: 'break' });
    expect(state.sessionType).toBe('break');

    // Run break session
    state = timerReducer(state, { type: 'TIMER_START' });
    while (state.timeRemaining > 0) {
      state = timerReducer(state, { type: 'TIMER_TICK' });
    }

    // Complete break → work (no increment)
    state = timerReducer(state, { type: 'TIMER_COMPLETE', nextSession: 'work' });
    expect(state.sessionType).toBe('work');
    expect(state.sessionsToday).toBe(1); // unchanged

    // Start next work session
    state = timerReducer(state, { type: 'TIMER_START' });
    expect(state.status).toBe('running');
    expect(state.timeRemaining).toBe(WORK_DURATION);
    expect(state.sessionsToday).toBe(1);
  });

  it('reset mid-session and start fresh', () => {
    let state = idle();

    // Start and tick a few times
    state = timerReducer(state, { type: 'TIMER_START' });
    for (let i = 0; i < 50; i++) {
      state = timerReducer(state, { type: 'TIMER_TICK' });
    }
    expect(state.timeRemaining).toBe(WORK_DURATION - 50);
    expect(state.sessionsToday).toBe(0);

    // Reset
    state = timerReducer(state, { type: 'TIMER_RESET' });
    expect(state.status).toBe('idle');
    expect(state.timeRemaining).toBe(WORK_DURATION);
    expect(state.sessionsToday).toBe(0);

    // Start again works
    state = timerReducer(state, { type: 'TIMER_START' });
    expect(state.status).toBe('running');
    expect(state.timeRemaining).toBe(WORK_DURATION);
  });
});

// ── Immutability across all actions ──────────────────────────────────────────

describe('immutability', () => {
  const actions: { name: string; action: TimerAction; initialState: TimerState }[] = [
    { name: 'TIMER_START (idle)', action: { type: 'TIMER_START' }, initialState: idle() },
    { name: 'TIMER_START (paused)', action: { type: 'TIMER_START' }, initialState: paused() },
    { name: 'TIMER_PAUSE', action: { type: 'TIMER_PAUSE' }, initialState: running() },
    { name: 'TIMER_RESET', action: { type: 'TIMER_RESET' }, initialState: running() },
    { name: 'TIMER_TICK', action: { type: 'TIMER_TICK' }, initialState: running() },
    { name: 'TIMER_COMPLETE', action: { type: 'TIMER_COMPLETE', nextSession: 'break' }, initialState: running() },
    { name: 'SESSION_INCREMENT', action: { type: 'SESSION_INCREMENT' }, initialState: idle() },
  ];

  for (const { name, action, initialState } of actions) {
    it(`${name} returns a new object`, () => {
      const next = timerReducer(initialState, action);
      expect(next).not.toBe(initialState);
    });

    it(`${name} does not mutate the original state`, () => {
      const before = { ...initialState };
      timerReducer(initialState, action);
      expect(initialState).toEqual(before);
    });
  }
});
