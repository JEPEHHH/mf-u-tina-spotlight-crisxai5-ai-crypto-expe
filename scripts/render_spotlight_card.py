#!/usr/bin/env python3
"""Procedural offline renderer for the @crisxai5 Spotlight X card (1080x1350 PNG).

Uses only Python 3 standard library plus system ffmpeg/libfreetype to produce a
crisp, phone-readable 4:5 vertical portrait graphic introducing @crisxai5 as a
must-follow AI and crypto expert.
"""

from __future__ import annotations

import math
import pathlib
import struct
import subprocess
import tempfile
import zlib

WIDTH = 1080
HEIGHT = 1350

FONT_SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_SANS_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO_XBOLD = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf"
FONT_MONO_BOLD = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf"
FONT_MONO_MED = "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Medium.ttf"


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def write_png_rgb(path: pathlib.Path, width: int, height: int, rgb: bytearray) -> None:
    stride = width * 3
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        start = y * stride
        rows.extend(rgb[start : start + stride])
    compressed = zlib.compress(bytes(rows), level=6)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    data = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", ihdr)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )
    path.write_bytes(data)


def clamp_u8(val: float) -> int:
    if val <= 0.0:
        return 0
    if val >= 255.0:
        return 255
    return int(val + 0.5)


def blend_pixel(buf: bytearray, width: int, height: int, x: int, y: int, r: int, g: int, b: int, alpha: float) -> None:
    if x < 0 or y < 0 or x >= width or y >= height or alpha <= 0.0:
        return
    idx = (y * width + x) * 3
    if alpha >= 1.0:
        buf[idx] = r
        buf[idx + 1] = g
        buf[idx + 2] = b
        return
    inv = 1.0 - alpha
    buf[idx] = clamp_u8(buf[idx] * inv + r * alpha)
    buf[idx + 1] = clamp_u8(buf[idx + 1] * inv + g * alpha)
    buf[idx + 2] = clamp_u8(buf[idx + 2] * inv + b * alpha)


def draw_filled_circle(
    buf: bytearray,
    width: int,
    height: int,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    alpha: float = 1.0,
) -> None:
    r, g, b = color
    x0 = max(0, int(cx - radius - 2))
    x1 = min(width - 1, int(cx + radius + 2))
    y0 = max(0, int(cy - radius - 2))
    y1 = min(height - 1, int(cy + radius + 2))
    for y in range(y0, y1 + 1):
        dy = y + 0.5 - cy
        dy2 = dy * dy
        for x in range(x0, x1 + 1):
            dx = x + 0.5 - cx
            dist = math.sqrt(dx * dx + dy2)
            cov = max(0.0, min(1.0, radius + 0.5 - dist))
            if cov > 0.0:
                blend_pixel(buf, width, height, x, y, r, g, b, cov * alpha)


def draw_soft_glow(
    buf: bytearray,
    width: int,
    height: int,
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    strength: float,
) -> None:
    r, g, b = color
    x0 = max(0, int(cx - radius))
    x1 = min(width - 1, int(cx + radius))
    y0 = max(0, int(cy - radius))
    y1 = min(height - 1, int(cy + radius))
    inv_r2 = 1.0 / (radius * radius)
    for y in range(y0, y1 + 1):
        dy = y - cy
        dy2 = dy * dy
        row_base = y * width * 3
        for x in range(x0, x1 + 1):
            dx = x - cx
            d2 = (dx * dx + dy2) * inv_r2
            if d2 < 1.0:
                falloff = (1.0 - d2)
                w = falloff * falloff * strength
                idx = row_base + x * 3
                buf[idx] = clamp_u8(buf[idx] + r * w)
                buf[idx + 1] = clamp_u8(buf[idx + 1] + g * w)
                buf[idx + 2] = clamp_u8(buf[idx + 2] + b * w)


