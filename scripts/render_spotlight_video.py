#!/usr/bin/env python3
"""Procedural offline renderer for the @crisxai5 12-second Spotlight X video (MP4).

Generates a 1080x1350 (4:5 mobile-first) 30fps H.264/AAC MP4 video with 4 crisp
animated scenes and a synthesized stereo ambient audio track using only Python 3
standard library plus system ffmpeg.
"""

from __future__ import annotations

import math
import pathlib
import struct
import subprocess
import tempfile
import wave

from render_spotlight_card import (
    FONT_MONO_BOLD,
    FONT_MONO_MED,
    FONT_MONO_XBOLD,
    FONT_SANS_BOLD,
    FONT_SANS_REG,
    HEIGHT,
    WIDTH,
    blend_pixel,
    clamp_u8,
    draw_filled_circle,
    draw_line,
    draw_rounded_panel,
    draw_soft_glow,
    escape_drawtext,
    write_png_rgb,
)

FPS = 30
SCENE_DURATION = 3.5
XFADE_DURATION = 0.5
TOTAL_DURATION = 12.5


def make_scene_backdrop(
    glow_a: tuple[float, float, tuple[int, int, int], float],
    glow_b: tuple[float, float, tuple[int, int, int], float],
    border_accent: tuple[int, int, int],
) -> bytearray:
    buf = bytearray(WIDTH * HEIGHT * 3)
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = clamp_u8(6 + 10 * (1.0 - abs(2.0 * t - 0.6)))
        g = clamp_u8(10 + 15 * (1.0 - abs(2.0 * t - 0.5)))
        b = clamp_u8(20 + 26 * (1.0 - t * 0.4))
        row = bytes((r, g, b)) * WIDTH
        start = y * WIDTH * 3
        buf[start : start + WIDTH * 3] = row

    draw_soft_glow(buf, WIDTH, HEIGHT, glow_a[0], glow_a[1], 450, glow_a[2], glow_a[3])
    draw_soft_glow(buf, WIDTH, HEIGHT, glow_b[0], glow_b[1], 420, glow_b[2], glow_b[3])

    for gx in range(54, WIDTH, 54):
        for gy in range(0, HEIGHT, 2):
            blend_pixel(buf, WIDTH, HEIGHT, gx, gy, 148, 163, 184, 0.055)
    for gy in range(54, HEIGHT, 54):
        for gx in range(0, WIDTH, 2):
            blend_pixel(buf, WIDTH, HEIGHT, gx, gy, 148, 163, 184, 0.055)

    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 36, 36, WIDTH - 72, HEIGHT - 72, 34,
        fill=(10, 16, 30), fill_alpha=0.18,
        border=border_accent, border_alpha=0.38, border_width=3,
    )
    return buf


def build_scene1_canvas() -> bytearray:
    """Scene 1: Scroll-stopping hook."""
    buf = make_scene_backdrop(
        (240, 260, (34, 211, 238), 0.28),
        (860, 1080, (52, 211, 153), 0.22),
        (34, 211, 238),
    )
    # Top radar badge
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 270, 240, 540, 64, 32,
        fill=(14, 116, 144), fill_alpha=0.44,
        border=(34, 211, 238), border_alpha=0.85, border_width=2,
    )
    draw_filled_circle(buf, WIDTH, HEIGHT, 308, 272, 9.0, (52, 211, 153), 1.0)

    # Central dramatic card
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 84, 370, 912, 540, 36,
        fill=(15, 23, 42), fill_alpha=0.84,
        border=(34, 211, 238), border_alpha=0.60, border_width=3,
    )
    # Bottom progress indicator dots (1/4 active)
    for idx in range(4):
        cx = 468 + idx * 48
        if idx == 0:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 10.0, (34, 211, 238), 1.0)
        else:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 7.0, (100, 116, 139), 0.7)
    return buf


