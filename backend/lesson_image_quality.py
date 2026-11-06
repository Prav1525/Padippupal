"""Shared image-quality checks for textbook lesson assets."""
from __future__ import annotations

import fitz

def is_decorative_warm_texture(payload: bytes) -> bool:
    """Reject the repeated pale-yellow paper texture mistakenly mapped as lesson art.

    This is deliberately a narrow pixel heuristic: it only flags images that are
    overwhelmingly bright yellow, have a yellow-paper mean colour, and have low
    luminance variation. Dark star fields and real yellow/orange astronomy photos
    do not meet all three conditions.
    """
    try:
        pix = fitz.Pixmap(payload)
        # Embedded PDF JPEGs are frequently CMYK (four channels); convert every
        # decoded source to RGB before applying channel-based quality checks.
        pix = fitz.Pixmap(fitz.csRGB, pix)
        samples = pix.samples
        channels = pix.n
        count = len(samples) // channels
        if count == 0:
            return False
        # Bound the work for large uploads while sampling across the whole image.
        step = max(1, count // 4096)
        red = green = blue = luminance = luminance_sq = yellow = sampled = 0
        for index in range(0, count, step):
            offset = index * channels
            r, g, b = samples[offset], samples[offset + 1], samples[offset + 2]
            y = 0.2126 * r + 0.7152 * g + 0.0722 * b
            red += r; green += g; blue += b
            luminance += y; luminance_sq += y * y
            if r > 220 and g > 165 and b < 155 and r - g > 20 and g - b > 30:
                yellow += 1
            sampled += 1
        mean_r, mean_g, mean_b = red / sampled, green / sampled, blue / sampled
        mean_y = luminance / sampled
        variance = max(0.0, luminance_sq / sampled - mean_y * mean_y)
        luminance_std = variance ** 0.5
        return (yellow / sampled >= 0.75 and mean_r >= 220 and
                mean_g >= 170 and mean_b <= 155 and luminance_std <= 45)
    except Exception:
        # Unsupported/corrupt decoders must not turn a valid signature into a
        # false quality verdict; MIME/signature checks remain authoritative.
        return False

