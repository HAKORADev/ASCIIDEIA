# ASCIIDEIA Skill for AI Agents

## Overview

ASCIIDEIA is a Python tool that converts images and videos into ASCII art, plays them in the terminal with interactive controls, and exports them as PNG or MP4 files. This skill enables AI agents to leverage ASCIIDEIA's full potential for ASCII art media generation in automated, headless, and batch-processing workflows.

The tool offers **3 color modes** (colored, bw, gray) and **3 algorithms** (chars, blocks, dots) for a total of **9 unique visual styles**. It processes local files and YouTube/TikTok URLs, runs entirely on CPU, and is fully cross-platform.

**Core Philosophy**: ASCIIDEIA is a **one-command tool** — a single CLI line does everything. For agents, the `render` flag is the primary interface: it produces a file and exits cleanly. Without `render`, the tool launches an interactive TUI that **will hang** in non-TTY environments.

---

# SECTION 1: UNDERSTANDING THE ARCHITECTURE

## What ASCIIDEIA Actually Is

ASCIIDEIA is not an AI model — it is a **deterministic conversion pipeline** that maps pixel brightness to characters from a predefined ramp, then optionally wraps those characters in ANSI color codes. Understanding this pipeline is crucial for choosing the right color mode and algorithm combination.

### The Conversion Pipeline (Image)

```
INPUT IMAGE
    │
    ▼
┌─────────────────────┐
│  OpenCV: Read Image │   cv2.imread() → BGR numpy array
└─────────┬───────────┘
          │
          ▼
┌─────────────────────────┐
│  Resize to ASCII Width  │   cv2.resize(frame, (width, height))
│  Height = W * H / W / 2 │   (/2 because chars are ~2:1 aspect ratio)
└─────────┬───────────────┘
          │
          ▼
┌─────────────────────────────────┐
│  Convert Color Spaces           │   cv2.cvtColor → grayscale + RGB
│  gray = cvtColor(BGR2GRAY)      │
│  rgb  = cvtColor(BGR2RGB)       │
└─────────┬───────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────┐
│  Compute Brightness Map                       │
│                                               │
│  colored: 0.299*R + 0.587*G + 0.114*B       │  (ITU-R BT.601 luminance)
│  bw/gray: grayscale value directly            │  (OpenCV's cvtColor)
│                                               │
│  Dark threshold: brightness < 12 → space ' '  │  (DARK_THRESHOLD = 12)
└─────────┬────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────┐
│  Map Brightness → Character from Ramp    │
│                                          │
│  index = clamp(brightness/255 * (n-1))   │
│  char = RAMP[index]                      │
│  if brightness < 12: char = ' '          │
└─────────┬───────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│  Apply Color (per character)                │
│                                             │
│  colored: \033[38;2;R;G;Bm + char + RESET  │  24-bit RGB per char
│  gray:    \033[38;2;G;G;Gm + char + RESET  │  Grayscale per char
│  bw:      char only (no escape codes)       │  Plain text
└─────────┬───────────────────────────────────┘
          │
          ▼
      ASCII ART STRING
```

### The Render Pipeline (PNG — Images)

```
ASCII ART STRING (with or without ANSI codes)
    │
    ▼
┌──────────────────────────────────────────┐
│  Parse ANSI Escape Sequences             │
│  Extract (character, R, G, B) tuples    │
│  per visible character                   │
│  (bw mode: no ANSI → all white chars)   │
└─────────┬────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────┐
│  Create PIL Image (black background)     │
│  For each char: draw.text(pos, char,    │
│      font=monospace, fill=(R,G,B))      │
│  char_w=7, char_h=14, font_size=12      │
└─────────┬────────────────────────────────┘
          │
          ▼
┌────────────────────────────┐
│  Save as PNG via PIL       │
│  pil_img.save(output_path) │
└────────────────────────────┘
```

### The Render Pipeline (MP4 — Videos)

```
VIDEO FILE
    │
    ▼
┌──────────────────────────────────────────────────┐
│  For each frame:                                 │
│    1. frame_to_ascii(frame, width, color, algo)  │
│    2. ascii_to_rgb_image(ascii_art, has_ansi)    │
│       → numpy RGB array (render_w × render_h × 3)│
│    3. Write raw RGB bytes to ffmpeg stdin pipe   │
│                                                   │
│  ffmpeg command:                                  │
│    ffmpeg -y -f rawvideo -pixel_format rgb24      │
│      -video_size WxH -framerate FPS              │
│      -i pipe:0                                    │
│      [-i audio.wav]  (if audio exists)            │
│      -c:v libx264 -preset medium -crf 23          │
│      -pix_fmt yuv420p                             │
│      [-c:a aac -b:a 128k]  (if audio exists)      │
│      output.mp4                                   │
└──────────────────────────────────────────────────┘
```

### The Interactive Player (and Why It Hangs in Non-TTY)