def draw_line(
    buf: bytearray,
    width: int,
    height: int,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    color: tuple[int, int, int],
    thickness: float = 1.5,
    alpha: float = 0.5,
) -> None:
    r, g, b = color
    dx = x1 - x0
    dy = y1 - y0
    steps = max(1, int(math.hypot(dx, dy) * 1.5))
    half_t = max(1, int(thickness + 1))
    for i in range(steps + 1):
        t = i / steps
        px = x0 + dx * t
        py = y0 + dy * t
        ix = int(px)
        iy = int(py)
        for oy in range(-half_t, half_t + 1):
            for ox in range(-half_t, half_t + 1):
                d = math.hypot((ix + ox) - px, (iy + oy) - py)
                cov = max(0.0, min(1.0, thickness - d))
                if cov > 0.0:
                    blend_pixel(buf, width, height, ix + ox, iy + oy, r, g, b, cov * alpha)


def draw_rounded_panel(
    buf: bytearray,
    width: int,
    height: int,
    x: int,
    y: int,
    w: int,
    h: int,
    radius: int,
    fill: tuple[int, int, int],
    fill_alpha: float,
    border: tuple[int, int, int],
    border_alpha: float,
    border_width: int = 2,
) -> None:
    fr, fg, fb = fill
    br, bg, bb = border
    x_end = min(width, x + w)
    y_end = min(height, y + h)
    rad = float(radius)
    inner_rad = max(0.0, rad - border_width)
    for py in range(max(0, y), y_end):
        ry = py - y
        cy_dist = 0.0
        if ry < radius:
            cy_dist = radius - ry
        elif ry >= h - radius:
            cy_dist = ry - (h - radius - 1)
        row_idx = py * width * 3
        for px in range(max(0, x), x_end):
            rx = px - x
            cx_dist = 0.0
            if rx < radius:
                cx_dist = radius - rx
            elif rx >= w - radius:
                cx_dist = rx - (w - radius - 1)
            if cx_dist > 0.0 and cy_dist > 0.0:
                dist = math.hypot(cx_dist, cy_dist)
                if dist > rad + 0.5:
                    continue
                edge_cov = max(0.0, min(1.0, rad + 0.5 - dist))
                is_border = dist >= inner_rad
            else:
                edge_cov = 1.0
                is_border = (
                    rx < border_width
                    or rx >= w - border_width
                    or ry < border_width
                    or ry >= h - border_width
                )
            idx = row_idx + px * 3
            if is_border:
                a = border_alpha * edge_cov
                inv = 1.0 - a
                buf[idx] = clamp_u8(buf[idx] * inv + br * a)
                buf[idx + 1] = clamp_u8(buf[idx + 1] * inv + bg * a)
                buf[idx + 2] = clamp_u8(buf[idx + 2] * inv + bb * a)
            else:
                a = fill_alpha * edge_cov
                inv = 1.0 - a
                buf[idx] = clamp_u8(buf[idx] * inv + fr * a)
                buf[idx + 1] = clamp_u8(buf[idx + 1] * inv + fg * a)
                buf[idx + 2] = clamp_u8(buf[idx + 2] * inv + fb * a)


