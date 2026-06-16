import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { AppError } from '../errors/AppError';
import { JwtPayload } from '../types/auth';

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) {
  throw new Error('JWT_SECRET environment variable is required');
}
const ALLOWED_ALGORITHMS: jwt.Algorithm[] = ['HS256'];

export function auth(required = true) {
  return (req: Request, _res: Response, next: NextFunction): void => {
    const authHeader = req.headers.authorization;

    if (!authHeader) {
      if (!required) {
        return next();
      }
      return next(new AppError(401, 'UNAUTHORIZED', 'Missing authorization header'));
    }

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return next(new AppError(401, 'UNAUTHORIZED', 'Authorization header must be: Bearer <token>'));
    }

    const token = parts[1];

    try {
      const decoded = jwt.verify(token, JWT_SECRET, {
        algorithms: ALLOWED_ALGORITHMS,
      }) as JwtPayload;

      if (!decoded.sub) {
        return next(new AppError(401, 'UNAUTHORIZED', 'Token missing sub claim'));
      }

      req.user = decoded;
      next();
    } catch (err) {
      if (err instanceof AppError) {
        return next(err);
      }
      if (err instanceof jwt.TokenExpiredError) {
        return next(new AppError(401, 'TOKEN_EXPIRED', 'Token has expired'));
      }
      if (err instanceof jwt.JsonWebTokenError) {
        return next(new AppError(401, 'INVALID_TOKEN', 'Invalid token'));
      }
      if (err instanceof jwt.NotBeforeError) {
        return next(new AppError(401, 'TOKEN_NOT_ACTIVE', 'Token not yet active'));
      }
      return next(new AppError(401, 'UNAUTHORIZED', 'Authentication failed'));
    }
  };
}
