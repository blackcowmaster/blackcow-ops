import { sanitizeText } from '../../src/lib/sanitize';

describe('sanitizeText', () => {
  // ── trim ──────────────────────────────────────────────
  describe('trim', () => {
    it('trims leading and trailing whitespace', () => {
      expect(sanitizeText('  hello  ')).toBe('hello');
    });

    it('trims newlines and tabs', () => {
      expect(sanitizeText('\n\ttest\n')).toBe('test');
    });

    it('preserves text with no surrounding whitespace', () => {
      expect(sanitizeText('no-trim')).toBe('no-trim');
    });
  });

  // ── stripTags ─────────────────────────────────────────
  describe('stripTags', () => {
    it('strips <b> tags', () => {
      expect(sanitizeText('<b>bold</b>')).toBe('bold');
    });

    it('strips <script> tags with content', () => {
      expect(sanitizeText('<script>alert(1)</script>')).toBe('alert(1)');
    });

    it('strips self-closing <img> with onerror', () => {
      expect(sanitizeText('<img src=x onerror=alert(1)>')).toBe('');
    });

    it('strips <br/> self-closing tag', () => {
      expect(sanitizeText('text <br/> more')).toBe('text  more');
    });

    it('strips <a> tags', () => {
      expect(sanitizeText("<a href='x'>link</a>")).toBe('link');
    });
  });

  // ── htmlEscape ────────────────────────────────────────
  describe('htmlEscape', () => {
    it('escapes & to &amp;', () => {
      expect(sanitizeText('A & B')).toBe('A &amp; B');
    });

    it('escapes < and >', () => {
      expect(sanitizeText('a < b > c')).toBe('a &lt; b &gt; c');
    });

    it('escapes double quotes', () => {
      expect(sanitizeText('say "hello"')).toBe('say &quot;hello&quot;');
    });

    it('escapes single quotes', () => {
      const result = sanitizeText("it's");
      // Depending on whether ' is before or after the word
      expect(result).toMatch(/&#x27;/);
      expect(result).toContain('it');
      expect(result).toContain('s');
    });
  });

  // ── emoji preservation ────────────────────────────────
  describe('emoji', () => {
    it('preserves emoji in text', () => {
      expect(sanitizeText('Hello 🎉 world 🌍')).toBe('Hello 🎉 world 🌍');
    });

    it('preserves multiple emoji only', () => {
      expect(sanitizeText('🎉🌟💯')).toBe('🎉🌟💯');
    });
  });

  // ── CJK / Unicode ─────────────────────────────────────
  describe('unicode', () => {
    it('preserves Japanese characters', () => {
      expect(sanitizeText('日本語テスト')).toBe('日本語テスト');
    });
  });

  // ── combined scenarios ────────────────────────────────
  describe('combined', () => {
    it('trims, strips tags, and escapes in one pass', () => {
      const result = sanitizeText("  <script>alert('xss')</script> 🎉  ");
      expect(result).toContain('alert');
      expect(result).toContain('&#x27;xss&#x27;');
      expect(result).toContain('🎉');
      // Order: trim → stripTags → htmlEscape
      // Input: "  <script>alert('xss')</script> 🎉  "
      // After trim: "<script>alert('xss')</script> 🎉"
      // After stripTags: "alert('xss') 🎉"
      // After htmlEscape: "alert(&#x27;xss&#x27;) 🎉"
      expect(result).toBe("alert(&#x27;xss&#x27;) 🎉");
    });

    it('strips tags then escapes remaining entities', () => {
      expect(sanitizeText('<b>Hello & Welcome</b>')).toBe('Hello &amp; Welcome');
    });
  });

  // ── edge cases ────────────────────────────────────────
  describe('edge cases', () => {
    it('returns null for null input', () => {
      expect(sanitizeText(null)).toBeNull();
    });

    it('returns undefined for undefined input', () => {
      expect(sanitizeText(undefined)).toBeUndefined();
    });

    it('returns empty string for empty string input', () => {
      expect(sanitizeText('')).toBe('');
    });

    it('returns plain text unchanged', () => {
      expect(sanitizeText('Plain text')).toBe('Plain text');
    });

    it('re-escapes already-escaped data (intentional)', () => {
      // Double-escaping is intentional: data should only be sanitized once at write time.
      // If already-escaped data enters, it gets re-escaped → consumer must not double-sanitize.
      expect(sanitizeText('&amp;')).toBe('&amp;amp;');
    });
  });
});
