# Pomodoro Timer App
React Native + Expo SDK 52+ cross-platform Pomodoro timer.

## Quick Start

```bash
cd pomodoro-app
npm install
npx expo start
```

## Features
- 25-min work timer with drift-compensated engine
- 5-min auto-break timer
- Task list with AsyncStorage persistence
- Daily session counter + streak tracking
- Session statistics (focus minutes, streak)
- Cross-platform notifications (iOS, Android, Web)
- Dark mode (light/dark/system) with persistence
- Responsive SVG circular progress

## Architecture
```
pomodoro-app/
├── app/                    # Expo Router file-based routes
│   ├── _layout.tsx         # Root layout + providers
│   ├── index.tsx           # Home screen (timer)
│   └── tasks.tsx           # Task list screen (modal)
├── src/
│   ├── pomodoro/           # Core logic (framework-agnostic)
│   │   ├── types.ts        # All TypeScript types
│   │   ├── timerReducer.ts # State machine
│   │   ├── timerEngine.ts  # Drift-compensating timer
│   │   ├── useTimer.ts     # React hook adapter
│   │   └── sessionStats.ts # Stats computation
│   ├── context/            # React Context providers
│   │   ├── TimerContext.tsx
│   │   ├── TaskContext.tsx
│   │   └── ThemeContext.tsx
│   ├── components/         # UI components
│   │   ├── CircularProgress.tsx
│   │   ├── TimerDisplay.tsx
│   │   ├── SessionTypeIndicator.tsx
│   │   ├── TimerControls.tsx
│   │   ├── SessionCounter.tsx
│   │   ├── SessionStatsCard.tsx
│   │   ├── TaskInput.tsx
│   │   ├── TaskItem.tsx
│   │   ├── TaskBadge.tsx
│   │   ├── EmptyState.tsx
│   │   ├── ErrorBoundary.tsx
│   │   └── ThemeToggle.tsx
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   └── TaskListScreen.tsx
│   └── lib/
│       ├── notifications.ts
│       └── storage.ts
├── assets/
├── app.json
├── babel.config.js
├── package.json
└── tsconfig.json
```
