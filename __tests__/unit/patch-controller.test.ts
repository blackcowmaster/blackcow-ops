import { Request, Response } from 'express';
import { patch } from '../../src/controllers/tasks.controller';
import { tasksService } from '../../src/services/tasks.service';
import { Task, UpdateTaskDto } from '../../src/types/task';

// ── Module-level mocks ───────────────────────────────────
// jest.mock is hoisted above imports, so these replace the modules
// before controller.ts loads them.

jest.mock('../../src/services/tasks.service', () => ({
  tasksService: {
    update: jest.fn(),
  },
}));

// Spy on response helpers. We keep real taskToResponse but mock success
// to assert the controller calls it.
jest.mock('../../src/lib/response', () => {
  const actual = jest.requireActual('../../src/lib/response');
  return {
    ...actual,
    success: jest.fn(),
  };
});

const mockedUpdate = jest.mocked(tasksService.update);

// ── Fixtures ──────────────────────────────────────────────

const VALID_UUID = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11';
const USER_ID = 'user-abc-123';
const next = jest.fn();

function mockTask(overrides: Partial<Task> = {}): Task {
  return {
    id: VALID_UUID,
    user_id: USER_ID,
    title: 'Test Task',
    description: 'Description',
    status: 'todo',
    priority: 'medium',
    due_date: null,
    created_at: '2025-01-01T00:00:00.000Z',
    updated_at: '2025-01-01T00:00:00.000Z',
    deleted_at: null,
    ...overrides,
  };
}

function mockReq(overrides: Partial<Request> = {}): Request {
  const req = {
    params: { id: VALID_UUID },
    body: {},
    user: { sub: USER_ID },
    ...overrides,
  };
  return req as unknown as Request;
}

function mockRes(): Response {
  const res: Partial<Response> = {};
  res.status = jest.fn().mockReturnValue(res);
  res.json = jest.fn().mockReturnValue(res);
  return res as Response;
}

// ── Tests ─────────────────────────────────────────────────

describe('patch controller', () => {
  let req: Request;
  let res: Response;

  beforeEach(() => {
    jest.clearAllMocks();
    req = mockReq();
    res = mockRes();
  });

  // ── Parameter extraction ─────────────────────────────
  describe('parameter extraction', () => {
    it('extracts id from req.params.id and passes it as first arg to service', async () => {
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, expect.any(String), expect.anything());
    });

    it('extracts userId from req.user.sub and passes it as second arg to service', async () => {
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(expect.any(String), USER_ID, expect.anything());
    });

    it('passes req.body as the third argument (dto) to service', async () => {
      const dto: UpdateTaskDto = { title: 'Patched Title' };
      req.body = dto;
      mockedUpdate.mockResolvedValue(mockTask({ title: 'Patched Title' }));
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(expect.any(String), expect.any(String), dto);
    });

    it('casts req.params.id and req.body explicitly via type assertions', async () => {
      // The controller does: const id = req.params.id as string;
      // and const dto = req.body as UpdateTaskDto;
      // Verify this doesn't crash for various input shapes
      req.params = { id: 'any-string-value' };
      req.body = { status: 'done' };
      mockedUpdate.mockResolvedValue(mockTask({ status: 'done' }));
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith('any-string-value', USER_ID, { status: 'done' });
    });
  });

  // ── Service delegation ───────────────────────────────
  describe('service delegation', () => {
    it('calls tasksService.update exactly once', async () => {
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledTimes(1);
    });

    it('passes a partial body with a single field through to service', async () => {
      req.body = { description: 'only desc' };
      mockedUpdate.mockResolvedValue(mockTask({ description: 'only desc' }));
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, USER_ID, { description: 'only desc' });
    });

    it('passes a multi-field body through to service', async () => {
      req.body = { title: 'New', status: 'in_progress', priority: 'high' };
      mockedUpdate.mockResolvedValue(mockTask({ title: 'New', status: 'in_progress', priority: 'high' }));
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, USER_ID, req.body);
    });

    it('passes errors to next() when tasksService.update rejects', async () => {
      const error = new Error('Service error');
      mockedUpdate.mockRejectedValue(error);

      const localNext = jest.fn();
      patch(req, res, localNext);

      // asyncHandler's .catch(next) runs as a microtask; flush to see the call
      await new Promise((resolve) => setImmediate(resolve));

      expect(mockedUpdate).toHaveBeenCalledTimes(1);
      expect(localNext).toHaveBeenCalledWith(error);
    });

    it('passes 404 errors to next() when service throws not-found', async () => {
      const notFoundError = new Error('Task not found');
      (notFoundError as any).statusCode = 404;
      mockedUpdate.mockRejectedValue(notFoundError);

      const localNext = jest.fn();
      patch(req, res, localNext);

      await new Promise((resolve) => setImmediate(resolve));

      expect(localNext).toHaveBeenCalledWith(notFoundError);
    });

    it('passes 403 errors to next() when service throws forbidden', async () => {
      const forbiddenError = new Error('Forbidden');
      (forbiddenError as any).statusCode = 403;
      mockedUpdate.mockRejectedValue(forbiddenError);

      const localNext = jest.fn();
      patch(req, res, localNext);

      await new Promise((resolve) => setImmediate(resolve));

      expect(localNext).toHaveBeenCalledWith(forbiddenError);
    });
  });

  // ── Response handling ─────────────────────────────────
  describe('response handling', () => {
    it('wraps task via taskToResponse and sends with success()', async () => {
      const task = mockTask({ title: 'Response Check' });
      mockedUpdate.mockResolvedValue(task);

      // Dynamically import the real taskToResponse for assertion
      const { taskToResponse } = await import('../../src/lib/response');
      const { success: mockedSuccess } = await import('../../src/lib/response');

      await patch(req, res, next);

      expect(mockedSuccess).toHaveBeenCalledWith(res, taskToResponse(task));
    });

    it('success() receives the Express response object as first arg', async () => {
      mockedUpdate.mockResolvedValue(mockTask());
      const { success: mockedSuccess } = await import('../../src/lib/response');

      await patch(req, res, next);

      expect(mockedSuccess).toHaveBeenCalledWith(res, expect.anything());
    });
  });

  // ── Edge cases ───────────────────────────────────────
  describe('edge cases', () => {
    it('handles undefined req.body (casts to undefined)', async () => {
      req.body = undefined as any;
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, USER_ID, undefined);
    });

    it('handles null req.body (casts to null)', async () => {
      req.body = null as any;
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, USER_ID, null);
    });

    it('handles empty body {} cast as UpdateTaskDto (schema-level refine catches it, not controller)', async () => {
      // Controller does not validate — it just passes through.
      // The empty-body rejection is a schema concern, tested in patch-schema.test.ts.
      req.body = {};
      mockedUpdate.mockResolvedValue(mockTask());
      await patch(req, res, next);
      expect(mockedUpdate).toHaveBeenCalledWith(VALID_UUID, USER_ID, {});
    });
  });
});
