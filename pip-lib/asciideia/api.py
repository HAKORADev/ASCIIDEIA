import cv2
import os
import re
import shutil
import subprocess
import sys
import time
import tempfile

from .core import (
    ALGO_CHARS, ALGO_BLOCKS, ALGO_DOTS,
    ALGORITHM_MODES, ALGORITHM_RAMPS,
    COLOR_COLORED, COLOR_BW, COLOR_GRAY,
    COLOR_MODES,
    RENDER_MODERN, RENDER_RETRO, RENDER_MODES,
    BG_DARK, BG_NONE, BG_MODES,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS,
    DARK_THRESHOLD, RETRO_CHAR_WIDTH,
    frame_to_ascii, image_to_ascii,
    ascii_to_rgb_image, render_png, render_mp4,
    format_time, sanitize_filename, generate_output_name,
    get_video_metadata, get_image_metadata,
    has_audio_track, extract_audio,
    compute_display_width_for_terminal,
    RESET, BOLD, DIM, CURSOR_HOME, CLEAR_SCREEN,
    HIDE_CURSOR, SHOW_CURSOR, ALT_SCREEN_ON, ALT_SCREEN_OFF,
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_GRAY, C_MAGENTA, C_BLUE, C_WHITE,
    _color_seq, _select_chars, _detect_color_depth,
)

URL_PATTERNS = {
    'youtube': [
        r'https?://(www\.)?youtube\.com/watch\?v=',
        r'https?://(www\.)?youtube\.com/shorts/',
        r'https?://youtu\.be/',
        r'https?://(www\.)?youtube\.com/embed/',
    ],
    'tiktok': [
        r'https?://(www\.)?tiktok\.com/@[\w.]+/video/',
        r'https?://vm\.tiktok\.com/',
        r'https?://(www\.)?tiktok\.com/t/',
    ]
}

def is_url(text):
    for patterns in URL_PATTERNS.values():
        for pattern in patterns:
            if re.match(pattern, text.strip()):
                return True
    return False

def detect_platform(url):
    for platform, patterns in URL_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url.strip()):
                return platform
    return None

def download_video(url):
    try:
        import yt_dlp
    except ImportError:
        raise RuntimeError("yt-dlp is required for URL downloads. Install with: pip install yt-dlp")
    tmp = tempfile.mkdtemp()
    outtmpl = os.path.join(tmp, "download_%(id)s.%(ext)s")
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'unknown')
            filename = ydl.prepare_filename(info)
            if not os.path.exists(filename):
                base = os.path.splitext(filename)[0]
                for ext in ['.mp4', '.mkv', '.webm', '.avi']:
                    if os.path.exists(base + ext):
                        filename = base + ext
                        break
            return filename, title
    except Exception as e:
        shutil.rmtree(tmp, ignore_errors=True)
        raise RuntimeError(f"Download failed: {e}")

def _validate_color(color):
    m = {
        'colored': COLOR_COLORED, 'colour': COLOR_COLORED, 'color': COLOR_COLORED, 'all': COLOR_COLORED,
        'bw': COLOR_BW, 'black': COLOR_BW, 'blackwhite': COLOR_BW,
        'gray': COLOR_GRAY, 'grey': COLOR_GRAY, 'grayscale': COLOR_GRAY, 'greyscale': COLOR_GRAY,
    }
    if color in COLOR_MODES:
        return color
    return m.get(color.lower(), COLOR_COLORED)

def _validate_algo(algo):
    m = {
        'chars': ALGO_CHARS, 'characters': ALGO_CHARS, 'c': ALGO_CHARS,
        'blocks': ALGO_BLOCKS, 'block': ALGO_BLOCKS, 'b': ALGO_BLOCKS,
        'dots': ALGO_DOTS, 'dot': ALGO_DOTS, 'd': ALGO_DOTS, 'braille': ALGO_DOTS,
    }
    if algo in ALGORITHM_MODES:
        return algo
    return m.get(algo.lower(), ALGO_CHARS)

