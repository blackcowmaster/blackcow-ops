// src/components/TaskItem.tsx
// Individual task row: checkbox + title + delete button.

import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

interface TaskItemProps {
  id: string;
  title: string;
  completed: boolean;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  bgColor: string;
  textColor: string;
  secondaryColor: string;
  successColor: string;
  borderColor: string;
}

export function TaskItem({
  id,
  title,
  completed,
  onToggle,
  onDelete,
  bgColor,
  textColor,
  secondaryColor,
  successColor,
  borderColor,
}: TaskItemProps) {
  return (
    <View style={[styles.container, { backgroundColor: bgColor, borderColor }]}>
      {/* Checkbox */}
      <TouchableOpacity
        onPress={() => onToggle(id)}
        style={[
          styles.checkbox,
          {
            borderColor: completed ? successColor : borderColor,
            backgroundColor: completed ? successColor : 'transparent',
          },
        ]}
        accessibilityLabel={completed ? 'Mark incomplete' : 'Mark complete'}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: completed }}
      >
        {completed && <Text style={styles.checkmark}>{'\u2713'}</Text>}
      </TouchableOpacity>

      {/* Title */}
      <Text
        style={[
          styles.title,
          {
            color: completed ? secondaryColor : textColor,
            textDecorationLine: completed ? 'line-through' : 'none',
          },
        ]}
        numberOfLines={2}
      >
        {title}
      </Text>

      {/* Delete */}
      <TouchableOpacity
        onPress={() => onDelete(id)}
        style={styles.deleteButton}
        accessibilityLabel="Delete task"
        accessibilityRole="button"
      >
        <Text style={[styles.deleteIcon, { color: secondaryColor }]}>
          {'\u2715'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 16,
    marginVertical: 4,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    gap: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkmark: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  title: {
    flex: 1,
    fontSize: 16,
    lineHeight: 22,
  },
  deleteButton: {
    padding: 4,
  },
  deleteIcon: {
    fontSize: 16,
    fontWeight: '600',
  },
});
