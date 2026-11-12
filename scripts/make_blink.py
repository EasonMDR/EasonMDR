#!/usr/bin/env python3
"""Generate a blinking GIF from the Minecraft skin avatar.

Workflow follows the slack-gif-creator skill: build frames with PIL,
quantize to a small global palette, then assemble an optimized looping GIF.
"""

from pathlib import Path
from PIL import Image

SCALE = 4
OPEN_MS = 2600
HALF_MS = 90
CLOSED_MS = 150
EYE_DARK = (69, 46, 39)


def find_eye_boxes(img):
    px = img.load()
    w, h = img.size
    dark = set()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r < 90 and g < 90 and b < 90:
                dark.add((x, y))
    if not dark:
        raise RuntimeError("No dark eye pixels found in the avatar")
    xs = sorted({x for x, _ in dark})
    mid = (min(xs) + max(xs)) / 2
    left = [p for p in dark if p[0] < mid]
    right = [p for p in dark if p[0] >= mid]

    def bbox(points):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        return min(xs), min(ys), max(xs), max(ys)

    return bbox(left), bbox(right)


def render_frame(img, boxes, mode):
    frame = img.copy()
    if mode == "open":
        return frame
    px = frame.load()
    for x0, y0, x1, y1 in boxes:
        if mode == "half":
            cover_rows = range(y0, y0 + (y1 - y0 + 1) // 2)
        else:
            cover_rows = range(y0, y1 + 1)
        for x in range(x0, x1 + 1):
            lid_color = px[x, y0 - 1]
            for y in cover_rows:
                px[x, y] = lid_color
        if mode == "closed":
            mid_y = (y0 + y1) // 2
            for x in range(x0 + 1, x1):
                px[x, mid_y] = EYE_DARK
    return frame


def main():
    base = Path(__file__).resolve().parent.parent
    src = base / "assets" / "avatar.png"
    out = base / "assets" / "avatar-blink.gif"

    img = Image.open(src).convert("RGB")
    boxes = find_eye_boxes(img)

    modes = ["open", "half", "closed", "half"]
    durations = [OPEN_MS, HALF_MS, CLOSED_MS, HALF_MS]
    frames = [
        render_frame(img, boxes, mode)
        .resize((img.width * SCALE, img.height * SCALE), Image.Resampling.NEAREST)
        for mode in modes
    ]

    palette = frames[0].quantize(colors=64)
    gif_frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    gif_frames[0].save(
        out,
        save_all=True,
        append_images=gif_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )

    size_kb = out.stat().st_size / 1024
    print(f"GIF: {out}")
    print(f"Size: {size_kb:.1f} KB")
    print(f"Dimensions: {gif_frames[0].width}x{gif_frames[0].height}")
    print(f"Frames: {len(gif_frames)} | durations(ms): {durations} | loop: infinite")


if __name__ == "__main__":
    main()