```
┌─────────────────────────────────────────────────────────┐
│  Interactive TUI Flow                                    │
│                                                          │
│  1. Switch to alternate screen buffer (ESC[?1049h)       │
│  2. Hide cursor (ESC[?25l)                               │
│  3. Render ASCII art to screen                           │
│  4. Start KeyListener thread (reads stdin in raw mode)   │
│  5. Main loop:                                           │
│     - Read keys from listener queue                      │
│     - 1/2/3: switch color mode, redraw                   │
│     - 4/5/6: switch algorithm, redraw                    │
│     - P: pause/resume (video)                            │
│     - J/L: seek ±5s or frame step (video)                │
│     - I/K: speed up/slow down (video)                    │
│     - S: toggle sound (video)                            │
│     - R: replay (video)                                  │
│     - Q/Esc/Enter: quit                                  │
│  6. On quit: restore cursor, exit alternate screen       │
│                                                          │
│  ⚠ WHY IT HANGS IN NON-TTY:                             │
│  - KeyListener calls termios.tcgetattr(stdin) /          │
│    tty.setcbreak(stdin) → fails without a TTY            │
│  - select.select([stdin]) blocks forever on pipes        │
│  - msvcrt.kbhit() never returns true on Windows pipes    │
│  - The main loop never receives quit key                 │
│  - Process hangs indefinitely                            │
│                                                          │
│  ✅ SOLUTION: Always use `render "path"` flag in         │
│     non-interactive/agent environments.                  │
└─────────────────────────────────────────────────────────┘
```

---

# SECTION 2: COMPLETE ONE-LINE CLI COMMANDS CATALOG

## Command Format

```
python asciideia.py <mode> <path> [color <val>] [algo <val>] [render "path"]
```

## Image Commands — All 9 Color × Algorithm Combinations

### Colored Mode (24-bit RGB)

```bash
# Colored + Chars (default, highest detail)
python asciideia.py image "photo.png" color colored algo chars

# Colored + Chars — render to PNG
python asciideia.py image "photo.png" color colored algo chars render "./output/"

# Colored + Blocks (chunky colored blocks)
python asciideia.py image "photo.png" color colored algo blocks

# Colored + Blocks — render to PNG
python asciideia.py image "photo.png" color colored algo blocks render "./output/"

# Colored + Dots (dot-matrix with color)
python asciideia.py image "photo.png" color colored algo dots

# Colored + Dots — render to PNG
python asciideia.py image "photo.png" color colored algo dots render "./output/"
```

### BW Mode (Black & White, no ANSI codes)

```bash
# BW + Chars (classic ASCII art look)
python asciideia.py image "photo.png" color bw algo chars

# BW + Chars — render to PNG
python asciideia.py image "photo.png" color bw algo chars render "./output/"

# BW + Blocks (high-contrast block art)
python asciideia.py image "photo.png" color bw algo blocks

# BW + Blocks — render to PNG
python asciideia.py image "photo.png" color bw algo blocks render "./output/"

# BW + Dots (minimalist dot art)
python asciideia.py image "photo.png" color bw algo dots

# BW + Dots — render to PNG
python asciideia.py image "photo.png" color bw algo dots render "./output/"
```

### Gray Mode (Grayscale ANSI)

```bash
# Gray + Chars (smooth grayscale detail)
python asciideia.py image "photo.png" color gray algo chars

# Gray + Chars — render to PNG
python asciideia.py image "photo.png" color gray algo chars render "./output/"

# Gray + Blocks (shaded blocks)
python asciideia.py image "photo.png" color gray algo blocks

# Gray + Blocks — render to PNG
python asciideia.py image "photo.png" color gray algo blocks render "./output/"

# Gray + Dots (subtle dot shading)
python asciideia.py image "photo.png" color gray algo dots

# Gray + Dots — render to PNG
python asciideia.py image "photo.png" color gray algo dots render "./output/"
```

### Minimal Image Commands (using defaults)

```bash
# Default: colored + chars, interactive viewer
python asciideia.py image "photo.png"

# Default: colored + chars, render to PNG
python asciideia.py image "photo.png" render "./output/"

# Using mode shortcuts
python asciideia.py i "photo.png" render "./output/"
python asciideia.py img "photo.png" render "./output/"
```

## Video Commands — All 9 Color × Algorithm Combinations (with render)

```bash
# Colored + Chars (default)
python asciideia.py video "clip.mp4" color colored algo chars render "./output/"

# Colored + Blocks
python asciideia.py video "clip.mp4" color colored algo blocks render "./output/"

# Colored + Dots
python asciideia.py video "clip.mp4" color colored algo dots render "./output/"

# BW + Chars
python asciideia.py video "clip.mp4" color bw algo chars render "./output/"

# BW + Blocks
python asciideia.py video "clip.mp4" color bw algo blocks render "./output/"

# BW + Dots
python asciideia.py video "clip.mp4" color bw algo dots render "./output/"

# Gray + Chars
python asciideia.py video "clip.mp4" color gray algo chars render "./output/"

# Gray + Blocks
python asciideia.py video "clip.mp4" color gray algo blocks render "./output/"

# Gray + Dots
python asciideia.py video "clip.mp4" color gray algo dots render "./output/"
```

### Minimal Video Commands

