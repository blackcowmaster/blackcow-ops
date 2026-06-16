import { tasksRepository } from '../repositories/tasks.repository';
import { AppError } from '../errors/AppError';
import { Task, CreateTaskDto, UpdateTaskDto, BulkDeleteItemResult } from '../types/task';
import { PaginatedQuery } from '../types/api';

export class TasksService {
  async getAll(userId: string, pq: PaginatedQuery) {
    return tasksRepository.findAll(userId, pq);
  }

  async getById(id: string, userId: string): Promise<Task> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) {
      throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    }
    return task;
  }

  async create(dto: CreateTaskDto, userId: string): Promise<Task> {
    return tasksRepository.create(dto, userId);
  }

  async update(id: string, userId: string, dto: UpdateTaskDto): Promise<Task> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) {
      throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    }
    // Ownership check
    if (task.user_id !== userId) {
      // Defense-in-depth: repository findById already filters by user_id in SQL,
      // so this branch is normally unreachable. Kept as a safety net.
      throw new AppError(403, 'FORBIDDEN', 'You do not have permission to update this task');
    }

    const updated = await tasksRepository.update(id, userId, dto);
    if (!updated) {
      throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found after update`);
    }
    return updated;
  }

  async remove(id: string, userId: string): Promise<Task> {
    const task = await tasksRepository.findById(id, userId);
    if (!task) {
      throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    }
    if (task.user_id !== userId) {
      // Defense-in-depth: repository findById already filters by user_id in SQL.
      throw new AppError(403, 'FORBIDDEN', 'You do not have permission to delete this task');
    }

    const deleted = await tasksRepository.remove(id, userId);
    if (!deleted) {
      throw new AppError(404, 'NOT_FOUND', `Task with id ${id} not found`);
    }
    return deleted;
  }

  async bulkRemove(ids: string[], userId: string): Promise<BulkDeleteItemResult[]> {
    const results: BulkDeleteItemResult[] = [];

    for (const id of ids) {
      try {
        const task = await tasksRepository.findById(id, userId);
        if (!task) {
          results.push({ id, status: 'not_found', error: `Task with id ${id} not found` });
          continue;
        }
        if (task.user_id !== userId) {
          results.push({ id, status: 'forbidden', error: 'You do not have permission to delete this task' });
          continue;
        }

        await tasksRepository.remove(id, userId);
        results.push({ id, status: 'deleted' });
      } catch (err) {
        // Catch unexpected errors (e.g. DB failure) — treat as not_found to avoid leaking internals
        results.push({
          id,
          status: 'not_found',
          error: err instanceof Error ? err.message : 'Unexpected error during deletion',
        });
      }
    }

    return results;
  }
}

export const tasksService = new TasksService();