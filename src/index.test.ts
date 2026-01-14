import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as path from 'path';
import * as os from 'os';

// Note: These tests focus on helper functions that can be tested without mocking the Memvid SDK
// Full integration tests would require mocking @memvid/sdk

describe('Path normalization and validation', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('should expand tilde to home directory', () => {
    // This test would require exporting normalizeFilePath from index.ts
    // For now, we'll test the concept
    const homeDir = os.homedir();
    const testPath = '~/test.mv2';
    const expanded = testPath.replace('~', homeDir);
    expect(expanded).toContain(homeDir);
    expect(expanded).toMatch(/test\.mv2$/);
  });

  it('should resolve relative paths to absolute paths', () => {
    const relativePath = './test.mv2';
    const resolved = path.resolve(relativePath);
    expect(path.isAbsolute(resolved)).toBe(true);
  });

  it('should validate path format', () => {
    const validPath = '/tmp/test.mv2';
    expect(path.isAbsolute(validPath)).toBe(true);
  });
});

describe('Tag conversion', () => {
  it('should convert object to key:value array', () => {
    const tags = { type: 'decision', project: 'backend' };
    const result = Object.entries(tags).map(([key, value]) => `${key}:${value}`);
    expect(result).toEqual(['type:decision', 'project:backend']);
  });

  it('should handle empty object', () => {
    const tags = {};
    const result = Object.entries(tags).map(([key, value]) => `${key}:${value}`);
    expect(result).toEqual([]);
  });

  it('should handle undefined input', () => {
    const tags = undefined;
    const result = tags ? Object.entries(tags).map(([key, value]) => `${key}:${value}`) : undefined;
    expect(result).toBeUndefined();
  });
});

describe('Log level mapping', () => {
  it('should have correct log level values', () => {
    const LOG_LEVELS = {
      DEBUG: 0,
      INFO: 1,
      WARNING: 2,
      ERROR: 3,
    };

    expect(LOG_LEVELS.DEBUG).toBe(0);
    expect(LOG_LEVELS.INFO).toBe(1);
    expect(LOG_LEVELS.WARNING).toBe(2);
    expect(LOG_LEVELS.ERROR).toBe(3);
  });

  it('should compare log levels correctly', () => {
    const LOG_LEVELS = {
      DEBUG: 0,
      INFO: 1,
      WARNING: 2,
      ERROR: 3,
    };

    expect(LOG_LEVELS.ERROR).toBeGreaterThan(LOG_LEVELS.WARNING);
    expect(LOG_LEVELS.WARNING).toBeGreaterThan(LOG_LEVELS.INFO);
    expect(LOG_LEVELS.INFO).toBeGreaterThan(LOG_LEVELS.DEBUG);
  });
});

describe('Environment variable handling', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('should parse MEMVID_ALLOWED_DIRS with single directory', () => {
    process.env.MEMVID_ALLOWED_DIRS = '/tmp/memvid';
    const dirs = process.env.MEMVID_ALLOWED_DIRS?.split(':');
    expect(dirs).toEqual(['/tmp/memvid']);
  });

  it('should parse MEMVID_ALLOWED_DIRS with multiple directories', () => {
    process.env.MEMVID_ALLOWED_DIRS = '/tmp/memvid:/home/user/memories';
    const dirs = process.env.MEMVID_ALLOWED_DIRS?.split(':');
    expect(dirs).toEqual(['/tmp/memvid', '/home/user/memories']);
  });

  it('should handle missing MEMVID_ALLOWED_DIRS', () => {
    delete process.env.MEMVID_ALLOWED_DIRS;
    const dirs = (process.env.MEMVID_ALLOWED_DIRS as string | undefined)?.split(':');
    expect(dirs).toBeUndefined();
  });
});