```bash
# Default: colored + chars, interactive player
python asciideia.py video "clip.mp4"

# Default: colored + chars, render to MP4
python asciideia.py video "clip.mp4" render "./output/"

# Using mode shortcuts
python asciideia.py v "clip.mp4" render "./output/"
python asciideia.py vid "clip.mp4" render "./output/"
```

## URL Commands

```bash
# YouTube video — render to MP4 with defaults
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" render "./output/"

# YouTube video — colored dots
python asciideia.py video "https://www.youtube.com/watch?v=dQw4w9WgXcQ" color colored algo dots render "./output/"

# YouTube Shorts
python asciideia.py video "https://www.youtube.com/shorts/abc123" color gray algo chars render "./output/"

# TikTok video
python asciideia.py video "https://www.tiktok.com/@user/video/123456789" color bw algo blocks render "./output/"

# TikTok short URL
python asciideia.py video "https://vm.tiktok.com/abc123/" render "./output/"

# URL with interactive player (requires TTY)
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color gray algo dots
```

> **Note**: URLs are only supported for video mode. Image mode does not accept URLs.

## Flag Reference Table

### Mode (Positional, Required)

| Full | Short | Shortest | Action |
|------|-------|----------|--------|
| `image` | `i` | `img` | Process as image |
| `video` | `v` | `vid` | Process as video |

### Color Flag

| Flag | Short | Accepted Values | Short Values | Maps To |
|------|-------|----------------|-------------|---------|
| `color` | `colour`, `c` | `colored` | `colour`, `color`, `all` | `colored` |
| | | `bw` | `black`, `blackwhite` | `bw` |
| | | `gray` | `grey`, `grayscale`, `greyscale` | `gray` |

**Default**: `colored`

### Algorithm Flag

| Flag | Short | Accepted Values | Short Values | Maps To |
|------|-------|----------------|-------------|---------|
| `algo` | `algorithm`, `a` | `chars` | `characters`, `c` | `chars` |
| | | `blocks` | `block`, `b` | `blocks` |
| | | `dots` | `dot`, `d`, `braille` | `dots` |

**Default**: `chars`

> **Warning**: The short value `c` for `chars` and `c` for `color` are in different flag contexts — `algo c` means "chars algorithm", `color c` is not a valid flag short form. The `c` shortcut for `color` is the *flag name* (`c bw`), not a value.

### Render Flag

| Flag | Short | Value | Behavior |
|------|-------|-------|----------|
| `render` | `r` | `"path/to/dir/"` | Render to PNG/MP4 in specified directory, then EXIT cleanly |

**Default**: Not set (launches interactive TUI)

---

# SECTION 3: COLOR MODE DETAILS

## Colored (24-bit RGB)

### How It Works
- Each pixel's RGB values are read directly from the source image
- Brightness is computed using the **ITU-R BT.601 luminance formula**: `0.299 * R + 0.587 * G + 0.114 * B`
- This luminance value selects the character from the ramp
- The original RGB color is applied as an ANSI 24-bit foreground color: `\033[38;2;R;G;Bm`
- Each character gets its own unique color

### Technical Details
- Brightness formula weighs green heaviest (human eyes are most sensitive to green)
- Brightness < 12 (DARK_THRESHOLD) → character is forced to space `' '`, regardless of algorithm
- Output contains ANSI escape sequences (not plain text)
- In render mode: ANSI sequences are parsed back to (char, R, G, B) tuples, then drawn to PIL image

### When to Use
- **Most cases** — this is the default for good reason
- Source images/videos with rich, varied colors
- When the full visual impact of the original is desired
- Presentations, demonstrations, social media exports

## BW (Black & White)

### How It Works
- Grayscale value from OpenCV's `cvtColor(BGR2GRAY)` is used directly as brightness
- Character is selected from the ramp based on this brightness
- **No ANSI color codes** are added — output is plain text characters only
- In render mode: all characters are drawn in white (255, 255, 255) on black background

### Technical Details
- Uses OpenCV's built-in grayscale conversion (also BT.601-based internally, but applied at the pixel level before brightness computation)
- Smallest output size — no escape sequences inflate the string
- Fastest to compute and render (no per-character color wrapping)
- Most compatible output (plain ASCII text, works everywhere)

### When to Use
- Classic ASCII art aesthetic — the "traditional" look
- Terminals that don't support 24-bit color
- When output needs to be copy-pasted as plain text
- Minimalist or retro visual style
- Fastest rendering for batch processing (especially video)

## Gray (Grayscale)

### How It Works
- Grayscale value from OpenCV is used for brightness (same as BW)
- The grayscale value is also applied as an ANSI color: `\033[38;2;G;G;Gm`
- Each character gets a shade of gray that matches its brightness
- Visually, the characters "fade" from dark to light in addition to using different ramp characters

### Technical Details
- Combines the character ramp variation with grayscale shading
- Double-encodes brightness: both through character shape AND through color
- Output contains ANSI escape sequences
- In render mode: ANSI sequences are parsed, each char drawn with its gray fill color

### When to Use
- When you want more visual nuance than BW but don't need full color
- When color is distracting or doesn't add meaning (e.g., documents, diagrams)
- Artistic grayscale aesthetic
- Middle ground between BW and colored