def build_scene2_canvas() -> bytearray:
    """Scene 2: Hero introduction of @crisxai5."""
    buf = make_scene_backdrop(
        (540, 420, (34, 211, 238), 0.30),
        (220, 1020, (56, 189, 248), 0.22),
        (52, 211, 153),
    )
    # Constellation halo around hero card
    nodes = [
        (140, 210), (260, 160), (410, 200),
        (680, 185), (840, 155), (940, 230),
        (170, 1050), (350, 1110), (740, 1090), (920, 1020),
    ]
    edges = [(0, 1), (1, 2), (3, 4), (4, 5), (6, 7), (8, 9)]
    for i, j in edges:
        x0, y0 = nodes[i]
        x1, y1 = nodes[j]
        draw_line(buf, WIDTH, HEIGHT, x0, y0, x1, y1, (52, 211, 153), thickness=2.0, alpha=0.38)
    for nx, ny in nodes:
        draw_filled_circle(buf, WIDTH, HEIGHT, nx, ny, 9.0, (52, 211, 153), 0.25)
        draw_filled_circle(buf, WIDTH, HEIGHT, nx, ny, 4.5, (167, 243, 208), 0.95)

    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 84, 330, 912, 600, 36,
        fill=(15, 23, 42), fill_alpha=0.88,
        border=(52, 211, 153), border_alpha=0.72, border_width=3,
    )
    # Accent bar
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 360, 626, 360, 8, 4,
        fill=(34, 211, 238), fill_alpha=0.95,
        border=(52, 211, 153), border_alpha=0.95, border_width=1,
    )
    for idx in range(4):
        cx = 468 + idx * 48
        if idx == 1:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 10.0, (52, 211, 153), 1.0)
        else:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 7.0, (100, 116, 139), 0.7)
    return buf


def build_scene3_canvas() -> bytearray:
    """Scene 3: Four high-signal pillars."""
    buf = make_scene_backdrop(
        (210, 310, (96, 165, 250), 0.24),
        (870, 960, (167, 139, 250), 0.24),
        (96, 165, 250),
    )
    pillars = [
        (84, 290, 912, 184, (34, 211, 238)),
        (84, 504, 912, 184, (52, 211, 153)),
        (84, 718, 912, 184, (96, 165, 250)),
        (84, 932, 912, 184, (167, 139, 250)),
    ]
    for px, py, pw, ph, accent in pillars:
        draw_rounded_panel(
            buf, WIDTH, HEIGHT, px, py, pw, ph, 26,
            fill=(15, 23, 42), fill_alpha=0.86,
            border=accent, border_alpha=0.62, border_width=2,
        )
        draw_rounded_panel(
            buf, WIDTH, HEIGHT, px + 26, py + 34, 10, ph - 68, 5,
            fill=accent, fill_alpha=0.95,
            border=accent, border_alpha=0.95, border_width=1,
        )
    for idx in range(4):
        cx = 468 + idx * 48
        if idx == 2:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 10.0, (96, 165, 250), 1.0)
        else:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 7.0, (100, 116, 139), 0.7)
    return buf


def build_scene4_canvas() -> bytearray:
    """Scene 4: Clean CTA end card."""
    buf = make_scene_backdrop(
        (540, 380, (52, 211, 153), 0.30),
        (540, 980, (34, 211, 238), 0.26),
        (52, 211, 153),
    )
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 84, 280, 912, 740, 38,
        fill=(15, 23, 42), fill_alpha=0.88,
        border=(52, 211, 153), border_alpha=0.78, border_width=3,
    )
    # Bright CTA pill
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 240, 760, 600, 104, 52,
        fill=(52, 211, 153), fill_alpha=0.96,
        border=(167, 243, 208), border_alpha=0.95, border_width=2,
    )
    for idx in range(4):
        cx = 468 + idx * 48
        if idx == 3:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 10.0, (52, 211, 153), 1.0)
        else:
            draw_filled_circle(buf, WIDTH, HEIGHT, cx, 1210, 7.0, (100, 116, 139), 0.7)
    return buf


def centered_text(
    text: str,
    y: int,
    size: int,
    color: str,
    font: str = FONT_SANS_BOLD,
    delay: float = 0.0,
) -> str:
    alpha_expr = (
        f"if(lt(t,{delay:.2f}),0,if(lt(t,{delay + 0.35:.2f}),(t-{delay:.2f})/0.35,1))"
        if delay > 0.0
        else "min(1,t/0.35)"
    )
    return (
        f"drawtext=fontfile='{font}'"
        f":text='{escape_drawtext(text)}'"
        f":x=(w-text_w)/2:y={y}:fontsize={size}:fontcolor={color}"
        f":alpha='{alpha_expr}'"
    )


def left_text(
    text: str,
    x: int,
    y: int,
    size: int,
    color: str,
    font: str = FONT_SANS_BOLD,
    delay: float = 0.0,
) -> str:
    alpha_expr = (
        f"if(lt(t,{delay:.2f}),0,if(lt(t,{delay + 0.30:.2f}),(t-{delay:.2f})/0.30,1))"
        if delay > 0.0
        else "min(1,t/0.30)"
    )
    return (
        f"drawtext=fontfile='{font}'"
        f":text='{escape_drawtext(text)}'"
        f":x={x}:y={y}:fontsize={size}:fontcolor={color}"
        f":alpha='{alpha_expr}'"
    )


