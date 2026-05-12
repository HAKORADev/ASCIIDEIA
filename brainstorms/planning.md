ASCIIDEIA Documentation Planning
=================================

STYLE OBSERVATIONS FROM OTHER REPOS:
- VODER: Centered logo + badge, feature bullets, modes table, models table, system reqs table, docs table
- Klarity: Same pattern, badges (release/colab/hf), showcase section with images, dual model modes
- IMDER: Same pattern, badges (pypi/github/license), two ways to use table, algorithm table

COMMON PATTERNS:
- README: logo centered, badges, quick start, core capabilities table, usage guide, system reqs, supported formats, showcase, documentation links, license
- CHANGELOG: Keep a Changelog format, semver, sections: Added/Changed/Fixed/Removed
- Guide.md: Table of contents, deep dive per feature, tips, troubleshooting
- Bots.md: For AI agents, quick start, installation, one-liner patterns, command reference, troubleshooting, example workflows
- skill.md: Architecture understanding, complete CLI catalog, cross-features, combos, troubleshooting, pro tips

ASCIIDEIA-SPECIFIC:
- No system requirements (any system runs it)
- BUT ffmpeg is needed for video render/export
- 3 color modes x 3 algorithms = 9 combos
- Interactive mode + oneline mode
- Render flag now exits after rendering (no TUI hang)
- Windows support added (msvcrt + ctypes)
- Output naming: ASCIIDEIA_type_name_color_algo_ts.ext
- YouTube/TikTok URL support via yt-dlp
- Supported formats: images (10 types) + videos (13 types)

REPO DESCRIPTION:
ASCII Art Media Converter & Player — Convert images and videos to ASCII art in your terminal with 3 color modes and 3 rendering algorithms, then play them live or export as PNG/MP4.

TAGS:
ascii, ascii-art, terminal, image-processing, video-processing, opencv, python, cross-platform, media-converter, terminal-art

CHANGELOG v0.6.0:
- Initial public release
- 3 color modes (colored, bw, gray)
- 3 algorithms (chars, blocks, dots/braille)
- Interactive TUI with keyboard controls
- Oneline CLI mode
- Render to PNG/MP4
- YouTube/TikTok URL support
- Windows support (msvcrt + ANSI enable)
- Audio playback for video (ffplay)
- Output naming with color+algo metadata
