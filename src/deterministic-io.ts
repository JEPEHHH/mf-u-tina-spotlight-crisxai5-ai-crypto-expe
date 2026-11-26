// Deterministic, offline file I/O utilities for the program/v1 harness.

import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

export interface RuntimePaths {
  readonly botDir: string;
  readonly outputDir: string;
  readonly inputPostPath: string;
  readonly outputPostPath: string;
  readonly postCopyPath: string;
}

export interface CopyOutcome {
  readonly sourcePath: string;
  readonly destinationPath: string;
  readonly bytesWritten: number;
  readonly sha256: string;
  readonly parsedJson: unknown;
}

export function resolveRuntimePaths(env: NodeJS.ProcessEnv): RuntimePaths {
  const botDir = resolve(env.MAKEFUN_BOT_DIR ?? '/bot');
  const outputDir = resolve(env.MAKEFUN_OUTPUT_DIR ?? '/output');

  return {
    botDir,
    outputDir,
    inputPostPath: join(botDir, 'POST.json'),
    outputPostPath: join(outputDir, 'POST.json'),
    postCopyPath: join(botDir, 'post_copy.txt'),
  };
}

export function sha256Hex(buffer: Buffer): string {
  return createHash('sha256').update(buffer).digest('hex');
}

export function readAndCopyPostFile(paths: RuntimePaths): CopyOutcome {
  if (!existsSync(paths.inputPostPath)) {
    throw new Error(`Missing required file: ${paths.inputPostPath}`);
  }

  const rawBytes = readFileSync(paths.inputPostPath);
  let parsedJson: unknown;
  try {
    parsedJson = JSON.parse(rawBytes.toString('utf8'));
  } catch (err) {
    throw new Error(
      `Invalid JSON in ${paths.inputPostPath}: ${(err as Error).message}`,
    );
  }

  mkdirSync(dirname(paths.outputPostPath), { recursive: true });
  writeFileSync(paths.outputPostPath, rawBytes);

  return {
    sourcePath: paths.inputPostPath,
    destinationPath: paths.outputPostPath,
    bytesWritten: rawBytes.byteLength,
    sha256: sha256Hex(rawBytes),
    parsedJson,
  };
}
