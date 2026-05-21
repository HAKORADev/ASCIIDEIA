# Changelog

All notable changes to ASCIIDEIA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.6.1] - 2026-05-21

### Added

- **Background Mode Selection** — Choose between Dark (default, leaves black pixels empty for black terminal backgrounds) and Transparent (prints black characters instead of skipping them, so output looks correct on any terminal background color). Available for both images and videos.
- **Interactive Background Prompt** — After the render mode selection (Modern/Retro), a new prompt asks for background mode: Dark or Transparent.
- **Oneline Background Flag** — New `bg` flag for oneline mode accepts `dark` or `none` (e.g., `bg none`). Default is `dark`.

---

## [0.6.0] - 2026-05-13

### Added

- **3 Color Modes** — Colored (24-bit RGB per character), BW (pure black & white), and Gray (grayscale shading). Switchable live during playback with keys 1/2/3.
- **3 Rendering Algorithms** — Chars (standard ASCII ramp with 67+ brightness levels), Blocks (Unicode block elements ░▒▓█ with 5 levels), and Dots (Braille dot patterns ⠁⠃⠉⣿ with 12 levels). Switchable live during playback with keys 4/5/6.
- **2 Render Modes** — Modern (full source resolution, filter-like detail) and Retro (~140 characters wide, visible individual characters for authentic ASCII art feel). Controlled via `render_mode` flag or interactive menu when rendering.
- **Dynamic Terminal Color Depth Detection** — Automatically detects terminal color support (24-bit true-color, 256-color, 16-color, or none) and uses the highest supported depth. Non-TTY environments always use 24-bit for best render quality.
- **Interactive Terminal Playback** — Full TUI with alternate screen buffer, hidden cursor, and real-time rendering. Images display in an interactive viewer with live mode switching. Videos play with a progress bar, time display, and speed indicator.
- **Video Playback Controls** — Pause/Resume (P), Seek ±5 seconds (J/L), Frame stepping when paused (J/L), Speed control from 0.25x to 2.00x in 0.25 increments (I/K), Sound toggle (S), Replay from start (R), Quit (Q/Esc).
- **Image Viewer Controls** — Color mode switching (1/2/3), Algorithm switching (4/5/6), Quit (Q/Esc/Enter).
- **Oneline CLI Mode** — Non-interactive command-line interface with positional arguments and flags. Mode shortcuts: `image|i|img` and `video|v|vid`. Flag shortcuts: `color|c`, `algo|a`, `render|r`.
- **Render to Standard Media** — Export images as PNG and videos as MP4 with the `render` flag. Video renders include audio from the source when present. Render mode exits cleanly without launching the interactive player.
- **Output File Naming** — Rendered files follow the pattern `ASCIIDEIA_{type}_{original-name}_{color}_{algorithm}_{timestamp}.{format}`. The color mode and algorithm are embedded in the filename for easy identification.
- **YouTube & TikTok URL Support** — Paste a YouTube or TikTok URL as the input path. ASCIIDEIA downloads the video using yt-dlp and processes it automatically. Supports youtube.com, youtu.be, tiktok.com, and vm.tiktok.com URLs.
- **Audio Playback** — Videos with audio tracks have their audio extracted and played via ffplay during ASCII playback. Audio stays synchronized with the video during speed changes and seeking. Mute toggle available with S key.
- **Cross-Platform Support** — Full support for Windows, Linux, and macOS. Platform-specific terminal handling via conditional imports: `termios`/`tty`/`select` on POSIX, `msvcrt`/`ctypes` on Windows. Windows ANSI virtual terminal processing enabled automatically via `SetConsoleMode`.
- **Windows Key Listener** — Custom `KeyListener` implementation using `msvcrt.kbhit()` and `msvcrt.getch()` for Windows. Extended key sequences (arrow keys, function keys) are properly consumed. Escape key detected correctly.
- **POSIX Key Listener** — `termios` raw mode with `select`-based non-blocking stdin reads. Escape sequences from arrow keys and function keys are consumed and discarded. Bare Escape key is properly detected.
- **10 Image Formats** — PNG, JPG, JPEG, BMP, WebP, TIFF, TIF, ICO, PPM, PGM, PBM.
- **13 Video Formats** — MP4, AVI, MKV, MOV, WebM, FLV, WMV, M4V, MPG, MPEG, 3GP, OGV, GIF.
- **Dark Threshold Processing** — Pixels with brightness below 12 are rendered as spaces, producing clean black backgrounds instead of dim artifacts.
- **Terminal Size Adaptation** — ASCII output dimensions are automatically calculated from the terminal size, accounting for the 2:1 character aspect ratio. Content is truncated to fit the visible terminal area.
- **ANSI Color Rendering** — 24-bit true-color escape sequences (`\033[38;2;R;G;Bm`) for per-character coloring. ANSI line truncation preserves color codes while respecting visible character limits.
- **PNG Rendering Pipeline** — Converts ASCII art with ANSI codes to an RGB image using PIL. Parses ANSI color sequences, renders each character with a monospace font at the correct position and color. Supports Noto Sans SC and DejaVu Sans Mono fonts with automatic detection.
- **MP4 Rendering Pipeline** — Frame-by-frame ASCII-to-RGB conversion piped to ffmpeg as raw video. Audio from the source is re-encoded as AAC and muxed into the output. H.264 encoding with configurable CRF quality.
- **Audio Extraction** — FFmpeg-based audio extraction to PCM WAV (44100Hz, stereo). Used for both live playback and MP4 rendering with audio.
- **Atempo Filter Chain** — Audio speed adjustment using ffmpeg's atempo filter. Supports the full 0.25x–2.00x range by chaining multiple atempo filters when values fall outside the single-filter 0.5–2.0 range.
- **Video Metadata Detection** — FPS, frame count, resolution, and duration extracted via OpenCV with ffprobe fallback for accurate frame rate detection (handles fractional FPS like 24000/1001).
- **Interactive Menu System** — Guided prompts for media type selection, file path input, color mode, algorithm, and render options when running without CLI arguments.