## Brightness Computation Comparison

| Color Mode | Brightness Source | Formula | Character Color |
|-----------|-------------------|---------|----------------|
| `colored` | Computed from RGB | `0.299*R + 0.587*G + 0.114*B` | Original RGB per pixel |
| `bw` | OpenCV grayscale | OpenCV's `cvtColor(BGR2GRAY)` | None (plain text) |
| `gray` | OpenCV grayscale | OpenCV's `cvtColor(BGR2GRAY)` | `(G, G, G)` per pixel |

**Key difference**: In `colored` mode, brightness is computed from the RGB channels using the luminance formula. In `bw` and `gray` modes, OpenCV's grayscale conversion is used directly. The results are very similar but may differ slightly due to implementation details. The practical impact is negligible for most content.

---

# SECTION 4: ALGORITHM DETAILS

## Chars Algorithm (67+ Levels)

### Character Ramp
```
 `.'`,:;!~+-=|<>iv)\/_1[]{}?clfsxzjfrnueoadqkpmygwh87654XZ#MW&8%B@$
```
(Dark → Light, left to right. Space character ` ` is the darkest, `$` is the lightest.)

### Technical Details
- **67 distinct brightness levels** (ramp length = 68 including space, but space is also the dark-threshold override)
- Index computation: `brightness / 255 * 66`, clamped to [0, 66]
- The ramp is ordered from "lightest visual weight" to "heaviest visual weight"
- Characters were selected and ordered based on their perceived brightness when rendered in a monospace font at typical terminal sizes
- The ramp includes a diverse set of ASCII characters: punctuation, letters, digits, and symbols
- Contains duplicate characters in the source definition (the `8` appears twice) — this is by design as part of the ramp's brightness distribution

### Visual Style
- **Highest detail** — with 67 brightness levels, fine gradients and subtle tonal differences are preserved
- Classic "ASCII art" look that most people expect
- Best for photographs, portraits, landscapes — anything with smooth gradients
- In `bw` mode: the traditional green-phosphor-terminal aesthetic

### Best Use Cases
| Use Case | Why |
|----------|-----|
| Photographs | 67 levels capture fine tonal detail |
| Portraits | Facial features need many brightness levels |
| Detailed scenes | More levels = more recognizable output |
| Default/unknown content | Always produces reasonable results |

## Blocks Algorithm (5 Levels)

### Character Ramp
```
 ░▒▓█
```
(Dark → Light: space, light shade, medium shade, dark shade, full block)

### Technical Details
- **4 distinct brightness levels** (ramp length = 5 including space, but space is also the dark-threshold override)
- Index computation: `brightness / 255 * 4`, clamped to [0, 4]
- Unicode block elements from the Block Elements Unicode block (U+2591–U+2593, U+2588)
- Very coarse brightness quantization — each level covers a wide range

### Visual Style
- **Low detail, chunky** — images look like mosaic/pixel art
- Bold, graphic quality — good for logos, icons, simple shapes
- The large character size makes each "pixel" very visible
- In `colored` mode: looks like a color mosaic or stained glass
- In `bw` mode: stark, high-contrast, posterized look

### Best Use Cases
| Use Case | Why |
|----------|-----|
| Logos and icons | Simple shapes don't need fine detail |
| High-contrast graphics | Block elements amplify contrast |
| Retro/pixel art aesthetic | Chunky blocks = pixel art vibe |
| Small source images | Low detail input doesn't benefit from more levels |
| Quick previews | Fewer levels = faster mental parsing |

## Dots Algorithm (12 Levels)

### Character Ramp
```
 ⠁⠃⠉⠋⠛⠟⠿⡿⣇⣗⣧⣷⣿
