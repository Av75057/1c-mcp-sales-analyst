import { describe, it, expect, vi } from 'vitest';
import { cn, formatCurrency, formatNumber, formatDate, debounce } from '../../src/shared/lib/utils';

describe('cn', () => {
  it('merges classes', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });
  it('handles conditional', () => {
    expect(cn('base', false && 'hidden', 'visible')).toBe('base visible');
  });
  it('handles tailwind merge', () => {
    expect(cn('px-4', 'px-2')).toBe('px-2');
  });
  it('handles undefined', () => {
    expect(cn('a', undefined, 'b')).toBe('a b');
  });
});

describe('formatCurrency', () => {
  it('formats rubles', () => {
    const result = formatCurrency(1250000);
    expect(result).toContain('1');
    expect(result).toContain('₽');
  });
  it('handles zero', () => {
    expect(formatCurrency(0)).toContain('0');
  });
  it('handles negative', () => {
    expect(formatCurrency(-500)).toContain('500');
  });
});

describe('formatNumber', () => {
  it('formats with separators', () => {
    const r = formatNumber(1234567);
    expect(r.length).toBeGreaterThan(7);
  });
  it('handles zero', () => {
    expect(formatNumber(0)).toBe('0');
  });
});

describe('formatDate', () => {
  it('formats ISO date', () => {
    const r = formatDate('2026-07-04T10:00:00');
    expect(r).toBeTruthy();
    expect(typeof r).toBe('string');
  });
  it('handles empty string', () => {
    const r = formatDate('');
    expect(r).toBe('Invalid Date');
  });
});

describe('debounce', () => {
  it('creates a debounced function', () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 100);
    debounced();
    debounced();
    debounced();
    expect(fn).not.toHaveBeenCalled();
  });

  it('calls after delay', async () => {
    const fn = vi.fn();
    const debounced = debounce(fn, 50);
    debounced();
    await new Promise(r => setTimeout(r, 100));
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
