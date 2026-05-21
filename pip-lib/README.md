# ASCIIDEIA

[![PyPI version](https://badge.fury.io/py/asciideia.svg)](https://pypi.org/project/asciideia/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ASCII Art Media Converter, Player & Renderer — Python Package**

A Python package for converting images and videos to ASCII art with multiple color modes, rendering algorithms, and export capabilities. This is the lightweight, automation-friendly version of the [full ASCIIDEIA tool](https://github.com/HAKORADev/ASCIIDEIA), designed for integration into pipelines, scripts, and other applications.

## What it does

ASCIIDEIA converts images and videos into ASCII art with real-time terminal playback, interactive controls, and standard media rendering (PNG/MP4 export). It supports multiple color modes, character algorithms, render modes, and background options.

Supported formats:
- **Images**: PNG, JPG, JPEG, BMP, WebP, TIFF, TIF, ICO, PPM, PGM, PBM
- **Video**: MP4, AVI, MKV, MOV, WebM, FLV, WMV, M4V, MPG, MPEG, 3GP, OGV, GIF
- **URLs**: YouTube and TikTok (requires yt-dlp)

## Installation

```bash
pip install asciideia
```

Requirements: Python 3.8+, OpenCV, NumPy, Pillow. FFmpeg optional (required for video rendering and audio features).

## Usage

### As a Python Library

```python
import asciideia

# Convert an image to ASCII string
ascii_art = asciideia.convert_image("photo.png", color="colored", algo="chars", bg="dark")

# Convert a video frame (numpy array) to ASCII
ascii_art = asciideia.convert_frame(frame, width=120, color="colored", algo="blocks")

# Render image to PNG file
out_path = asciideia.render_image(
    "photo.png",
    output_dir="./output",
    color="colored",
    algo="chars",
    render_mode="modern",
    bg="dark"
)

# Render video to MP4 file
out_path = asciideia.render_video(
    "clip.mp4",
    output_dir="./output",
    color="colored",
    algo="chars",
    render_mode="modern",
    bg="dark"
)

# Get video metadata
meta = asciideia.get_video_metadata("clip.mp4")

# Check if video has audio
has_audio = asciideia.has_audio_track("clip.mp4")
```

### Command Line

```bash
# Interactive mode
asciideia

# Image to terminal
asciideia image photo.png

# Video to terminal
asciideia video clip.mp4

# With options
asciideia image photo.png color bw algo blocks bg none

# Render to file
asciideia image photo.png render ./output
asciideia video clip.mp4 color colored algo chars rm retro bg dark r ./output

# Show help
asciideia help
```

### Options

| Flag | Aliases | Values | Default |
|------|---------|--------|---------|
| `color` | `c`, `colour` | `colored`, `bw`, `gray` | `colored` |
| `algo` | `a`, `algorithm` | `chars`, `blocks`, `dots` | `chars` |
| `render` | `r` | folder path | (play in terminal) |
| `render_mode` | `rm`, `rendition` | `modern`, `retro` | `modern` |
| `bg` | `background` | `dark`, `none` | `dark` |

## GitHub Repository

For the full-featured interactive application and source code:
https://github.com/HAKORADev/ASCIIDEIA

## License

MIT License
