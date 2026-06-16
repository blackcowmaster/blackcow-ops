// src/context/TaskContext.tsx
// React Context provider for task CRUD with AsyncStorage persistence.

import React, {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
} from 'react';
import type { Task, TaskAction } from '../pomodoro/types';
import { loadTasks, saveTasks } from '../lib/storage';

// ── Reducer ──

function taskReducer(state: Task[], action: TaskAction): Task[] {
  switch (action.type) {
    case 'TASK_ADD':
      return [
        ...state,
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
          title: action.payload.title,
          completed: false,
          createdAt: new Date().toISOString(),
        },
      ];
    case 'TASK_TOGGLE':
      return state.map((t) =>
        t.id === action.payload.id ? { ...t, completed: !t.completed } : t,
      );
    case 'TASK_DELETE':
      return state.filter((t) => t.id !== action.payload.id);
    case 'TASKS_HYDRATE':
      return action.payload.tasks;
    default:
      return state;
  }
}

// ── Context ──

interface TaskContextValue {
  tasks: Task[];
  pendingCount: number;
  addTask: (title: string) => void;
  toggleTask: (id: string) => void;
  deleteTask: (id: string) => void;
}

const TaskContext = createContext<TaskContextValue | undefined>(undefined);

export function TaskProvider({ children }: { children: React.ReactNode }) {
  const [tasks, dispatch] = useReducer(taskReducer, []);

  // Hydrate on mount
  useEffect(() => {
    loadTasks().then((loaded) => {
      if (loaded.length > 0) {
        dispatch({ type: 'TASKS_HYDRATE', payload: { tasks: loaded } });
      }
    });
  }, []);

  // Persist on change
  useEffect(() => {
    saveTasks(tasks);
  }, [tasks]);

  const addTask = useCallback(
    (title: string) => {
      const trimmed = title.trim();
      if (trimmed.length === 0) return;
      dispatch({ type: 'TASK_ADD', payload: { title: trimmed } });
    },
    [],
  );

  const toggleTask = useCallback((id: string) => {
    dispatch({ type: 'TASK_TOGGLE', payload: { id } });
  }, []);

  const deleteTask = useCallback((id: string) => {
    dispatch({ type: 'TASK_DELETE', payload: { id } });
  }, []);

  const pendingCount = tasks.filter((t) => !t.completed).length;

  return (
    <TaskContext.Provider
      value={{ tasks, pendingCount, addTask, toggleTask, deleteTask }}
    >
      {children}
    </TaskContext.Provider>
  );
}

export function useTaskContext(): TaskContextValue {
  const ctx = useContext(TaskContext);
  if (!ctx) {
    throw new Error('useTaskContext must be used within a TaskProvider');
  }
  return ctx;
}
