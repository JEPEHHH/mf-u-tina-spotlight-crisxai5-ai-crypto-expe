#!/usr/bin/env node
// Offline deterministic verifier for the Spotlight @crisxai5 entry repository.
// Confirms two-run byte-for-byte determinism of main.ts, LICENSE compliance,
// post_copy.txt rules compliance, and rendered media asset integrity.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, rmSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';

const REPO_ROOT = resolve(import.meta.dirname, '..');

function assert(condition, message) {
  if (!condition) {
    throw new Error(`Verification failed: ${message}`);
  }
}

function sha256(buf) {
  return createHash('sha256').update(buf).digest('hex');
}

function verifyLicense() {
  const licensePath = join(REPO_ROOT, 'LICENSE');
  assert(existsSync(licensePath), 'Root LICENSE file is missing');
  const text = readFileSync(licensePath, 'utf8');
  assert(text.includes('SPDX-License-Identifier: MIT'), 'LICENSE missing SPDX MIT header');
  assert(text.includes('Copyright (c) 2026 jepehhh'), 'LICENSE missing 2026 jepehhh copyright');
  assert(
    text.includes('Permission is hereby granted, free of charge'),
    'LICENSE missing full MIT text',
  );
  return 'LICENSE: MIT (2026 jepehhh) OK';
}

function verifyDeterminism() {
  const tmpBase = join(REPO_ROOT, '.tmp-verify-determinism');
  const outA = join(tmpBase, 'run-a');
  const outB = join(tmpBase, 'run-b');

  rmSync(tmpBase, { recursive: true, force: true });
  mkdirSync(outA, { recursive: true });
  mkdirSync(outB, { recursive: true });

  try {
    const runOnce = (outputDir) =>
      execFileSync(process.execPath, [join(REPO_ROOT, 'main.ts')], {
        cwd: REPO_ROOT,
        env: {
          ...process.env,
          MAKEFUN_BOT_DIR: REPO_ROOT,
          MAKEFUN_OUTPUT_DIR: outputDir,
        },
        encoding: 'utf8',
      });

    const stdoutA = runOnce(outA);
    const stdoutB = runOnce(outB);
    assert(stdoutA === '', `Expected silent stdout on run A, got: ${stdoutA}`);
    assert(stdoutB === '', `Expected silent stdout on run B, got: ${stdoutB}`);

    const srcBytes = readFileSync(join(REPO_ROOT, 'POST.json'));
    const bytesA = readFileSync(join(outA, 'POST.json'));
    const bytesB = readFileSync(join(outB, 'POST.json'));

    assert(bytesA.equals(srcBytes), 'Run A output does not match POST.json byte-for-byte');
    assert(bytesB.equals(srcBytes), 'Run B output does not match POST.json byte-for-byte');
    assert(bytesA.equals(bytesB), 'Run A and Run B outputs differ');

    const validateOut = execFileSync(
      process.execPath,
      [join(REPO_ROOT, 'main.ts'), '--validate'],
      {
        cwd: REPO_ROOT,
        env: {
          ...process.env,
          MAKEFUN_BOT_DIR: REPO_ROOT,
          MAKEFUN_OUTPUT_DIR: outA,
        },
        encoding: 'utf8',
      },
    );
    const report = JSON.parse(validateOut);
    assert(report.postCopyValid === true, `post_copy.txt failed validation: ${report.postCopyIssues}`);
    assert(
      report.postCopyPlayCode === 'makefun-pigeon-crayfish-bungalow',
      `Unexpected play code: ${report.postCopyPlayCode}`,
    );

    return {
      summary: `main.ts determinism: 2 runs matched byte-for-byte (sha256=${sha256(bytesA)}, ${bytesA.byteLength} bytes)`,
      report,
    };
  } finally {
    rmSync(tmpBase, { recursive: true, force: true });
  }
}

function verifyMediaAssets() {
  const pngPath = join(REPO_ROOT, 'assets', 'spotlight_crisxai5.png');
  const mp4Path = join(REPO_ROOT, 'assets', 'spotlight_crisxai5.mp4');

  assert(existsSync(pngPath), 'Missing assets/spotlight_crisxai5.png');
  assert(existsSync(mp4Path), 'Missing assets/spotlight_crisxai5.mp4');

  const pngBytes = readFileSync(pngPath);
  const pngMagic = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  assert(pngBytes.subarray(0, 8).equals(pngMagic), 'PNG header signature mismatch');
  const pngWidth = pngBytes.readUInt32BE(16);
  const pngHeight = pngBytes.readUInt32BE(20);
  assert(pngWidth === 1080 && pngHeight === 1350, `Unexpected PNG size: ${pngWidth}x${pngHeight}`);

  const mp4Size = statSync(mp4Path).size;
  assert(mp4Size > 100_000, `MP4 file unexpectedly small: ${mp4Size} bytes`);

  const probeJson = execFileSync(
    'ffprobe',
    [
      '-v', 'error',
      '-show_entries', 'format=duration:stream=codec_type,codec_name,width,height,pix_fmt,sample_rate,channels',
      '-of', 'json',
      mp4Path,
    ],
    { encoding: 'utf8' },
  );
  const probe = JSON.parse(probeJson);
  const duration = Number(probe.format?.duration ?? 0);
  assert(duration > 5 && duration <= 140, `MP4 duration out of X bounds: ${duration}s`);

  const videoStream = (probe.streams ?? []).find((s) => s.codec_type === 'video');
  const audioStream = (probe.streams ?? []).find((s) => s.codec_type === 'audio');
  assert(videoStream?.codec_name === 'h264', `Expected H.264 video, got ${videoStream?.codec_name}`);
  assert(videoStream?.pix_fmt === 'yuv420p', `Expected yuv420p, got ${videoStream?.pix_fmt}`);
  assert(audioStream?.codec_name === 'aac', `Expected AAC audio, got ${audioStream?.codec_name}`);

  return `Media assets OK: PNG ${pngWidth}x${pngHeight} (${pngBytes.byteLength}B), MP4 ${videoStream.width}x${videoStream.height} H.264/AAC ${duration.toFixed(2)}s (${mp4Size}B)`;
}

function main() {
  const results = [];
  results.push(verifyLicense());
  const det = verifyDeterminism();
  results.push(det.summary);
  results.push(
    `post_copy.txt OK: ${det.report.postCopyWeightedLength}/280 chars, playCode=${det.report.postCopyPlayCode}, hashtags=${det.report.postCopyHashtags.join(' ')}`,
  );
  results.push(verifyMediaAssets());

  for (const line of results) {
    process.stdout.write(`[PASS] ${line}\n`);
  }
}

main();
