#!/usr/bin/env python3

import cv2
import os
import re
import shutil
import subprocess
import sys
import termios
import time
import tty
import threading

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

BANNER = r"""
 █████  ███████  ██████ ██ ██ ██████  ███████ ██  █████
██   ██ ██      ██      ██ ██ ██   ██ ██      ██ ██   ██
███████ ███████ ██      ██ ██ ██   ██ █████   ██ ███████
██   ██      ██ ██      ██ ██ ██   ██ ██      ██ ██   ██
██   ██ ███████  ██████ ██ ██ ██████  ███████ ██ ██   ██
"""

ALGO_CHARS = 'chars'
ALGO_BLOCKS = 'blocks'
ALGO_DOTS = 'dots'

ALGORITHM_RAMPS = {
    ALGO_CHARS: " `.'`,:;!~+-=|<>iv)\\/_1[]{}?clfsxzjfrnueoadqkpmygwh87654XZ#MW&8%B@$",
    ALGO_BLOCKS: " ░▒▓█",
    ALGO_DOTS: " ⠁⠃⠉⠋⠛⠟⠿⡿⣇⣗⣧⣷⣿",
}

_ALGORITHM_ARRAYS = {k: np.array(list(v)) for k, v in ALGORITHM_RAMPS.items()}

DARK_THRESHOLD = 12

COLOR_COLORED = 'colored'
COLOR_BW = 'bw'
COLOR_GRAY = 'gray'

COLOR_MODES = [COLOR_COLORED, COLOR_BW, COLOR_GRAY]
ALGORITHM_MODES = [ALGO_CHARS, ALGO_BLOCKS, ALGO_DOTS]

SPEED_STEPS = [0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00]
SPEED_DEFAULT_IDX = 3

COLOR_LABELS = {COLOR_COLORED: 'Color', COLOR_BW: 'BW', COLOR_GRAY: 'Gray'}
ALGO_LABELS = {ALGO_CHARS: 'Chars', ALGO_BLOCKS: 'Blocks', ALGO_DOTS: 'Dots'}

_COLOR_HINT_STYLE = {
    COLOR_COLORED: "\033[96m",
    COLOR_BW: "\033[97m",
    COLOR_GRAY: "\033[90m",
}
_ALGO_HINT_STYLE = {
    ALGO_CHARS: "\033[92m",
    ALGO_BLOCKS: "\033[93m",
    ALGO_DOTS: "\033[95m",
}

IMAGE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.bmp', '.webp',
    '.tiff', '.tif', '.ico', '.ppm', '.pgm', '.pbm',
}
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv',
    '.wmv', '.m4v', '.mpg', '.mpeg', '.3gp', '.ogv', '.gif',
}

SCRIPT_DIR = Path(__file__).resolve().parent
TEMP_DIR = SCRIPT_DIR / "ascii_temp"
RESULTS_DIR = SCRIPT_DIR / "results"

RESET      = "\033[0m"
BOLD       = "\033[1m"
DIM        = "\033[2m"
CURSOR_UP  = "\033[A"
CURSOR_HOME = "\033[H"
CLEAR_SCREEN = "\033[2J"
HIDE_CURSOR  = "\033[?25l"
SHOW_CURSOR  = "\033[?25h"
ALT_SCREEN_ON  = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"

C_CYAN    = "\033[96m"
C_GREEN   = "\033[92m"
C_YELLOW  = "\033[93m"
C_RED     = "\033[91m"
C_GRAY    = "\033[90m"
C_MAGENTA = "\033[95m"
C_BLUE    = "\033[94m"
C_WHITE   = "\033[97m"

def format_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def sanitize_filename(name, max_len=50):
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[\s]+', '-', sanitized.strip())
    return sanitized[:max_len] if sanitized else "untitled"

def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False

def get_terminal_width():
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80

def get_terminal_height():
    try:
        return os.get_terminal_size().lines
    except OSError:
        return 24

def compute_display_width_for_terminal(src_w, src_h):
    term_w = get_terminal_width()
    term_h = get_terminal_height()
    max_height = max(term_h - 3, 10)

    width = min(src_w, term_w)
    ascii_h = compute_ascii_height(width, src_w, src_h)

    if ascii_h > max_height and max_height > 0:
        width = max(20, int(max_height * src_w / src_h * 2))
        width = min(width, term_w)

    return width

def compute_ascii_height(ascii_width, orig_w, orig_h):
    if orig_w <= 0 or orig_h <= 0:
        return max(1, ascii_width // 2)
    return max(1, int(ascii_width * orig_h / orig_w / 2))

def print_info(msg):
    print(f"  {C_GREEN}[INFO]{RESET} {msg}")

def print_warn(msg):
    print(f"  {C_YELLOW}[WARN]{RESET} {msg}")

def print_error(msg):
    print(f"  {C_RED}[ERROR]{RESET} {msg}")

def print_step(msg):
    print(f"\n  {C_CYAN}▸{RESET} {msg}")

def clear_temp():
    if TEMP_DIR.exists():
        shutil.rmtree(str(TEMP_DIR), ignore_errors=True)
    ensure_dir(str(TEMP_DIR))

def clear_results():
    ensure_dir(str(RESULTS_DIR))

def purge_temp():
    if TEMP_DIR.exists():
        shutil.rmtree(str(TEMP_DIR), ignore_errors=True)

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
        print_error("yt-dlp is required for URL downloads. Install with: pip install yt-dlp")
        sys.exit(1)

    clear_temp()
    outtmpl = str(TEMP_DIR / "download_%(id)s.%(ext)s")

    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }

    print_step("Downloading video...")
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
        print_error(f"Download failed: {e}")
        return None, None

def validate_media_path(path):
    expanded = os.path.expanduser(path)
    if os.path.isfile(expanded):
        return expanded
    return None

