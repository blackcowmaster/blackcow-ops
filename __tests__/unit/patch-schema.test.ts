import { patchTaskSchema } from '../../src/schemas/task.schema';

// Helper: wraps parse in try/catch and returns { success, data, errors }
function tryParse(input: Record<string, unknown>) {
  try {
    const data = patchTaskSchema.parse(input);
    return { success: true as const, data, errors: null };
  } catch (err: any) {
    return { success: false as const, data: null, errors: err.issues ?? err };
  }
}

describe('patchTaskSchema', () => {
  // ── Empty body rejection (refine) ─────────────────────
  describe('empty body rejection', () => {
    it('rejects empty object — refine: at least one field required', () => {
      const result = tryParse({});
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/at least one field/i);
      }
    });
  });

  // ── Title field (preprocessed with sanitizeText) ──────
  describe('title — preprocessed with sanitizeText', () => {
    it('accepts valid title', () => {
      const result = tryParse({ title: 'Valid Title' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.title).toBe('Valid Title');
    });

    it('trims whitespace from title', () => {
      const result = tryParse({ title: '  Trimmed  ' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.title).toBe('Trimmed');
    });

    it('rejects empty string title (after trim → empty)', () => {
      const result = tryParse({ title: '' });
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/must not be empty/i);
      }
    });

    it('rejects whitespace-only title (after sanitize → empty)', () => {
      const result = tryParse({ title: '   ' });
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/must not be empty/i);
      }
    });

    it('rejects title that collapses to empty after tag stripping', () => {
      const result = tryParse({ title: '<script></script>' });
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/must not be empty/i);
      }
    });

    it('strips HTML tags but keeps inner text before validation', () => {
      const result = tryParse({ title: '<b>Bold</b>' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.title).toBe('Bold');
    });

    it('rejects title exceeding 200 characters', () => {
      const long = 'a'.repeat(201);
      const result = tryParse({ title: long });
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/200/);
      }
    });

    it('accepts title of exactly 200 characters', () => {
      const result = tryParse({ title: 'a'.repeat(200) });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.title).toBe('a'.repeat(200));
    });

    it('title is optional — omitting is valid', () => {
      const result = tryParse({ description: 'only desc' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.title).toBeUndefined();
    });
  });

  // ── Description field (transform with sanitizeText) ───
  describe('description — transformed with sanitizeText', () => {
    it('accepts valid description', () => {
      const result = tryParse({ description: 'A valid description.' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBe('A valid description.');
    });

    it('strips HTML tags from description', () => {
      const result = tryParse({ description: '<script>evil()</script>' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBe('evil()');
    });

    it('trims whitespace from description', () => {
      const result = tryParse({ description: '  spaced  ' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBe('spaced');
    });

    it('escapes HTML entities in description', () => {
      const result = tryParse({ description: 'A & B < C > D' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBe('A &amp; B &lt; C &gt; D');
    });

    it('rejects description exceeding 5000 characters', () => {
      const long = 'x'.repeat(5001);
      const result = tryParse({ description: long });
      expect(result.success).toBe(false);
      if (result.errors) {
        const messages = result.errors.map((i: any) => i.message).join(' ');
        expect(messages).toMatch(/5000/);
      }
    });

    it('accepts description of exactly 5000 characters', () => {
      const result = tryParse({ description: 'x'.repeat(5000) });
      expect(result.success).toBe(true);
    });

    it('description is optional — omitting is valid', () => {
      const result = tryParse({ title: 'test' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBeUndefined();
    });
  });

  // ── Status enum ───────────────────────────────────────
  describe('status — enum validation', () => {
    const validStatuses = ['todo', 'in_progress', 'done'] as const;

    for (const status of validStatuses) {
      it(`accepts status "${status}"`, () => {
        const result = tryParse({ status });
        expect(result.success).toBe(true);
        if (result.success) expect(result.data.status).toBe(status);
      });
    }

    it('rejects invalid status', () => {
      const result = tryParse({ status: 'invalid' });
      expect(result.success).toBe(false);
    });

    it('rejects numeric status', () => {
      const result = tryParse({ status: 123 });
      expect(result.success).toBe(false);
    });

    it('status is optional — omitting is valid', () => {
      const result = tryParse({ title: 'test' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.status).toBeUndefined();
    });
  });

  // ── Priority enum ─────────────────────────────────────
  describe('priority — enum validation', () => {
    const validPriorities = ['low', 'medium', 'high'] as const;

    for (const priority of validPriorities) {
      it(`accepts priority "${priority}"`, () => {
        const result = tryParse({ priority });
        expect(result.success).toBe(true);
        if (result.success) expect(result.data.priority).toBe(priority);
      });
    }

    it('rejects invalid priority', () => {
      const result = tryParse({ priority: 'critical' });
      expect(result.success).toBe(false);
    });

    it('priority is optional — omitting is valid', () => {
      const result = tryParse({ title: 'test' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.priority).toBeUndefined();
    });
  });

  // ── due_date field ────────────────────────────────────
  describe('due_date — ISO 8601 datetime validation', () => {
    it('accepts valid ISO 8601 datetime', () => {
      const result = tryParse({ due_date: '2025-12-31T23:59:59.000Z' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.due_date).toBe('2025-12-31T23:59:59.000Z');
    });

    it('rejects invalid date string', () => {
      const result = tryParse({ due_date: 'not-a-date' });
      expect(result.success).toBe(false);
    });

    it('rejects date-only string (not ISO 8601 datetime)', () => {
      const result = tryParse({ due_date: '2025-01-01' });
      expect(result.success).toBe(false);
    });

    it('due_date is optional — omitting is valid', () => {
      const result = tryParse({ title: 'test' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.due_date).toBeUndefined();
    });
  });

  // ── Valid partial updates (1+ fields) ─────────────────
  describe('valid partial updates', () => {
    it('accepts title-only patch', () => {
      const result = tryParse({ title: 'New Title' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.title).toBe('New Title');
        expect(result.data.description).toBeUndefined();
        expect(result.data.status).toBeUndefined();
        expect(result.data.priority).toBeUndefined();
        expect(result.data.due_date).toBeUndefined();
      }
    });

    it('accepts description-only patch', () => {
      const result = tryParse({ description: 'New desc' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.description).toBe('New desc');
    });

    it('accepts status-only patch', () => {
      const result = tryParse({ status: 'done' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.status).toBe('done');
    });

    it('accepts priority-only patch', () => {
      const result = tryParse({ priority: 'high' });
      expect(result.success).toBe(true);
      if (result.success) expect(result.data.priority).toBe('high');
    });

    it('accepts due_date-only patch', () => {
      const result = tryParse({ due_date: '2026-06-15T12:00:00.000Z' });
      expect(result.success).toBe(true);
    });

    it('accepts multiple fields patch', () => {
      const result = tryParse({ title: 'Multi', status: 'in_progress', priority: 'high' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.title).toBe('Multi');
        expect(result.data.status).toBe('in_progress');
        expect(result.data.priority).toBe('high');
      }
    });

    it('accepts all fields patch', () => {
      const result = tryParse({
        title: 'All',
        description: 'Full update',
        status: 'done',
        priority: 'low',
        due_date: '2025-01-01T00:00:00.000Z',
      });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.title).toBe('All');
        expect(result.data.description).toBe('Full update');
        expect(result.data.status).toBe('done');
        expect(result.data.priority).toBe('low');
        expect(result.data.due_date).toBe('2025-01-01T00:00:00.000Z');
      }
    });
  });

  // ── Extra field filtering ──────────────────────────────
  describe('extra field handling', () => {
    it('strips unknown fields from output', () => {
      const result = tryParse({ title: 'Clean', extraField: 'should be stripped' });
      expect(result.success).toBe(true);
      if (result.success) {
        expect(result.data.title).toBe('Clean');
        expect((result.data as any).extraField).toBeUndefined();
      }
    });
  });
});
