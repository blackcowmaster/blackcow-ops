import { Request, Response, NextFunction } from 'express';
import crypto from 'crypto';
import { AppError } from '../errors/AppError';
import { ApiResponse } from '../types/api';

export const errorHandler = (
  err: Error,
  _req: Request,
  res: Response,
  _next: NextFunction,
): void => {
  if (err instanceof AppError) {
    const body: ApiResponse<null> = {
      data: null,
      error: err.message,
      meta: { correlationId: err.correlationId },
    };
    res.status(err.statusCode).json(body);
    return;
  }

  // For unknown errors, return generic message — never leak stack traces
  const correlationId = crypto.randomUUID();
  console.error(`[${correlationId}] Unexpected error: ${err.message}`);

  const body: ApiResponse<null> = {
    data: null,
    error: 'Internal server error',
    meta: { correlationId },
  };
  res.status(500).json(body);
};