def validate_export_path(path):
    if not path or not path.strip():
        return None
    path = path.strip().strip('"').strip("'")
    path = path.replace('\\', os.sep).replace('/', os.sep)
    try:
        p = Path(path)
        if not p.is_absolute():
            p = Path.cwd() / p
        try:
            os.makedirs(str(p), exist_ok=True)
        except OSError as e:
            if "No such file" in str(e) or "Permission denied" in str(e):
                print_error(f"Cannot create directory: {e}")
                return None
        return str(p)
    except Exception as e:
        print_error(f"Invalid path: {e}")
        return None

def get_video_metadata(path):
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / max(fps, 1)
    cap.release()

    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'v:0',
             '-show_entries', 'stream=r_frame_rate,nb_frames,duration,width,height',
             '-of', 'csv=p=0', path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(',')
            if len(parts) >= 1 and '/' in parts[0]:
                num, den = parts[0].split('/')
                try:
                    fps = float(num) / float(den)
                except (ValueError, ZeroDivisionError):
                    pass
    except Exception:
        pass

    return {
        'fps': fps if fps > 0 else 30.0,
        'total_frames': total_frames,
        'width': w,
        'height': h,
        'duration': duration,
    }

def get_image_metadata(path):
    try:
        with Image.open(path) as img:
            return {'width': img.size[0], 'height': img.size[1], 'format': img.format}
    except Exception:
        return None

def has_audio_track(path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a',
             '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', path],
            capture_output=True, text=True, timeout=10
        )
        return bool(result.stdout.strip())
    except Exception:
        return False

def extract_audio(video_path, output_path):
    try:
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '44100', '-ac', '2',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        print_warn(f"Audio extraction failed: {e}")
        return False

def _select_chars(brightness, algorithm):
    ramp = ALGORITHM_RAMPS[algorithm]
    arr = _ALGORITHM_ARRAYS[algorithm]
    n_chars = len(ramp) - 1
    indices = np.clip((brightness / 255.0 * n_chars).astype(np.int32), 0, n_chars)
    char_map = arr[indices]

    dark_mask = brightness < DARK_THRESHOLD
    char_map[dark_mask] = ' '

    return char_map


def frame_to_ascii(frame, width, color_mode, algorithm):
    h, w = frame.shape[:2]
    height = max(1, int(h * width / w / 2))
    resized = cv2.resize(frame, (width, height))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    brightness = gray.astype(np.float32)

    if color_mode == COLOR_COLORED:
        r = rgb[:, :, 0].astype(np.float32)
        g = rgb[:, :, 1].astype(np.float32)
        b = rgb[:, :, 2].astype(np.float32)
        brightness = 0.299 * r + 0.587 * g + 0.114 * b

    char_map = _select_chars(brightness, algorithm)

    if color_mode == COLOR_BW:
        lines = []
        for row in range(height):
            lines.append(''.join(char_map[row]))
        return '\n'.join(lines)

    elif color_mode == COLOR_COLORED:
        lines = []
        for row in range(height):
            parts = []
            for col in range(width):
                rv = int(rgb[row, col, 0])
                gv = int(rgb[row, col, 1])
                bv = int(rgb[row, col, 2])
                ch = char_map[row, col]
                parts.append(f"\033[38;2;{rv};{gv};{bv}m{ch}")
            parts.append(RESET)
            lines.append(''.join(parts))
        return '\n'.join(lines)

    else:
        lines = []
        for row in range(height):
            parts = []
            for col in range(width):
                g_val = int(gray[row, col])
                ch = char_map[row, col]
                parts.append(f"\033[38;2;{g_val};{g_val};{g_val}m{ch}")
            parts.append(RESET)
            lines.append(''.join(parts))
        return '\n'.join(lines)


def image_to_ascii(image_path, width, color_mode=COLOR_COLORED, algorithm=ALGO_CHARS):
    img = cv2.imread(image_path)
    if img is None:
        print_error(f"Cannot read image: {image_path}")
        return None
    return frame_to_ascii(img, width, color_mode, algorithm)


