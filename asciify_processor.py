"""Convert an image to ASCII art using the settings configured below."""

import html
import re
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from asciify import asciify
from asciify.utils import CHARSET_PRESETS


# Edit these settings before running the program.
COLOR_MODE = "color"  # "color" or "bw"
EDGES_DETECTION = False
WIDTH = 256  # Set both dimensions for text output; use None for both to use terminal size.
HEIGHT = 256
KEEP_ASPECT_RATIO = True
FACTOR_TYPE = "wide"  # "in_terminal", "wide", or "tall"
BLUR = [(3, 3), 1.5, 1.5]  # Kernel size, sigma x, sigma y.
CANNY_THRESH = (200, 300)
ANGLES_THRESH = 3
ASPECT_RATIO_CORRECTION = 1.10
CHARSET_PRESET = "unicode_blocks"  # "default", "classic", "extended", "braille", "unicode_blocks", or "custom".
CUSTOM_CHARSET = " .:-=+*#@"  # Used only when CHARSET_PRESET is "custom".
OUTPUT_FORMAT = "text"  # "text", "html", or "png"; PNG does not support edge detection.
OUTPUT_PATH = None  # HTML/PNG require a file path.
##D:/Github/asciify-them/output/output.html

ANSI_COLOR = re.compile(r"\x1b\[38;2;(\d+);(\d+);(\d+)m")


def _ansi_to_html(ansi_text):
    """Convert the renderer's ANSI true-color text into HTML color spans."""
    parts = []
    position = 0
    color_is_open = False

    for match in ANSI_COLOR.finditer(ansi_text):
        parts.append(html.escape(ansi_text[position : match.start()]))
        if color_is_open:
            parts.append("</span>")
        red, green, blue = match.groups()
        parts.append(
            f'<span style="color: rgb({red}, {green}, {blue})">'
        )
        color_is_open = True
        position = match.end()

    parts.append(html.escape(ansi_text[position:]))
    if color_is_open:
        parts.append("</span>")

    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>ASCII art</title>\n"
        "<style>body{background:#111;color:#fff}pre{font-family:monospace;"
        "font-size:8px;line-height:1;white-space:pre;}</style>\n"
        "</head>\n"
        f"<body><pre>{''.join(parts)}</pre></body>\n"
        "</html>\n"
    )


def main():
    """Read an image path, convert it using the configured settings, and save it."""
    raw_path = input("Paste the image path: ").strip()
    if len(raw_path) >= 2 and raw_path[0] == raw_path[-1] and raw_path[0] in {"'", '"'}:
        raw_path = raw_path[1:-1]

    image_path = Path(raw_path).expanduser()
    if not image_path.is_file():
        print(f"Image file not found: {image_path}", file=sys.stderr)
        return 1

    if COLOR_MODE not in {"color", "bw"}:
        raise ValueError("COLOR_MODE must be 'color' or 'bw'")
    if FACTOR_TYPE not in {"in_terminal", "wide", "tall"}:
        raise ValueError("FACTOR_TYPE must be 'in_terminal', 'wide', or 'tall'")
    if OUTPUT_FORMAT not in {"text", "html", "png"}:
        raise ValueError("OUTPUT_FORMAT must be 'text', 'html', or 'png'")
    if CHARSET_PRESET == "custom":
        charset = list(CUSTOM_CHARSET)
    elif CHARSET_PRESET in CHARSET_PRESETS:
        charset = list(CHARSET_PRESETS[CHARSET_PRESET])
    else:
        available = ", ".join((*CHARSET_PRESETS, "custom"))
        raise ValueError(f"CHARSET_PRESET must be one of: {available}")
    if not charset:
        raise ValueError("The selected character set cannot be empty")
    if OUTPUT_FORMAT == "png" and EDGES_DETECTION:
        raise ValueError("PNG output does not support edge detection")
    if OUTPUT_FORMAT == "png" and OUTPUT_PATH is None:
        raise ValueError("Set OUTPUT_PATH to a file name when using PNG output")
    if OUTPUT_FORMAT == "html" and OUTPUT_PATH is None:
        raise ValueError("Set OUTPUT_PATH to a file name when using HTML output")
    if OUTPUT_FORMAT in {"text", "html"} and (WIDTH is None) != (HEIGHT is None):
        raise ValueError(
            "For text or HTML output, set both WIDTH and HEIGHT, or leave both None"
        )

    image_path = image_path.resolve()
    if cv2.imread(str(image_path)) is None:
        print(
            f"Could not read an image from {image_path}. "
            "Check that the file is a supported image.",
            file=sys.stderr,
        )
        return 1

    try:
        result = asciify(
            image_path=str(image_path),
            color_mode=COLOR_MODE,
            edges_detection=EDGES_DETECTION,
            width=WIDTH,
            height=HEIGHT,
            keep_aspect_ratio=KEEP_ASPECT_RATIO,
            f_type=FACTOR_TYPE,
            blur=BLUR,
            canny_thresh=CANNY_THRESH,
            angles_thresh=ANGLES_THRESH,
            aspect_ratio_correction=ASPECT_RATIO_CORRECTION,
            charset=charset,
            output_format="png" if OUTPUT_FORMAT == "png" else "text",
        )

        if OUTPUT_FORMAT == "png":
            if isinstance(result, str):
                raise RuntimeError("PNG conversion did not return image data")
            output_path = Path(OUTPUT_PATH).expanduser()
            image = cv2.cvtColor(result, cv2.COLOR_RGB2BGR)
            if not cv2.imwrite(str(output_path), image):
                raise OSError(f"Could not write PNG output to {output_path}")
            print(f"Saved PNG image to {output_path}")
        elif isinstance(result, str) and OUTPUT_FORMAT == "html":
            output_path = Path(OUTPUT_PATH).expanduser()
            output_path.write_text(_ansi_to_html(result), encoding="utf-8")
            print(f"Saved colored HTML ASCII art to {output_path}")
        elif isinstance(result, str):
            if OUTPUT_PATH is None:
                print(result)
            else:
                output_path = Path(OUTPUT_PATH).expanduser()
                output_path.write_text(result, encoding="utf-8")
                print(f"Saved ASCII art to {output_path}")
        else:
            raise RuntimeError("Text conversion did not return ASCII text")
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Conversion failed: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
