/**
 * Sanitize free-text input before storage.
 *
 * Pipeline (order matters):
 *  1. Trim leading/trailing whitespace
 *  2. Strip HTML tags — remove anything matching `<...>` including
 *     `<script>`, `<img onerror=...>`, self-closing `<br/>`, etc.
 *  3. HTML-escape the five critical entities:
 *     & → &amp;   (MUST be first to avoid double-escaping)
 *     < → &lt;
 *     > → &gt;
 *     " → &quot;
 *     ' → &#x27;
 *
 * Emoji and all other Unicode code points pass through unchanged
 * (regex operates on ASCII HTML syntax only).
 *
 * @returns sanitized string, or null/undefined if input was null/undefined.
 */
export function sanitizeText(input: string | null | undefined): string | null | undefined {
  if (input == null) return input;
  let s = input.trim();
  s = s.replace(/<[a-zA-Z/][^>]*>/g, '');  // strip HTML tags (preserve comparison ops)
  s = s.replace(/&/g, '&amp;');        // escape & first
  s = s.replace(/</g, '&lt;');
  s = s.replace(/>/g, '&gt;');
  s = s.replace(/"/g, '&quot;');
  s = s.replace(/'/g, '&#x27;');
  return s;
}