def synthesize_audio(wav_path: pathlib.Path, duration_sec: float) -> None:
    """Synthesize a clean, deterministic stereo ambient synth progression (48kHz)."""
    sample_rate = 48000
    total_samples = int(sample_rate * duration_sec)
    # Four warm cyber-ambient chords matching the 4 visual beats
    chords = [
        (220.00, 261.63, 329.63, 440.00),  # Am7
        (174.61, 220.00, 261.63, 349.23),  # Fmaj7
        (196.00, 246.94, 293.66, 392.00),  # G6
        (261.63, 329.63, 392.00, 523.25),  # Cmaj7 resolve
    ]
    beat_len = duration_sec / 4.0

    frames = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        chord_idx = min(3, int(t / beat_len))
        local_t = t - chord_idx * beat_len
        freqs = chords[chord_idx]

        # Smooth chord envelope + global fade in/out
        env = min(1.0, local_t / 0.18) * (0.72 + 0.28 * math.exp(-local_t * 1.1))
        if t < 0.25:
            env *= t / 0.25
        if t > duration_sec - 0.8:
            env *= max(0.0, (duration_sec - t) / 0.8)

        # Gentle rhythmic pulse (120 BPM subtle shimmer)
        pulse = 0.88 + 0.12 * math.sin(2.0 * math.pi * 2.0 * t)

        left = 0.0
        right = 0.0
        for k, f in enumerate(freqs):
            phase = 2.0 * math.pi * f * t
            detune = 2.0 * math.pi * (f * 1.003) * t
            amp = 0.18 if k < 2 else 0.11
            left += amp * math.sin(phase)
            right += amp * math.sin(detune + 0.15 * k)

        # Soft chime accent on beat transitions
        chime_freq = freqs[3] * 2.0
        chime = 0.08 * math.exp(-local_t * 5.5) * math.sin(2.0 * math.pi * chime_freq * local_t)

        l_val = max(-0.92, min(0.92, (left * env * pulse + chime)))
        r_val = max(-0.92, min(0.92, (right * env * pulse + chime * 0.9)))
        frames.extend(struct.pack("<hh", int(l_val * 32767), int(r_val * 32767)))

    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(frames))


def render_scene_clip(
    base_png: pathlib.Path,
    out_mp4: pathlib.Path,
    draw_filters: list[str],
) -> None:
    # Subtle animated top progress bar across each scene
    bar_filter = (
        f"drawbox=x=76:y=56:w='min(928,928*t/{SCENE_DURATION:.2f})':h=6"
        f":color=0x22D3EE@0.85:t=fill"
    )
    vf = ",".join([bar_filter, *draw_filters, "format=yuv420p"])
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-i",
        str(base_png),
        "-t",
        f"{SCENE_DURATION:.2f}",
        "-r",
        str(FPS),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)