def build_base_canvas() -> bytearray:
    """Create the 1080x1350 midnight cyber canvas with glow, grid, and cards."""
    buf = bytearray(WIDTH * HEIGHT * 3)

    # Vertical deep-space gradient
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        r = clamp_u8(7 + 9 * (1.0 - abs(2.0 * t - 0.7)))
        g = clamp_u8(11 + 14 * (1.0 - abs(2.0 * t - 0.6)))
        b = clamp_u8(22 + 24 * (1.0 - t * 0.45))
        row = bytes((r, g, b)) * WIDTH
        start = y * WIDTH * 3
        buf[start : start + WIDTH * 3] = row

    # Ambient radial highlights (cyan top-left, emerald mid-right, indigo bottom)
    draw_soft_glow(buf, WIDTH, HEIGHT, 210, 210, 420, (34, 211, 238), 0.24)
    draw_soft_glow(buf, WIDTH, HEIGHT, 920, 470, 390, (52, 211, 153), 0.20)
    draw_soft_glow(buf, WIDTH, HEIGHT, 540, 1210, 460, (56, 189, 248), 0.18)

    # Subtle technical grid
    grid_step = 54
    for gx in range(grid_step, WIDTH, grid_step):
        for gy in range(0, HEIGHT, 2):
            blend_pixel(buf, WIDTH, HEIGHT, gx, gy, 148, 163, 184, 0.06)
    for gy in range(grid_step, HEIGHT, grid_step):
        for gx in range(0, WIDTH, 2):
            blend_pixel(buf, WIDTH, HEIGHT, gx, gy, 148, 163, 184, 0.06)

    # Decorative AI + on-chain constellation in upper-right header zone
    nodes = [
        (742, 92),
        (838, 72),
        (942, 98),
        (868, 140),
        (978, 148),
        (774, 144),
    ]
    edges = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4), (0, 5), (5, 3), (2, 3)]
    for i, j in edges:
        x0, y0 = nodes[i]
        x1, y1 = nodes[j]
        draw_line(buf, WIDTH, HEIGHT, x0, y0, x1, y1, (34, 211, 238), thickness=1.8, alpha=0.38)
    for nx, ny in nodes:
        draw_filled_circle(buf, WIDTH, HEIGHT, nx, ny, 9.0, (34, 211, 238), 0.24)
        draw_filled_circle(buf, WIDTH, HEIGHT, nx, ny, 4.2, (165, 243, 252), 0.92)

    # Top outer frame border
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 36, 36, WIDTH - 72, HEIGHT - 72, 34,
        fill=(10, 16, 30), fill_alpha=0.22,
        border=(56, 189, 248), border_alpha=0.32, border_width=2,
    )

    # Top badge pill: "AI & CRYPTO SIGNAL SPOTLIGHT"
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 76, 84, 526, 56, 28,
        fill=(14, 116, 144), fill_alpha=0.36,
        border=(34, 211, 238), border_alpha=0.78, border_width=2,
    )
    draw_filled_circle(buf, WIDTH, HEIGHT, 108, 112, 8.0, (52, 211, 153), 1.0)

    # Hero identity card for @crisxai5
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 76, 174, 928, 308, 30,
        fill=(15, 23, 42), fill_alpha=0.84,
        border=(34, 211, 238), border_alpha=0.58, border_width=3,
    )
    # Glowing vertical accent bar inside hero card
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 108, 212, 10, 232, 5,
        fill=(34, 211, 238), fill_alpha=0.95,
        border=(52, 211, 153), border_alpha=0.95, border_width=1,
    )

    # 2x2 Pillar Cards (crisp, phone-readable grid)
    cards = [
        (76, 520, 448, 248, (34, 211, 238)),   # AI AGENTS
        (556, 520, 448, 248, (52, 211, 153)),  # CRYPTO ALPHA
        (76, 796, 448, 248, (96, 165, 250)),   # WEB3 TOOLING
        (556, 796, 448, 248, (167, 139, 250)), # ON-CHAIN AUTO
    ]
    for cx, cy, cw, ch, accent in cards:
        draw_rounded_panel(
            buf, WIDTH, HEIGHT, cx, cy, cw, ch, 26,
            fill=(15, 23, 42), fill_alpha=0.82,
            border=accent, border_alpha=0.52, border_width=2,
        )
        # Top accent stripe inside each card
        draw_rounded_panel(
            buf, WIDTH, HEIGHT, cx + 28, cy + 28, 72, 8, 4,
            fill=accent, fill_alpha=0.95,
            border=accent, border_alpha=0.95, border_width=1,
        )

    # Bottom CTA Banner
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 76, 1084, 928, 186, 28,
        fill=(12, 74, 110), fill_alpha=0.42,
        border=(52, 211, 153), border_alpha=0.80, border_width=3,
    )
    # Right-side CTA pill button visual
    draw_rounded_panel(
        buf, WIDTH, HEIGHT, 686, 1138, 282, 78, 39,
        fill=(52, 211, 153), fill_alpha=0.96,
        border=(167, 243, 208), border_alpha=0.95, border_width=2,
    )

    return buf


def escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("%", "\\%")
    )


