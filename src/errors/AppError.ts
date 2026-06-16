import crypto from 'crypto';

export class AppError extends Error {
  public readonly statusCode: number;
  public readonly code: string;
  public readonly correlationId: string;

  constructor(statusCode: number, code: string, message: string) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.correlationId = crypto.randomUUID();
    Object.setPrototypeOf(this, AppError.prototype);
    Error.captureStackTrace(this, this.constructor);
  }
}