class AudioPlayer:
    def __init__(self, audio_path):
        self.audio_path = audio_path
        self.process = None
        self._start_offset = 0.0
        self._play_real_start = 0.0
        self.paused_at = 0.0
        self.is_playing = False
        self.is_muted = False
        self.speed = 1.0

    def play(self, start_offset=0, speed=1.0):
        self._kill()
        self.speed = speed
        self._start_offset = start_offset
        self._play_real_start = time.time()
        try:
            cmd = [
                'ffplay', '-nodisp', '-autoexit',
                '-loglevel', 'quiet',
                '-ss', str(start_offset),
            ]
            if speed != 1.0:
                cmd.extend(['-af', self._build_atempo(speed)])
            cmd.extend(['-i', self.audio_path])
            self.process = subprocess.Popen(
                cmd, stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            self.is_playing = True
        except FileNotFoundError:
            print_warn("ffplay not found. Audio playback disabled.")

    @staticmethod
    def _build_atempo(speed):
        if 0.5 <= speed <= 2.0:
            return f"atempo={speed:.4f}"
        filters = []
        remaining = speed
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        filters.append(f"atempo={remaining:.4f}")
        return ",".join(filters)

    def get_position(self):
        if self.is_playing:
            return self._start_offset + (time.time() - self._play_real_start) * self.speed
        return self.paused_at

    def pause(self):
        if self.is_playing:
            self.paused_at = self.get_position()
            self._kill()
            self.is_playing = False

    def resume(self):
        if not self.is_playing:
            self.play(start_offset=self.paused_at, speed=self.speed)

    def toggle_mute(self):
        if self.is_muted:
            self.resume()
            self.is_muted = False
        else:
            self.pause()
            self.is_muted = True

    def stop(self):
        self._kill()
        self.is_playing = False

    def replay(self):
        self._kill()
        self.is_playing = False
        self.is_muted = False
        self.play(start_offset=0)

    def set_speed(self, speed):
        current_pos = self.get_position() if self.is_playing else self.paused_at
        was_playing = self.is_playing and not self.is_muted
        self._kill()
        self.is_playing = False
        self.speed = speed
        if was_playing:
            self.play(start_offset=current_pos, speed=speed)
        else:
            self.paused_at = current_pos

    def seek(self, position_seconds):
        position_seconds = max(0.0, position_seconds)
        was_playing = self.is_playing and not self.is_muted
        self._kill()
        self.is_playing = False
        if was_playing:
            self.play(start_offset=position_seconds, speed=self.speed)
        else:
            self.paused_at = position_seconds

    def _kill(self):
        if self.process:
            try:
                self.process.kill()
                self.process.wait(timeout=2)
            except Exception:
                pass
            self.process = None


class KeyListener:
    def __init__(self):
        self._queue = deque()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._old_term = None
        try:
            fd = sys.stdin.fileno()
            self._old_term = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            self._old_term = None
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        import select as sel
        while not self._stop_event.is_set():
            try:
                ready, _, _ = sel.select([sys.stdin], [], [], 0.05)
                if not ready:
                    continue
                ch = sys.stdin.read(1)
                if not ch:
                    continue

                if ch == '\x1b':
                    import select as _sel
                    got_more = False
                    while True:
                        r, _, _ = _sel.select([sys.stdin], [], [], 0.01)
                        if r:
                            sys.stdin.read(1)
                            got_more = True
                        else:
                            break
                    if not got_more:
                        with self._lock:
                            self._queue.append('\x1b')
                    continue
                else:
                    resolved = ch.lower()
                    with self._lock:
                        self._queue.append(resolved)
            except Exception:
                pass

    def get_key(self):
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def drain_keys(self):
        with self._lock:
            keys = list(self._queue)
            self._queue.clear()
            return keys

    def stop(self):
        self._stop_event.set()
        if self._old_term is not None:
            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old_term)
            except Exception:
                pass


def truncate_ansi_line(line, max_chars):
    result = []
    visible_count = 0
    i = 0
    while i < len(line) and visible_count < max_chars:
        if line[i] == '\033':
            end = line.find('m', i)
            if end != -1:
                result.append(line[i:end+1])
                i = end + 1
                continue
        result.append(line[i])
        visible_count += 1
        i += 1
    if visible_count >= max_chars:
        result.append(RESET)
    return ''.join(result)


def truncate_ascii_frame(ascii_frame, max_width, max_height=None):
    lines = ascii_frame.split('\n')
    if max_height is not None and len(lines) > max_height:
        lines = lines[:max_height]
    truncated = []
    for line in lines:
        if '\033[' in line:
            truncated.append(truncate_ansi_line(line, max_width))
        else:
            truncated.append(line[:max_width])
    return '\n'.join(truncated)


def _build_hints(color_mode, algorithm, paused, sound_on, has_audio, is_video=True, speed=1.0):
    parts = []

    for i, cm in enumerate(COLOR_MODES):
        if cm == color_mode:
            style = _COLOR_HINT_STYLE[cm]
            parts.append(f"{BOLD}{style}{i+1}:{COLOR_LABELS[cm]}{RESET}")
        else:
            parts.append(f"{DIM}{C_GRAY}{i+1}:{COLOR_LABELS[cm]}{RESET}")

    for i, am in enumerate(ALGORITHM_MODES):
        if am == algorithm:
            style = _ALGO_HINT_STYLE[am]
            parts.append(f"{BOLD}{style}{i+4}:{ALGO_LABELS[am]}{RESET}")
        else:
            parts.append(f"{DIM}{C_GRAY}{i+4}:{ALGO_LABELS[am]}{RESET}")

    if is_video:
        seek_label = "Step" if paused else "Seek"
        parts.append(f"{C_GRAY}[J/L]{RESET}{seek_label}")

        speed_style = C_GREEN if speed == 1.0 else C_YELLOW
        parts.append(f"{C_GRAY}[I/K]{RESET}{speed_style}x{speed:.2f}{RESET}")

        pause_label = "Resume" if paused else "Pause"
        parts.append(f"{C_GRAY}[P]{RESET}{pause_label}")
        if has_audio:
            sound_style = C_GREEN if sound_on else C_RED
            parts.append(f"{C_GRAY}[S]{RESET}{sound_style}{'ON' if sound_on else 'OFF'}{RESET}")
        parts.append(f"{C_GRAY}[R]{RESET}eplay")

    parts.append(f"{C_GRAY}[Q]{RESET}uit")

    return "  " + "  ".join(parts) + RESET


