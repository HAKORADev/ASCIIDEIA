# ASCIIDEIA Technical Guide

## Table of Contents

- [Introduction & Vision](#introduction--vision)
- [The Philosophy: Terminal-Native Art](#the-philosophy-terminal-native-art)
- [Color Modes Deep Dive](#color-modes-deep-dive)
  - [Colored: 24-bit RGB](#colored-24-bit-rgb)
  - [BW: Pure Black & White](#bw-pure-black--white)
  - [Gray: Grayscale Shading](#gray-grayscale-shading)
- [Algorithms Deep Dive](#algorithms-deep-dive)
  - [Chars: The 67-Level ASCII Ramp](#chars-the-67-level-ascii-ramp)
  - [Blocks: Unicode ░▒▓█](#blocks-unicode-▒)
  - [Dots: Braille ⠁⠃⠉⣿](#dots-braille-)
- [The 9 Combinations](#the-9-combinations)
- [Interactive Playback](#interactive-playback)
  - [Image Viewer](#image-viewer)
  - [Video Player](#video-player)
  - [Keyboard Mapping](#keyboard-mapping)
  - [Hints Bar](#hints-bar)
- [Oneline CLI Mode](#oneline-cli-mode)
  - [Syntax](#syntax)
  - [Flags](#flags)
  - [Shortcuts and Aliases](#shortcuts-and-aliases)
  - [Examples](#examples)
- [Render to Standard Media](#render-to-standard-media)
  - [PNG Pipeline](#png-pipeline)
  - [MP4 Pipeline](#mp4-pipeline)
  - [Output Naming Convention](#output-naming-convention)
- [URL Support](#url-support)
  - [YouTube](#youtube)
  - [TikTok](#tiktok)
  - [yt-dlp Integration](#yt-dlp-integration)
  - [Error Handling](#error-handling)
- [Cross-Platform Architecture](#cross-platform-architecture)
  - [Windows vs POSIX](#windows-vs-posix)
  - [KeyListener Split](#keylistener-split)
  - [ANSI Enable on Windows](#ansi-enable-on-windows)
  - [Conditional Imports](#conditional-imports)
  - [File Opening](#file-opening)
- [Terminal Adaptation](#terminal-adaptation)
  - [Character Aspect Ratio 2:1](#character-aspect-ratio-21)
  - [Auto-Sizing](#auto-sizing)
  - [Truncation](#truncation)
  - [Alternate Screen Buffer](#alternate-screen-buffer)
- [Audio System](#audio-system)
  - [Extraction](#extraction)
  - [Playback](#playback)
  - [Synchronization](#synchronization)
  - [Atempo Filter Chains](#atempo-filter-chains)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)

---

## Introduction & Vision

ASCIIDEIA is a terminal-native media converter that transforms images and videos into ASCII art, plays them live in your terminal with full interactive controls, and exports them as standard PNG and MP4 files. It runs entirely on CPU, requires no GPU, and works on Windows, Linux, and macOS without platform-specific setup beyond a standard Python environment.

**What ASCIIDEIA Actually Does:**

At its core, ASCIIDEIA converts visual media into character-based representations. Every pixel — or group of pixels — in an image or video frame is mapped to a character from a carefully chosen ramp, and that character is colored according to the original pixel data. For images, the result is a static ASCII art rendering displayed in an interactive viewer where you can switch between 3 color modes and 3 algorithms in real time. For videos, the result is a real-time ASCII animation played back in the terminal with pause, seek, speed control, audio, and live mode switching.

But ASCIIDEIA is not just a converter — it is a complete playback environment. The interactive TUI uses alternate screen buffers, hidden cursors, and ANSI escape sequences to create a seamless viewing experience that feels like a native terminal application rather than a script dumping text to stdout. The video player includes a progress bar, time display, speed indicator, and context-sensitive controls. The image viewer lets you experiment with different rendering styles on the fly, pressing keys to cycle through combinations and finding the look that best suits each piece of content.

**Why ASCIIDEIA Exists:**

ASCII art converters have existed for decades, but they typically fall into one of two categories: simple one-shot scripts that dump static text to the terminal, or complex libraries with steep learning curves that require programmatic integration. Neither category provides a polished, interactive experience. ASCIIDEIA was built to fill this gap — a tool that treats terminal ASCII art as a first-class medium rather than a novelty.

The vision is simple: paste a YouTube URL or drag a video file into your terminal, and watch it play as ASCII art in real time with sound. Take a screenshot, convert it to ASCII, and experiment with Braille dot patterns or Unicode block elements until you find the rendering that looks best. Export the result as a PNG for sharing or an MP4 for upload. All of this without leaving the terminal, without installing a GUI toolkit, and without needing a GPU.

**What Makes ASCIIDEIA Different:**

Most ASCII art tools offer a single rendering algorithm — typically the standard character ramp — and a single color mode — either colored or monochrome. ASCIIDEIA provides 3 distinct algorithms (chars, blocks, dots) and 3 distinct color modes (colored, bw, gray), yielding 9 possible combinations. Each combination produces a fundamentally different visual result, and you can switch between them live during playback with a single keypress. This is not a superficial feature — the character ramp, block elements, and Braille dot patterns each have different brightness resolution, visual density, and aesthetic character, and the choice of color mode fundamentally changes how the human eye interprets the brightness information encoded in the characters.

Beyond rendering, ASCIIDEIA provides a complete playback and export pipeline. The interactive TUI is not an afterthought — it is a core design element. The video player tracks audio position independently of video frames, synchronizes them during seek and speed changes, and handles edge cases like pausing mid-playback, resuming at the correct position, and replaying from the start. The render pipeline produces standard PNG and MP4 files that can be opened by any image viewer or video player, making the output truly portable.

---

## The Philosophy: Terminal-Native Art

### The Terminal as a Canvas

ASCIIDEIA treats the terminal not as a constraint to work around, but as a legitimate display medium with its own aesthetic properties. Terminal characters have a fixed aspect ratio of approximately 2:1 — each character cell is roughly twice as tall as it is wide. This is not a bug to correct; it is a fundamental property of the medium, and ASCIIDEIA's rendering pipeline accounts for it explicitly by dividing the vertical dimension by 2 when computing the ASCII output size.

The character aspect ratio is what distinguishes terminal art from pixel art. When you render an image at 160 characters wide, you get approximately 80 rows of text — not 160 — because each character represents a roughly 2:1 pixel block. This is why ASCIIDEIA computes the ASCII height as `int(ascii_width * orig_h / orig_w / 2)`, and why the auto-sizing algorithm adjusts the width to ensure the output fits within the terminal's visible area without scrolling.

### No Degraded Modes

There are no "fast" or "low quality" rendering options in ASCIIDEIA. Every algorithm runs at its full resolution on every frame. The Chars ramp always uses all 67 brightness levels. The Blocks ramp always uses all 5 Unicode stages. The Dots ramp always uses all 12 Braille patterns. The difference between the algorithms is not quality — it is style. Chars provides the most brightness resolution and the most detailed rendering. Blocks provides a chunky, high-contrast aesthetic with fewer gradations. Dots provides a dot-matrix aesthetic that looks like a thermal printer or LED display.

This is a deliberate design choice. Offering a "reduced" character ramp for faster rendering would produce genuinely worse output, not just faster output. The rendering is already CPU-bound and fast enough for real-time video playback on any modern system. There is no performance problem that degraded quality would solve.

### Dark Threshold

Pixels with brightness below 12 (on a 0–255 scale) are rendered as spaces rather than the dimmest character in the ramp. This produces clean black backgrounds instead of fields of barely-visible dots, backticks, and periods. The threshold value of 12 was chosen because it sits below the point where characters become perceptible on most terminal themes — below this brightness, the character glyph is essentially invisible against the black background, but the ANSI color code still takes up bytes in the output string. Replacing these with spaces saves output bandwidth and produces a cleaner visual result.

---

## Color Modes Deep Dive

ASCIIDEIA provides three color modes that determine how the original pixel colors are represented in the terminal output. The choice of color mode affects both the visual appearance and the technical characteristics of the output — colored and gray modes use ANSI escape sequences, while BW mode produces plain text.

### Colored: 24-bit RGB

**How It Works:**

In colored mode, each character in the ASCII output is wrapped in a 24-bit true-color ANSI escape sequence that sets the foreground color to the RGB value of the corresponding pixel in the source image. The escape sequence format is `\033[38;2;R;G;Bm`, where R, G, and B are the red, green, and blue channel values (0–255) of the pixel at that position.

The brightness value used to select the character from the algorithm ramp is computed using the ITU-R BT.601 luminance formula: `0.299 * R + 0.587 * G + 0.114 * B`. This weighted average accounts for the human eye's different sensitivity to red, green, and blue light, producing a brightness value that better matches human perception than a simple average. The green channel receives the highest weight because the human eye is most sensitive to green light.

**Why Separate Brightness Computation Matters:**

The luminance-based brightness computation is used for character selection, while the raw RGB values are used for coloring. This separation is critical because it means the character chosen for each position reflects the perceived brightness of the pixel — a bright yellow pixel (R=255, G=255, B=0) will be rendered with a bright character like `@` or `#`, while a dark blue pixel (R=0, G=0, B=139) will be rendered with a dark character like `.` or `` ` ``. The character and the color work together: the character controls the "ink density" and the ANSI color controls the hue.

**Output Characteristics:**

Colored mode produces the largest output strings because every character requires an ANSI escape sequence. For a 160×80 character rendering, each row contains up to 160 escape sequences plus 160 characters plus a reset code. This is approximately 25–30 bytes per character position, yielding roughly 320–380 KB per frame. For real-time video playback at 30 FPS, this means writing approximately 10–11 MB per second to the terminal — well within the capability of modern terminal emulators, but something to be aware of when rendering over slow SSH connections.

**When to Use Colored:**

Colored mode is the default and the best choice for most content. It preserves the full chromatic information of the source, making it the only mode that can faithfully represent colorful images and videos. Use colored mode when the original content has meaningful color information — photographs, screenshots, colorful artwork, and any video where color is part of the visual message.

### BW: Pure Black & White

**How It Works:**

In BW mode, characters are selected from the algorithm ramp based on pixel brightness, but no ANSI color codes are emitted. The output is plain text — characters on a background, with no per-character coloring. The brightness computation uses the grayscale conversion of the source pixel, which is the same as the OpenCV grayscale channel value (the `cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)` result).

The absence of ANSI codes means that the character selection alone carries all the visual information. This places maximum importance on the algorithm choice — in BW mode with the Chars algorithm, the 67-level ramp provides 67 distinct brightness gradations. With the Blocks algorithm, only 5 gradations are available, which produces a very high-contrast, stencil-like result. With the Dots algorithm, 12 gradations are available, producing a dot-matrix look.

**Output Characteristics:**

BW mode produces the smallest output strings because there are no ANSI escape sequences. Each character is simply the glyph from the ramp, so the output is roughly 1 byte per character position plus newlines. For a 160×80 rendering, this is approximately 13 KB per frame — orders of magnitude smaller than colored mode. This makes BW mode ideal for slow terminal connections or environments where ANSI support is limited.

**When to Use BW:**

BW mode is best for content where color is not important — black and white photographs, text documents, line art, and diagrams. It is also the preferred mode for terminals that do not support 24-bit color, or for scenarios where the output will be processed by tools that cannot parse ANSI sequences (piping to a file, processing with grep, etc.). The classic "ASCII art" aesthetic that most people associate with the term is BW mode with the Chars algorithm.

### Gray: Grayscale Shading

**How It Works:**

In gray mode, each character is wrapped in an ANSI escape sequence that sets the foreground color to a grayscale value equal to the pixel's brightness. The escape sequence format is `\033[38;2;G;G;Gm`, where G is the grayscale value (0–255). Setting all three RGB channels to the same value produces a shade of gray on any terminal that supports 24-bit color.

The character selection uses the same grayscale brightness as BW mode, so the characters reflect the same brightness information. The difference is that gray mode adds a per-character color that reinforces the brightness gradient — dark characters are darkened further by the gray color, and bright characters are brightened further. This produces a smoother visual gradient than BW mode alone, because the ANSI color provides an additional layer of brightness control beyond what the character glyph can convey.

**Output Characteristics:**

Gray mode produces output strings that are the same size as colored mode — every character position requires an ANSI escape sequence. However, the visual result is monochromatic, using only shades of gray rather than the full RGB spectrum. The file size is identical because the escape sequence format is the same length regardless of whether R, G, and B are different values (colored) or the same value (gray).

**When to Use Gray:**

Gray mode is best when you want a smoother, more photographic look than BW mode provides, but without the distraction of color. It works well for portraits, architectural photographs, and any content where tonal gradation is more important than hue. It is also useful as a middle ground — more visually rich than BW, but less busy than colored. For content with subtle lighting and shadow, gray mode with the Chars algorithm often produces the most aesthetically pleasing result.

---

## Algorithms Deep Dive

ASCIIDEIA provides three rendering algorithms that determine how pixel brightness is mapped to characters. Each algorithm uses a different character set — a "ramp" — with different numbers of brightness levels, visual characteristics, and aesthetic qualities.

### Chars: The 67-Level ASCII Ramp

**The Character Set:**

The Chars algorithm uses the following ramp, which provides 67 distinct brightness levels plus a space for the darkest values:

```
 `.'`,:;!~+-=|<>iv)\/_1[]{}?clfsxzjfrnueoadqkpmygwh87654XZ#MW&8%B@$
```

The ramp is ordered from lightest to darkest — the backtick and period represent the dimmest visible content, while `$` and `@` represent the brightest. The space character is used for pixels below the dark threshold (brightness < 12), which covers pure black and near-black pixels.

**How Brightness Mapping Works:**

For each pixel, the brightness value (0–255) is normalized and mapped to an index in the character ramp. The formula is `index = brightness / 255 * (len(ramp) - 1)`, clipped to valid bounds. This means a pixel with brightness 0 maps to the first character (space, due to the dark threshold), and a pixel with brightness 255 maps to the last character (`$`).

The 67 levels of gradation make the Chars algorithm the highest-resolution option available. This many levels means that subtle tonal differences in the source image are preserved in the ASCII output — a gradual sky gradient will render as a smooth transition rather than visible banding.

**Why This Specific Ramp:**

The character ramp is not arbitrary. Each character was chosen because it occupies a specific amount of visual "ink" on screen — the number of illuminated pixels in the character glyph when rendered in a monospace font. A period has very few illuminated pixels (light), while an at-sign has many (dark). The ordering of the ramp reflects this increasing visual density, ensuring that the brightness-to-character mapping produces a visually accurate representation of the source.

Some characters appear out of strict density order because they were chosen to also provide visual texture. The exact ramp used in ASCIIDEIA is tuned for visual quality on typical terminal fonts, and it includes duplicate characters at certain brightness levels to smooth the perceptual transition.

**Visual Character:**

Chars produces the most detailed and photorealistic ASCII art of the three algorithms. The 67 brightness levels allow for smooth gradients and fine detail. The result looks like a traditional ASCII art rendering — the kind you might see in a README or a classic demoscene production. It is the default algorithm for good reason: it provides the best overall quality for most content.

### Blocks: Unicode ░▒▓█

**The Character Set:**

The Blocks algorithm uses Unicode block elements with 5 brightness levels:

```
 ░▒▓█
```

From left to right: space (empty), light shade, medium shade, dark shade, and full block. These are Unicode characters U+2591 through U+2593 plus U+2588, specifically designed to represent fractional fill levels in text-based displays.

**How Brightness Mapping Works:**

The same brightness normalization formula applies, but with only 5 levels in the ramp (including space), the mapping is much coarser. Each brightness level covers a range of approximately 51 values (255 / 5), so two pixels that differ by 30 in brightness may map to the same block character. This produces visible banding in gradients but creates a bold, high-contrast aesthetic.

**Visual Character:**

Blocks produces chunky, posterized output that resembles pixel art or mosaic tiles. The limited brightness range means that subtle details are lost, but the strong contrast creates a distinctive, graphic look that works well for logos, icons, silhouettes, and any content with bold shapes and clear edges. It is the most "abstract" of the three algorithms — the original image is clearly recognizable but reduced to its most essential forms.

The block characters are significantly wider than typical ASCII characters in some terminal fonts, which can produce a slightly different aspect ratio than the Chars algorithm. On most modern terminal emulators with Unicode support, the blocks render as filled rectangles at 25%, 50%, 75%, and 100% density, creating a smooth visual step between levels.

**When to Use Blocks:**

Blocks is ideal for content with high contrast and simple shapes. Logos, icons, text overlays, and high-contrast illustrations render well with blocks. It is also the best choice when you want a stylized, abstract look rather than a photorealistic one. Avoid blocks for content with subtle gradients or fine detail — the 5-level ramp will posterize these into visible bands.

### Dots: Braille ⠁⠃⠉⣿

**The Character Set:**

The Dots algorithm uses Unicode Braille patterns with 12 brightness levels:

```
 ⠁⠃⠉⠋⠛⠟⠿⡿⣇⣗⣧⣷⣿
```

These are Braille dot patterns (U+2801 through U+28FF) ordered by the number of dots present in each pattern. A Braille character cell contains 8 dot positions arranged in a 2×4 grid, and each pattern activates a different combination of these dots. The ordering goes from patterns with few dots (light) to patterns with all dots filled (dark).

**How Brightness Mapping Works:**

With 12 brightness levels plus space, the Dots algorithm sits between Chars (67 levels) and Blocks (5 levels) in terms of brightness resolution. This provides moderate tonal gradation — enough to represent smooth gradients without the banding of Blocks, but without the fine detail of Chars.

**Visual Character:**

Dots produces a unique dot-matrix aesthetic that resembles LED displays, thermal printers, and retro terminal displays. Each character position is a cluster of up to 8 small dots, creating a stippled effect that is unlike either the glyph-based rendering of Chars or the filled-rectangle rendering of Blocks. The visual texture is light and airy — the black background shows through the gaps between dots, giving the output a characteristic "screen door" look.

This algorithm is particularly effective for large-format displays where the viewer is at a distance, because the dot pattern creates the illusion of continuous tones through optical mixing (similar to halftone printing in newspapers). Up close, the individual dots are visible; at a distance, they blend into a smooth image.

**When to Use Dots:**

Dots is ideal for creating a retro or futuristic aesthetic. It works well for portraits, landscapes, and any content where the dot-matrix look is part of the artistic statement. It is also a good choice when you want more brightness resolution than Blocks provides but prefer a different visual texture than Chars. The dot-matrix look pairs particularly well with colored mode, where the colored dots create a pointillist effect similar to the paintings of Georges Seurat.

---

## The 9 Combinations

The 3 color modes and 3 algorithms create a 3×3 matrix of possible rendering styles. Each combination has distinct visual properties and ideal use cases.

| | Colored | BW | Gray |
|---|---|---|---|
| **Chars** | Full-color detailed | Classic ASCII | Smooth monochrome |
| **Blocks** | Chunky colored tiles | High-contrast stencil | Shaded monochrome blocks |
| **Dots** | Pointillist color | Minimalist dots | Subtle dot shading |

### Colored + Chars

The default combination and the most photorealistic option. Full 24-bit color per character with 67 brightness levels produces the most accurate representation of the source content. This is the best combination for general use — photographs, screenshots, video playback, and any content where visual fidelity matters. The colored characters carry both hue and brightness information, and the 67-level ramp preserves subtle tonal details.

### Colored + Blocks

A bold, stylized look with full color but reduced tonal resolution. The 5-level block ramp creates visible banding in gradients, but the colored blocks produce a mosaic or stained-glass effect that can be visually striking. Best for content with bold colors and simple shapes — logos, pixel art, high-contrast illustrations, and stylized graphics where the posterization effect is desirable rather than a limitation.

### Colored + Dots

A pointillist rendering where colored Braille dots create an effect reminiscent of pointillist painting or LED billboards. The 12 brightness levels provide moderate tonal gradation, and the colored dots create an optical mixing effect that can look remarkably smooth at a distance. This is one of the most aesthetically distinctive combinations — it looks like nothing else in the terminal art space. Best for artistic content, portraits, and any situation where the dot-matrix aesthetic is the point.

### BW + Chars

The classic ASCII art look. Black characters on a dark background (or white on light, depending on terminal theme), with 67 brightness levels providing maximum tonal detail without any color information. This is the combination that most people think of when they hear "ASCII art" — it is the style of the classic ASCII art archives, the demoscene, and early internet culture. Best for black and white photography, text-based displays, and environments where color is not available or desired.

### BW + Blocks

The most abstract combination. Five levels of fill density without any color produces a high-contrast, stencil-like rendering that reduces any image to its most essential shapes. The visual result is similar to a woodcut print or a stencil poster — bold, graphic, and stripped of all subtlety. Best for logos, silhouettes, and any content where you want maximum contrast and minimum detail.

### BW + Dots

A minimalist dot-matrix rendering. Twelve levels of dot density without color produces a subtle, textured monochrome output that looks like a thermal printout or a newspaper halftone. The dots create a lighter visual texture than filled characters, giving the output an airy, delicate quality. Best for content where you want the dot aesthetic without the distraction of color — black and white portraits, architectural photographs, and technical illustrations.

### Gray + Chars

A smooth monochrome rendering that combines the 67-level character ramp with per-character grayscale ANSI coloring. This is the most tonally smooth monochrome option — the character glyph and the gray color work together to create a continuous brightness gradient that is smoother than either BW (character only) or a flat gray (color only) could achieve alone. Best for content with subtle lighting and tonal gradation where color is not important — portraits, moody photographs, and black and white film.

### Gray + Blocks

A shaded monochrome rendering using block elements with per-character grayscale coloring. The 5 block levels are reinforced by the gray color, producing a smoother transition than BW + Blocks but retaining the chunky, graphic aesthetic. The gray coloring fills in the visual gaps between block levels, reducing the posterization effect. Best for content where you want the bold block aesthetic with slightly smoother tonal transitions than pure BW allows.

### Gray + Dots

A subtle dot-matrix rendering with per-character grayscale shading. This is perhaps the most refined of the dot-matrix combinations — the gray coloring adds a layer of tonal smoothness on top of the dot patterns, creating an effect similar to a high-quality halftone print. The result is both textured and smooth, with the dot pattern providing visual interest and the gray coloring providing tonal accuracy. Best for content where you want maximum tonal quality with the dot aesthetic — fine art photography, detailed illustrations, and any content where subtlety matters.

---

## Interactive Playback

ASCIIDEIA provides two interactive playback modes: an image viewer for static images and a video player for animated content. Both use the same rendering engine and support live switching between color modes and algorithms, but the video player adds playback controls for pause, seek, speed, and audio.

### Image Viewer

When you open an image in ASCIIDEIA — either through the interactive menu or the oneline CLI — the tool enters the image viewer mode. This mode renders the image as ASCII art using the current color mode and algorithm, displays it on an alternate screen buffer (so your terminal history is preserved), and enters a key-wait loop.

The image viewer is deliberately simple because an image is a static object — there is no temporal dimension to control. The primary interaction is switching between the 9 rendering combinations to find the look you prefer. Each keypress triggers a full re-render of the image with the new parameters, which is instantaneous for images because there is only one frame to process.

When you quit the image viewer (Q, Esc, or Enter), the alternate screen buffer is restored, returning you to your previous terminal state with no leftover artifacts.

### Video Player

The video player is ASCIIDEIA's most complex interactive component. It reads frames from the video file sequentially, converts each frame to ASCII art in real time, and writes the result to the terminal at the video's native frame rate (adjusted for the current playback speed). The player maintains several pieces of state:

- **Frame counter** — tracks the current position in the video
- **Pause state** — whether playback is paused or active
- **Speed index** — which of the 8 speed steps is currently selected
- **Sound state** — whether audio is enabled and currently playing
- **Video-ended flag** — whether the last frame has been reached

The main loop follows this structure on each iteration:

1. Drain all pending key events from the listener
2. Process each key — update state, seek, change speed, toggle modes
3. If paused, sleep briefly and continue
4. If video ended, sleep briefly and continue
5. Read the next frame from the video capture
6. Convert the frame to ASCII art
7. Write the ASCII art and progress meter to the terminal
8. Sleep for the remaining frame time to maintain the target frame rate

The frame timing uses `time.perf_counter()` to measure the actual elapsed time per frame, then sleeps for the remaining portion of the target frame delay. This ensures that the playback speed is as accurate as possible given the variable rendering time per frame.

### Keyboard Mapping

| Key | Image Viewer | Video Player |
|-----|-------------|-------------|
| `1` | Switch to Colored mode | Switch to Colored mode |
| `2` | Switch to BW mode | Switch to BW mode |
| `3` | Switch to Gray mode | Switch to Gray mode |
| `4` | Switch to Chars algorithm | Switch to Chars algorithm |
| `5` | Switch to Blocks algorithm | Switch to Blocks algorithm |
| `6` | Switch to Dots algorithm | Switch to Dots algorithm |
| `J` | — | Seek back 5s / Step back 1 frame |
| `L` | — | Seek forward 5s / Step forward 1 frame |
| `I` | — | Increase speed |
| `K` | — | Decrease speed |
| `P` | — | Pause / Resume |
| `S` | — | Toggle sound (when audio present) |
| `R` | — | Replay from start |
| `Q` | Quit | Quit |
| `Esc` | Quit | Quit |
| `Enter` | Quit | — |
| `Ctrl+C` | Quit | Quit |

The J/L keys have dual behavior depending on pause state. When the video is playing, they seek ±5 seconds. When the video is paused, they step forward or backward by one frame. This dual behavior is intentional — when you pause to examine a specific frame, you typically want fine-grained control to find the exact frame you are looking for, not a 5-second jump.

### Hints Bar

Both the image viewer and video player display a hints bar at the bottom of the screen that shows the current state and available controls. The hints bar uses ANSI styling to highlight the active color mode and algorithm in their respective colors, while inactive options are displayed in dim gray. The video player hints bar additionally shows the current speed, pause state, and sound status.

The color mode indicators use these colors:
- **Colored**: Cyan (`\033[96m`)
- **BW**: White (`\033[97m`)
- **Gray**: Dark gray (`\033[90m`)

The algorithm indicators use these colors:
- **Chars**: Green (`\033[92m`)
- **Blocks**: Yellow (`\033[93m`)
- **Dots**: Magenta (`\033[95m`)

The active option is rendered in bold with its respective color, while inactive options are rendered in dim gray. This provides immediate visual feedback about the current rendering configuration without requiring any explicit status display.

---

## Oneline CLI Mode

The oneline CLI mode allows you to run ASCIIDEIA with all parameters specified on the command line, bypassing the interactive menu system entirely. This is useful for scripting, batch processing, automation, and quick one-shot conversions where you know exactly what you want and do not want to navigate through prompts.

### Syntax

```
python asciideia.py <mode> <path> [flags]
```

The mode and path are positional arguments — they must appear in order. The flags are keyword arguments that can appear in any order after the path.

### Flags

| Flag | Values | Default | Description |
|------|--------|---------|-------------|
| `color` | `colored`, `bw`, `gray` | `colored` | Color mode for rendering |
| `algo` | `chars`, `blocks`, `dots` | `chars` | Algorithm for rendering |
| `render` | `"path"` | (none) | Render as PNG/MP4 to the specified directory and exit |

When the `render` flag is not provided, ASCIIDEIA enters the interactive playback mode (image viewer or video player) with the specified color mode and algorithm as defaults. When the `render` flag is provided with a directory path, ASCIIDEIA renders the output as a PNG (images) or MP4 (videos) file in that directory and exits without launching the interactive player.

### Shortcuts and Aliases

The oneline CLI supports multiple aliases for each parameter to reduce typing:

**Mode aliases:**
- `image`, `i`, `img` → image mode
- `video`, `v`, `vid` → video mode

**Flag aliases:**
- `color`, `colour`, `c` → color flag
- `algo`, `algorithm`, `a` → algorithm flag
- `render`, `r` → render flag

**Color value aliases:**
- `colored`, `colour`, `color`, `all` → colored mode
- `bw`, `black`, `blackwhite` → BW mode
- `gray`, `grey`, `grayscale`, `greyscale` → gray mode

**Algorithm value aliases:**
- `chars`, `characters`, `c` → Chars algorithm
- `blocks`, `block`, `b` → Blocks algorithm
- `dots`, `dot`, `d`, `braille` → Dots algorithm

The aliases are case-insensitive. Unrecognized values produce a warning and fall back to the default (colored for color, chars for algorithm).

### Examples

```bash
python asciideia.py image "photo.png"

python asciideia.py i "photo.png" c gray a dots

python asciideia.py video "clip.mp4" algo dots

python asciideia.py v "clip.mp4" color bw algo blocks render "./output/"

python asciideia.py image "landscape.jpg" render "./out/"

python asciideia.py video "https://youtu.be/dQw4w9WgXcQ" color gray

python asciideia.py vid "movie.mp4" a braille c grayscale r "/tmp/ascii/"
```

---

## Render to Standard Media

The render pipeline converts ASCII art into standard media files that can be opened by any image viewer or video player. This is the bridge between the terminal-native art that ASCIIDEIA produces and the standard file formats that the rest of the world expects.

### PNG Pipeline

The PNG rendering pipeline converts a static ASCII art image into a PNG file. The pipeline works as follows:

1. **Generate ASCII art** — The source image is converted to ASCII art using the specified color mode and algorithm at the full resolution of the source image (not the terminal-adapted size). This means a 4000-pixel-wide photograph will produce a 4000-character-wide ASCII rendering, regardless of terminal size.

2. **Parse ANSI sequences** — If the color mode is colored or gray, the ANSI escape sequences in the ASCII art are parsed into per-character RGB tuples. The `parse_ansi_colored_line` function walks each line character by character, tracking the current foreground color and building a list of `(character, R, G, B)` tuples. For BW mode, lines are stored as plain strings with a default white color.

3. **Create PIL Image** — A new RGB image is created with dimensions based on the number of characters and rows, multiplied by the character cell size (7×14 pixels by default). The background is set to black.

4. **Render characters** — Each character is drawn onto the PIL image using `ImageDraw.text()` at the correct position and color. The position is calculated as `(col * char_w, row * char_h)`, where `char_w=7` and `char_h=14` for the default monospace font at size 12.

5. **Save as PNG** — The resulting PIL image is saved as a PNG file using `Image.save()`.

**Font Selection:**

The PNG renderer searches for a monospace TrueType font on the system. The search order is:

1. `/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf`
2. `/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf`
3. `/usr/share/fonts/truetype/freefont/FreeMono.ttf`
4. `/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf`

If no TrueType font is found, the PIL default font is used as a fallback. The default font has limited glyph coverage and may not render Unicode characters (blocks, Braille dots) correctly, so installing a monospace font is strongly recommended for PNG rendering.

### MP4 Pipeline

The MP4 rendering pipeline converts a video into an ASCII art video. This is significantly more complex than the PNG pipeline because it must process every frame, maintain a consistent output resolution, and optionally include audio.

1. **Read first frame** — The first frame of the source video is read and converted to ASCII art, then rendered as an RGB image using the same process as the PNG pipeline. This establishes the output resolution (`render_w × render_h`) that all subsequent frames must match.

2. **Launch ffmpeg** — An ffmpeg process is started with the following configuration:
   - Input: raw RGB24 video data from pipe, at the source video's frame rate
   - Output: H.264 encoded MP4 with CRF 23 quality and medium preset
   - Audio: If the source video has an audio track, it is extracted to a WAV file and provided as a second input to ffmpeg, re-encoded as AAC at 128 kbps
   - Pixel format: yuv420p (maximum compatibility with video players)

3. **Process frames** — Each subsequent frame is read from the source video, converted to ASCII art, rendered as an RGB image, and written as raw bytes to the ffmpeg process's stdin. If any frame produces an RGB image with different dimensions than the first frame, it is resized to match using PIL's `Image.resize()`.

4. **Finalize** — After all frames are processed, the stdin pipe is closed and ffmpeg finalizes the output file. Progress is reported every 30 frames.

**Why Raw Video Piping:**

The MP4 pipeline uses raw RGB24 data piped to ffmpeg rather than writing individual PNG frames to disk. This approach has several advantages:

- **No temporary files** — Individual frames never touch disk, eliminating I/O overhead and disk space requirements
- **Lower latency** — Each frame is processed and sent to ffmpeg immediately, without waiting for disk writes
- **Simpler cleanup** — There are no intermediate frame files to delete after rendering
- **Consistent quality** — Raw RGB data has no compression artifacts that could compound with the H.264 encoding

The tradeoff is memory usage — the raw RGB data for each frame must fit in memory. For a typical ASCII rendering (e.g., 1120×560 pixels at 3 bytes per pixel), each frame is approximately 1.9 MB, which is negligible on any modern system.

### Output Naming Convention

Rendered files follow a consistent naming pattern that encodes the rendering parameters:

```
ASCIIDEIA_{type}_{name}_{color}_{algorithm}_{timestamp}.{format}
```

| Component | Values | Description |
|-----------|--------|-------------|
| `type` | `image`, `video` | Media type |
| `name` | sanitized original filename | Source identifier (max 50 chars) |
| `color` | `colored`, `bw`, `gray` | Color mode used |
| `algorithm` | `chars`, `blocks`, `dots` | Algorithm used |
| `timestamp` | Unix epoch seconds | Unique identifier |
| `format` | `png`, `mp4` | Output format |

Example output names:

```
ASCIIDEIA_image_sunset_colored_chars_1715612345.png
ASCIIDEIA_video_intro-bw_blocks_1715612350.mp4
ASCIIDEIA_image_portrait_gray_dots_1715612360.png
```

The original filename is sanitized by removing non-alphanumeric characters (except hyphens and underscores), replacing spaces with hyphens, and truncating to 50 characters. This ensures the filename is filesystem-safe while remaining human-readable.

The timestamp component serves as a unique identifier to prevent filename collisions when rendering the same source multiple times with different parameters.

---

## URL Support

ASCIIDEIA can download videos directly from YouTube and TikTok URLs, eliminating the need to manually download a video file before converting it. URL support is integrated into both the interactive menu and the oneline CLI — simply paste the URL as the file path, and ASCIIDEIA handles the download automatically.

### YouTube

**Supported URL formats:**

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`
- `https://www.youtube.com/embed/VIDEO_ID`

YouTube URL detection uses regular expressions that match the standard watch URL format, the shortened youtu.be format, Shorts URLs, and embed URLs. All of these are common ways to share YouTube videos, and ASCIIDEIA handles them transparently.

### TikTok

**Supported URL formats:**

- `https://www.tiktok.com/@username/video/VIDEO_ID`
- `https://vm.tiktok.com/SHORT_CODE`
- `https://www.tiktok.com/t/SHORT_CODE`

TikTok URL detection handles both the full URL format (with the username and video ID path) and the shortened share link format (vm.tiktok.com or tiktok.com/t/). The shortened formats redirect to the full URL, and yt-dlp resolves these redirects automatically.

### yt-dlp Integration

URL downloading is powered by yt-dlp, a command-line tool for downloading videos from YouTube and many other platforms. ASCIIDEIA imports yt-dlp as a Python library and uses its `YoutubeDL` class to extract video information and download content.

**Download Configuration:**

```python
ydl_opts = {
    'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
    'outtmpl': str(TEMP_DIR / "download_%(id)s.%(ext)s"),
    'quiet': True,
    'no_warnings': True,
    'merge_output_format': 'mp4',
}
```

The download format is constrained to 1080p maximum resolution. This is intentional — ASCII art does not benefit from resolutions higher than 1080p because the terminal cannot display that many characters. Downloading 4K video would waste bandwidth and storage space with no improvement in output quality. The merged output format is forced to MP4 for compatibility with the video playback pipeline.

Downloaded files are stored in the `ascii_temp/` directory with a filename based on the video ID. After the ASCIIDEIA session ends, the temporary directory is cleaned up automatically.

### Error Handling

If yt-dlp is not installed, ASCIIDEIA prints a clear error message: `yt-dlp is required for URL downloads. Install with: pip install yt-dlp`. The tool then exits rather than failing silently or attempting a fallback.

If the download fails (network error, video unavailable, age restriction, etc.), ASCIIDEIA reports the error from yt-dlp and either returns to the interactive menu or exits (depending on the mode). The temporary directory is cleaned up in both cases.

URLs are not supported for image mode — if you paste a URL while in image mode, ASCIIDEIA displays an error message explaining that URLs only work with video mode. This is because YouTube and TikTok only serve video content, and attempting to download a single frame from a video URL would be misleading (the frame would depend on the video's thumbnail, which may not represent the actual content).

---

## Cross-Platform Architecture

ASCIIDEIA runs on Windows, Linux, and macOS with identical functionality and controls. The cross-platform support is not superficial — it extends to the lowest levels of the input handling, terminal control, and file management code.

### Windows vs POSIX

The fundamental platform split in ASCIIDEIA is between Windows and POSIX (Linux/macOS). This split exists because the two families use completely different APIs for non-blocking keyboard input:

| Feature | Windows | POSIX (Linux/macOS) |
|---------|---------|---------------------|
| Keyboard input | `msvcrt.kbhit()` + `msvcrt.getch()` | `select.select()` + `sys.stdin.read(1)` |
| Terminal raw mode | Not needed (msvcrt handles it) | `termios.tcgetattr()` + `tty.setcbreak()` |
| Terminal restore | Not needed | `termios.tcsetattr()` on cleanup |
| ANSI support | Must be enabled via `SetConsoleMode` | Enabled by default in most terminals |
| Extended key sequences | `\x00` or `\xe0` prefix bytes | `\x1b[` prefix sequences |

### KeyListener Split

The `KeyListener` class is the core of the interactive playback system — it reads keyboard input in a background thread and queues key events for the main loop to process. The class is split into two implementations:

**POSIX implementation (`_listen_posix`):**

The POSIX listener puts the terminal into cbreak (raw) mode at initialization, which disables line buffering and echo. It then uses `select.select()` with a 50ms timeout to poll stdin for available data. When data is available, it reads one character at a time.

Escape key detection on POSIX is complicated by the fact that many key sequences start with the escape character `\x1b`. Arrow keys, function keys, and other special keys produce multi-byte sequences like `\x1b[A` (up arrow). To distinguish a standalone Escape press from an escape sequence, the POSIX listener uses a secondary `select()` call with a 10ms timeout after receiving an `\x1b` character. If more data arrives within 10ms, it is an escape sequence — the additional bytes are consumed and discarded. If no more data arrives, it is a standalone Escape key, which is queued as `\x1b`.

When the listener stops, it restores the terminal to its original settings using `termios.tcsetattr()` with the saved terminal attributes from initialization. This ensures the terminal is left in a usable state after the program exits.

**Windows implementation (`_listen_windows`):**

The Windows listener uses `msvcrt.kbhit()` to check if a key is available, then `msvcrt.getch()` to read it. Extended key sequences (arrow keys, function keys) on Windows produce a two-byte sequence starting with `\x00` or `\xe0`. The Windows listener detects these prefix bytes and consumes the following byte, effectively discarding extended key events. This is simpler than the POSIX approach because Windows uses a consistent two-byte format for extended keys.

When no key is available, the Windows listener sleeps for 20ms before checking again. This prevents the thread from consuming 100% CPU while waiting for input.

Both implementations convert all input to lowercase before queuing, ensuring that key handling is case-insensitive across platforms.

### ANSI Enable on Windows

Windows 10 and later support ANSI escape sequences in the console, but the feature must be explicitly enabled. ASCIIDEIA calls `_enable_windows_ansi()` at startup, which uses the Windows API to set the `ENABLE_VIRTUAL_TERMINAL_PROCESSING` flag (0x0004) on the standard output handle.

The function obtains the standard output handle via `kernel32.GetStdHandle(-11)`, reads the current console mode, sets the virtual terminal processing flag, and writes the new mode back. If any step fails — for example, if the output is redirected to a pipe, or if the Windows version is too old — the function silently passes without raising an error. This graceful degradation ensures that ASCIIDEIA does not crash on systems where ANSI support is unavailable, even though the visual output may be garbled.

### Conditional Imports

Platform-specific modules are imported conditionally at the top of the file:

```python
_IS_WINDOWS = sys.platform == 'win32'

if _IS_WINDOWS:
    import msvcrt
    import ctypes
else:
    import termios
    import tty
```

This pattern ensures that only the modules needed for the current platform are imported. On Linux, the `msvcrt` and `ctypes` modules are never loaded (and would not exist anyway). On Windows, `termios` and `tty` are never imported (and would fail if they were). The `_IS_WINDOWS` flag is used throughout the codebase to branch between platform-specific code paths.

### File Opening

After rendering a PNG or MP4 file, ASCIIDEIA attempts to open the file using the system's default application:

- **macOS**: `open <path>`
- **Windows**: `os.startfile(<path>)`
- **Linux**: `xdg-open <path>`

This is a convenience feature that lets you immediately view the rendered output without navigating to the file manually. If the open command fails (e.g., no default application for the file type, or running in a headless environment), the error is silently ignored.

---

## Terminal Adaptation

Terminal displays are fundamentally different from pixel displays. Characters are not square — they are approximately twice as tall as they are wide. Terminals have a fixed number of columns and rows. And the visible area varies depending on the terminal window size and any UI elements (tabs, scrollbars, status bars). ASCIIDEIA's terminal adaptation system accounts for all of these factors to produce output that fits the visible terminal area.

### Character Aspect Ratio 2:1

In a typical monospace terminal font, each character cell is approximately twice as tall as it is wide. A character that is 7 pixels wide might be 14 pixels tall. This means that if you render a square image (e.g., 100×100 pixels) as ASCII art at 100 characters wide, the output will be approximately 100 characters wide and 50 rows tall (not 100 rows), because each row of characters covers roughly 2 pixel rows.

ASCIIDEIA accounts for this by dividing the vertical dimension by 2 when computing the ASCII output height:

```python
height = max(1, int(ascii_width * orig_h / orig_w / 2))
```

The `/2` factor compensates for the character aspect ratio, ensuring that the output maintains the original image's aspect ratio despite the non-square character cells. Without this correction, circles would appear as tall ovals and squares would appear as tall rectangles.

### Auto-Sizing

When ASCIIDEIA prepares to display content, it calculates the optimal ASCII output width based on three factors:

1. **Source dimensions** — The original image or video resolution
2. **Terminal width** — The number of columns in the terminal (via `os.get_terminal_size().columns`)
3. **Terminal height** — The number of rows in the terminal (minus 3 rows for the progress bar and hints)

The algorithm starts by setting the width to `min(source_width, terminal_width)`. It then computes the corresponding ASCII height. If the ASCII height exceeds the available terminal height (minus 3 rows for the UI), the width is reduced until the height fits. The formula for the reduced width is:

```python
width = max(20, int(max_height * src_w / src_h * 2))
```

The `*2` factor accounts for the character aspect ratio (inverting the `/2` used in the height calculation), and the result is clamped to the terminal width.

The minimum width of 20 characters prevents the output from becoming unreadably narrow on very short terminal windows.

### Truncation

Even after auto-sizing, the output may occasionally exceed the terminal dimensions — for example, if the terminal is resized after the initial calculation, or if the source image has unusual dimensions. ASCIIDEIA applies two levels of truncation:

**Width truncation** — Each line of the ASCII output is truncated to the terminal width. For lines containing ANSI escape sequences, the `truncate_ansi_line` function walks the line character by character, counting visible characters while preserving escape sequences intact. When the visible character count reaches the terminal width, a RESET code is appended and the line is cut. This ensures that ANSI color codes are not split mid-sequence, which could produce garbled output.

**Height truncation** — The number of lines in the output is limited to the available terminal height. Lines beyond the limit are simply omitted.

### Alternate Screen Buffer

Both the image viewer and video player use the alternate screen buffer (enabled via `\033[?1049h`). This is the same mechanism used by terminal applications like vim, less, and htop. The alternate screen buffer provides a separate, independent display area that does not affect the terminal's scrollback history. When ASCIIDEIA exits, it switches back to the primary screen buffer (`\033[?1049l`), restoring the terminal to its previous state with no leftover ASCII art in the scrollback.

The cursor is also hidden during playback (`\033[?25l`) and restored on exit (`\033[?25h`). This prevents the cursor from flickering on top of the ASCII art during rendering.

---

## Audio System

When a video has an audio track, ASCIIDEIA extracts the audio and plays it alongside the ASCII art. The audio system handles extraction, playback, synchronization with the video, and speed adjustment using ffmpeg's atempo filter.

### Extraction

Audio extraction is performed using ffmpeg with the following command:

```
ffmpeg -y -i <video_path> -vn -acodec pcm_s16le -ar 44100 -ac 2 <output.wav>
```

The audio is extracted as uncompressed PCM WAV at 44100 Hz sample rate with stereo channels. The PCM format is chosen because it is the simplest format for ffplay to handle without additional decoding latency. The 44100 Hz sample rate is a standard audio CD quality that is universally supported. Stereo output preserves the spatial information of the original audio.

The extraction runs as a subprocess with a 300-second timeout. If the extraction fails (e.g., the video has no audio track despite reporting one, or the audio codec is not supported), ASCIIDEIA prints a warning and continues playback without sound.

### Playback

Audio playback is handled by ffplay, ffmpeg's lightweight audio and video player. ASCIIDEIA launches ffplay in a subprocess with the following flags:

- `-nodisp` — No video display window (audio only)
- `-autoexit` — Exit when the audio finishes playing
- `-loglevel quiet` — Suppress ffplay's status output
- `-ss <offset>` — Start playback at the specified offset (for seek and resume)

The ffplay process's stdin is kept open (connected to a pipe) so that ASCIIDEIA can kill the process cleanly when seeking, pausing, or exiting. stdout and stderr are redirected to DEVNULL to prevent ffplay's output from interfering with the ASCII art display.

If ffplay is not found on the system, ASCIIDEIA prints a warning and disables audio for the session. The rest of the playback continues normally without sound.

### Synchronization

Audio-video synchronization in ASCIIDEIA is position-based rather than clock-based. The `AudioPlayer` class tracks its current playback position using wall-clock time:

- When playing: `position = start_offset + (current_time - play_start_time) * speed`
- When paused: `position = paused_at`

When the user seeks (J/L keys), ASCIIDEIA:

1. Calculates the target seek time based on the current video frame position
2. Sets the video capture to the corresponding frame
3. Kills the current ffplay process
4. Starts a new ffplay process at the seek position

When the user changes speed (I/K keys), ASCIIDEIA:

1. Records the current playback position
2. Kills the current ffplay process
3. Starts a new ffplay process at the same position with the new speed

This approach ensures that the audio and video stay synchronized after seek and speed changes. The synchronization is not frame-accurate — there is a small delay when restarting the ffplay process — but it is close enough for a comfortable viewing experience. The delay is typically under 100ms, which is imperceptible for most content.

### Atempo Filter Chains

FFmpeg's `atempo` filter adjusts the playback speed of audio without changing the pitch. However, the atempo filter has a limited range: it only accepts values between 0.5 and 2.0. ASCIIDEIA supports speeds from 0.25x to 2.00x, which means the slowest speed (0.25x) is below the atempo filter's minimum.

To handle this, ASCIIDEIA chains multiple atempo filters. The `_build_atempo` method uses the following algorithm:

1. If the speed is within the 0.5–2.0 range, use a single atempo filter
2. If the speed is below 0.5, chain `atempo=0.5` filters until the remaining speed is within range, then apply the remaining speed as a final filter
3. If the speed is above 2.0, chain `atempo=2.0` filters until the remaining speed is within range, then apply the remaining speed as a final filter

For example, at 0.25x speed:
- Chain: `atempo=0.5,atempo=0.5` (0.5 × 0.5 = 0.25)

For a hypothetical speed of 0.15x (not currently in the speed steps):
- Chain: `atempo=0.5,atempo=0.3` (0.5 × 0.3 = 0.15)

The filters are comma-separated and passed to ffplay as a single `-af` argument. FFmpeg processes the chain in order, applying each filter to the output of the previous one.

---

## Tips & Best Practices

### Choosing the Right Combination

**For photographs and realistic images:**
Start with Colored + Chars (the default). If the image has subtle color gradients, colored mode preserves them. If you want a more artistic look, switch to Colored + Dots for a pointillist effect, or Gray + Chars for a smooth monochrome rendering.

**For logos and icons:**
Use Colored + Blocks or BW + Blocks. The 5-level ramp posterizes the image into bold shapes, which is ideal for simple, high-contrast designs. The chunky block aesthetic makes logos immediately recognizable even at small sizes.

**For video playback:**
Use Colored + Chars for most content. If the video has a lot of fine detail and you are experiencing rendering lag (unlikely on modern systems), switch to Blocks or Dots for slightly faster per-frame rendering. If the video is primarily dark (night scenes, space content), BW mode may produce cleaner output than colored mode because dark-colored characters on a dark background can be difficult to see.

**For social media and sharing:**
Use the render flag to export as PNG or MP4. Render at the source resolution for maximum quality. Colored + Dots often produces the most visually distinctive and shareable output — the dot-matrix aesthetic is unique and eye-catching.

### Terminal Considerations

**Terminal size matters.** The larger your terminal window, the more characters are available for rendering, and the more detailed the output will be. Maximize your terminal window before launching ASCIIDEIA for the best results.

**Font choice affects quality.** The default monospace font in your terminal determines how the characters, blocks, and dots look. A font with clear character distinction (like DejaVu Sans Mono, JetBrains Mono, or Fira Code) will produce better results than a font where characters are hard to distinguish at small sizes.

**24-bit color support is essential for colored and gray modes.** Most modern terminal emulators support 24-bit color, but some older terminals or minimal terminals (like the Linux virtual console) may not. If you see garbled escape sequences instead of colors, switch to BW mode.

**SSH connections may be slow for colored video.** Colored mode produces approximately 25–30 bytes per character position, which can overwhelm slow SSH connections. If you experience lag, switch to BW mode (1 byte per character) or Gray mode (same byte count but potentially less visual data to process on the remote end).

### Render Tips

**Render at source resolution.** When using the `render` flag, ASCIIDEIA renders at the full source resolution, not the terminal-adapted size. This means a 4K video will produce a much more detailed ASCII art MP4 than a 480p video. If you want the highest quality render, start with the highest resolution source available.

**BW renders are universally compatible.** A BW + Chars PNG contains no ANSI codes and can be viewed by any application that understands text rendering. This makes it the most portable choice for sharing ASCII art in contexts where the viewer may not have a 24-bit color terminal.

**Choose your algorithm for the output medium.** If the PNG will be viewed at a small size, Blocks provides the most recognizable output. If it will be viewed at full size, Chars provides the most detail. If it will be printed, Dots creates an interesting halftone effect that looks good on paper.

### URL Tips

**YouTube Shorts work natively.** ASCIIDEIA detects YouTube Shorts URLs and handles them the same as regular YouTube videos. The vertical aspect ratio of Shorts actually works well in the terminal because the character aspect ratio (2:1) is closer to a vertical format.

**TikTok share links are supported.** The shortened `vm.tiktok.com` and `tiktok.com/t/` links that TikTok generates when you share a video are automatically resolved by yt-dlp. You do not need to find the full URL.

**yt-dlp must be installed separately.** ASCIIDEIA does not install yt-dlp as a dependency because it is only needed for URL support. Install it with `pip install yt-dlp` before attempting to use URLs.

---

## Troubleshooting

### Garbled Output or Escape Sequences Visible

**Symptom:** You see `\033[38;2;...m` sequences in the output instead of colored characters.

**Cause:** Your terminal does not support 24-bit ANSI color, or on Windows, the virtual terminal processing flag was not set.

**Solutions:**
- On Windows: Ensure you are using Windows Terminal, ConEmu, or another modern terminal that supports ANSI. The legacy `cmd.exe` may not support 24-bit color on older Windows versions.
- Switch to BW mode (press `2`) to avoid ANSI sequences entirely.
- Try a different terminal emulator (Windows Terminal, Alacritty, Kitty, iTerm2).

### Video Playback Is Choppy

**Symptom:** Frames are dropped or the playback stutters.

**Cause:** The rendering loop cannot keep up with the video frame rate.

**Solutions:**
- Reduce the terminal window size — smaller terminals require fewer characters per frame.
- Switch to Blocks or Dots algorithm — these have fewer brightness levels and may render slightly faster.
- Close other applications that may be consuming CPU.
- Note: On most modern systems, even a 1080p video at 30 FPS will play smoothly. If you experience choppy playback, the bottleneck is likely the terminal emulator's rendering speed, not ASCIIDEIA's processing speed.

### Audio Not Playing

**Symptom:** The video plays but there is no sound.

**Cause:** ffplay is not installed, or the video has no audio track.

**Solutions:**
- Install ffmpeg (which includes ffplay) via your system package manager.
- Check that ffplay is in your PATH by running `ffplay -version`.
- If the source video has no audio track (indicated by `[S]OFF` in the hints bar with red coloring), there is nothing to play. This is expected for GIFs and some silent video clips.
- If you are in a remote SSH session, audio playback is not possible because ffplay outputs to the local sound device, not the remote one.

### Cannot Download from YouTube or TikTok

**Symptom:** `yt-dlp is required for URL downloads` error, or download fails.

**Solutions:**
- Install yt-dlp: `pip install yt-dlp`
- Update yt-dlp to the latest version: `pip install -U yt-dlp` — YouTube frequently changes their page format, and outdated yt-dlp versions may fail.
- Some videos are age-restricted, private, or region-locked. These cannot be downloaded without authentication cookies, which ASCIIDEIA does not currently support.
- If you are behind a proxy or firewall, yt-dlp may need additional configuration to reach the video servers.

### PNG Render Shows Missing Characters or Blocks

**Symptom:** The rendered PNG file contains blank spaces where characters should be, or block/Braille characters appear as empty boxes.

**Cause:** The system does not have a monospace TrueType font that includes Unicode block elements and Braille patterns.

**Solutions:**
- Install a monospace font with Unicode coverage (DejaVu Sans Mono, Noto Sans Mono, or FreeMono).
- On Linux: `sudo apt install fonts-dejavu-core` or `sudo apt install fonts-freefont-ttf`
- The PNG renderer falls back to PIL's default font, which only covers basic ASCII. Block and Braille characters require a TrueType font with Unicode support.

### Terminal Not Restored After Quitting

**Symptom:** After quitting ASCIIDEIA, the terminal does not echo typed characters or behaves strangely.

**Cause:** The terminal was left in raw mode because the cleanup code did not execute (e.g., due to a hard crash or `kill -9`).

**Solutions:**
- On POSIX systems, run `reset` to restore the terminal to its default state.
- If the cursor is hidden, run `echo -e "\033[?25h"` to make it visible again.
- If echo is disabled, try pressing Enter and typing `stty echo` (you will not see what you type).
- This is a rare occurrence that only happens if ASCIIDEIA is forcefully terminated. Normal exit (Q, Esc, Ctrl+C) always restores the terminal properly.

### MP4 Render Fails

**Symptom:** `ffmpeg encoding failed` error during MP4 rendering.

**Cause:** ffmpeg is not installed, or the encoding parameters are incompatible with the output format.

**Solutions:**
- Ensure ffmpeg is installed and in your PATH: `ffmpeg -version`
- Check that the output directory exists and is writable.
- If the source video is very long, the rendering may take significant time and disk space. Ensure you have sufficient free disk space for the output file.
- If the error persists, check the ffmpeg error message (printed in the ASCIIDEIA output) for specific details about what went wrong.

### GIF Files Play but Have No Audio

**Symptom:** A `.gif` file plays as a video but the sound icon shows OFF.

**Cause:** GIF is an image format that does not support audio. ASCIIDEIA treats animated GIFs as video files (they contain multiple frames), but there is no audio track to extract.

**Solution:** This is expected behavior. GIF files are silent by definition.

---
