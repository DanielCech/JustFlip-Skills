#!/usr/bin/env bash
# Converts an SVG drawn for a JustFlip card into the PNG the app can display.
#
#   scripts/svg_to_png.sh input.svg output.png [width]
#
# Renders at 1200 px wide by default (a phone card face is ~330 pt ≈ 1000 px) on
# an opaque white plate — the app draws no background behind images, so a
# transparent PNG vanishes in dark mode.
set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "usage: $0 input.svg output.png [width]" >&2
    exit 64
fi

input=$1
output=$2
width=${3:-1200}

if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert --width "$width" --keep-aspect-ratio --background-color '#FFFFFF' "$input" --output "$output"
elif command -v magick >/dev/null 2>&1; then
    magick -background '#FFFFFF' -density 300 "$input" -resize "${width}x" -flatten "$output"
elif python3 -c 'import cairosvg' >/dev/null 2>&1; then
    python3 -c 'import sys, cairosvg; cairosvg.svg2png(url=sys.argv[1], write_to=sys.argv[2], output_width=int(sys.argv[3]), background_color="#FFFFFF")' "$input" "$output" "$width"
else
    echo "Install one of: rsvg-convert (brew install librsvg), ImageMagick, or python cairosvg." >&2
    exit 69
fi

echo "$output"
