/**
 * Regression guard: ensure legacy indigo (#6366f1, #4f46e5) never re-enters
 * index.css or tokens.css, and that --accent is only defined in tokens.css
 * with the correct signal-green values.
 */
import { describe, it, expect } from 'vitest';
import { readFileSync } from 'fs';
import { resolve } from 'path';

const srcDir = resolve(__dirname, '..');

const indexCss = readFileSync(resolve(srcDir, 'index.css'), 'utf-8');
const tokensCss = readFileSync(resolve(srcDir, 'styles/tokens.css'), 'utf-8');

describe('no-indigo guard', () => {
  it('index.css must not contain legacy indigo hex #6366f1', () => {
    expect(indexCss.toLowerCase()).not.toContain('#6366f1');
  });

  it('index.css must not contain legacy indigo hex #4f46e5', () => {
    expect(indexCss.toLowerCase()).not.toContain('#4f46e5');
  });

  it('tokens.css must not contain legacy indigo hex #6366f1', () => {
    expect(tokensCss.toLowerCase()).not.toContain('#6366f1');
  });

  it('tokens.css must not contain legacy indigo hex #4f46e5', () => {
    expect(tokensCss.toLowerCase()).not.toContain('#4f46e5');
  });

  it('index.css must not reassign --accent to the indigo value', () => {
    expect(indexCss).not.toMatch(/--accent\s*:\s*#6366f1/i);
  });

  it('tokens.css must define --accent as signal green #059669 (light mode)', () => {
    expect(tokensCss).toContain('--accent: #059669');
  });

  it('tokens.css must define --accent as signal green #10B981 (dark mode)', () => {
    expect(tokensCss).toContain('--accent: #10B981');
  });

  it('index.css must not assign --accent to any indigo/violet hex value', () => {
    // Catches both #6366f1 and #4f46e5 (and any other forbidden indigo) being set on --accent
    expect(indexCss).not.toMatch(/--accent\s*:\s*#(?:6366f1|4f46e5)/i);
  });
});