def render_video(output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = pathlib.Path(tmpdir)

        scenes = [
            (
                build_scene1_canvas(),
                [
                    centered_text("SIGNAL SPOTLIGHT", 256, 30, "0xE0F2FE", FONT_MONO_XBOLD, 0.0),
                    centered_text("BUILDING IN", 458, 62, "0x94A3B8", FONT_SANS_BOLD, 0.15),
                    centered_text("AI + CRYPTO?", 544, 88, "0xF8FAFC", FONT_SANS_BOLD, 0.30),
                    centered_text("Stop scrolling past the noise.", 688, 36, "0x38BDF8", FONT_SANS_REG, 0.55),
                    centered_text("Here is one account worth bookmarking.", 748, 32, "0xCBD5E1", FONT_SANS_REG, 0.75),
                ],
            ),
            (
                build_scene2_canvas(),
                [
                    centered_text("MEET THE EXPERT", 408, 30, "0x34D399", FONT_MONO_XBOLD, 0.0),
                    centered_text("@crisxai5", 472, 112, "0xF8FAFC", FONT_SANS_BOLD, 0.20),
                    centered_text("AI & Crypto Strategist on X", 674, 42, "0xE0F2FE", FONT_SANS_BOLD, 0.45),
                    centered_text("Practical insights. Zero fluff.", 744, 34, "0xCBD5E1", FONT_SANS_REG, 0.65),
                    centered_text("https://x.com/crisxai5", 826, 30, "0x38BDF8", FONT_MONO_BOLD, 0.85),
                ],
            ),
            (
                build_scene3_canvas(),
                [
                    centered_text("WHY FOLLOW @crisxai5", 162, 46, "0xF8FAFC", FONT_SANS_BOLD, 0.0),
                    centered_text("FOUR HIGH-SIGNAL PILLARS", 224, 24, "0x38BDF8", FONT_MONO_BOLD, 0.10),

                    left_text("01  AI AGENTS", 142, 326, 32, "0x22D3EE", FONT_MONO_XBOLD, 0.20),
                    left_text("Autonomous workflows & real builder systems", 142, 384, 28, "0xE2E8F0", FONT_SANS_REG, 0.25),

                    left_text("02  CRYPTO ALPHA", 142, 540, 32, "0x34D399", FONT_MONO_XBOLD, 0.45),
                    left_text("High-conviction narratives & ecosystem shifts", 142, 598, 28, "0xE2E8F0", FONT_SANS_REG, 0.50),

                    left_text("03  WEB3 TOOLING", 142, 754, 32, "0x60A5FA", FONT_MONO_XBOLD, 0.70),
                    left_text("Protocols, frameworks, and infra that ship", 142, 812, 28, "0xE2E8F0", FONT_SANS_REG, 0.75),

                    left_text("04  ON-CHAIN AUTOMATION", 142, 968, 32, "0xA78BFA", FONT_MONO_XBOLD, 0.95),
                    left_text("Machine intelligence executing on live chains", 142, 1026, 28, "0xE2E8F0", FONT_SANS_REG, 1.00),
                ],
            ),
            (
                build_scene4_canvas(),
                [
                    centered_text("UPGRADE YOUR X FEED", 364, 30, "0x6EE7B7", FONT_MONO_XBOLD, 0.0),
                    centered_text("FOLLOW", 436, 66, "0xCBD5E1", FONT_SANS_BOLD, 0.15),
                    centered_text("@crisxai5", 518, 108, "0xF8FAFC", FONT_SANS_BOLD, 0.30),
                    centered_text("AI Agents  |  Crypto Alpha  |  Web3", 662, 32, "0xBAE6FD", FONT_SANS_REG, 0.45),
                    centered_text("x.com/crisxai5", 794, 36, "0x06201A", FONT_MONO_XBOLD, 0.55),
                    centered_text("#AI  #Crypto  #AIAgents  #Web3", 920, 26, "0x94A3B8", FONT_MONO_MED, 0.70),
                ],
            ),
        ]

        clip_paths: list[pathlib.Path] = []
        for idx, (canvas, filters) in enumerate(scenes, start=1):
            base_png = tmp / f"scene_{idx}.png"
            clip_mp4 = tmp / f"scene_{idx}.mp4"
            write_png_rgb(base_png, WIDTH, HEIGHT, canvas)
            render_scene_clip(base_png, clip_mp4, filters)
            clip_paths.append(clip_mp4)

        audio_wav = tmp / "soundtrack.wav"
        synthesize_audio(audio_wav, TOTAL_DURATION)

        # Concatenate 4 clips with smooth 0.5s crossfades -> 3.5*4 - 0.5*3 = 12.5s
        offset1 = SCENE_DURATION - XFADE_DURATION
        offset2 = offset1 + SCENE_DURATION - XFADE_DURATION
        offset3 = offset2 + SCENE_DURATION - XFADE_DURATION
        filter_complex = (
            f"[0:v][1:v]xfade=transition=fade:duration={XFADE_DURATION}:offset={offset1:.2f}[v01];"
            f"[v01][2:v]xfade=transition=fade:duration={XFADE_DURATION}:offset={offset2:.2f}[v02];"
            f"[v02][3:v]xfade=transition=fade:duration={XFADE_DURATION}:offset={offset3:.2f},format=yuv420p[vout]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(clip_paths[0]),
            "-i",
            str(clip_paths[1]),
            "-i",
            str(clip_paths[2]),
            "-i",
            str(clip_paths[3]),
            "-i",
            str(audio_wav),
            "-filter_complex",
            filter_complex,
            "-map",
            "[vout]",
            "-map",
            "4:a",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-ar",
            "48000",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    out_file = repo_root / "assets" / "spotlight_crisxai5.mp4"
    render_video(out_file)
    print(f"Rendered {out_file} ({out_file.stat().st_size} bytes)")