def _validate_render_mode(render_mode):
    m = {
        'modern': RENDER_MODERN, 'm': RENDER_MODERN, '1': RENDER_MODERN,
        'retro': RENDER_RETRO, 'r': RENDER_RETRO, '2': RENDER_RETRO,
    }
    if render_mode in RENDER_MODES:
        return render_mode
    return m.get(render_mode.lower(), RENDER_MODERN)

def _validate_bg(bg):
    m = {
        'dark': BG_DARK, 'black': BG_DARK, 'd': BG_DARK, '1': BG_DARK,
        'none': BG_NONE, 'transparent': BG_NONE, 'n': BG_NONE, '2': BG_NONE,
    }
    if bg in BG_MODES:
        return bg
    return m.get(bg.lower(), BG_DARK)

def _detect_media_type(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        return 'image'
    if ext in VIDEO_EXTENSIONS:
        return 'video'
    return None

def render_image(path, output_dir=None, color='colored', algo='chars', render_mode='modern', bg='dark', width=None):
    color = _validate_color(color)
    algo = _validate_algo(algo)
    render_mode = _validate_render_mode(render_mode)
    bg = _validate_bg(bg)

    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    if width is None:
        meta = get_image_metadata(path)
        if meta:
            width = compute_display_width_for_terminal(meta['width'], meta['height'])
        else:
            width = 80

    ascii_art = image_to_ascii(path, width, color, algo, bg)
    if ascii_art is None:
        raise RuntimeError(f"Failed to convert image: {path}")

    has_ansi = color != COLOR_BW

    if output_dir is None:
        return ascii_art

    os.makedirs(output_dir, exist_ok=True)
    original_name = os.path.splitext(os.path.basename(path))[0]
    ext = 'png'
    filename = generate_output_name('image', original_name, color, algo, ext)
    out_path = os.path.join(output_dir, filename)
    render_png(ascii_art, out_path, has_ansi, render_mode, bg)
    return out_path

def render_video(path, output_dir=None, color='colored', algo='chars', render_mode='modern', bg='dark', width=None):
    color = _validate_color(color)
    algo = _validate_algo(algo)
    render_mode = _validate_render_mode(render_mode)
    bg = _validate_bg(bg)

    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Video file not found: {path}")

    meta = get_video_metadata(path)
    if not meta:
        raise RuntimeError(f"Cannot read video metadata: {path}")

    if width is None:
        width = compute_display_width_for_terminal(meta['width'], meta['height'])

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(path), 'results')
    os.makedirs(output_dir, exist_ok=True)

    original_name = os.path.splitext(os.path.basename(path))[0]
    audio_path = None
    if has_audio_track(path):
        tmp = tempfile.mkdtemp()
        audio_path = os.path.join(tmp, f"audio_{int(time.time())}.wav")
        if not extract_audio(path, audio_path):
            audio_path = None

    filename = generate_output_name('video', original_name, color, algo, 'mp4')
    out_path = os.path.join(output_dir, filename)

    result = render_mp4(path, width, color, algo, meta['fps'], audio_path, out_path, render_mode, bg)
    if audio_path and os.path.exists(audio_path):
        tmp_dir = os.path.dirname(audio_path)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if result is None:
        raise RuntimeError(f"Failed to render video: {path}")
    return result

def convert_image(path, color='colored', algo='chars', bg='dark', width=None):
    color = _validate_color(color)
    algo = _validate_algo(algo)
    bg = _validate_bg(bg)

    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image file not found: {path}")

    if width is None:
        meta = get_image_metadata(path)
        if meta:
            width = compute_display_width_for_terminal(meta['width'], meta['height'])
        else:
            width = 80

    return image_to_ascii(path, width, color, algo, bg)

def convert_frame(frame, width, color='colored', algo='chars', bg='dark'):
    color = _validate_color(color)
    algo = _validate_algo(algo)
    bg = _validate_bg(bg)
    return frame_to_ascii(frame, width, color, algo, bg)