def play_ascii_image(image_path, color_mode=COLOR_COLORED, algorithm=ALGO_CHARS):
    img = cv2.imread(image_path)
    if img is None:
        print_error(f"Cannot read image: {image_path}")
        return

    h, w = img.shape[:2]
    display_width = compute_display_width_for_terminal(w, h)

    ascii_art = frame_to_ascii(img, display_width, color_mode, algorithm)

    term_w = get_terminal_width()
    term_h = get_terminal_height() - 3
    ascii_art = truncate_ascii_frame(ascii_art, term_w, max_height=term_h)

    sys.stdout.write(ALT_SCREEN_ON)
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(CLEAR_SCREEN + CURSOR_HOME)
    sys.stdout.write(ascii_art)
    sys.stdout.write(RESET + "\n")
    hints = _build_hints(color_mode, algorithm, False, False, False, is_video=False)
    sys.stdout.write(hints)
    sys.stdout.flush()

    listener = KeyListener()
    try:
        while True:
            keys = listener.drain_keys()
            should_quit = False
            should_redraw = False

            for key in keys:
                if key == 'q' or key == '\x03':
                    should_quit = True
                    break
                elif key == '\x1b':
                    should_quit = True
                    break
                elif key in ('\n', '\r'):
                    should_quit = True
                    break
                elif key == '1':
                    color_mode = COLOR_COLORED
                    should_redraw = True
                elif key == '2':
                    color_mode = COLOR_BW
                    should_redraw = True
                elif key == '3':
                    color_mode = COLOR_GRAY
                    should_redraw = True
                elif key == '4':
                    algorithm = ALGO_CHARS
                    should_redraw = True
                elif key == '5':
                    algorithm = ALGO_BLOCKS
                    should_redraw = True
                elif key == '6':
                    algorithm = ALGO_DOTS
                    should_redraw = True

            if should_quit:
                break

            if should_redraw:
                ascii_art = frame_to_ascii(img, display_width, color_mode, algorithm)
                ascii_art = truncate_ascii_frame(ascii_art, term_w, max_height=term_h)
                sys.stdout.write(CURSOR_HOME)
                sys.stdout.write(ascii_art)
                sys.stdout.write(RESET + "\n")
                hints = _build_hints(color_mode, algorithm, False, False, False, is_video=False)
                sys.stdout.write(hints)
                sys.stdout.flush()
            else:
                time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.write(ALT_SCREEN_OFF)
        sys.stdout.flush()


def play_ascii_video(video_path, color_mode=None, algorithm=None):
    if color_mode is None:
        color_mode = COLOR_COLORED
    if algorithm is None:
        algorithm = ALGO_CHARS

    cap_preview = cv2.VideoCapture(video_path)
    if not cap_preview.isOpened():
        print_error("Cannot open video file.")
        return
    src_w = int(cap_preview.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap_preview.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap_preview.release()

    display_width = compute_display_width_for_terminal(src_w, src_h)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print_error("Cannot open video file.")
        return

    meta = get_video_metadata(video_path)
    if not meta:
        print_error("Cannot read video metadata.")
        cap.release()
        return

    fps = meta['fps']
    total_frames = meta['total_frames']
    duration = meta['duration']

    speed_idx = SPEED_DEFAULT_IDX
    speed = SPEED_STEPS[speed_idx]

    has_audio = has_audio_track(video_path)
    audio_player = None
    sound_on = has_audio

    if has_audio:
        audio_path = str(TEMP_DIR / f"audio_{int(time.time())}.wav")
        print_step("Extracting audio...")
        if extract_audio(video_path, audio_path):
            audio_player = AudioPlayer(audio_path)
        else:
            print_warn("Audio extraction failed. Playing without sound.")
            sound_on = False
            has_audio = False

    sys.stdout.write(ALT_SCREEN_ON)
    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.write(CLEAR_SCREEN)
    sys.stdout.flush()

    if audio_player:
        audio_player.play()

    listener = KeyListener()
    paused = False
    frame_count = 0
    last_frame_raw = None
    video_ended = False

    def _display_frame(frame, show_meter=True):
        ascii_art = frame_to_ascii(frame, display_width, color_mode, algorithm)
        sys.stdout.write(CURSOR_HOME)
        sys.stdout.write(ascii_art)
        if show_meter:
            progress = frame_count / max(total_frames, 1) if total_frames > 0 else 0
            bar_len = 30
            filled = int(bar_len * progress)
            bar = "█" * filled + "░" * (bar_len - filled)
            current_time = frame_count / max(fps, 1)
            speed_str = f"x{speed:.2f}"
            meter = f"\n{RESET}{C_GRAY}[{bar}] {progress*100:.0f}% | {format_time(current_time)} / {format_time(duration)} | {speed_str}{RESET}"
            hints = _build_hints(color_mode, algorithm, paused, sound_on, has_audio, is_video=True, speed=speed)
            sys.stdout.write(meter + "\n" + hints)
        sys.stdout.flush()

    try:
        while True:
            t_start = time.perf_counter()

            keys = listener.drain_keys()
            should_quit = False
            mode_changed = False
            need_pause_display = False

            seek_offset = 0.0
            frame_step = 0

            for key in keys:
                if key == 'q' or key == '\x03':
                    should_quit = True
                    break
                elif key == '\x1b':
                    should_quit = True
                    break
                elif key == 'p':
                    paused = not paused
                    if audio_player and sound_on:
                        if paused:
                            audio_player.pause()
                        else:
                            audio_player.resume()
                elif key == 'r':
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    video_ended = False
                    paused = False
                    last_frame_raw = None
                    seek_offset = 0.0
                    frame_step = 0
                    if audio_player:
                        audio_player.replay()
                        if speed != 1.0:
                            audio_player.set_speed(speed)
                    sys.stdout.write(CLEAR_SCREEN + CURSOR_HOME)
                    sys.stdout.flush()
                    break
                elif key == 's' and has_audio:
                    sound_on = not sound_on
                    if audio_player:
                        audio_player.toggle_mute()
                elif key == 'j':
                    if paused:
                        frame_step -= 1
                    else:
                        seek_offset -= 5.0
                elif key == 'l':
                    if paused:
                        frame_step += 1
                    else:
                        seek_offset += 5.0
                elif key == 'i':
                    if speed_idx < len(SPEED_STEPS) - 1:
                        speed_idx += 1
                        speed = SPEED_STEPS[speed_idx]
                        if audio_player and sound_on and not audio_player.is_muted:
                            audio_player.set_speed(speed)
                        if (paused or video_ended) and last_frame_raw is not None:
                            _display_frame(last_frame_raw)
                elif key == 'k':
                    if speed_idx > 0:
                        speed_idx -= 1
                        speed = SPEED_STEPS[speed_idx]
                        if audio_player and sound_on and not audio_player.is_muted:
                            audio_player.set_speed(speed)
                        if (paused or video_ended) and last_frame_raw is not None:
                            _display_frame(last_frame_raw)
                elif key == '1':
                    color_mode = COLOR_COLORED
                    mode_changed = True
                elif key == '2':
                    color_mode = COLOR_BW
                    mode_changed = True
                elif key == '3':
                    color_mode = COLOR_GRAY
                    mode_changed = True
                elif key == '4':
                    algorithm = ALGO_CHARS
                    mode_changed = True
                elif key == '5':
                    algorithm = ALGO_BLOCKS
                    mode_changed = True
                elif key == '6':
                    algorithm = ALGO_DOTS
                    mode_changed = True

            if should_quit:
                break

            if seek_offset != 0.0:
                current_time = frame_count / max(fps, 1)
                seek_time = max(0.0, min(duration, current_time + seek_offset))
                target_frame = max(0, min(total_frames - 1, int(seek_time * fps)))
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                frame_count = target_frame - 1
                video_ended = False
                if audio_player and sound_on:
                    audio_player.seek(seek_time)

            if frame_step != 0:
                target = max(0, min(total_frames - 1, frame_count + frame_step))
                if target != frame_count:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target)
                    ret, frame = cap.read()
                    if ret:
                        frame_count = target
                        last_frame_raw = frame
                        video_ended = False
                        need_pause_display = True

            if need_pause_display:
                _display_frame(last_frame_raw)
            elif mode_changed and last_frame_raw is not None and (paused or video_ended):
                _display_frame(last_frame_raw)

            if video_ended:
                time.sleep(0.05)
                continue

            if paused:
                time.sleep(0.02)
                continue

            ret, frame = cap.read()
            if not ret:
                video_ended = True
                if last_frame_raw is not None:
                    ascii_art = frame_to_ascii(last_frame_raw, display_width, color_mode, algorithm)
                    sys.stdout.write(CURSOR_HOME)
                    sys.stdout.write(ascii_art)
                completion = f"\n{RESET}{C_GREEN}  \u25b6 Playback complete!{RESET}"
                hints = _build_hints(color_mode, algorithm, paused, sound_on, has_audio, is_video=True, speed=speed)
                sys.stdout.write(completion + "\n" + hints)
                sys.stdout.flush()
                continue

            frame_count += 1
            last_frame_raw = frame

            _display_frame(frame)

            frame_delay = (1.0 / fps) / speed
            elapsed = time.perf_counter() - t_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        cap.release()
        if audio_player:
            audio_player.stop()
        sys.stdout.write(SHOW_CURSOR + RESET)
        sys.stdout.write(ALT_SCREEN_OFF)
        sys.stdout.flush()