```
(Dark → Light: space, then 12 Braille patterns of increasing density)

### Technical Details
- **12 distinct brightness levels** (ramp length = 13 including space, but space is also the dark-threshold override)
- Index computation: `brightness / 255 * 12`, clamped to [0, 12]
- Unicode Braille patterns from the Braille Patterns block (U+2800–U+28FF)
- Each Braille character represents a 2×4 grid of dots, so this algorithm effectively creates a **sub-character-resolution** display — each character cell can represent 8 sub-pixels

### Visual Style
- **Medium detail, dot-matrix** — looks like a dot-matrix printer or LED display
- Unique aesthetic — the Braille dots create a stippled/dithered appearance
- In `colored` mode: resembles a color LED display or pointillist painting
- In `bw` mode: minimalist, technical, or "hacker" aesthetic
- Characters are visually lighter than blocks or chars at the same brightness

### Best Use Cases
| Use Case | Why |
|----------|-----|
| Technical/scientific imagery | Dot-matrix aesthetic fits |
| Artistic/stylized output | Unique look stands out |
| Terminal-friendly displays | Braille chars render well in most terminals |
| Medium-detail needs | More nuance than blocks, less busy than chars |
| "Hacker" aesthetic | Braille dots = matrix/code vibe |

## Algorithm Comparison Summary

| Property | Chars | Blocks | Dots |
|----------|-------|--------|------|
| **Brightness Levels** | 67 | 4 | 12 |
| **Ramp Length** | 68 | 5 | 13 |
| **Detail Level** | Highest | Lowest | Medium |
| **Visual Weight** | Medium | Heavy | Light |
| **Character Type** | ASCII | Unicode blocks | Braille dots |
| **Terminal Compatibility** | Universal | Good | Good |
| **Render Speed** | Medium | Fastest | Medium |
| **Distinctive Look** | Classic | Mosaic | Dot-matrix |

---

# SECTION 5: RENDER MODE FOR AGENTS

## The Cardinal Rule

> **ALWAYS use `render "path"` when running ASCIIDEIA in a non-TTY environment (agents, scripts, CI/CD, Docker, cron jobs). Without `render`, the tool launches an interactive TUI that will hang indefinitely.**

## How Render Works

When the `render` flag is provided with a directory path:

1. ASCIIDEIA converts the image/video to ASCII art (same pipeline as interactive mode)
2. Instead of displaying in terminal, it bakes the ASCII art into a standard media file
3. **For images**: ASCII art → parse ANSI → PIL draw characters → save PNG
4. **For videos**: For each frame → ASCII art → PIL draw → raw RGB → ffmpeg pipe → save MP4
5. The process **exits cleanly** with return code 0 on success
6. Output file path is printed to stdout: `  [INFO] Saved to /path/to/output.png`

## Output File Naming Convention

```
ASCIIDEIA_{type}_{original-name}_{color}_{algorithm}_{timestamp}.{format}
```

| Component | Values | Description |
|-----------|--------|-------------|
| `type` | `image`, `video` | Media type |
| `original-name` | Sanitized filename | Source file's name (without extension), max 50 chars, special chars removed, spaces → hyphens |
| `color` | `colored`, `bw`, `gray` | Color mode used |
| `algorithm` | `chars`, `blocks`, `dots` | Algorithm used |
| `timestamp` | Unix epoch (int) | `int(time.time())` at render time |
| `format` | `png` (image), `mp4` (video) | Output format |

### Examples

```
ASCIIDEIA_image_photo_colored_chars_1778603647.png
ASCIIDEIA_image_portrait_bw_blocks_1778603700.png
ASCIIDEIA_video_demo_colored_dots_1778603800.mp4
ASCIIDEIA_video_Minecraft-Gameplay_gray_chars_1778603900.mp4
```

## How to Find the Output File

1. **The output directory** is whatever path you provide after `render`
2. **The filename** is auto-generated using the convention above
3. **The exact path** is printed to stdout in an `[INFO]` line
4. To capture the output path programmatically:

```bash
# Capture the output path from stdout
OUTPUT=$(python asciideia.py image "photo.png" render "./output/" 2>&1 | rg "Saved to" | rg -o '/.*\.png')
echo "Output file: $OUTPUT"
```

## Common Render Patterns for Agents

### Single Image Render

```bash
python asciideia.py image "input.png" color colored algo chars render "./results/"
```

### Single Video Render

```bash
python asciideia.py video "input.mp4" color colored algo chars render "./results/"
```

### Render All 9 Combinations for an Image

```bash
for color in colored bw gray; do
  for algo in chars blocks dots; do
    python asciideia.py image "photo.png" color "$color" algo "$algo" render "./results/"
  done
