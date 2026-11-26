# Spotlight @crisxai5 — AI & Crypto Expert on X

Entry repository for the make.fun bounty `u-tina-spotlight-crisxai5-ai-crypto-expert-on-x-7c1ed9ad`.

## Deliverables

- `main.ts` — Deterministic Node 22 entrypoint (zero external dependencies, fully offline) that validates and writes `POST.json` to `/output/POST.json` (or `$MAKEFUN_OUTPUT_DIR/POST.json`).
- `src/post-config.ts`, `src/copy-validator.ts`, `src/deterministic-io.ts` — Modular TypeScript helpers for X URL parsing, copy verification, and deterministic file output.
- `assets/spotlight_crisxai5.png` — Original 1080×1350 (4:5 mobile-first) spotlight graphic introducing `@crisxai5`.
- `assets/spotlight_crisxai5.mp4` — Original 12.5-second 1080×1350 H.264/AAC animated spotlight video with synthesized ambient soundtrack.
- `post_copy.txt` — Final X post text featuring `@crisxai5`, `https://x.com/crisxai5`, four targeted hashtags (`#AI #Crypto #AIAgents #Web3`), and the competition play code `makefun-pigeon-crayfish-bungalow`.
- `POST.json` — Public X post address read by the make.fun grader.
- `scripts/render_spotlight_card.py` & `scripts/render_spotlight_video.py` — Pure Python 3 standard library + `ffmpeg` scripts that reproduce the PNG and MP4 assets offline.
- `scripts/verify_entry.mjs` — Local verification suite confirming two-run byte-for-byte determinism, copy compliance, license compliance, and media stream health.

## Publishing Steps (Hand-off)

1. From a **public** X account, create a new post and upload `assets/spotlight_crisxai5.mp4` (or `assets/spotlight_crisxai5.png`) natively.
2. Paste the exact text from `post_copy.txt` into the post body (do not alter `@crisxai5` or `makefun-pigeon-crayfish-bungalow`).
3. Publish before `2026-11-27 11:35 UTC`, copy the post link (`https://x.com/<handle>/status/<id>`), and update `POST.json`.
4. Keep the post live and the account public until final results are published.

## Local Deterministic Verification

```bash
MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts
MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts --validate
node scripts/verify_entry.mjs
```

## License

MIT License — Copyright (c) 2026 jepehhh (see `LICENSE`).