def parse_ansi_colored_line(line):
    result = []
    i = 0
    current_color = (255, 255, 255)
    while i < len(line):
        if line[i] == '\033' and i + 1 < len(line) and line[i + 1] == '[':
            end = line.find('m', i)
            if end != -1:
                seq = line[i + 2:end]
                if seq.startswith('38;2;'):
                    parts = seq.split(';')
                    if len(parts) >= 5:
                        try:
                            current_color = (int(parts[2]), int(parts[3]), int(parts[4]))
                        except ValueError:
                            pass
                elif seq == '0':
                    current_color = (255, 255, 255)
                i = end + 1
                continue
        if line[i] not in ('\033', '['):
            result.append((line[i], *current_color))
        i += 1
    return result


def find_monospace_font():
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeMono.ttf',
        '/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf',
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            return fp
    return None


def ascii_to_rgb_image(ascii_frame, has_ansi, char_w=7, char_h=14, font_size=12):
    lines = ascii_frame.split('\n')
    font_path = find_monospace_font()

    max_len = 0
    parsed_lines = []
    for line in lines:
        if has_ansi:
            parsed = parse_ansi_colored_line(line)
            parsed_lines.append(parsed)
            max_len = max(max_len, len(parsed))
        else:
            parsed_lines.append(line)
            max_len = max(max_len, len(line))

    if max_len == 0:
        return np.zeros((1, 1, 3), dtype=np.uint8)

    img_w = max_len * char_w
    img_h = len(lines) * char_h

    img = Image.new('RGB', (img_w, img_h), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        if font_path:
            font = ImageFont.truetype(font_path, font_size)
        else:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    for y, line_data in enumerate(parsed_lines):
        y_pos = y * char_h
        if has_ansi:
            x_pos = 0
            for ch, r, g, b in line_data:
                draw.text((x_pos, y_pos), ch, font=font, fill=(r, g, b))
                x_pos += char_w
        else:
            draw.text((0, y_pos), line_data, font=font, fill=(255, 255, 255))

    return np.array(img)


def render_png(ascii_frame, output_path, has_ansi):
    img = ascii_to_rgb_image(ascii_frame, has_ansi)
    pil_img = Image.fromarray(img)
    pil_img.save(output_path)
    return output_path


def render_mp4(video_path, media_width, color_mode, algorithm, fps, audio_path, output_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print_error("Cannot open video for rendering.")
        return None

    has_ansi = color_mode in (COLOR_COLORED, COLOR_GRAY)

    ret, first_frame = cap.read()
    if not ret:
        print_error("Cannot read video frames.")
        cap.release()
        return None

    first_ascii = frame_to_ascii(first_frame, media_width, color_mode, algorithm)
    sample_img = ascii_to_rgb_image(first_ascii, has_ansi)
    render_h, render_w = sample_img.shape[:2]

    cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo', '-pixel_format', 'rgb24',
        '-video_size', f'{render_w}x{render_h}',
        '-framerate', str(fps),
        '-i', 'pipe:0',
    ]
    if audio_path and os.path.exists(audio_path):
        cmd.extend(['-i', audio_path])
    cmd.extend([
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-pix_fmt', 'yuv420p',
    ])
    if audio_path and os.path.exists(audio_path):
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
    cmd.append(output_path)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    try:
        proc.stdin.write(sample_img.tobytes())
    except BrokenPipeError:
        cap.release()
        proc.stdin.close()
        proc.wait()
        print_error("ffmpeg pipe broke on first frame.")
        return None

    frame_count = 1
    meta = get_video_metadata(video_path)
    total = meta['total_frames'] if meta else 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ascii_art = frame_to_ascii(frame, media_width, color_mode, algorithm)
        rgb = ascii_to_rgb_image(ascii_art, has_ansi)
        if rgb.shape[0] != render_h or rgb.shape[1] != render_w:
            pil_img = Image.fromarray(rgb).resize((render_w, render_h))
            rgb = np.array(pil_img)
        try:
            proc.stdin.write(rgb.tobytes())
        except BrokenPipeError:
            break
        frame_count += 1
        if total > 0 and frame_count % 30 == 0:
            pct = frame_count / total * 100
            print(f"\r  Rendering... {pct:.0f}% ({frame_count}/{total})", end='', flush=True)

    if total > 0:
        print(f"\r  Rendering... 100% ({frame_count}/{total})")
    cap.release()

    try:
        proc.stdin.close()
    except BrokenPipeError:
        pass
    proc.wait()

    if proc.returncode == 0:
        return output_path
    else:
        try:
            stderr_output = proc.stderr.read().decode()[-300:]
        except Exception:
            stderr_output = "unknown error"
        print_error(f"ffmpeg encoding failed: {stderr_output}")
        return None


def ask_choice(prompt, options, default=1):
    print(f"\n  {C_CYAN}{prompt}{RESET}")
    for i, opt in enumerate(options, 1):
        marker = f" {C_YELLOW}[default]{RESET}" if i == default else ""
        print(f"    {BOLD}{i}.{RESET} {opt}{marker}")
    while True:
        try:
            choice = input(f"  {C_WHITE}▸{RESET} ").strip()
            if not choice:
                return default
            n = int(choice)
            if 1 <= n <= len(options):
                return n
            print_error(f"Choose between 1-{len(options)}")
        except ValueError:
            print_error("Enter a number")
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)


