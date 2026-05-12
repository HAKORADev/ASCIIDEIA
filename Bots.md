# ASCIIDEIA - Bot & AI Agent Usage Guide

This document provides comprehensive instructions for AI agents, bots, and automated systems on how to effectively use ASCIIDEIA for ASCII art conversion tasks. AI agents typically operate in headless environments without continuous terminal access, so this guide focuses on the `render` flag for non-interactive file export and one-liner command patterns.

## Table of Contents

1. [Hello, AI Agent!](#hello-ai-agent)
2. [Quick Assessment / Pre-Flight Check](#quick-assessment--pre-flight-check)
3. [Installation Workflow](#installation-workflow)
4. [FFmpeg Setup](#ffmpeg-setup)
5. [Mode Selection Guide](#mode-selection-guide)
6. [Command Reference](#command-reference)
7. [Common User Scenarios](#common-user-scenarios)
8. [Hardware Recommendations](#hardware-recommendations)
9. [Output File Naming](#output-file-naming)
10. [Troubleshooting Commands](#troubleshooting-commands)
11. [Error Handling](#error-handling)
12. [Notes for AI Agents](#notes-for-ai-agents)
13. [User Interaction Template](#user-interaction-template)
14. [Example Workflows](#example-workflows)

---

## Hello, AI Agent!

If you are reading this, you are likely an AI assistant helping a user convert images or videos into ASCII art. This document provides instructions for automated installation and usage guidance.

**Key concept for agents:** ASCIIDEIA has two distinct behaviours:

- **Without `render` flag** → Launches an **interactive terminal player** (TUI). This requires a real TTY and keyboard input. **Agents should avoid this mode** — it will hang in headless environments.
- **With `render` flag** → Renders to a file (PNG for images, MP4 for videos) and **exits immediately**. This is the mode agents should always use.

---

## Quick Assessment / Pre-Flight Check

Before proceeding, assess the user's needs:

1. **What type of content?** Image (photo, screenshot) or video (clip, animation)
2. **What visual style?** Colored, black & white, or grayscale
3. **What character style?** Classic characters, block elements, or Braille dots
4. **What's the output goal?** View in terminal (interactive) or export as file (render)

Verify the user's environment:

```bash
# Check Python version (3.8+ required)
python --version

# Check if FFmpeg is installed (REQUIRED for video)
ffmpeg -version

# Check if ffprobe is installed (part of FFmpeg)
ffprobe -version

# Check Python dependencies
python -c "import cv2; import numpy; from PIL import Image; print('All dependencies OK')"
```

---

## Installation Workflow

### Step 1: Clone and Setup

```bash
# Clone repository
git clone https://github.com/HAKORADev/ASCIIDEIA.git
cd ASCIIDEIA

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**Package explanations:**

| Package | Purpose |
|---------|---------|
| `opencv-python` | Image/video loading, frame extraction, resizing |
| `numpy` | Array operations for brightness mapping and character selection |
| `Pillow` | PNG rendering, font rendering for image export |
| `yt-dlp` | YouTube and TikTok URL download support |

### Step 2: Install FFmpeg (if needed)

**Windows:**
```bash
winget install FFmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg       # Debian/Ubuntu
sudo pacman -S ffmpeg         # Arch
```

### Step 3: Verify Optional Components

```bash
# ffplay comes bundled with FFmpeg (for audio during interactive playback)
# Not needed for render mode
```

### Verify Installation

```bash
python -c "import cv2; import numpy; from PIL import Image; print('All dependencies OK')"
ffmpeg -version
```

---

## FFmpeg Setup

**⚠️ CRITICAL: FFmpeg is REQUIRED for video processing and MP4 rendering.**

Without FFmpeg in your system PATH:
- Video mode will fail to read metadata
- MP4 rendering will fail entirely
- Audio extraction will fail

### Install FFmpeg

**Windows (winget):**
```powershell
winget install FFmpeg
```

**Windows (manual):**
```powershell
# Download from https://www.gyan.dev/ffmpeg/builds/
# Extract to C:\ffmpeg
# Add C:\ffmpeg\bin to system PATH
setx PATH "%PATH%;C:\ffmpeg\bin" /M
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

**Linux (apt):**
```bash
sudo apt update && sudo apt install ffmpeg
```

### Verify FFmpeg Installation

```bash
ffmpeg -version
ffprobe -version
```

### Automated FFmpeg Download (Linux/macOS)

```bash
# Download and install FFmpeg if not present
if ! command -v ffmpeg &> /dev/null; then
    cd /tmp
    wget https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.tar.xz
    tar -xf ffmpeg-release-essentials.tar.xz
    sudo cp ffmpeg-*/*/bin/ffmpeg /usr/local/bin/
    sudo cp ffmpeg-*/*/bin/ffprobe /usr/local/bin/
    rm -rf ffmpeg-*
fi
```

---

## Mode Selection Guide

Help the user choose the right settings:

| User Wants | Mode | Color | Algorithm | Command |
|------------|------|-------|-----------|---------|
| Color photo to ASCII PNG | `image` | `colored` | `chars` | `python asciideia.py image "photo.png" color colored algo chars render "./out/"` |
| Classic B&W ASCII art | `image` | `bw` | `chars` | `python asciideia.py image "photo.png" color bw algo chars render "./out/"` |
| Smooth grayscale image | `image` | `gray` | `chars` | `python asciideia.py image "photo.png" color gray algo chars render "./out/"` |
| Chunky block art | `image` | `colored` | `blocks` | `python asciideia.py image "photo.png" color colored algo blocks render "./out/"` |
| Dot-matrix style | `image` | `colored` | `dots` | `python asciideia.py image "photo.png" color colored algo dots render "./out/"` |
| Video to ASCII MP4 | `video` | `colored` | `chars` | `python asciideia.py video "clip.mp4" color colored algo chars render "./out/"` |
| B&W video export | `video` | `bw` | `chars` | `python asciideia.py video "clip.mp4" color bw algo chars render "./out/"` |
| YouTube video to ASCII | `video` | `colored` | `dots` | `python asciideia.py video "https://youtu.be/..." algo dots render "./out/"` |

### Color Mode Quick Reference

| Mode | Shortcuts Accepted | Description |
|------|--------------------|-------------|
| `colored` | `color`, `colour`, `all` | Full 24-bit RGB color per character |
| `bw` | `black`, `blackwhite` | Pure black & white, no color codes |
| `gray` | `grey`, `grayscale`, `greyscale` | Grayscale shading per character |

### Algorithm Quick Reference

| Algorithm | Shortcuts Accepted | Character Set | Detail Level |
|-----------|--------------------|---------------|--------------|
| `chars` | `characters`, `c` | Standard ASCII ramp (67+ levels) | Highest |
| `blocks` | `block`, `b` | Unicode blocks ░▒▓█ (5 levels) | Low, chunky |
| `dots` | `dot`, `d`, `braille` | Braille dots ⠁⠃⠉⣿ (12 levels) | Medium, dot-matrix |

---

## Command Reference

### Syntax

```bash
python asciideia.py <mode> <path> [color <mode>] [algo <type>] [render "path"] [render_mode <mode>]
```

### Parameters

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `<mode>` | `image` / `i` / `img` for images, `video` / `v` / `vid` for videos | Yes | — |
| `<path>` | Path to local file or YouTube/TikTok URL | Yes | — |
| `color <mode>` | Color mode: `colored`, `bw`, or `gray` (shortcut: `c`) | No | `colored` |
| `algo <type>` | Algorithm: `chars`, `blocks`, or `dots` (shortcut: `a`; `dots` also accepts `braille`/`d`) | No | `chars` |
| `render "path"` | Output directory for rendered file. Shortcut: `r`. When specified, renders and EXITS (no TUI). | No | None (launches interactive player) |
| `render_mode <mode>` | Render resolution: `modern` (full source resolution) or `retro` (~140 chars, visible characters). Shortcut: `rm`. | No | `modern` |

### Mode Options

| Mode | Shortcuts | Input Types | Output Format |
|------|-----------|-------------|---------------|
| `image` | `i`, `img` | PNG, JPG, BMP, WebP, TIFF, ICO, PPM, PGM, PBM | PNG |
| `video` | `v`, `vid` | MP4, AVI, MKV, MOV, WebM, FLV, WMV, M4V, MPG, MPEG, 3GP, OGV, GIF | MP4 |

### Render Flag Behaviour

| Flag Present | Behaviour | Suitable for Agents? |
|--------------|-----------|---------------------|
| `render "./out/"` | Renders PNG/MP4 to the specified directory and **exits** | ✅ Yes — headless safe |
| No `render` flag | Launches **interactive terminal player** (TUI) with keyboard controls | ❌ No — requires TTY, will hang headless |

**⚠️ AI Agents: Always use the `render` flag.** Without it, ASCIIDEIA enters an interactive loop waiting for keyboard input, which will hang in automated environments.

### Render Mode

| Mode | Flag | Description | When to Use |
|------|------|-------------|-------------|
| **Modern** | `render_mode modern` | Full source resolution rendering. Characters are tiny — output looks like a color filter on the original. | High-quality exports, printing, sharing as normal-looking media |
| **Retro** | `render_mode retro` | ~140 characters wide rendering. Individual characters are clearly visible in the output. Feels like authentic ASCII art. | Classic ASCII art aesthetic, terminals, posters, sharing as recognizable ASCII |

**Examples:**
```bash
# Modern — full resolution (default)
python asciideia.py image "photo.png" render "./out/"

# Retro — visible characters
python asciideia.py image "photo.png" render "./out/" render_mode retro

# Retro with shortcuts
python asciideia.py i "photo.png" r "./out/" rm retro
```

### URL Support

| Platform | URL Patterns | Dependency |
|----------|-------------|------------|
| YouTube | `youtube.com/watch?v=`, `youtube.com/shorts/`, `youtu.be/`, `youtube.com/embed/` | `yt-dlp` |
| TikTok | `tiktok.com/@.../video/`, `vm.tiktok.com/`, `tiktok.com/t/` | `yt-dlp` |

URLs are auto-detected. When a URL is passed instead of a file path, ASCIIDEIA downloads the video using yt-dlp, then processes it normally. Only works in `video` mode.

### Examples

**Image — default colored chars:**
```bash
python asciideia.py image "photo.png" render "./output/"
```

**Image — black & white with Braille dots:**
```bash
python asciideia.py i "photo.png" color bw algo dots render "./output/"
```

**Image — grayscale blocks:**
```bash
python asciideia.py img "landscape.jpg" color gray algo blocks render "./output/"
```

**Video — colored with default chars:**
```bash
python asciideia.py video "clip.mp4" render "./output/"
```

**Video — B&W with block elements:**
```bash
python asciideia.py v "demo.mp4" color bw algo blocks render "./output/"
```

**Video — from YouTube URL:**
```bash
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color gray algo dots render "./output/"
```

**Video — from TikTok URL:**
```bash
python asciideia.py vid "https://vm.tiktok.com/ABC123/" render "./output/"
```

---

## Common User Scenarios

### Scenario 1: Convert a Photo to ASCII Art PNG

**Problem:** User has a photo and wants an ASCII art version as a shareable image

**Solution:**
```bash
python asciideia.py image "photo.png" color colored algo chars render "./output/"
```

**Explanation:** Converts the image to colored ASCII art using the full character ramp (highest detail) and saves as PNG. The `render` flag ensures it exports and exits without launching the interactive viewer.

---

### Scenario 2: Retro-Style Black & White ASCII Art

**Problem:** User wants classic, old-school ASCII art with no color

**Solution:**
```bash
python asciideia.py image "selfie.jpg" color bw algo chars render "./output/"
```

**Explanation:** `bw` mode produces pure black & white output using only ASCII characters, no ANSI color codes. This creates the classic "terminal art" look.

---

### Scenario 3: Convert a Video to ASCII MP4

**Problem:** User has a video clip and wants an ASCII art version as a playable MP4

**Solution:**
```bash
python asciideia.py video "clip.mp4" color colored algo dots render "./output/"
```

**Explanation:** Converts the video frame-by-frame to ASCII art using Braille dots for a dot-matrix visual style. Audio from the source is preserved in the output MP4. The `render` flag makes it export and exit.

---

### Scenario 4: Download and Convert a YouTube Video

**Problem:** User wants to convert a YouTube video to ASCII art without manually downloading it

**Solution:**
```bash
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color gray algo chars render "./output/"
```

**Explanation:** When a URL is detected, ASCIIDEIA uses yt-dlp to download the video (max 1080p), then processes it as a local file. Requires `yt-dlp` installed (`pip install yt-dlp`).

---

### Scenario 5: Chunky Block Art for a Pixel Art Look

**Problem:** User wants a stylized, low-detail "pixel art" style using block characters

**Solution:**
```bash
python asciideia.py image "avatar.png" color colored algo blocks render "./output/"
```

**Explanation:** The `blocks` algorithm uses only 5 Unicode block levels (░▒▓█) producing a chunky, mosaic-like result. Works well for profile pictures and simple graphics.

---

### Scenario 6: Grayscale Video with Maximum Detail

**Problem:** User wants a detailed grayscale ASCII video, not full color

**Solution:**
```bash
python asciideia.py video "presentation.mp4" color gray algo chars render "./output/"
```

**Explanation:** `gray` mode applies grayscale shading per character. Combined with `chars` (67+ brightness levels), this produces the smoothest monochrome output. Audio is preserved.

---

### Scenario 7: Batch Process Multiple Images

**Problem:** User wants to convert several images at once

**Solution:**
```bash
python asciideia.py image "photo1.png" color colored algo chars render "./batch/" && \
python asciideia.py image "photo2.jpg" color bw algo chars render "./batch/" && \
python asciideia.py image "photo3.bmp" color gray algo dots render "./batch/"
```

**Explanation:** Chain commands with `&&` to process multiple files sequentially. Each command runs independently and exits after rendering. Output files are named uniquely with timestamps.

---

### Scenario 8: Quick Default Export (Minimal Typing)

**Problem:** User just wants a quick ASCII art export with defaults

**Solution:**
```bash
python asciideia.py image "photo.png" render "./output/"
```

**Explanation:** Omitting `color` and `algo` uses defaults: `colored` + `chars`. This gives full-color, high-detail ASCII art with the least typing.

---

## Hardware Recommendations

### CPU Requirements

| Task | Minimum | Recommended |
|------|---------|-------------|
| Image conversion | Any modern CPU | Any modern CPU |
| Video conversion (short, <1 min) | Dual-core | Quad-core |
| Video conversion (long, >5 min) | Quad-core | 8+ cores |
| MP4 rendering | Quad-core | 8+ cores |

### RAM Requirements

| Task | Minimum | Recommended |
|------|---------|-------------|
| Image processing | 512 MB | 1 GB |
| Video processing | 1 GB | 2 GB |
| HD video rendering | 2 GB | 4 GB |

### GPU

**Not required.** ASCIIDEIA runs entirely on CPU. No CUDA, no GPU acceleration.

### Storage

- **Image output (PNG):** Typically 100 KB – 5 MB per image
- **Video output (MP4):** Typically 1–10 MB per minute of video
- **Temp files:** Cleared automatically after processing; stored in `ASCIIDEIA/ascii_temp/`

---

## Output File Naming

ASCIIDEIA automatically generates descriptive output filenames:

```
ASCIIDEIA_{type}_{original-name}_{color}_{algorithm}_{timestamp}.{format}
```

| Component | Description | Example |
|-----------|-------------|---------|
| `ASCIIDEIA_` | Fixed prefix | `ASCIIDEIA_` |
| `{type}` | `image` or `video` | `image` |
| `{original-name}` | Sanitized original filename (max 50 chars) | `my-photo` |
| `{color}` | Color mode used | `colored`, `bw`, or `gray` |
| `{algorithm}` | Algorithm used | `chars`, `blocks`, or `dots` |
| `{timestamp}` | Unix timestamp at creation time | `1778603647` |
| `.{format}` | `png` for images, `mp4` for videos | `.png` |

**Examples:**

| Input | Command | Output Filename |
|-------|---------|-----------------|
| `cat.png` | `image ... color colored algo chars` | `ASCIIDEIA_image_cat_colored_chars_1778603647.png` |
| `demo.mp4` | `video ... color bw algo blocks` | `ASCIIDEIA_video_demo_bw_blocks_1778603650.mp4` |
| YouTube URL | `video ... color gray algo dots` | `ASCIIDEIA_video_Rickroll-never-gonna-give-you-up_gray_dots_1778603655.mp4` |

**Output location:** Files are saved to the directory specified by the `render` flag. The directory is created automatically if it doesn't exist.

---

## Troubleshooting Commands

### Check System Status

```bash
# Verify Python dependencies
python -c "import cv2; import numpy; from PIL import Image; print('OK')"

# Check FFmpeg availability
ffmpeg -version && echo "FFmpeg OK" || echo "FFmpeg MISSING"

# Check yt-dlp availability
python -c "import yt_dlp; print('yt-dlp OK')" || echo "yt-dlp not installed"

# Check if a video has audio
ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "video.mp4"
```

### Verify Image File

```bash
python -c "from PIL import Image; img = Image.open('photo.png'); print(f'Size: {img.size}, Format: {img.format}')"
```

### Verify Video File

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames -of csv=p=0 "clip.mp4"
```

### Clean Up Temp Files

```bash
# Remove ASCIIDEIA temp directory
rm -rf ASCIIDEIA/ascii_temp/

# Remove ASCIIDEIA results directory
rm -rf ASCIIDEIA/results/
```

---

## Error Handling

### "Cannot read image" / "File not found"

**Cause:** File path is incorrect or file doesn't exist

**Solution:** Use absolute paths and verify the file exists:

```bash
# Wrong (relative path)
python asciideia.py image photo.png render "./out/"

# Correct (absolute path)
python asciideia.py image "/home/user/photos/photo.png" render "/home/user/output/"
```

### "Not an image file" / "Not a video file"

**Cause:** File extension doesn't match the selected mode

**Solution:** Ensure the file extension matches the mode:

```bash
# Wrong — using video mode on an image
python asciideia.py video "photo.png" render "./out/"

# Correct — use image mode for images
python asciideia.py image "photo.png" render "./out/"
```

### "yt-dlp is required for URL downloads"

**Cause:** Processing a YouTube/TikTok URL without yt-dlp installed

**Solution:**
```bash
pip install yt-dlp
```

### "ffmpeg is not installed or not found in PATH"

**Cause:** FFmpeg not installed or not in system PATH

**Solution:** Install FFmpeg (see [FFmpeg Setup](#ffmpeg-setup)) and verify:
```bash
ffmpeg -version
```

### "Cannot read video metadata"

**Cause:** Corrupted video file or unsupported codec

**Solution:**
1. Verify the video plays in a standard player
2. Try re-encoding: `ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4`
3. Use the re-encoded file as input

### "Cannot open video for rendering"

**Cause:** Video file is locked, corrupted, or codec not supported by OpenCV

**Solution:** Re-encode the video with FFmpeg first:
```bash
ffmpeg -i "input.avi" -c:v libx264 -c:a aac -movflags +faststart "input_reencoded.mp4"
python asciideia.py video "input_reencoded.mp4" render "./output/"
```

### Program Hangs Without Output (No render Flag)

**Cause:** Running without the `render` flag launches the interactive TUI player, which requires a real terminal (TTY) with keyboard input

**Solution:** Always use the `render` flag in automated/headless environments:

```bash
# Wrong — will hang waiting for keyboard input
python asciideia.py image "photo.png"

# Correct — renders and exits
python asciideia.py image "photo.png" render "./output/"
```

### ImportError / ModuleNotFoundError

**Cause:** Python packages not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### Slow Video Rendering

**Cause:** Video is long or high resolution; frame-by-frame ASCII conversion + FFmpeg encoding is CPU-intensive

**Solutions:**
1. Use a faster algorithm: `algo blocks` (5 levels) instead of `algo chars` (67+ levels)
2. Pre-process the video to a lower resolution:
   ```bash
   ffmpeg -i "input.mp4" -vf "scale=640:-1" -c:a copy "input_small.mp4"
   python asciideia.py video "input_small.mp4" render "./output/"
   ```

### Download Failed (YouTube/TikTok URL)

**Cause:** yt-dlp version outdated, video is private/age-restricted, or network issue

**Solution:**
```bash
# Update yt-dlp
pip install --upgrade yt-dlp

# Try again
python asciideia.py video "https://youtu.be/..." render "./output/"
```

---

## Notes for AI Agents

1. **Always use the `render` flag** in headless/automated environments. Without it, ASCIIDEIA enters an interactive terminal player that will hang indefinitely.
2. **Always check FFmpeg** before processing videos — it is required for video metadata reading, audio extraction, and MP4 rendering.
3. **yt-dlp is included in requirements.txt** — needed when the user provides a YouTube or TikTok URL instead of a local file path.
4. **ffplay is optional** — only used for audio during interactive playback. Not needed for `render` mode.
5. **No GPU required** — ASCIIDEIA is entirely CPU-based.
6. **Output directory is auto-created** — the path specified in `render` will be created if it doesn't exist.
7. **Default settings are sensible** — `color colored` + `algo chars` gives the best visual quality for most use cases.
8. **`blocks` is fastest** — only 5 brightness levels means less computation per pixel. Good for quick previews.
9. **`chars` is most detailed** — 67+ brightness levels produce the finest gradation in both images and videos.
10. **`dots` (Braille) is a middle ground** — 12 brightness levels with a dot-matrix aesthetic. Visually distinct from `chars`.
11. **Video rendering is slow** — each frame must be converted to ASCII and then rendered to an image before FFmpeg encoding. A 1-minute video at 30fps requires 1,800 frame conversions.
12. **Audio is preserved in MP4 output** — if the source video has an audio track, it is extracted and re-muxed into the rendered MP4.
13. **Temp files are cleaned automatically** — the `ascii_temp/` directory is managed by ASCIIDEIA. Manual cleanup is only needed if the process is interrupted.
14. **File validation is extension-based** — ASCIIDEIA checks the file extension against supported formats. A renamed file with the wrong extension will be rejected.
15. **URLs only work in video mode** — passing a URL with `image` mode will fail because the downloaded file is always a video.

---

## User Interaction Template

When helping a user convert images/videos to ASCII art:

> "I'll help you create ASCII art with ASCIIDEIA. First, let me check what we're working with:
> 
> 1. Is this an image or a video?
> 2. Do you want it in full color, black & white, or grayscale?
> 3. What character style do you prefer — classic text characters (most detailed), block elements (chunky/pixelated), or Braille dots (dot-matrix)?
> 4. Do you have a local file, or do you want to use a YouTube/TikTok URL?
> 
> Based on your answers, I'll set up the right command. I'll use the `render` flag to export the result as a file (PNG for images, MP4 for videos)."

---

## Example Workflows

### Workflow 1: Quick Image to ASCII Art

```bash
# Setup
cd /workspace
git clone https://github.com/HAKORADev/ASCIIDEIA.git
cd ASCIIDEIA
pip install -r requirements.txt

# Convert image with defaults (colored + chars)
python asciideia.py image "/photos/cat.png" render "./results/"

# Output: ./results/ASCIIDEIA_image_cat_colored_chars_1778603647.png
```

### Workflow 2: Video to B&W ASCII MP4

```bash
# Ensure FFmpeg is available
command -v ffmpeg || (sudo apt update && sudo apt install -y ffmpeg)

# Install dependencies
pip install -r requirements.txt

# Convert video to black & white ASCII art MP4
python asciideia.py video "/videos/demo.mp4" color bw algo chars render "./output/"

# Output: ./output/ASCIIDEIA_video_demo_bw_chars_1778603650.mp4
```

### Workflow 3: YouTube Video to Colored Braille Dots MP4

```bash
# Install all dependencies
pip install -r requirements.txt

# Download and convert a YouTube video
python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color colored algo dots render "./ascii_output/"

# Output: ./ascii_output/ASCIIDEIA_video_Rickroll-never-gonna-give-you-up_colored_dots_1778603655.mp4
```

### Workflow 4: Batch Process Multiple Images in Different Styles

```bash
cd ASCIIDEIA
pip install -r requirements.txt
mkdir -p ./batch_output

# Process each image with a different style
python asciideia.py image "/photos/portrait.png" color colored algo chars render "./batch_output/" && \
python asciideia.py image "/photos/landscape.jpg" color bw algo blocks render "./batch_output/" && \
python asciideia.py image "/photos/sunset.bmp" color gray algo dots render "./batch_output/"

# Three files produced:
# ./batch_output/ASCIIDEIA_image_portrait_colored_chars_*.png
# ./batch_output/ASCIIDEIA_image_landscape_bw_blocks_*.png
# ./batch_output/ASCIIDEIA_image_sunset_gray_dots_*.png
```

### Workflow 5: Full Pipeline — Download, Convert, and Deliver

```bash
# Full automated pipeline
cd /workspace/ASCIIDEIA
pip install -r requirements.txt

# Define output directory
OUTPUT_DIR="/workspace/deliverables"
mkdir -p "$OUTPUT_DIR"

# Step 1: Convert a TikTok video to grayscale ASCII
python asciideia.py video "https://vm.tiktok.com/ABC123/" color gray algo chars render "$OUTPUT_DIR/"

# Step 2: Also convert a local image
python asciideia.py image "/workspace/thumbnail.png" color colored algo dots render "$OUTPUT_DIR/"

# List outputs
ls -la "$OUTPUT_DIR"/ASCIIDEIA_*
```

### Workflow 6: Compare All Three Algorithms on the Same Image

```bash
cd ASCIIDEIA
pip install -r requirements.txt
mkdir -p ./comparison

# Same image, three algorithms
python asciideia.py image "sample.png" color colored algo chars render "./comparison/" && \
python asciideia.py image "sample.png" color colored algo blocks render "./comparison/" && \
python asciideia.py image "sample.png" color colored algo dots render "./comparison/"

# Three files in ./comparison/ — one for each algorithm style
# User can compare side by side to choose their preferred look
```

---

**Good luck, AI agent! Help the user create beautiful ASCII art with ASCIIDEIA!**
