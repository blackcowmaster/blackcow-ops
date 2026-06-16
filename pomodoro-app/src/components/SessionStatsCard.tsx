// src/components/SessionStatsCard.tsx
// Card displaying today's session statistics with focus minutes and streak.

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { formatDuration } from '../pomodoro/sessionStats';

interface SessionStatsCardProps {
  sessionsToday: number;
  totalFocusMinutes: number;
  currentStreak: number;
  bgColor: string;
  textColor: string;
  secondaryColor: string;
  accentColor: string;
  borderColor: string;
}

export function SessionStatsCard({
  sessionsToday,
  totalFocusMinutes,
  currentStreak,
  bgColor,
  textColor,
  secondaryColor,
  accentColor,
  borderColor,
}: SessionStatsCardProps) {
  const focusTimeLabel = formatDuration(totalFocusMinutes * 60);

  return (
    <View style={[styles.card, { backgroundColor: bgColor, borderColor }]}>
      <Text style={[styles.title, { color: secondaryColor }]}>
        TODAY'S STATS
      </Text>
      <View style={styles.row}>
        <StatItem
          value={`${sessionsToday}`}
          label="Sessions"
          valueColor={accentColor}
          labelColor={secondaryColor}
        />
        <StatItem
          value={focusTimeLabel}
          label="Focus time"
          valueColor={textColor}
          labelColor={secondaryColor}
        />
        <StatItem
          value={`${currentStreak}`}
          label="Day streak"
          valueColor={accentColor}
          labelColor={secondaryColor}
        />
      </View>
    </View>
  );
}

function StatItem({
  value,
  label,
  valueColor,
  labelColor,
}: {
  value: string;
  label: string;
  valueColor: string;
  labelColor: string;
}) {
  return (
    <View style={styles.statItem}>
      <Text
        style={[styles.statValue, { color: valueColor }]}
        numberOfLines={1}
        adjustsFontSizeToFit
      >
        {value}
      </Text>
      <Text style={[styles.statLabel, { color: labelColor }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 20,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  title: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 2,
    marginBottom: 16,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 22,
    fontWeight: '700',
    fontVariant: ['tabular-nums'],
  },
  statLabel: {
    fontSize: 11,
    fontWeight: '500',
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
});
