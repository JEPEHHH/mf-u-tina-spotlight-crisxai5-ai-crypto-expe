// Offline validation for X post copy against the Spotlight @crisxai5 rules.

import {
  PLAY_CODE_PATTERN,
  SPONSOR_MENTION,
  SPONSOR_PROFILE_URL,
} from './post-config.ts';

export interface CopyCheckReport {
  readonly valid: boolean;
  readonly weightedLength: number;
  readonly hashtags: readonly string[];
  readonly playCode: string | null;
  readonly hasSponsorMention: boolean;
  readonly hasProfileUrl: boolean;
  readonly issues: readonly string[];
}

const URL_REGEX = /https?:\/\/\S+/gi;
const HASHTAG_REGEX = /#[A-Za-z][A-Za-z0-9_]*/g;
const X_TCO_URL_WEIGHT = 23;
const X_MAX_POST_LENGTH = 280;

export function measureXWeightedLength(text: string): number {
  const normalized = text.trim();
  let length = 0;
  let lastIndex = 0;

  for (const match of normalized.matchAll(URL_REGEX)) {
    const start = match.index ?? 0;
    length += start - lastIndex;
    length += X_TCO_URL_WEIGHT;
    lastIndex = start + match[0].length;
  }

  length += normalized.length - lastIndex;
  return length;
}

export function containsWholeWordMention(text: string, mention: string): boolean {
  const escaped = mention.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`(^|[^A-Za-z0-9_])${escaped}(?=$|[^A-Za-z0-9_])`, 'i');
  return pattern.test(text);
}

export function validatePostCopy(rawText: string): CopyCheckReport {
  const text = rawText.trim();
  const issues: string[] = [];

  const hasSponsorMention = containsWholeWordMention(text, SPONSOR_MENTION);
  if (!hasSponsorMention) {
    issues.push(`Post text must include ${SPONSOR_MENTION} as a whole word.`);
  }

  const hasProfileUrl = text.toLowerCase().includes(SPONSOR_PROFILE_URL.toLowerCase());
  if (!hasProfileUrl) {
    issues.push(`Post text should include ${SPONSOR_PROFILE_URL}.`);
  }

  const hashtags = text.match(HASHTAG_REGEX) ?? [];
  if (hashtags.length < 3 || hashtags.length > 5) {
    issues.push(
      `Post text should include 3 to 5 hashtags (found ${hashtags.length}).`,
    );
  }

  const playCodeMatch = text.match(PLAY_CODE_PATTERN);
  const playCode = playCodeMatch ? playCodeMatch[0].toLowerCase() : null;
  if (playCode === null) {
    issues.push('Post text must contain a makefun-<word>-<word>-<word> play code.');
  }

  const weightedLength = measureXWeightedLength(text);
  if (weightedLength > X_MAX_POST_LENGTH) {
    issues.push(
      `Post exceeds standard X limit (${weightedLength}/${X_MAX_POST_LENGTH} chars).`,
    );
  }

  return {
    valid: issues.length === 0,
    weightedLength,
    hashtags,
    playCode,
    hasSponsorMention,
    hasProfileUrl,
    issues,
  };
}
