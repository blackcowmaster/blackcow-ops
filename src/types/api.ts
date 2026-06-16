export interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  meta?: ApiMeta;
}

export interface ApiMeta {
  page?: number;
  limit?: number;
  total?: number;
  hasMore?: boolean;
  cursor?: string;
  correlationId?: string;
}

export interface PaginatedQuery {
  page: number;
  limit: number;
  sort_by: 'created_at' | 'due_date' | 'priority' | 'title';
  order: 'asc' | 'desc';
  status?: string;
  priority?: string;
  cursor?: string;
  mode: 'cursor' | 'offset';
}

export interface ApiError {
  errors: Array<{ field: string; message: string }>;
}