done
```

### Render Video with Audio

```bash
# Audio from the source video is automatically included in the MP4 render
python asciideia.py video "clip.mp4" color colored algo chars render "./output/"
# Output MP4 will contain AAC audio at 128kbps if source has audio
```

### Render from URL

```bash
# Download + convert + render in one command
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color gray algo dots render "./output/"
```

### Batch Render Multiple Files

```bash
for file in images/*.png; do
  python asciideia.py image "$file" color colored algo chars render "./ascii_output/"
done
```

### Render with Timeout Protection

```bash
# Video rendering can be slow — add a timeout
timeout 600 python asciideia.py video "long_video.mp4" color colored algo chars render "./output/"
```

---

# SECTION 6: PLATFORM CONSIDERATIONS

## Terminal Input Handling

ASCIIDEIA uses different keyboard input mechanisms per platform:

| Platform | Module | Mechanism |
|----------|--------|-----------|
| **Windows** | `msvcrt` + `ctypes` | `msvcrt.kbhit()` for polling, `msvcrt.getch()` for reading. `ctypes` used to enable ANSI escape code support on Windows console. |
| **Linux/macOS** | `termios` + `tty` + `select` | `termios.tcgetattr()` saves terminal state, `tty.setcbreak()` puts terminal in raw mode, `select.select()` polls stdin for input with timeout. On exit, `termios.tcsetattr()` restores original state. |

**Agent Impact**: Neither input mechanism works in non-TTY environments. Always use `render` mode.

## Windows ANSI Support

On Windows, ASCIIDEIA calls `_enable_windows_ansi()` which uses `ctypes` to set the `ENABLE_VIRTUAL_TERMINAL_PROCESSING` flag (0x0004) on the console output handle. This is required for ANSI escape sequences to work in the Windows console.

**Agent Impact**: This function only works when a real console is attached. In headless/pipe environments, it silently fails. Render mode does not depend on console ANSI support.

## Dependencies Installation

### Linux (Debian/Ubuntu)

```bash
# Python dependencies
pip install -r reqs-linux.txt
# (contains: opencv-python, numpy, Pillow)

# FFmpeg (required for video processing and MP4 rendering)
sudo apt install ffmpeg

# yt-dlp (optional, for YouTube/TikTok URLs)
pip install yt-dlp
```

### Linux (Fedora/RHEL)

```bash
pip install opencv-python numpy Pillow
sudo dnf install ffmpeg
pip install yt-dlp
```

### macOS

```bash
# Python dependencies
pip install opencv-python numpy Pillow

# FFmpeg
brew install ffmpeg

# yt-dlp
pip install yt-dlp
```

### Windows

```bash
# Python dependencies
pip install -r reqs-windows.txt
# (contains: opencv-python, numpy, Pillow)

# FFmpeg
winget install FFmpeg

# yt-dlp
pip install yt-dlp
```

## FFmpeg Requirements

FFmpeg provides three tools used by ASCIIDEIA:

| Tool | Purpose | Required |
|------|---------|----------|
| `ffmpeg` | Audio extraction from video, MP4 rendering via pipe | **Yes** for any video operation |
| `ffprobe` | Video metadata (FPS, frame count, resolution, duration), audio track detection | **Yes** for any video operation |
| `ffplay` | Audio playback during interactive video playback | Optional (graceful fallback if missing) |

**Agent Impact**: For image-only workflows, FFmpeg is not needed. For any video operation (including `render`), both `ffmpeg` and `ffprobe` must be on the system PATH.

## Font Considerations for Render

When rendering to PNG/MP4, ASCIIDEIA uses PIL/Pillow to draw characters. It searches for a monospace font in this order:

1. `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`
2. `/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf`
3. `/usr/share/fonts/truetype/freefont/FreeMono.ttf`
4. `/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf`
5. PIL's built-in default font (fallback)

**If no monospace font is found**, PIL's default font is used, which may produce inconsistent character widths and degrade visual quality.

**Agent Impact**: On Linux servers without desktop font packages, install `fonts-dejavu-core` or similar:
```bash
sudo apt install fonts-dejavu-core    # Debian/Ubuntu
sudo dnf install dejavu-sans-mono-fonts  # Fedora
```

---

# SECTION 7: ERROR HANDLING

## Common Errors and Solutions

### Missing FFmpeg

**Symptoms:**
- `Cannot open video file` when processing a video that exists
- `Audio extraction failed` warnings
- `ffmpeg encoding failed` during MP4 render
- `ffprobe` command not found errors

**Cause:** FFmpeg/ffprobe not installed or not on PATH

**Solution:**
```bash
# Verify FFmpeg is available
ffmpeg -version
ffprobe -version

# Install (platform-specific, see Section 6)
sudo apt install ffmpeg     # Linux
brew install ffmpeg         # macOS
winget install FFmpeg       # Windows
```

### Missing yt-dlp

**Symptoms:**
```
  [ERROR] yt-dlp is required for URL downloads. Install with: pip install yt-dlp
```

**Cause:** yt-dlp not installed when a YouTube/TikTok URL is provided

**Solution:**
```bash
pip install yt-dlp
```

> **Note**: yt-dlp is only needed for URL downloads. Local file processing does not require it.

### File Not Found

**Symptoms:**
```
  [ERROR] File not found: /path/to/nonexistent.png
```

**Cause:** The provided path does not point to an existing file

**Solutions:**
- Verify the file path is correct and the file exists
- Use absolute paths to avoid working directory issues
- `~` (home directory) is expanded automatically via `os.path.expanduser()`
- On Windows, use forward slashes or properly escaped backslashes in quoted paths

### Unsupported Format

**Symptoms:**
```
  [ERROR] Not an image file. Supported: .png, .jpg, .jpeg, .bmp, .webp, ...
  [ERROR] Not a video file. Supported: .mp4, .avi, .mkv, .mov, .webm, ...
```

**Cause:** File extension does not match the mode's expected formats

**Solutions:**
- Ensure `image` mode is used with image extensions: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`, `.tiff`, `.tif`, `.ico`, `.ppm`, `.pgm`, `.pbm`
- Ensure `video` mode is used with video extensions: `.mp4`, `.avi`, `.mkv`, `.mov`, `.webm`, `.flv`, `.wmv`, `.m4v`, `.mpg`, `.mpeg`, `.3gp`, `.ogv`, `.gif`
- Note: `.gif` is treated as a video format (animated GIF)

### URL Not Supported for Images

**Symptoms:**
```
  [ERROR] URLs are not supported for images. Please provide a local file path.
```

**Cause:** A URL was provided in image mode

**Solution:** Download the image first, then process locally:
```bash
# Download the image first (using curl or wget)
curl -o "image.png" "https://example.com/image.png"
python asciideia.py image "image.png" render "./output/"
```

### Cannot Read Video Metadata

**Symptoms:**
```
  [ERROR] Cannot read video metadata.
```

**Cause:** Video file is corrupt, codec not supported by OpenCV, or FFmpeg not available

**Solutions:**
- Verify the video plays in a standard media player
- Ensure FFmpeg is installed (OpenCV may need it for some codecs)
- Try converting the video to a standard format first: `ffmpeg -i input.mkv -c:v libx264 -c:a aac output.mp4`

### ffmpeg Pipe Breaks During MP4 Render

**Symptoms:**
```
  [ERROR] ffmpeg pipe broke on first frame.
```

**Cause:** ffmpeg process crashed or was killed, possibly due to:
- Insufficient memory for the render resolution
- Invalid ffmpeg parameters
- Corrupt frame data

**Solutions:**
- Check available system memory
- Try a different video or reduce source resolution
- Verify ffmpeg works standalone: `ffmpeg -f rawvideo -pixel_format rgb24 -video_size 100x100 -framerate 30 -i /dev/zero -t 1 -y test.mp4`

### Unknown Flag Warning

**Symptoms:**
```
  [WARN] Unknown flag: xyz
```

**Cause:** A flag name that isn't recognized was passed

**Solution:** Only these flags are recognized:
- `color` / `colour` / `c`
- `algo` / `algorithm` / `a`
- `render` / `r`

### Unknown Color Mode Warning

**Symptoms:**
```
  [WARN] Unknown color mode 'xyz', using colored.
```

**Cause:** Unrecognized color value after the `color` flag

**Solution:** Use one of: `colored`, `bw`, `gray` (or their accepted aliases)

### Unknown Algorithm Warning

**Symptoms:**
```
  [WARN] Unknown algorithm 'xyz', using chars.
```

**Cause:** Unrecognized algorithm value after the `algo` flag

**Solution:** Use one of: `chars`, `blocks`, `dots` (or their accepted aliases)

---

# SECTION 8: PRO TIPS FOR AGENTS

## Choosing the Right Color + Algorithm Combo

### Decision Matrix

| Input Type | Best Combo | Why |
|-----------|-----------|-----|
| Color photograph | `colored chars` | Full color + maximum detail = most recognizable |
| Black & white photo | `gray chars` | Grayscale matches source, chars preserves detail |
| Logo / icon | `colored blocks` | Bold blocks emphasize simple shapes and colors |
| Screenshot / UI | `colored chars` | Fine detail needed for text and UI elements |
| Technical diagram | `bw chars` | Clean, readable, no color distraction |
| Abstract / artistic | `colored dots` | Unique dot-matrix aesthetic |
| High-contrast graphic | `bw blocks` | Posterized, bold, minimal |
| Portrait | `gray chars` or `colored chars` | Smooth gradients essential |
| Landscape | `colored chars` | Color adds crucial context |
| Low-resolution source | `colored blocks` | Source has limited detail anyway |
| Very dark image | `colored dots` or `gray dots` | Braille dots are visually lighter, show more in dark areas |

## When to Use Chars vs Blocks vs Dots

### Use Chars When:
- You want the most detail and accuracy
- The source has smooth gradients (photos, portraits)
- You're unsure what to pick (safest default)
- You need the output to be recognizable at small sizes

### Use Blocks When:
- The source is simple (logos, icons, high-contrast graphics)
- You want a bold, posterized aesthetic
- The viewer is far from the screen
- You want the fastest video rendering (fewer brightness levels = simpler processing)
- You're going for a retro/pixel-art look

### Use Dots When:
- You want a unique, distinctive aesthetic
- The source is technical or scientific
- You want a "hacker" or "matrix" visual style
- The image has fine details that blocks would destroy but chars would over-render
- You want something that looks good on both dark and light terminal backgrounds

## Batch Rendering Patterns

### Render All Styles for Comparison

```bash
#!/bin/bash
# Render all 9 combinations for an image
INPUT="photo.png"
OUTDIR="./all_styles/"

for color in colored bw gray; do
  for algo in chars blocks dots; do
    echo "Rendering $color + $algo..."
    python asciideia.py image "$INPUT" color "$color" algo "$algo" render "$OUTDIR"
  done
done
echo "All renders complete. Check $OUTDIR"
```

### Batch Process a Directory

```bash
#!/bin/bash
# Convert all images in a directory
INDIR="./photos/"
OUTDIR="./ascii_art/"

for img in "$INDIR"*.{png,jpg,jpeg}; do
  [ -f "$img" ] || continue
  python asciideia.py image "$img" color colored algo chars render "$OUTDIR"
done
```

### Video Batch with Progress

```bash
#!/bin/bash
# Convert multiple videos
VIDEOS=(video1.mp4 video2.mp4 video3.mp4)
OUTDIR="./ascii_videos/"
TOTAL=${#VIDEOS[@]}
COUNT=0

for vid in "${VIDEOS[@]}"; do
  COUNT=$((COUNT + 1))
  echo "[$COUNT/$TOTAL] Processing $vid..."
  python asciideia.py video "$vid" color colored algo chars render "$OUTDIR"
done
echo "All videos processed."
```

## Video Rendering Time Estimates

Video rendering is **CPU-intensive** because every frame must be:
1. Decoded by OpenCV
2. Converted to ASCII art (resize + brightness + character selection)
3. Rendered to an RGB image via PIL (for each character: font draw)
4. Fed to ffmpeg as raw RGB

### Approximate Times (1080p, 30 FPS)

| Algorithm | Speed Factor | 1-min Video | 5-min Video | 10-min Video |
|-----------|-------------|-------------|-------------|--------------|
| `chars` | ~0.5–1× realtime | 30–60s | 2.5–5min | 5–10min |
| `blocks` | ~1–2× realtime | 15–30s | 1.5–3min | 3–6min |
| `dots` | ~0.5–1× realtime | 30–60s | 2.5–5min | 5–10min |

**Factors affecting speed:**
- Source resolution (4K = much slower than 1080p)
- Frame rate (60 FPS = 2× the frames of 30 FPS)
- CPU power (single-threaded — no GPU acceleration)
- Color mode (`bw` is slightly faster — no ANSI parsing needed for render)
- Algorithm (`blocks` is fastest — fewest brightness levels)

**Tip for agents**: Set appropriate timeouts. A 10-minute video at 1080p with `chars` may take 5–10 minutes to render.

## Working with URLs

### Supported Platforms

| Platform | URL Patterns |
|----------|-------------|
| **YouTube** | `youtube.com/watch?v=`, `youtube.com/shorts/`, `youtu.be/`, `youtube.com/embed/` |
| **TikTok** | `tiktok.com/@user/video/`, `vm.tiktok.com/`, `tiktok.com/t/` |

### URL Handling Flow

```
URL Input
    │
    ▼
┌──────────────────────────────────────┐
│  yt-dlp downloads video             │
│  Format: bestvideo[height≤1080]+    │
│          bestaudio/best[height≤1080] │
│  Merge: mp4                         │
│  Saved to: ascii_temp/download_*    │
└─────────┬────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────┐
│  Downloaded video processed as       │
│  normal local file                   │
│  Original title used in output name  │
└──────────────────────────────────────┘
```

### URL Tips

- **Always use `render` mode** with URLs in agent environments (downloading takes time, you don't want the TUI to hang after download)
- **yt-dlp must be installed** — the error message is clear if it's missing
- **Download quality is capped at 1080p** — this is intentional to keep processing time reasonable
- **The video title** from yt-dlp is used as the `original-name` in the output filename
- **Temporary download files** are stored in `ascii_temp/` and cleaned up automatically on exit
- **Network errors** produce clear error messages — catch them with exit code checks

```bash
# Safe URL rendering pattern for agents
python asciideia.py video "https://youtu.be/VIDEO_ID" color colored algo chars render "./output/" || {
  echo "ASCIIDEIA failed for URL. Check yt-dlp installation and network."
  exit 1
}
```

## Render Output File Discovery

After a render, the exact output path is printed to stdout. To reliably extract it:

```bash
# Parse the output path from ASCIIDEIA's stdout
RESULT=$(python asciideia.py image "photo.png" render "./output/" 2>&1)
echo "$RESULT"

# Extract just the file path
FILEPATH=$(echo "$RESULT" | rg "Saved to" | sed 's/.*Saved to //')
echo "Rendered file: $FILEPATH"

# Check if file exists
if [ -f "$FILEPATH" ]; then
  echo "Success: $FILEPATH"
else
  echo "Failed: output file not found"
fi
```

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success (render complete, or interactive session ended normally) |
| `1` | Error (file not found, bad format, missing dependency, render failure) |

**Note**: When `sys.exit(1)` is called (validation errors, missing files), the process exits immediately. When render succeeds, the process exits with code 0.

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  ASCIIDEIA Agent Quick Reference                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ALWAYS use render in non-TTY:                               │
│    python asciideia.py <mode> <path> render "./out/"        │
│                                                              │
│  Image (all 9 combos):                                       │
│    python asciideia.py image "f.png" color <C> algo <A>     │
│    color: colored | bw | gray                               │
│    algo:  chars | blocks | dots                             │
│                                                              │
│  Video (all 9 combos):                                       │
│    python asciideia.py video "f.mp4" color <C> algo <A>     │
│    render "./out/"                                           │
│                                                              │
│  URL:                                                        │
│    python asciideia.py video "https://..." render "./out/"  │
│                                                              │
│  Output: ASCIIDEIA_{type}_{name}_{color}_{algo}_{ts}.{fmt}  │
│  Image → PNG  |  Video → MP4 (with audio if source has it)  │
│                                                              │
│  Defaults: color=colored  algo=chars                         │
│  Shortcuts: i=img  v=vid  c=color  a=algo  r=render         │
│                                                              │
│  Dependencies: opencv-python, numpy, Pillow                  │
│  FFmpeg: required for video  |  yt-dlp: optional for URLs   │
│                                                              │
│  ⚠ NEVER run without render in agent/CI/Docker environments │
└─────────────────────────────────────────────────────────────┘
```