def ask_path(prompt, is_export=False, expected_type=None):
    while True:
        try:
            path = input(f"  {C_WHITE}▸{RESET} {prompt}: ").strip().strip('"').strip("'")
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if not path:
            return None
        if is_export:
            result = validate_export_path(path)
            if result:
                return result
            print_error("Invalid path. Try again.")
        else:
            if is_url(path):
                if expected_type == 'image':
                    print_error("URLs are not supported for images. Please provide a local file path.")
                    continue
                return path
            validated = validate_media_path(path)
            if validated:
                if expected_type:
                    ext = os.path.splitext(validated)[1].lower()
                    if expected_type == 'image' and ext not in IMAGE_EXTENSIONS:
                        print_error(f"Not an image file. Supported formats: {', '.join(sorted(IMAGE_EXTENSIONS))}")
                        continue
                    elif expected_type == 'video' and ext not in VIDEO_EXTENSIONS:
                        print_error(f"Not a video file. Supported formats: {', '.join(sorted(VIDEO_EXTENSIONS))}")
                        continue
                return validated
            print_error(f"File not found: {path}")


def ask_yes_no(prompt, default='n'):
    default_str = 'Y/n' if default == 'y' else 'y/N'
    while True:
        try:
            answer = input(f"  {C_WHITE}▸{RESET} {prompt} ({default_str}): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return default == 'y'
        if not answer:
            return default == 'y'
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print_error("Enter y or n")


def generate_output_name(media_type, original_name, extension):
    ts = int(time.time())
    name = sanitize_filename(original_name)
    return f"ASCIIDEIA_{media_type}_{name}_{ts}.{extension}"


def run_interactive():
    while True:
        print(BANNER)
        print(f"  {C_GRAY}ASCII Art Media Converter & Player{RESET}")
        print(f"  {C_GRAY}{'─' * 50}{RESET}")
        print()

        clear_temp()
        clear_results()

        choice = ask_choice("Media type?", ["Image", "Video"], default=2)
        is_video = (choice == 2)

        if is_video:
            path = ask_path("Path to video file or URL", expected_type='video')
        else:
            path = ask_path("Path to image file", expected_type='image')
        if not path:
            print_error("No path provided.")
            if ask_choice("What next?", ["Start again", "Exit"], default=1) == 2:
                break
            continue

        original_name = "local"
        source = "local"

        if is_url(path):
            source = detect_platform(path) or "url"
            print_step(f"Detected {source} URL. Downloading...")
            local_path, title = download_video(path)
            if not local_path:
                print_error("Download failed.")
                if ask_choice("What next?", ["Start again", "Exit"], default=1) == 2:
                    break
                continue
            path = local_path
            original_name = title or "downloaded"
            print_info(f"Downloaded: {original_name}")
        else:
            original_name = os.path.splitext(os.path.basename(path))[0]

        has_audio = False
        fps = 30.0
        if is_video:
            meta = get_video_metadata(path)
            if not meta:
                print_error("Cannot read video metadata.")
                if ask_choice("What next?", ["Start again", "Exit"], default=1) == 2:
                    break
                continue
            src_w, src_h = meta['width'], meta['height']
            fps = meta['fps']
            has_audio = has_audio_track(path)
            print_info(f"Video: {src_w}x{src_h} @ {fps:.1f} FPS | Audio: {'Yes' if has_audio else 'No'} | {format_time(meta['duration'])}")
        else:
            img_meta = get_image_metadata(path)
            if not img_meta:
                print_error("Cannot read image metadata.")
                if ask_choice("What next?", ["Start again", "Exit"], default=1) == 2:
                    break
                continue
            src_w, src_h = img_meta['width'], img_meta['height']
            print_info(f"Image: {src_w}x{src_h} | Format: {img_meta.get('format', '?')}")

        display_width = compute_display_width_for_terminal(src_w, src_h)
        display_h = compute_ascii_height(display_width, src_w, src_h)
        print_info(f"Terminal: {display_width}x{display_h} chars")

        if ask_yes_no("Render as standard media?", 'n'):
            _do_render(path, is_video, original_name)

        if is_video:
            play_ascii_video(path)
        else:
            play_ascii_image(path)

        if ask_choice("What next?", ["Start again", "Exit"], default=1) == 2:
            break


def _do_render(path, is_video, original_name):
    clear_results()

    choice = ask_choice("Render color mode?", ["Colored", "Black & White", "Grayscale"], default=1)
    color_mode = COLOR_MODES[choice - 1]

    choice = ask_choice("Render algorithm?", ["Characters", "Blocks", "Dots"], default=1)
    algorithm = ALGORITHM_MODES[choice - 1]

    has_ansi = color_mode in (COLOR_COLORED, COLOR_GRAY)

    if is_video:
        meta = get_video_metadata(path)
        if not meta:
            print_error("Cannot read video metadata for rendering.")
            return
        fps = meta['fps']
        has_audio = has_audio_track(path)
        media_width = meta['width']

        fname = generate_output_name('video', original_name, 'mp4')
        out_path = str(RESULTS_DIR / fname)

        audio_render_path = None
        if has_audio:
            audio_render_path = str(TEMP_DIR / f"audio_render_{int(time.time())}.wav")
            if not extract_audio(path, audio_render_path):
                audio_render_path = None

        print_step("Rendering video... This may take a while.")
        result = render_mp4(path, media_width, color_mode, algorithm, fps, audio_render_path, out_path)
        if result:
            print_info(f"Saved to {out_path}")
            _open_file(out_path)
        else:
            print_error("Video rendering failed.")
    else:
        img_meta = get_image_metadata(path)
        if not img_meta:
            print_error("Cannot read image metadata for rendering.")
            return
        media_width = img_meta['width']

        fname = generate_output_name('image', original_name, 'png')
        out_path = str(RESULTS_DIR / fname)

        ascii_art = image_to_ascii(path, media_width, color_mode, algorithm)
        if ascii_art:
            render_png(ascii_art, out_path, has_ansi)
            print_info(f"Saved to {out_path}")
            _open_file(out_path)


def _open_file(filepath):
    try:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', filepath])
        elif sys.platform == 'win32':
            os.startfile(filepath)
        else:
            subprocess.Popen(['xdg-open', filepath], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def parse_oneline(args):
    if not args:
        return None

    config = {
        'mode': None,
        'path': None,
        'color': 'colored',
        'algo': 'chars',
        'render': None,
    }

    i = 0
    if i >= len(args):
        return None
    mode = args[i].lower()
    if mode not in ('image', 'video', 'i', 'v', 'img', 'vid'):
        return None

    if mode in ('image', 'i', 'img'):
        config['mode'] = 'image'
    elif mode in ('video', 'v', 'vid'):
        config['mode'] = 'video'

    i += 1
    if i >= len(args):
        print_error("No path provided.")
        sys.exit(1)
    config['path'] = args[i]
    i += 1

    while i < len(args):
        flag = args[i].lower()
        if flag in ('color', 'colour', 'c') and i + 1 < len(args):
            i += 1
            val = args[i].lower()
            if val in ('colored', 'colour', 'color', 'all'):
                config['color'] = 'colored'
            elif val in ('bw', 'black', 'blackwhite', 'blackwhite'):
                config['color'] = 'bw'
            elif val in ('gray', 'grey', 'grayscale', 'greyscale'):
                config['color'] = 'gray'
            else:
                print_warn(f"Unknown color mode '{val}', using colored.")
                config['color'] = 'colored'
        elif flag in ('algo', 'algorithm', 'a') and i + 1 < len(args):
            i += 1
            val = args[i].lower()
            if val in ('chars', 'characters', 'c'):
                config['algo'] = 'chars'
            elif val in ('blocks', 'block', 'b'):
                config['algo'] = 'blocks'
            elif val in ('dots', 'dot', 'd', 'braille'):
                config['algo'] = 'dots'
            else:
                print_warn(f"Unknown algorithm '{val}', using chars.")
                config['algo'] = 'chars'
        elif flag in ('render', 'r') and i + 1 < len(args):
            i += 1
            config['render'] = args[i]
        else:
            print_warn(f"Unknown flag: {flag}")
        i += 1

    return config


def run_oneline(config):
    clear_temp()
    clear_results()

    color_mode = config['color']
    if color_mode not in COLOR_MODES:
        color_mode = COLOR_COLORED

    algorithm = config['algo']
    if algorithm not in ALGORITHM_MODES:
        algorithm = ALGO_CHARS

    path = config['path']
    original_name = "local"

    if is_url(path):
        source = detect_platform(path) or "url"
        print_step(f"Downloading from {source}...")
        local_path, title = download_video(path)
        if not local_path:
            sys.exit(1)
        path = local_path
        original_name = title or "downloaded"
    else:
        validated = validate_media_path(path)
        if not validated:
            print_error(f"File not found: {path}")
            sys.exit(1)
        is_video = config['mode'] == 'video'
        ext = os.path.splitext(validated)[1].lower()
        if not is_video and ext not in IMAGE_EXTENSIONS:
            print_error(f"Not an image file. Supported: {', '.join(sorted(IMAGE_EXTENSIONS))}")
            sys.exit(1)
        if is_video and ext not in VIDEO_EXTENSIONS:
            print_error(f"Not a video file. Supported: {', '.join(sorted(VIDEO_EXTENSIONS))}")
            sys.exit(1)
        path = validated
        original_name = os.path.splitext(os.path.basename(path))[0]

    is_video = config['mode'] == 'video'

    has_audio = False
    fps = 30.0
    if is_video:
        meta = get_video_metadata(path)
        if not meta:
            print_error("Cannot read video metadata.")
            sys.exit(1)
        src_w, src_h = meta['width'], meta['height']
        fps = meta['fps']
        has_audio = has_audio_track(path)
        print_info(f"Video: {src_w}x{src_h} @ {fps:.1f} FPS")
    else:
        img_meta = get_image_metadata(path)
        if not img_meta:
            print_error("Cannot read image metadata.")
            sys.exit(1)
        src_w, src_h = img_meta['width'], img_meta['height']

    display_width = compute_display_width_for_terminal(src_w, src_h)
    print_info(f"Terminal: {display_width}x{compute_ascii_height(display_width, src_w, src_h)} chars")

    if config['render']:
        render_folder = validate_export_path(config['render'])
        if render_folder:
            has_ansi = color_mode in (COLOR_COLORED, COLOR_GRAY)
            if is_video:
                fname = generate_output_name('video', original_name, 'mp4')
                out_path = os.path.join(render_folder, fname)
                audio_render_path = None
                if has_audio:
                    audio_render_path = str(TEMP_DIR / f"audio_render_{int(time.time())}.wav")
                    extract_audio(path, audio_render_path)
                print_step("Rendering video...")
                result = render_mp4(path, src_w, color_mode, algorithm, fps, audio_render_path, out_path)
                if result:
                    print_info(f"Saved to {out_path}")
            else:
                fname = generate_output_name('image', original_name, 'png')
                out_path = os.path.join(render_folder, fname)
                ascii_art = image_to_ascii(path, src_w, color_mode, algorithm)
                if ascii_art:
                    render_png(ascii_art, out_path, has_ansi)
                    print_info(f"Saved to {out_path}")

    if is_video:
        play_ascii_video(path, color_mode, algorithm)
    else:
        play_ascii_image(path, color_mode, algorithm)


def show_help():
    print(BANNER)
    print(f"  {BOLD}ASCIIDEIA{RESET} — ASCII Art Media Converter & Player")
    print()
    print(f"  {C_CYAN}Usage:{RESET}")
    print(f"    python asciideia.py                                    {C_GRAY}# Interactive mode{RESET}")
    print(f"    python asciideia.py image \"photo.png\"                  {C_GRAY}# One-line image{RESET}")
    print(f"    python asciideia.py video \"clip.mp4\"                   {C_GRAY}# One-line video{RESET}")
    print(f"    python asciideia.py video \"clip.mp4\" algo dots         {C_GRAY}# With algorithm{RESET}")
    print(f"    python asciideia.py video \"clip.mp4\" render \"out/\"     {C_GRAY}# Render to file{RESET}")
    print()
    print(f"  {C_CYAN}Flags:{RESET}")
    print(f"    {BOLD}color{RESET}  colored|bw|gray    Color mode (default: colored)")
    print(f"    {BOLD}algo{RESET}   chars|blocks|dots  Algorithm (default: chars)")
    print(f"    {BOLD}render{RESET} \"path\"             Render as PNG/MP4")
    print()
    print(f"  {C_CYAN}In-terminal controls:{RESET}")
    print(f"    {BOLD}1/2/3{RESET}  Colored / BW / Grayscale")
    print(f"    {BOLD}4/5/6{RESET}  Characters / Blocks / Dots")
    print(f"    {BOLD}J/L{RESET}    Seek \u00b15s / Step frame   (video only)")
    print(f"    {BOLD}I/K{RESET}    Speed x0.25\u2013x2.00     (video only)")
    print(f"    {BOLD}P{RESET}      Pause / Resume          (video only)")
    print(f"    {BOLD}S{RESET}      Toggle sound            (video only)")
    print(f"    {BOLD}R{RESET}      Replay                  (video only)")
    print(f"    {BOLD}Q{RESET}      Quit")
    print()
    print(f"  {C_CYAN}Render as standard media:{RESET}")
    print(f"    Produces a baked PNG or MP4 file with the chosen color & algorithm.")
    print(f"    In interactive mode, color and algorithm questions are asked when rendering.")
    print(f"    In oneline mode, use the {BOLD}color{RESET} and {BOLD}algo{RESET} flags.")
    print(f"    If not specified, defaults to colored characters.")
    print()
    print(f"  {C_CYAN}Supported sources:{RESET}")
    print(f"    Local images: {', '.join(sorted(IMAGE_EXTENSIONS))}")
    print(f"    Local videos: {', '.join(sorted(VIDEO_EXTENSIONS))}")
    print(f"    YouTube URLs: youtube.com, youtu.be")
    print(f"    TikTok URLs:  tiktok.com, vm.tiktok.com")
    print()


def main():
    try:
        clear_temp()

        if len(sys.argv) > 1:
            arg1 = sys.argv[1].lower()
            if arg1 in ('-h', '--help', 'help'):
                show_help()
                return
            config = parse_oneline(sys.argv[1:])
            if config:
                run_oneline(config)
            else:
                show_help()
        else:
            run_interactive()
    finally:
        purge_temp()


if __name__ == '__main__':
    main()