def dt(
    text: str,
    x: int,
    y: int,
    size: int,
    color: str,
    font: str = FONT_SANS_BOLD,
) -> str:
    return (
        f"drawtext=fontfile='{font}'"
        f":text='{escape_drawtext(text)}'"
        f":x={x}:y={y}:fontsize={size}:fontcolor={color}"
    )


def render_card(output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas = build_base_canvas()

    filters = [
        # Top pill label
        dt("AI & CRYPTO SIGNAL SPOTLIGHT", 132, 99, 25, "0xE0F2FE", FONT_MONO_BOLD),

        # Hero block
        dt("MUST-FOLLOW VOICE ON X", 142, 212, 25, "0x34D399", FONT_MONO_BOLD),
        dt("@crisxai5", 138, 252, 96, "0xF8FAFC", FONT_SANS_BOLD),
        dt("AI Agents  |  Crypto Alpha  |  Web3 Builders", 142, 372, 31, "0xBAE6FD", FONT_SANS_REG),
        dt("x.com/crisxai5", 142, 422, 26, "0x38BDF8", FONT_MONO_BOLD),

        # Card 1: AI AGENTS
        dt("01 / AI AGENTS", 104, 574, 24, "0x22D3EE", FONT_MONO_XBOLD),
        dt("Autonomous Workflows", 104, 622, 30, "0xF8FAFC", FONT_SANS_BOLD),
        dt("Practical agent architectures", 104, 672, 23, "0xCBD5E1", FONT_SANS_REG),
        dt("and real builder playbooks.", 104, 706, 23, "0xCBD5E1", FONT_SANS_REG),

        # Card 2: CRYPTO ALPHA
        dt("02 / CRYPTO ALPHA", 584, 574, 24, "0x34D399", FONT_MONO_XBOLD),
        dt("Signal Over Noise", 584, 622, 30, "0xF8FAFC", FONT_SANS_BOLD),
        dt("High-conviction narratives,", 584, 672, 23, "0xCBD5E1", FONT_SANS_REG),
        dt("catalysts, and cycle shifts.", 584, 706, 23, "0xCBD5E1", FONT_SANS_REG),

        # Card 3: WEB3 TOOLING
        dt("03 / WEB3 TOOLING", 104, 850, 24, "0x60A5FA", FONT_MONO_XBOLD),
        dt("Builder-Grade Stack", 104, 898, 30, "0xF8FAFC", FONT_SANS_BOLD),
        dt("Sharp takes on protocols,", 104, 948, 23, "0xCBD5E1", FONT_SANS_REG),
        dt("SDKs, and infra shipping now.", 104, 982, 23, "0xCBD5E1", FONT_SANS_REG),

        # Card 4: ON-CHAIN AUTOMATION
        dt("04 / ON-CHAIN AUTO", 584, 850, 24, "0xA78BFA", FONT_MONO_XBOLD),
        dt("AI Meets Live Chains", 584, 898, 30, "0xF8FAFC", FONT_SANS_BOLD),
        dt("Autonomous execution, bots,", 584, 948, 23, "0xCBD5E1", FONT_SANS_REG),
        dt("and verifiable on-chain flows.", 584, 982, 23, "0xCBD5E1", FONT_SANS_REG),

        # Bottom CTA Banner
        dt("UPGRADE YOUR TIMELINE", 116, 1122, 24, "0x6EE7B7", FONT_MONO_BOLD),
        dt("Follow @crisxai5 on X", 116, 1158, 42, "0xF8FAFC", FONT_SANS_BOLD),
        dt("https://x.com/crisxai5", 116, 1216, 24, "0xBAE6FD", FONT_MONO_MED),
        dt("FOLLOW NOW ->", 720, 1163, 27, "0x06201A", FONT_MONO_XBOLD),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        base_png = pathlib.Path(tmpdir) / "base.png"
        write_png_rgb(base_png, WIDTH, HEIGHT, canvas)
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(base_png),
            "-vf",
            ",".join(filters),
            "-frames:v",
            "1",
            str(output_path),
        ]
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    out_file = repo_root / "assets" / "spotlight_crisxai5.png"
    render_card(out_file)
    print(f"Rendered {out_file} ({out_file.stat().st_size} bytes)")
