// X post configuration, URL parsing, and validation helpers for the
// Spotlight @crisxai5 make.fun bounty (Node 22, standard library only).

export interface PostEntry {
  readonly url: string;
}

export interface ParsedXPost {
  readonly rawUrl: string;
  readonly host: string;
  readonly handle: string | null;
  readonly statusId: string;
  readonly canonicalUrl: string;
}

export interface PostValidationResult {
  readonly ok: boolean;
  readonly isPlaceholder: boolean;
  readonly parsed: ParsedXPost | null;
  readonly errors: readonly string[];
}

export const COMPETITION_SLUG =
  'u-tina-spotlight-crisxai5-ai-crypto-expert-on-x-7c1ed9ad';

export const SPONSOR_MENTION = '@crisxai5';
export const SPONSOR_PROFILE_URL = 'https://x.com/crisxai5';
export const PLAY_CODE_PATTERN = /\bmakefun-[a-z]+-[a-z]+-[a-z]+\b/i;

const ALLOWED_X_HOSTS = new Set([
  'x.com',
  'www.x.com',
  'mobile.x.com',
  'twitter.com',
  'www.twitter.com',
  'mobile.twitter.com',
]);

const PLACEHOLDER_MARKERS = ['<handle>', '<id>', 'placeholder', 'example'];

export function isPlaceholderUrl(rawUrl: string): boolean {
  const lower = rawUrl.trim().toLowerCase();
  return PLACEHOLDER_MARKERS.some((marker) => lower.includes(marker));
}

export function parseXPostUrl(rawUrl: string): ParsedXPost | null {
  const trimmed = rawUrl.trim();
  let parsedUrl: URL;
  try {
    parsedUrl = new URL(trimmed);
  } catch {
    return null;
  }

  if (parsedUrl.protocol !== 'https:' && parsedUrl.protocol !== 'http:') {
    return null;
  }

  const host = parsedUrl.hostname.toLowerCase();
  if (!ALLOWED_X_HOSTS.has(host)) {
    return null;
  }

  const segments = parsedUrl.pathname.split('/').filter((s) => s.length > 0);

  // Format 1: /<handle>/status/<digits>
  if (segments.length >= 3 && segments[1].toLowerCase() === 'status') {
    const handle = segments[0];
    const statusId = segments[2];
    if (/^[A-Za-z0-9_]{1,15}$/.test(handle) && /^\d{5,25}$/.test(statusId)) {
      return {
        rawUrl: trimmed,
        host,
        handle,
        statusId,
        canonicalUrl: `https://x.com/${handle}/status/${statusId}`,
      };
    }
  }

  // Format 2: /i/web/status/<digits>
  if (
    segments.length >= 4 &&
    segments[0].toLowerCase() === 'i' &&
    segments[1].toLowerCase() === 'web' &&
    segments[2].toLowerCase() === 'status'
  ) {
    const statusId = segments[3];
    if (/^\d{5,25}$/.test(statusId)) {
      return {
        rawUrl: trimmed,
        host,
        handle: null,
        statusId,
        canonicalUrl: `https://x.com/i/web/status/${statusId}`,
      };
    }
  }

  return null;
}

export function validatePostEntry(value: unknown): PostValidationResult {
  const errors: string[] = [];

  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return {
      ok: false,
      isPlaceholder: false,
      parsed: null,
      errors: ['POST.json must contain a top-level JSON object.'],
    };
  }

  const record = value as Record<string, unknown>;
  if (typeof record.url !== 'string' || record.url.trim().length === 0) {
    return {
      ok: false,
      isPlaceholder: false,
      parsed: null,
      errors: ['POST.json must include a non-empty string field "url".'],
    };
  }

  const url = record.url.trim();
  const placeholder = isPlaceholderUrl(url);
  const parsed = parseXPostUrl(url);

  if (placeholder) {
    errors.push(
      'POST.json still contains a placeholder URL; publish on X and replace it before final submission.',
    );
  } else if (parsed === null) {
    errors.push(
      'POST.json "url" must match https://x.com/<handle>/status/<digits> or twitter.com equivalent.',
    );
  }

  return {
    ok: errors.length === 0,
    isPlaceholder: placeholder,
    parsed,
    errors,
  };
}
