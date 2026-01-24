/**
 * Date utility functions for MOSS.AO
 *
 * Backend stores all times in UTC without timezone suffix.
 * These utilities ensure proper conversion to user's local timezone.
 */

/**
 * Parse a UTC datetime string from the backend.
 * Backend returns ISO format without timezone (e.g., "2024-01-20T15:30:00")
 * This function treats such strings as UTC.
 */
export function parseUTCDate(dateString: string | null | undefined): Date | null {
  if (!dateString) return null;

  // If already has timezone info, parse directly
  if (dateString.endsWith('Z') || dateString.includes('+') || dateString.includes('-', 10)) {
    return new Date(dateString);
  }

  // Assume UTC for naive datetime strings from backend
  return new Date(dateString + 'Z');
}

/**
 * Convert app locale to browser locale.
 * 'ko' -> 'ko-KR', 'en' -> 'en-US'
 */
function toBrowserLocale(locale: string): string {
  if (locale === 'ko') return 'ko-KR';
  if (locale === 'en') return 'en-US';
  return locale;
}

/**
 * Format a UTC date string to local date and time.
 * e.g., "Jan 20, 2024, 11:30 PM" (English) or "2024년 1월 20일 오후 11:30" (Korean)
 */
export function formatLocalDateTime(
  dateString: string | null | undefined,
  locale: string = 'en'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleString(toBrowserLocale(locale), {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a UTC date string to local date only.
 * e.g., "Jan 20, 2024" (English) or "2024년 1월 20일" (Korean)
 */
export function formatLocalDate(
  dateString: string | null | undefined,
  locale: string = 'en'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleDateString(toBrowserLocale(locale), {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format a UTC date string to local time only.
 * e.g., "11:30 PM" (English) or "오후 11:30" (Korean)
 */
export function formatLocalTime(
  dateString: string | null | undefined,
  locale: string = 'en'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  return date.toLocaleTimeString(toBrowserLocale(locale), {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format a UTC date string to relative time.
 * e.g., "5 minutes ago", "2 hours ago", "3 days ago"
 */
export function formatRelativeTime(
  dateString: string | null | undefined,
  locale: string = 'en'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  // Use Intl.RelativeTimeFormat for localized relative time
  const rtf = new Intl.RelativeTimeFormat(toBrowserLocale(locale), { numeric: 'auto' });

  if (diffDays > 0) {
    return rtf.format(-diffDays, 'day');
  } else if (diffHours > 0) {
    return rtf.format(-diffHours, 'hour');
  } else if (diffMins > 0) {
    return rtf.format(-diffMins, 'minute');
  } else {
    return rtf.format(-diffSecs, 'second');
  }
}

/**
 * Format a UTC date string with both date and relative time.
 * e.g., "Jan 20, 2024 (2 hours ago)"
 */
export function formatDateWithRelative(
  dateString: string | null | undefined,
  locale: string = 'en'
): string {
  const date = parseUTCDate(dateString);
  if (!date) return 'N/A';

  const dateStr = formatLocalDate(dateString, locale);
  const relativeStr = formatRelativeTime(dateString, locale);

  return `${dateStr} (${relativeStr})`;
}
