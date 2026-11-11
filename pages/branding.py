"""Markenfarbe: aus einer Farbe alle Töne für helles und dunkles Design berechnen.

Die Shop-Betreiberin wählt in der Verwaltung nur eine Farbe. Schriftfarbe auf
Buttons, Link-Ton, Dunkelmodus-Variante und Verläufe werden hier so abgeleitet,
dass der Text lesbar bleibt (WCAG-Kontrast 4,5:1) – auch bei sehr hellen Farben.
"""
import colorsys
import re

DEFAULT_COLOR = "#db3012"

_HEX = re.compile(r"#[0-9a-fA-F]{6}")
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
INK = (24, 24, 27)      # #18181b: dunkle Schrift und dunkler Seitenhintergrund
FOOTER = (39, 39, 42)   # #27272a: hellste dunkle Fläche (Footer-Leiste)


def is_hex(value):
    return isinstance(value, str) and bool(_HEX.fullmatch(value))


def parse(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def mix(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def readable(color, background, target):
    """Farbe schrittweise abdunkeln bzw. aufhellen, bis der Kontrast zum Hintergrund reicht."""
    toward = BLACK if luminance(background) > 0.18 else WHITE
    for step in range(101):
        candidate = tuple(round(c) for c in mix(color, toward, step / 100))
        if contrast(candidate, background) >= target:
            return candidate
    return toward


def text_on(background):
    """Schriftfarbe für eine farbige Fläche: Weiß, wenn lesbar, sonst dunkel."""
    if contrast(WHITE, background) >= 4.5:
        return WHITE
    return INK if contrast(INK, background) >= 4.5 else BLACK


def shift_hue(rgb, degrees):
    h, l, s = colorsys.rgb_to_hls(*(c / 255 for c in rgb))
    return tuple(c * 255 for c in colorsys.hls_to_rgb((h + degrees / 360) % 1, l, s))


def tones(color):
    """Liefert (hell, dunkel): je ein Dict CSS-Variable -> Hex-Farbe."""
    brand = parse(color)
    on_brand = text_on(brand)
    hover = mix(brand, BLACK, 0.16) if on_brand == WHITE else mix(brand, WHITE, 0.25)
    link = readable(brand, WHITE, 5)
    ink = readable(brand, WHITE, 3)
    light = {
        "--primary": brand, "--primary-hover": hover, "--on-primary": on_brand,
        "--lime": brand, "--on-lime": on_brand,
        "--link": link, "--focus": ink, "--primary-ink": ink, "--wish": link,
        "--primary-soft": mix(brand, WHITE, 0.88),
        "--dark-accent": readable(brand, FOOTER, 4.5),
        "--grad-a": readable(mix(shift_hue(brand, 8), BLACK, 0.1), WHITE, 4.5),
        "--grad-b": readable(shift_hue(brand, -20), WHITE, 4.5),
        "--grad-c": readable(shift_hue(brand, -50), WHITE, 4.5),
    }
    glow = readable(brand, INK, 6)
    glow_hover = mix(glow, WHITE, 0.22)
    dark = {
        "--primary": glow, "--primary-hover": glow_hover, "--on-primary": text_on(glow),
        "--lime": glow, "--on-lime": text_on(glow),
        "--link": glow_hover, "--focus": glow_hover, "--primary-ink": glow,
        "--primary-soft": mix(glow, INK, 0.82),
    }
    return (
        {name: to_hex(value) for name, value in light.items()},
        {name: to_hex(value) for name, value in dark.items()},
    )


def brand_css(color):
    """CSS, das die Standardpalette überschreibt. Leer bei Standardfarbe oder ungültigem Wert."""
    if not is_hex(color) or color.lower() == DEFAULT_COLOR:
        return ""
    light, dark = tones(color)

    def block(values):
        return "".join(f"{name}:{value};" for name, value in values.items())

    return (
        ":root{" + block(light) + "}"
        '@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){' + block(dark) + "}}"
        ':root[data-theme="dark"]{' + block(dark) + "}"
    )


def favicon_svg(color, letter):
    """Standard-Favicon: farbiges Quadrat mit dem ersten Buchstaben des Shopnamens."""
    brand = parse(color) if is_hex(color) else parse(DEFAULT_COLOR)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{to_hex(brand)}"/>'
        '<text x="32" y="33" text-anchor="middle" dominant-baseline="central" '
        "font-family=\"system-ui,-apple-system,'Segoe UI',Roboto,sans-serif\" "
        f'font-size="36" font-weight="800" fill="{to_hex(text_on(brand))}">{letter}</text>'
        "</svg>"
    )
