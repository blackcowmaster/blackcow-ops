import { Response } from 'express';
import { ApiResponse, ApiMeta } from '../types/api';
import { Task, TaskResponse } from '../types/task';

export function taskToResponse(task: Task): TaskResponse {
  return {
    id: task.id,
    title: task.title,
    description: task.description,
    status: task.status,
    priority: task.priority,
    due_date: task.due_date,
    created_at: task.created_at,
    updated_at: task.updated_at,
  };
}

export function success<T>(res: Response, data: T, statusCode = 200): void {
  const body: ApiResponse<T> = { data, error: null };
  res.status(statusCode).json(body);
}

export function created<T>(res: Response, data: T): void {
  const body: ApiResponse<T> = { data, error: null };
  res.status(201).json(body);
}

export function noContent(res: Response): void {
  res.status(204).send();
}

export function paginated<T>(
  res: Response,
  data: T[],
  meta: {
    page: number;
    limit: number;
    total: number;
    hasMore: boolean;
    cursor?: string;
  },
): void {
  const metaPayload: ApiMeta = {
    page: meta.page,
    limit: meta.limit,
    total: meta.total,
    hasMore: meta.hasMore,
  };
  // Only include cursor in cursor mode
  if (meta.cursor) {
    metaPayload.cursor = meta.cursor;
  }

  const body: ApiResponse<T[]> = {
    data,
    error: null,
    meta: metaPayload,
  };
  res.status(200).json(body);
}
