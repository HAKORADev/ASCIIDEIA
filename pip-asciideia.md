# ASCIIDEIA PyPI Library Documentation

**The lightweight, automation-friendly ASCII art engine for Python.**

🔗 **PyPI Package:** [asciideia](https://pypi.org/project/asciideia/)
📦 **Install:** `pip install asciideia`
🐍 **Python:** 3.8+ required
📖 **Source Code:** [HAKORADev/ASCIIDEIA](https://github.com/HAKORADev/ASCIIDEIA) (GUI/CLI version)
🔄 **Version:** 0.0.1+ (API stable)

---

## Why This Library Exists

While the [main ASCIIDEIA repository](https://github.com/HAKORADev/ASCIIDEIA) provides a full-featured interactive terminal application with real-time playback controls, keyboard navigation, and audio sync, this PyPI distribution strips away the interactive layer to give you **pure processing power** that integrates anywhere. No terminal handling, no keyboard listeners, no screen management — just the core ASCII conversion and rendering algorithms accessible via Python API or CLI.

**Use this when:**
- Building automated pipelines or batch ASCII art generators
- Integrating ASCII art conversion into web apps, bots, or AI agents
- Creating your own UI wrapper (Tkinter, web interface, desktop app)
- Running on headless servers without terminal capabilities
- Rendering ASCII art to PNG images or MP4 videos programmatically
- Converting frames in real-time from your own video processing pipeline
- You simply want to `pip install` and run commands

---

## What ASCIIDEIA Does

ASCIIDEIA is an **ASCII art conversion engine** that transforms images and videos into character-based art using multiple algorithms and color modes. It can display ASCII art in the terminal, render it to PNG images, or produce full MP4 videos with audio — all from a simple, programmatic API.

**Key Features:**
- 🎨 **3 Color Modes:** Colored (full RGB), Black & White, Grayscale
- 🔤 **3 Algorithms:** Characters, Blocks (Unicode block elements), Dots (Braille patterns)
- 🖼️ **Image Support:** PNG, JPG, BMP, WebP, TIFF, and more
- 🎬 **Video Support:** MP4, AVI, MKV, MOV, WebM, and more
- 📺 **2 Render Modes:** Modern (high-detail filter-like), Retro (visible ASCII character grid)
- 🌑 **2 Background Modes:** Dark (skip dark pixels, black background), Transparent (show all pixels)
- 🔗 **URL Downloads:** YouTube and TikTok video download support via yt-dlp
- 🎵 **Audio Preservation:** Extract and preserve audio from source videos
- ⚡ **Headless Operation:** No terminal or GUI dependencies for rendering
- 🔧 **Automation Ready:** Simple API for scripting and integration

---

## Installation & Dependencies

### Basic Installation
```bash
pip install asciideia
```

### System Dependencies

**FFmpeg (Optional but Recommended)**
- **Why:** Required for video rendering (MP4 output) and audio extraction
- **Without it:** Image conversion and terminal display work fine, but video rendering is disabled
- **Install:**
  ```bash
  # Windows
  winget install FFmpeg

  # macOS
  brew install ffmpeg

  # Linux (Ubuntu/Debian)
  sudo apt install ffmpeg

  # Linux (Fedora/RHEL)
  sudo dnf install ffmpeg
  ```

**yt-dlp (Optional)**
- **Why:** Required only for downloading videos from YouTube or TikTok URLs
- **Without it:** URL download features are disabled; local files work fine
- **Install:**
  ```bash
  pip install yt-dlp
  ```

**Python Dependencies (Auto-installed):**
- `opencv-python` (>=4.5.0) — Core image/video processing and frame extraction
- `numpy` (>=1.21.0) — High-performance array operations for character mapping
- `Pillow` (>=9.0.0) — Image rendering, PNG export, and font handling

**No GUI Dependencies:** Unlike the source version, this doesn't require any terminal interaction libraries, making it ideal for server environments and automated pipelines.

---

## Core API Reference

### Constants

#### Algorithm Modes
| Constant | Value | Description |
|----------|-------|-------------|
| `ALGO_CHARS` | `'chars'` | Standard ASCII characters (70-character ramp) |
| `ALGO_BLOCKS` | `'blocks'` | Unicode block elements (░▒▓█) |
| `ALGO_DOTS` | `'dots'` | Braille dot patterns (8-dot cells) |
| `ALGORITHM_MODES` | `['chars', 'blocks', 'dots']` | List of all valid algorithm modes |
| `ALGORITHM_RAMPS` | dict | Maps each algorithm to its character ramp string |

#### Color Modes
| Constant | Value | Description |
|----------|-------|-------------|
| `COLOR_COLORED` | `'colored'` | Full 24-bit RGB color with ANSI escape codes |
| `COLOR_BW` | `'bw'` | Pure black and white, no color codes |
| `COLOR_GRAY` | `'gray'` | Grayscale with ANSI color codes |
| `COLOR_MODES` | `['colored', 'bw', 'gray']` | List of all valid color modes |

#### Render Modes
| Constant | Value | Description |
|----------|-------|-------------|
| `RENDER_MODERN` | `'modern'` | Full resolution, filter-like detail (7x14 char cells) |
| `RENDER_RETRO` | `'retro'` | Small character grid, visible ASCII characters (10x20 char cells) |
| `RENDER_MODES` | `['modern', 'retro']` | List of all valid render modes |

#### Background Modes
| Constant | Value | Description |
|----------|-------|-------------|
| `BG_DARK` | `'dark'` | Black background; dark pixels below threshold are replaced with spaces |
| `BG_NONE` | `'none'` | No background; all pixels including dark ones are rendered as characters |
| `BG_MODES` | `['dark', 'none']` | List of all valid background modes |
| `DARK_THRESHOLD` | `12` | Brightness threshold below which pixels are treated as dark (0-255) |

#### File Extension Sets
| Constant | Contents |
|----------|----------|
| `IMAGE_EXTENSIONS` | `{'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.tif', '.ico', '.ppm', '.pgm', '.pbm'}` |
| `VIDEO_EXTENSIONS` | `{'.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv', '.gif'}` |

---

### High-Level API Functions

#### `render_image(path, output_dir=None, color='colored', algo='chars', render_mode='modern', bg='dark', width=None)`

Converts an image file to ASCII art and optionally renders it to a PNG file. This is the primary function for image processing.

**Parameters:**

| Parameter | Type | Default | Description | Valid Values |
|-----------|------|---------|-------------|--------------|
| `path` | str | **Required** | Path to the image file | Any valid image file path (jpg, png, bmp, webp, tiff, etc.) |
| `output_dir` | str | None | Output directory for PNG rendering | Any writable directory path; if `None`, returns ASCII string only |
| `color` | str | `'colored'` | Color mode | `'colored'`, `'bw'`, `'gray'` (also accepts aliases like `'colour'`, `'black'`, `'grey'`, `'grayscale'`) |
| `algo` | str | `'chars'` | Algorithm mode | `'chars'`, `'blocks'`, `'dots'` (also accepts `'c'`, `'b'`, `'d'`, `'characters'`, `'braille'`) |
| `render_mode` | str | `'modern'` | Render quality mode | `'modern'`, `'retro'` (also accepts `'m'`, `'r'`, `'1'`, `'2'`) |
| `bg` | str | `'dark'` | Background mode | `'dark'`, `'none'` (also accepts `'black'`, `'d'`, `'transparent'`, `'n'`) |
| `width` | int | None | ASCII output width in characters | Any positive integer; if `None`, auto-calculated from terminal size and image dimensions |

**Returns:**
- If `output_dir` is `None`: `str` — The ASCII art string (with ANSI color codes if colored/gray)
- If `output_dir` is provided: `str` — Absolute path to the rendered PNG file

**Raises:**
- `FileNotFoundError` — If the image file doesn't exist
- `RuntimeError` — If the image cannot be converted

---

#### `render_video(path, output_dir=None, color='colored', algo='chars', render_mode='modern', bg='dark', width=None)`

Converts a video file to an ASCII art MP4 video. Extracts audio from the source if available and includes it in the output.

**Parameters:**

| Parameter | Type | Default | Description | Valid Values |
|-----------|------|---------|-------------|--------------|
| `path` | str | **Required** | Path to the video file | Any valid video file path (mp4, avi, mkv, mov, webm, etc.) |
| `output_dir` | str | None | Output directory for MP4 rendering | Any writable directory path; if `None`, uses `./results` next to the source file |
| `color` | str | `'colored'` | Color mode | Same as `render_image` |
| `algo` | str | `'chars'` | Algorithm mode | Same as `render_image` |
| `render_mode` | str | `'modern'` | Render quality mode | Same as `render_image` |
| `bg` | str | `'dark'` | Background mode | Same as `render_image` |
| `width` | int | None | ASCII output width in characters | Any positive integer; if `None`, auto-calculated from terminal size and video dimensions |

**Returns:** `str` — Absolute path to the rendered MP4 file

**Raises:**
- `FileNotFoundError` — If the video file doesn't exist
- `RuntimeError` — If the video metadata cannot be read or rendering fails

---

#### `convert_image(path, color='colored', algo='chars', bg='dark', width=None)`

Converts an image file to an ASCII art string. Lightweight version of `render_image` that only returns the ASCII string without any file rendering.

**Parameters:**

| Parameter | Type | Default | Description | Valid Values |
|-----------|------|---------|-------------|--------------|
| `path` | str | **Required** | Path to the image file | Any valid image file path |
| `color` | str | `'colored'` | Color mode | Same as `render_image` |
| `algo` | str | `'chars'` | Algorithm mode | Same as `render_image` |
| `bg` | str | `'dark'` | Background mode | Same as `render_image` |
| `width` | int | None | ASCII output width in characters | Any positive integer; if `None`, auto-calculated |

**Returns:** `str` — The ASCII art string (with ANSI escape codes for colored/gray modes)

**Raises:**
- `FileNotFoundError` — If the image file doesn't exist

---

#### `convert_frame(frame, width, color='colored', algo='chars', bg='dark')`

Converts a raw OpenCV frame (numpy array) to an ASCII art string. Ideal for integrating into custom video processing pipelines where you already have frames in memory.

**Parameters:**

| Parameter | Type | Default | Description | Valid Values |
|-----------|------|---------|-------------|--------------|
| `frame` | numpy.ndarray | **Required** | OpenCV BGR frame (shape: HxWx3) | Any valid numpy array from `cv2.imread()` or `cv2.VideoCapture.read()` |
| `width` | int | **Required** | ASCII output width in characters | Any positive integer |
| `color` | str | `'colored'` | Color mode | Same as `render_image` |
| `algo` | str | `'chars'` | Algorithm mode | Same as `render_image` |
| `bg` | str | `'dark'` | Background mode | Same as `render_image` |

**Returns:** `str` — The ASCII art string (with ANSI escape codes for colored/gray modes)

---

### URL & Download Functions

#### `is_url(text)`

Checks if a string matches a supported URL pattern (YouTube or TikTok).

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | str | **Required** | The string to check |

**Returns:** `bool` — `True` if the text matches a YouTube or TikTok URL pattern

---

#### `detect_platform(url)`

Detects which platform a URL belongs to.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | **Required** | The URL to check |

**Returns:** `str | None` — `'youtube'`, `'tiktok'`, or `None` if not recognized

---

#### `download_video(url)`

Downloads a video from a YouTube or TikTok URL using yt-dlp. The video is saved to a temporary directory and the file path is returned.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | **Required** | YouTube or TikTok video URL |

**Returns:** `tuple[str, str]` — `(file_path, title)` of the downloaded video

**Raises:**
- `RuntimeError` — If yt-dlp is not installed or the download fails

---

### Low-Level Core Functions

#### `frame_to_ascii(frame, width, color_mode, algorithm, bg='dark')`

Converts a raw OpenCV BGR frame to an ASCII art string. This is the core conversion engine used by all higher-level functions.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frame` | numpy.ndarray | **Required** | OpenCV BGR frame (HxWx3) |
| `width` | int | **Required** | ASCII output width in characters |
| `color_mode` | str | **Required** | One of `COLOR_COLORED`, `COLOR_BW`, `COLOR_GRAY` |
| `algorithm` | str | **Required** | One of `ALGO_CHARS`, `ALGO_BLOCKS`, `ALGO_DOTS` |
| `bg` | str | `'dark'` | One of `BG_DARK`, `BG_NONE` |

**Returns:** `str` — The ASCII art string

---

#### `image_to_ascii(image_path, width, color_mode='colored', algorithm='chars', bg='dark')`

Loads an image from disk and converts it to ASCII art.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_path` | str | **Required** | Path to the image file |
| `width` | int | **Required** | ASCII output width in characters |
| `color_mode` | str | `'colored'` | Color mode constant |
| `algorithm` | str | `'chars'` | Algorithm mode constant |
| `bg` | str | `'dark'` | Background mode constant |

**Returns:** `str` — The ASCII art string

**Raises:**
- `FileNotFoundError` — If the image file cannot be read

---

#### `ascii_to_rgb_image(ascii_frame, has_ansi, char_w=7, char_h=14, font_size=12, render_mode='modern', bg='dark')`

Renders an ASCII art string to an RGB (or RGBA) numpy array image. Uses Pillow to draw characters onto an image canvas with a monospace font.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ascii_frame` | str | **Required** | The ASCII art string (may contain ANSI codes) |
| `has_ansi` | bool | **Required** | Whether the string contains ANSI color codes |
| `char_w` | int | `7` | Character width in pixels |
| `char_h` | int | `14` | Character height in pixels |
| `font_size` | int | `12` | Font size in points |
| `render_mode` | str | `'modern'` | `'modern'` or `'retro'` (overrides char_w, char_h, font_size) |
| `bg` | str | `'dark'` | Background mode (`'dark'` or `'none'`) |

**Returns:** `numpy.ndarray` — RGB image array (HxWx3) or RGBA (HxWx4) if `bg='none'`

---

#### `render_png(ascii_frame, output_path, has_ansi, render_mode='modern', bg='dark')`

Renders an ASCII art string and saves it as a PNG image file.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ascii_frame` | str | **Required** | The ASCII art string |
| `output_path` | str | **Required** | Output file path for the PNG |
| `has_ansi` | bool | **Required** | Whether the string contains ANSI codes |
| `render_mode` | str | `'modern'` | `'modern'` or `'retro'` |
| `bg` | str | `'dark'` | Background mode |

**Returns:** `str` — The output file path

---

#### `render_mp4(video_path, media_width, color_mode, algorithm, fps, audio_path, output_path, render_mode='modern', bg='dark')`

Renders a full video as an ASCII art MP4 video. Processes each frame individually and pipes raw RGB data to FFmpeg for encoding.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `video_path` | str | **Required** | Path to the source video |
| `media_width` | int | **Required** | ASCII width in characters |
| `color_mode` | str | **Required** | Color mode constant |
| `algorithm` | str | **Required** | Algorithm mode constant |
| `fps` | float | **Required** | Output frame rate |
| `audio_path` | str | **Required** | Path to extracted audio WAV file, or `None` |
| `output_path` | str | **Required** | Output MP4 file path |
| `render_mode` | str | `'modern'` | `'modern'` or `'retro'` |
| `bg` | str | `'dark'` | Background mode |

**Returns:** `str | None` — The output file path on success, or `None` on failure

---

### Utility Functions

#### `get_video_metadata(path)`

Extracts metadata from a video file using OpenCV and ffprobe.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | Path to the video file |

**Returns:** `dict | None` — Dictionary with keys: `fps`, `total_frames`, `width`, `height`, `duration`; or `None` on failure

---

#### `get_image_metadata(path)`

Extracts metadata from an image file using Pillow.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | Path to the image file |

**Returns:** `dict | None` — Dictionary with keys: `width`, `height`, `format`; or `None` on failure

---

#### `has_audio_track(path)`

Checks whether a video file contains an audio track.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | str | Path to the video file |

**Returns:** `bool` — `True` if an audio track is detected

---

#### `extract_audio(video_path, output_path)`

Extracts the audio track from a video file and saves it as a 16-bit PCM WAV file at 44100 Hz stereo.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_path` | str | Path to the source video |
| `output_path` | str | Output WAV file path |

**Returns:** `bool` — `True` if extraction succeeded

---

#### `compute_display_width_for_terminal(src_w, src_h)`

Calculates the optimal ASCII width for a given image/video resolution, fitting within the current terminal dimensions.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `src_w` | int | Source image/video width in pixels |
| `src_h` | int | Source image/video height in pixels |

**Returns:** `int` — Recommended ASCII width in characters

---

#### `compute_ascii_height(ascii_width, orig_w, orig_h)`

Calculates the ASCII art height given a width and the original image dimensions.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ascii_width` | int | ASCII width in characters |
| `orig_w` | int | Original image width in pixels |
| `orig_h` | int | Original image height in pixels |

**Returns:** `int` — Corresponding ASCII height in character rows

---

#### `generate_output_name(media_type, original_name, color_mode, algorithm, extension)`

Generates a unique output filename with timestamp and parameter info.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `media_type` | str | `'image'` or `'video'` |
| `original_name` | str | Original filename (without extension) |
| `color_mode` | str | Color mode used |
| `algorithm` | str | Algorithm used |
| `extension` | str | File extension (e.g., `'png'`, `'mp4'`) |

**Returns:** `str` — Formatted filename like `ASCIIDEIA_image_photo_colored_chars_1700000000.png`

---

#### `format_time(seconds)`

Formats seconds into MM:SS string.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `seconds` | float | Duration in seconds |

**Returns:** `str` — Formatted time string (e.g., `'03:45'`)

---

#### `sanitize_filename(name, max_len=50)`

Sanitizes a string for use as a filename, removing special characters and truncating.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | **Required** | Raw filename string |
| `max_len` | int | `50` | Maximum filename length |

**Returns:** `str` — Sanitized filename

---

## Algorithm Details

### 🔤 **Characters** (`ALGO_CHARS`)
Uses a 70-character brightness ramp from space to `$`, mapping pixel brightness to progressively denser ASCII characters. This is the classic ASCII art approach that produces recognizable text-based representations. The ramp includes symbols like `` `.'`,:;!~+-=|<>iv)/_1[]{}?clfsxzjfrnueoadqkpmygwh87654XZ#MW&8%B@$ `` ordered from lightest to darkest.

**Best for:** Traditional ASCII art, text-based displays, terminal output, recognizable representations.

### 🟫 **Blocks** (`ALGO_BLOCKS`)
Uses Unicode block elements (` ░▒▓█`) to create smooth, gradient-like transitions. Only 4 levels of density, but the block characters fill their cells completely, creating a more solid, painterly look. Works exceptionally well with colored mode where the limited brightness levels are compensated by color information.

**Best for:** Smooth gradient effects, pixel-art style, colored output, poster-like results.

### ⠿ **Dots** (`ALGO_DOTS`)
Uses Braille dot patterns (` ⠁⠃⠉⠋⠛⠟⠿⡿⣇⣗⣧⣷⣿`) to represent brightness levels. Each Braille character is an 8-dot cell, allowing fine-grained density control within a single character cell. Creates a unique, dot-matrix aesthetic that looks distinctly different from both characters and blocks.

**Best for:** Dot-matrix displays, unique visual style, fine detail at small sizes, printer-style aesthetics.

---

## Mode Details

### Color Modes

**Colored** (`COLOR_COLORED`): Each character is wrapped in ANSI 24-bit color escape codes matching the original pixel's RGB value. Automatically falls back to 256-color or 16-color modes based on terminal capabilities. Produces the most visually faithful ASCII art.

**Black & White** (`COLOR_BW`): Pure monochrome output with no color codes. Characters are selected based on brightness only, producing clean, printer-friendly output that works in any terminal or text file.

**Grayscale** (`COLOR_GRAY`): Characters are colored with grayscale ANSI codes. Combines the structural clarity of character-based brightness mapping with subtle tonal variation through color, creating a softer, more nuanced appearance than pure BW.

### Render Modes

**Modern** (`RENDER_MODERN`): Uses 7x14 pixel character cells with 12pt font. Produces high-detail, filter-like output where individual characters are small and the overall image reads clearly at a glance. Best for photorealistic results and final output.

**Retro** (`RENDER_RETRO`): Uses 10x20 pixel character cells with 18pt font. Characters are larger and individually visible, creating a classic ASCII art aesthetic where you can see and read individual characters. Fixed width of 140 characters for consistent output. Best for artistic display and text-heavy aesthetics.

### Background Modes

**Dark** (`BG_DARK`): Default mode. Uses a black background and replaces pixels below the `DARK_THRESHOLD` (brightness < 12) with space characters. Creates clean output with empty dark areas, ideal for images with dark backgrounds or high contrast. The black background makes colored characters pop vividly.

**Transparent** (`BG_NONE`): Renders all pixels including dark ones as visible characters. No pixels are replaced with spaces, so even the darkest areas of the image are represented with characters. When rendered to PNG, produces an RGBA image with transparent background. Best for overlaying ASCII art on other content or when you want full image representation.

---

## Usage Examples

### Basic Image to ASCII String
```python
import asciideia

ascii_art = asciideia.convert_image("photo.jpg", color="colored", algo="chars", bg="dark")
print(ascii_art)
```

### Render Image to PNG
```python
import asciideia

out_path = asciideia.render_image(
    path="portrait.png",
    output_dir="./output",
    color="colored",
    algo="blocks",
    render_mode="modern",
    bg="dark"
)
print(f"Saved to: {out_path}")
```

### Render Image with Transparent Background
```python
import asciideia

out_path = asciideia.render_image(
    path="logo.png",
    output_dir="./output",
    color="colored",
    algo="chars",
    render_mode="modern",
    bg="none"
)
print(f"Transparent PNG: {out_path}")
```

### Render Video to MP4
```python
import asciideia

out_path = asciideia.render_video(
    path="clip.mp4",
    output_dir="./ascii_videos",
    color="colored",
    algo="chars",
    render_mode="modern",
    bg="dark"
)
print(f"Video saved to: {out_path}")
```

### Retro Style Black & White Image
```python
import asciideia

out_path = asciideia.render_image(
    path="landscape.jpg",
    output_dir="./retro_output",
    color="bw",
    algo="chars",
    render_mode="retro",
    bg="dark"
)
print(f"Retro ASCII art: {out_path}")
```

### Process a Single Frame from OpenCV
```python
import cv2
import asciideia

cap = cv2.VideoCapture("video.mp4")
ret, frame = cap.read()
if ret:
    ascii_art = asciideia.convert_frame(frame, width=80, color="colored", algo="dots", bg="dark")
    print(ascii_art)
cap.release()
```

### Download and Convert YouTube Video
```python
import asciideia

video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

if asciideia.is_url(video_url):
    platform = asciideia.detect_platform(video_url)
    print(f"Detected platform: {platform}")

    file_path, title = asciideia.download_video(video_url)
    print(f"Downloaded: {title}")

    out_path = asciideia.render_video(
        path=file_path,
        output_dir="./youtube_ascii",
        color="colored",
        algo="blocks",
        bg="dark"
    )
    print(f"ASCII video: {out_path}")
```

### Batch Process Multiple Images
```python
import os
import asciideia

input_dir = "./photos"
output_dir = "./ascii_art"
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    ext = os.path.splitext(filename)[1].lower()
    if ext in asciideia.IMAGE_EXTENSIONS:
        filepath = os.path.join(input_dir, filename)
        print(f"Converting: {filename}")

        out = asciideia.render_image(
            path=filepath,
            output_dir=output_dir,
            color="colored",
            algo="chars",
            render_mode="modern",
            bg="dark"
        )
        print(f"  -> {out}")
```

### Custom Width and All Algorithms
```python
import asciideia

image_path = "photo.jpg"
output_dir = "./all_algos"

for algo in asciideia.ALGORITHM_MODES:
    out = asciideia.render_image(
        path=image_path,
        output_dir=output_dir,
        color="colored",
        algo=algo,
        render_mode="modern",
        bg="dark",
        width=120
    )
    print(f"{algo}: {out}")
```

### Get Video Metadata Before Rendering
```python
import asciideia

video_path = "movie.mp4"
meta = asciideia.get_video_metadata(video_path)

if meta:
    print(f"Resolution: {meta['width']}x{meta['height']}")
    print(f"FPS: {meta['fps']:.1f}")
    print(f"Duration: {asciideia.format_time(meta['duration'])}")
    print(f"Total frames: {meta['total_frames']}")

    has_audio = asciideia.has_audio_track(video_path)
    print(f"Audio: {'Yes' if has_audio else 'No'}")

    out = asciideia.render_video(
        path=video_path,
        output_dir="./output",
        color="colored",
        algo="blocks",
        bg="dark"
    )
```

---

## Command Line Usage

After installation, the `asciideia` command is available globally.

### Interactive Mode (Wizard)
```bash
asciideia
```
Launches a step-by-step wizard prompting for media type, file path, color mode, algorithm, render mode, background mode, and output directory with validation and auto-detection.

### Direct Command Execution (Oneline Mode)
```bash
# Basic syntax
asciideia <mode> <path> [flags]

# Image to terminal display
asciideia image photo.png

# Video to terminal display
asciideia video clip.mp4

# Image with custom settings, render to PNG
asciideia image photo.png color bw algo blocks render ./output

# Video with retro render and transparent background
asciideia video clip.mp4 rm retro bg none render ./out

# Image with dots algorithm
asciideia i photo.png algo dots bg dark

# Video with grayscale and blocks
asciideia v clip.mp4 color gray algo blocks

# Download and convert YouTube video
asciideia video "https://www.youtube.com/watch?v=dQw4w9WgXcQ" render ./output

# Show help
asciideia help
```

### Command Line Flags
| Flag | Aliases | Description | Valid Values |
|------|---------|-------------|--------------|
| `color` | `c` | Color mode | `colored`, `bw`, `gray` |
| `algo` | `a`, `algorithm` | Algorithm mode | `chars`, `blocks`, `dots` |
| `render` | `r` | Render to folder (omit for terminal display) | Any directory path |
| `render_mode` | `rm`, `rendition` | Render quality | `modern`, `retro` |
| `bg` | `background` | Background mode | `dark`, `none` |

### Mode Shortcuts
| Mode | Shortcuts |
|------|-----------|
| `image` | `i`, `img` |
| `video` | `v`, `vid` |

---

## Advanced Integration Examples

### 1. Build Your Own GUI Wrapper

**Tkinter Example:**
```python
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import asciideia
import threading
import os

class AsciideiaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ASCIIDEIA Custom GUI")
        self.root.geometry("500x450")

        self.file_path = tk.StringVar()
        self.output_dir = tk.StringVar(value="./output")
        self.color_mode = tk.StringVar(value="colored")
        self.algorithm = tk.StringVar(value="chars")
        self.render_mode = tk.StringVar(value="modern")
        self.bg_mode = tk.StringVar(value="dark")
        self.width_var = tk.IntVar(value=0)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Image/Video File:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(self.root, textvariable=self.file_path, width=40).grid(row=0, column=1, padx=5)
        tk.Button(self.root, text="Browse", command=self.browse_file).grid(row=0, column=2)

        tk.Label(self.root, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(self.root, textvariable=self.output_dir, width=40).grid(row=1, column=1, padx=5)

        tk.Label(self.root, text="Color Mode:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self.root, textvariable=self.color_mode,
                     values=["colored", "bw", "gray"]).grid(row=2, column=1, sticky="w", padx=5)

        tk.Label(self.root, text="Algorithm:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self.root, textvariable=self.algorithm,
                     values=["chars", "blocks", "dots"]).grid(row=3, column=1, sticky="w", padx=5)

        tk.Label(self.root, text="Render Mode:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self.root, textvariable=self.render_mode,
                     values=["modern", "retro"]).grid(row=4, column=1, sticky="w", padx=5)

        tk.Label(self.root, text="Background:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        ttk.Combobox(self.root, textvariable=self.bg_mode,
                     values=["dark", "none"]).grid(row=5, column=1, sticky="w", padx=5)

        tk.Label(self.root, text="Width (0=auto):").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        tk.Spinbox(self.root, from_=0, to=500, textvariable=self.width_var, width=10).grid(row=6, column=1, sticky="w", padx=5)

        tk.Button(self.root, text="Render", command=self.process,
                  bg="green", fg="white", padx=20).grid(row=7, column=1, pady=20)

        self.status = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=8, column=0, columnspan=3, sticky="ew", padx=10, pady=5)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("All files", "*.*"), ("Images", "*.jpg *.png *.jpeg *.bmp *.webp"),
                       ("Videos", "*.mp4 *.avi *.mkv *.mov *.webm")]
        )
        if filename:
            self.file_path.set(filename)

    def process(self):
        if not self.file_path.get():
            messagebox.showerror("Error", "Please select a file")
            return

        self.status.config(text="Processing...")
        path = self.file_path.get()
        out_dir = self.output_dir.get()
        color = self.color_mode.get()
        algo = self.algorithm_mode.get()
        rm = self.render_mode.get()
        bg = self.bg_mode.get()
        w = self.width_var.get() or None

        def run():
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext in asciideia.VIDEO_EXTENSIONS:
                    result = asciideia.render_video(path, out_dir, color, algo, rm, bg, w)
                else:
                    result = asciideia.render_image(path, out_dir, color, algo, rm, bg, w)
                self.root.after(0, lambda: self.status.config(text=f"Done: {result}"))
                messagebox.showinfo("Success", f"Output: {result}")
            except Exception as e:
                self.root.after(0, lambda: self.status.config(text=f"Error: {e}"))
                messagebox.showerror("Error", str(e))

        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AsciideiaApp(root)
    root.mainloop()
```

**Web Interface (Flask API):**
```python
from flask import Flask, request, jsonify, send_file
import asciideia
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

@app.route('/api/convert', methods=['POST'])
def convert_api():
    try:
        data = request.json
        file_path = data.get('file_path')

        if not file_path:
            return jsonify({"error": "Missing file_path"}), 400

        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        os.makedirs(output_dir, exist_ok=True)

        ext = os.path.splitext(file_path)[1].lower()
        color = data.get('color', 'colored')
        algo = data.get('algo', 'chars')
        render_mode = data.get('render_mode', 'modern')
        bg = data.get('bg', 'dark')
        width = data.get('width')

        if ext in asciideia.VIDEO_EXTENSIONS:
            result = asciideia.render_video(file_path, output_dir, color, algo, render_mode, bg, width)
        else:
            result = asciideia.render_image(file_path, output_dir, color, algo, render_mode, bg, width)

        return jsonify({
            "success": True,
            "output_path": result,
            "download_url": f"/api/download/{os.path.basename(output_dir)}/{os.path.basename(result)}"
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/metadata', methods=['POST'])
def metadata_api():
    try:
        data = request.json
        file_path = data.get('file_path')
        ext = os.path.splitext(file_path)[1].lower()

        if ext in asciideia.VIDEO_EXTENSIONS:
            meta = asciideia.get_video_metadata(file_path)
            if meta:
                meta['has_audio'] = asciideia.has_audio_track(file_path)
        else:
            meta = asciideia.get_image_metadata(file_path)

        return jsonify({"success": True, "metadata": meta})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/download/<dir_name>/<file_name>')
def download_file(dir_name, file_name):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], dir_name, file_name)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000)
```

### 2. AI Agent Skill / Automation Tool

**AI Pipeline Integration:**
```python
import asciideia
import time
import os

class AsciideiaSkill:
    def __init__(self, workspace_dir="./ascii_workspace"):
        self.workspace_dir = workspace_dir
        os.makedirs(workspace_dir, exist_ok=True)

    def convert_image(self, image_path: str,
                      color: str = "colored",
                      algo: str = "chars",
                      bg: str = "dark") -> dict:
        timestamp = int(time.time())
        output_dir = f"{self.workspace_dir}/{timestamp}"

        try:
            result = asciideia.render_image(
                path=image_path,
                output_dir=output_dir,
                color=color,
                algo=algo,
                render_mode="modern",
                bg=bg
            )

            return {
                "success": True,
                "output_path": result,
                "output_dir": output_dir,
                "color": color,
                "algorithm": algo,
                "background": bg,
                "timestamp": timestamp
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": timestamp
            }

    def convert_video(self, video_path: str,
                      color: str = "colored",
                      algo: str = "blocks",
                      bg: str = "dark") -> dict:
        timestamp = int(time.time())
        output_dir = f"{self.workspace_dir}/{timestamp}"

        try:
            result = asciideia.render_video(
                path=video_path,
                output_dir=output_dir,
                color=color,
                algo=algo,
                render_mode="modern",
                bg=bg
            )

            return {
                "success": True,
                "output_path": result,
                "output_dir": output_dir,
                "color": color,
                "algorithm": algo,
                "background": bg,
                "timestamp": timestamp
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": timestamp
            }

    def batch_convert(self, file_paths: list,
                      color: str = "colored",
                      algo: str = "chars",
                      bg: str = "dark") -> list:
        results = []
        for i, path in enumerate(file_paths):
            ext = os.path.splitext(path)[1].lower()
            if ext in asciideia.VIDEO_EXTENSIONS:
                result = self.convert_video(path, color, algo, bg)
            else:
                result = self.convert_image(path, color, algo, bg)
            results.append({"file": path, "result": result})
            print(f"Processed {i+1}/{len(file_paths)}")
        return results
```

**Discord Bot Integration:**
```python
import discord
from discord.ext import commands
import asciideia
import aiohttp
import asyncio
import os

bot = commands.Bot(command_prefix="!")

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name="ascii")
async def ascii_command(ctx, algorithm: str = "blocks"):
    """Convert an attached image to ASCII art"""
    if not ctx.message.attachments:
        await ctx.send("Please attach an image!")
        return

    attachment = ctx.message.attachments[0]
    temp_path = f"temp_{attachment.filename}"

    await attachment.save(temp_path)
    await ctx.send("Converting to ASCII art...")

    def process():
        return asciideia.render_image(
            path=temp_path,
            output_dir="./discord_output",
            color="colored",
            algo=algorithm,
            render_mode="modern",
            bg="dark"
        )

    loop = asyncio.get_event_loop()
    try:
        result_path = await loop.run_in_executor(None, process)
        if result_path and os.path.exists(result_path):
            await ctx.send("Here's your ASCII art:", file=discord.File(result_path))
            os.remove(result_path)
        else:
            await ctx.send("Conversion failed.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

bot.run('YOUR_BOT_TOKEN')
```

### 3. Real-Time Video Processing Pipeline

```python
import cv2
import asciideia
import numpy as np
from PIL import Image

class RealTimeASCIIPipeline:
    def __init__(self, width=80, color="colored", algo="chars", bg="dark"):
        self.width = width
        self.color = color
        self.algo = algo
        self.bg = bg

    def process_frame(self, frame):
        ascii_art = asciideia.convert_frame(
            frame, self.width, self.color, self.algo, self.bg
        )
        return ascii_art

    def process_to_image(self, frame):
        ascii_art = asciideia.convert_frame(
            frame, self.width, self.color, self.algo, self.bg
        )
        has_ansi = self.color != "bw"
        rgb_array = asciideia.ascii_to_rgb_image(
            ascii_art, has_ansi, render_mode="modern", bg=self.bg
        )
        return rgb_array

    def process_video_stream(self, source=0):
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open video source: {source}")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                ascii_art = self.process_frame(frame)
                print(f"\033[H\033[2J{ascii_art}\033[0m")

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()

pipeline = RealTimeASCIIPipeline(width=80, color="colored", algo="blocks", bg="dark")
pipeline.process_video_stream("input.mp4")
```

### 4. Plugin Architecture for Existing Applications

```python
from typing import Dict, Any, List
import asciideia

class ASCIIDEIAPlugin:
    name = "asciideia_converter"
    version = "0.0.1"
    description = "ASCII art conversion plugin"
    supports = ["image", "video"]

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {
            "default_color": "colored",
            "default_algo": "chars",
            "default_render_mode": "modern",
            "default_bg": "dark",
            "output_dir": "./asciideia_output"
        }

    def validate_inputs(self, file_path: str) -> bool:
        import os
        return os.path.exists(file_path)

    def process(self, file_path: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        options = options or {}

        color = options.get("color", self.config["default_color"])
        algo = options.get("algo", self.config["default_algo"])
        render_mode = options.get("render_mode", self.config["default_render_mode"])
        bg = options.get("bg", self.config["default_bg"])
        width = options.get("width")
        output_dir = options.get("output_dir", self.config["output_dir"])

        try:
            import uuid
            out_dir = f"{output_dir}/{uuid.uuid4().hex[:8]}"
            os.makedirs(out_dir, exist_ok=True)

            ext = os.path.splitext(file_path)[1].lower()
            if ext in asciideia.VIDEO_EXTENSIONS:
                result = asciideia.render_video(
                    file_path, out_dir, color, algo, render_mode, bg, width
                )
            else:
                result = asciideia.render_image(
                    file_path, out_dir, color, algo, render_mode, bg, width
                )

            return {
                "success": True,
                "output_path": result,
                "output_dir": out_dir,
                "parameters": {"color": color, "algo": algo, "render_mode": render_mode, "bg": bg},
                "input_file": file_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "parameters": {"color": color, "algo": algo, "render_mode": render_mode, "bg": bg}
            }

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "color_modes": asciideia.COLOR_MODES,
            "algorithms": asciideia.ALGORITHM_MODES,
            "render_modes": asciideia.RENDER_MODES,
            "background_modes": asciideia.BG_MODES,
            "image_extensions": list(asciideia.IMAGE_EXTENSIONS),
            "video_extensions": list(asciideia.VIDEO_EXTENSIONS),
            "url_support": True,
            "audio_preservation": True
        }

pipeline = MediaPipeline()
pipeline.register_plugin("asciideia", ASCIIDEIAPlugin())
result = pipeline.process_with_plugin(
    "asciideia",
    file_path="photo.jpg",
    options={"algo": "dots", "bg": "none", "color": "gray"}
)
```

---

## Performance Characteristics & Optimization

### Resource Usage

**CPU Usage:**
- Single-threaded, CPU-bound processing
- Image conversion is fast (typically under 1 second)
- Video rendering is the bottleneck — each frame requires ASCII conversion + Pillow rendering
- No GPU acceleration (runs on any CPU)

**Memory Requirements:**
- Image processing: minimal RAM (~50-200 MB depending on width)
- Video processing: RAM scales with resolution and number of parallel processes
- Peak memory during video rendering: ~2x the rendered frame size per frame

**Storage Requirements:**
- PNG output: typically 100 KB - 5 MB depending on dimensions and complexity
- MP4 output: typically 1-50 MB per minute of video at standard resolutions
- Temporary WAV audio files during video rendering (~10 MB per minute)

### Processing Time Estimates

| Task | Width | Estimated Time | Notes |
|------|-------|----------------|-------|
| Image to ASCII string | 80 chars | <0.1 seconds | Near-instant |
| Image to PNG (modern) | 120 chars | 0.5-2 seconds | Depends on font rendering |
| Image to PNG (retro) | 140 chars | 1-3 seconds | Larger character cells |
| Video to MP4 (1 min) | 80 chars | 30-90 seconds | Per-frame ASCII + render |
| Video to MP4 (1 min) | 120 chars | 60-180 seconds | Higher resolution rendering |
| Video with audio | 80 chars | +5-10% overhead | Audio extraction + muxing |

**Factors affecting speed:**
- CPU speed (single core performance)
- Output width (more characters = more work)
- Render mode (retro uses larger font but same char count)
- Color mode (colored requires per-character color computation)
- Video length and frame rate
- FFmpeg encoding speed (preset: medium)

### Optimization Tips

```python
import asciideia

# Use smaller width for faster processing
result = asciideia.render_image(path, output_dir, width=60)

# BW mode is fastest (no color computation)
result = asciideia.render_image(path, output_dir, color="bw")

# Blocks algorithm is faster than chars (fewer characters to map)
result = asciideia.render_image(path, output_dir, algo="blocks")

# For video, extract metadata first to validate before rendering
meta = asciideia.get_video_metadata(video_path)
if meta and meta['duration'] < 600:  # Skip videos longer than 10 minutes
    result = asciideia.render_video(video_path, output_dir)
```

---

## Troubleshooting & Common Issues

### Installation Problems

**"No module named 'asciideia'"**
```bash
# Solution 1: Reinstall in current environment
pip uninstall asciideia
pip install asciideia

# Solution 2: Check Python environment
python -c "import sys; print(sys.executable)"
pip --version

# Solution 3: Install with verbose output
pip install asciideia -v
```

**"Failed building wheel for opencv-python"**
```bash
# Install pre-built binaries
pip install --upgrade pip
pip install opencv-python-headless

# Or use conda:
conda install -c conda-forge opencv
```

### Runtime Errors

**"FFmpeg not found" when rendering video**
```python
# Option 1: Install FFmpeg (recommended)
# See installation section above

# Option 2: Use image conversion only (no FFmpeg needed)
ascii_art = asciideia.convert_image("photo.jpg", color="colored", algo="chars", bg="dark")

# Option 3: Check FFmpeg availability
import subprocess
try:
    subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    print("FFmpeg available")
except FileNotFoundError:
    print("FFmpeg not installed - video rendering disabled")
```

**"yt-dlp is required for URL downloads"**
```python
# Install yt-dlp
pip install yt-dlp

# Or catch the error gracefully
try:
    path, title = asciideia.download_video(url)
except RuntimeError as e:
    print(f"Download failed: {e}")
    print("Install yt-dlp: pip install yt-dlp")
```

**"Cannot read image" or FileNotFoundError**
```python
import os

# Always check file exists before processing
path = "photo.jpg"
if not os.path.isfile(path):
    print(f"File not found: {path}")

# Use expanduser for home directory paths
path = os.path.expanduser("~/photos/image.png")
result = asciideia.render_image(path, "./output")
```

**"Cannot read video metadata"**
```python
# Validate video file before rendering
meta = asciideia.get_video_metadata(video_path)
if meta is None:
    print("Cannot read video - check file format and FFmpeg installation")
else:
    print(f"Video OK: {meta['width']}x{meta['height']} @ {meta['fps']:.1f} FPS")
```

**ANSI color codes appearing in saved text files**
```python
# BW mode produces clean text without ANSI codes
ascii_art = asciideia.convert_image("photo.jpg", color="bw", algo="chars", bg="dark")
with open("output.txt", "w") as f:
    f.write(ascii_art)
```

**Output PNG has black background when I want transparency**
```python
# Use bg="none" for transparent background
result = asciideia.render_image(
    path="logo.png",
    output_dir="./output",
    bg="none"
)
# Output will be RGBA PNG with transparent background
```

---

## Version Compatibility & Migration

### Current Version: 0.0.1
- **API Stability:** All public functions and constants maintain backward compatibility
- **Output Consistency:** Identical results to source ASCIIDEIA v0.6.1 with same parameters
- **Dependencies:** Locked to compatible versions of OpenCV, NumPy, Pillow

### Upgrading
```bash
# Safe to upgrade within 0.x.x
pip install --upgrade asciideia

# Check version
python -c "import asciideia; print('ASCIIDEIA loaded')"
```

### Migration Notes

**From standalone script to PyPI library:**
- Replace `import asciideia` (was a single script) with `pip install asciideia`
- Use `asciideia.render_image()` instead of running the script interactively
- Use `asciideia.convert_image()` for string-only output
- Use `asciideia.convert_frame()` for in-memory frame processing
- Handle return values instead of relying on terminal display

**From interactive to programmatic usage:**
- Remove terminal interaction code
- Use API functions with explicit parameters instead of interactive prompts
- Handle exceptions explicitly instead of relying on error prints
- Implement your own progress tracking for long video renders

---

## Support & Community

- **GitHub Issues:** [HAKORADev/ASCIIDEIA/issues](https://github.com/HAKORADev/ASCIIDEIA/issues)
- **PyPI Page:** [pypi.org/project/asciideia](https://pypi.org/project/asciideia/)
- **Documentation:** This document is the primary API documentation

**Reporting Issues:**
When reporting issues, include:
1. Python version: `python --version`
2. ASCIIDEIA version: `pip show asciideia`
3. Complete error traceback
4. Example code that reproduces the issue
5. Input file type and size

**Feature Requests:**
Submit via GitHub issues. Popular requests may be implemented in future versions.

---

## License & Attribution

ASCIIDEIA PyPI Library is released under the MIT License.

**Attribution:**
If you use ASCIIDEIA in your project, consider:
- Mentioning ASCIIDEIA in your documentation
- Linking to the GitHub repository
- Sharing your ASCII art creations with the community

**Commercial Use:**
Allowed without restrictions under MIT License.

---

**Ready to convert?** Start with:
```bash
pip install asciideia
python -c "import asciideia; print('ASCIIDEIA loaded successfully!')"
```

Then try the interactive mode:
```bash
asciideia
```

Or dive right into the API:
```python
import asciideia

result = asciideia.render_image("photo.jpg", "./output")
print(f"Saved to: {result}")
```
