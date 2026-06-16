import { Request, Response, NextFunction } from 'express';
import { ZodSchema, ZodError } from 'zod';
import { ApiError } from '../types/api';

type ValidationSource = 'body' | 'query' | 'params';

export function validate(schema: ZodSchema, source: ValidationSource = 'body') {
  return (req: Request, res: Response, next: NextFunction): void => {
    try {
      const parsed = schema.parse(req[source]);
      // Store parsed data — req.query is a getter in Express, so we use a custom key
      if (source === 'query') {
        (req as any).validatedQuery = parsed;
      } else {
        req[source] = parsed;
      }
      next();
    } catch (err) {
      if (err instanceof ZodError) {
        const errors: ApiError['errors'] = err.issues.map((e) => ({
          field: e.path.join('.'),
          message: e.message,
        }));
        res.status(400).json({ data: null, error: 'Validation failed', errors });
        return;
      }
      next(err);
    }
  };
}

export function validateParams(schema: ZodSchema) {
  return validate(schema, 'params');
}

export function validateQuery(schema: ZodSchema) {
  return validate(schema, 'query');
}

export function validateBody(schema: ZodSchema) {
  return validate(schema, 'body');
}
