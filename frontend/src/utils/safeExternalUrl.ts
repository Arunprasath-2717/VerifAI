/** Only navigate to absolute public HTTP(S) URLs supplied by external evidence. */
export function safeExternalUrl(url?: string | null): string | undefined {
  if (!url || typeof url !== 'string') return undefined;
  try {
    const parsed = new URL(url);
    if (!['https:', 'http:'].includes(parsed.protocol)) return undefined;
    // Reject URLs with embedded credentials, which are deceptive as citations.
    if (parsed.username || parsed.password) return undefined;
    return parsed.href;
  } catch {
    return undefined;
  }
}
