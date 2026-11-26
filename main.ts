// Entrypoint for Spotlight @crisxai5 (u-tina-spotlight-crisxai5-ai-crypto-expert-on-x-7c1ed9ad).
// Runs offline on Node 22 with zero external dependencies and writes POST.json
// deterministically to /output/POST.json (or MAKEFUN_OUTPUT_DIR/POST.json).

import { existsSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { validatePostCopy } from './src/copy-validator.ts';
import {
  readAndCopyPostFile,
  resolveRuntimePaths,
  type CopyOutcome,
  type RuntimePaths,
} from './src/deterministic-io.ts';
import { COMPETITION_SLUG, validatePostEntry } from './src/post-config.ts';

interface CliOptions {
  readonly validateMode: boolean;
  readonly strictPostUrl: boolean;
}

interface AssetInventory {
  readonly pngPresent: boolean;
  readonly pngBytes: number;
  readonly mp4Present: boolean;
  readonly mp4Bytes: number;
}

function parseCliArgs(argv: readonly string[]): CliOptions {
  const flags = new Set(argv.slice(2));
  return {
    validateMode: flags.has('--validate') || flags.has('--self-check'),
    strictPostUrl: flags.has('--strict'),
  };
}

function inspectBundledAssets(botDir: string): AssetInventory {
  const pngPath = join(botDir, 'assets', 'spotlight_crisxai5.png');
  const mp4Path = join(botDir, 'assets', 'spotlight_crisxai5.mp4');
  const pngPresent = existsSync(pngPath);
  const mp4Present = existsSync(mp4Path);

  return {
    pngPresent,
    pngBytes: pngPresent ? statSync(pngPath).size : 0,
    mp4Present,
    mp4Bytes: mp4Present ? statSync(mp4Path).size : 0,
  };
}

function buildValidationSummary(paths: RuntimePaths, outcome: CopyOutcome) {
  const postCheck = validatePostEntry(outcome.parsedJson);
  const copyExists = existsSync(paths.postCopyPath);
  const copyReport = copyExists
    ? validatePostCopy(readFileSync(paths.postCopyPath, 'utf8'))
    : null;
  const assets = inspectBundledAssets(paths.botDir);

  return {
    postCheck,
    copyExists,
    copyReport,
    payload: {
      competition: COMPETITION_SLUG,
      outputPath: outcome.destinationPath,
      bytesWritten: outcome.bytesWritten,
      sha256: outcome.sha256,
      postUrlValid: postCheck.ok,
      postUrlPlaceholder: postCheck.isPlaceholder,
      canonicalUrl: postCheck.parsed?.canonicalUrl ?? null,
      postUrlErrors: postCheck.errors,
      postCopyPresent: copyExists,
      postCopyValid: copyReport?.valid ?? false,
      postCopyWeightedLength: copyReport?.weightedLength ?? 0,
      postCopyPlayCode: copyReport?.playCode ?? null,
      postCopyHashtags: copyReport?.hashtags ?? [],
      postCopyIssues: copyReport?.issues ?? (copyExists ? [] : ['Missing post_copy.txt']),
      assets,
    },
  };
}

function executeEntry(env: NodeJS.ProcessEnv, argv: readonly string[]): number {
  const options = parseCliArgs(argv);
  const paths = resolveRuntimePaths(env);
  const outcome = readAndCopyPostFile(paths);

  if (options.validateMode) {
    const { postCheck, copyExists, copyReport, payload } = buildValidationSummary(
      paths,
      outcome,
    );
    process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);

    if (!copyExists || (copyReport !== null && !copyReport.valid)) {
      return 1;
    }
    if (options.strictPostUrl && !postCheck.ok) {
      return 1;
    }
    return 0;
  }

  const postCheck = validatePostEntry(outcome.parsedJson);
  if (!postCheck.ok && !postCheck.isPlaceholder) {
    process.stderr.write(`POST.json warning: ${postCheck.errors.join(' ')}\n`);
  }
  return 0;
}

try {
  const exitCode = executeEntry(process.env, process.argv);
  if (exitCode !== 0) {
    process.exit(exitCode);
  }
} catch (err) {
  const message = err instanceof Error ? err.message : String(err);
  process.stderr.write(`Entry execution failed: ${message}\n`);
  process.exit(1);
}
