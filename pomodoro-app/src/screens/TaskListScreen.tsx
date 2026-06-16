// src/screens/TaskListScreen.tsx
// Task management screen — add, complete, delete tasks with AsyncStorage persistence.

import React from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTaskContext } from '../context/TaskContext';
import { useTheme } from '../context/ThemeContext';
import { TaskInput } from '../components/TaskInput';
import { TaskItem } from '../components/TaskItem';
import { EmptyState } from '../components/EmptyState';
import type { Task } from '../pomodoro/types';

export function TaskListScreen() {
  const { tasks, addTask, toggleTask, deleteTask } = useTaskContext();
  const { colors } = useTheme();

  const renderItem = ({ item }: { item: Task }) => (
    <TaskItem
      id={item.id}
      title={item.title}
      completed={item.completed}
      onToggle={toggleTask}
      onDelete={deleteTask}
      bgColor={colors.cardBg}
      textColor={colors.textPrimary}
      secondaryColor={colors.textSecondary}
      successColor={colors.success}
      borderColor={colors.borderPrimary}
    />
  );

  const renderEmpty = () => (
    <EmptyState
      message="No tasks yet"
      textColor={colors.textPrimary}
      secondaryColor={colors.textSecondary}
    />
  );

  const keyExtractor = (item: Task) => item.id;

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: colors.bgPrimary }]}
      edges={['top']}
    >
      <View style={styles.content}>
        <TaskInput
          onSubmit={addTask}
          bgColor={colors.bgSecondary}
          textColor={colors.textPrimary}
          secondaryColor={colors.textSecondary}
          accentColor={colors.accent}
          borderColor={colors.borderPrimary}
        />
        <FlatList
          data={tasks}
          renderItem={renderItem}
          keyExtractor={keyExtractor}
          ListEmptyComponent={renderEmpty}
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  listContent: {
    paddingBottom: 24,
    flexGrow: 1,
  },
});
