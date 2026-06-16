import { z } from 'zod';
import { sanitizeText } from '../lib/sanitize';

const taskStatusEnum = z.enum(['todo', 'in_progress', 'done']);
const taskPriorityEnum = z.enum(['low', 'medium', 'high']);

export const createTaskSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be 200 characters or less')
    .transform(sanitizeText),
  description: z.string().max(5000, 'Description must be 5000 characters or less').optional()
    .transform((v) => v ? sanitizeText(v) : v),
  status: taskStatusEnum.optional(),
  priority: taskPriorityEnum.optional(),
  due_date: z.string().datetime({ message: 'Invalid ISO 8601 date' }).optional(),
});

export const updateTaskSchema = z
  .object({
    title: z.string().min(1).max(200).optional()
      .transform((v) => v ? sanitizeText(v) : v),
    description: z.string().max(5000).optional()
      .transform((v) => v ? sanitizeText(v) : v),
    status: taskStatusEnum.optional(),
    priority: taskPriorityEnum.optional(),
    due_date: z.string().datetime().optional(),
  })
  .refine((data) => Object.keys(data).length > 0, {
    message: 'At least one field must be provided for update',
  });

export const patchTaskSchema = z
  .object({
    title: z.preprocess(
      sanitizeText,
      z.string().min(1, 'Title must not be empty').max(200, 'Title must be 200 characters or less').optional(),
    ),
    description: z.string().max(5000, 'Description must be 5000 characters or less').optional()
      .transform((v) => v ? sanitizeText(v) : v),
    status: taskStatusEnum.optional(),
    priority: taskPriorityEnum.optional(),
    due_date: z.string().datetime({ message: 'Invalid ISO 8601 date' }).optional(),
  })
  .refine((data) => Object.keys(data).length > 0, {
    message: 'At least one field must be provided for update',
  });

export const taskIdSchema = z.object({
  id: z.string().uuid('Invalid task ID format'),
});

export const bulkDeleteSchema = z.object({
  ids: z
    .array(z.string().uuid('Invalid task ID format'))
    .min(1, 'At least one ID is required')
    .max(100, 'Cannot delete more than 100 tasks at once'),
});

const sortByEnum = z.enum(['created_at', 'due_date', 'priority', 'title']);
const orderEnum = z.enum(['asc', 'desc']);
const modeEnum = z.enum(['cursor', 'offset']);

export const paginationSchema = z.object({
  page: z
    .string()
    .optional()
    .transform((v) => (v ? parseInt(v, 10) : 1))
    .pipe(z.number().int().min(1)),
  limit: z
    .string()
    .optional()
    .transform((v) => (v ? parseInt(v, 10) : 25))
    .pipe(z.number().int().min(1).max(100)),
  sort_by: sortByEnum.optional().default('created_at'),
  order: orderEnum.optional().default('desc'),
  mode: modeEnum.optional().default('cursor'),
  status: taskStatusEnum.optional(),
  priority: taskPriorityEnum.optional(),
  cursor: z.string().optional(),
});

export type CreateTaskInput = z.infer<typeof createTaskSchema>;
export type UpdateTaskInput = z.infer<typeof updateTaskSchema>;
export type TaskIdInput = z.infer<typeof taskIdSchema>;
export type BulkDeleteInput = z.infer<typeof bulkDeleteSchema>;
export type PaginationInput = z.infer<typeof paginationSchema>;