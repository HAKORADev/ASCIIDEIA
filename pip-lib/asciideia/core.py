import cv2
import os
import re
import shutil
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

_IS_WINDOWS = sys.platform == 'win32'

def _enable_windows_ansi():
    if not _IS_WINDOWS:
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass

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

RENDER_MODERN = 'modern'
RENDER_RETRO = 'retro'
RENDER_MODES = [RENDER_MODERN, RENDER_RETRO]

RENDER_MODE_LABELS = {RENDER_MODERN: 'Modern', RENDER_RETRO: 'Retro'}

BG_DARK = 'dark'
BG_NONE = 'none'
BG_MODES = [BG_DARK, BG_NONE]
BG_LABELS = {BG_DARK: 'Dark', BG_NONE: 'Transparent'}

RETRO_CHAR_WIDTH = 140

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

_COLOR_DEPTH_24BIT = 3
_COLOR_DEPTH_256 = 2
_COLOR_DEPTH_16 = 1
_COLOR_DEPTH_NONE = 0

def _detect_color_depth():
    if not sys.stdout.isatty():
        return _COLOR_DEPTH_24BIT
    colorterm = os.environ.get('COLORTERM', '').lower()
    if colorterm in ('truecolor', '24bit'):
        return _COLOR_DEPTH_24BIT
    term = os.environ.get('TERM', '').lower()
    if '256color' in term:
        return _COLOR_DEPTH_256
    if not _IS_WINDOWS:
        try:
            result = subprocess.run(['tput', 'colors'], capture_output=True, text=True, timeout=2)
            n = int(result.stdout.strip())
            if n >= 16777216:
                return _COLOR_DEPTH_24BIT
            if n >= 256:
                return _COLOR_DEPTH_256
            if n >= 16:
                return _COLOR_DEPTH_16
            return _COLOR_DEPTH_NONE
        except Exception:
            pass
    else:
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            if mode.value & 0x0004:
                return _COLOR_DEPTH_24BIT
            return _COLOR_DEPTH_16
        except Exception:
            pass
    if term:
        return _COLOR_DEPTH_16
    return _COLOR_DEPTH_NONE

_COLOR_DEPTH = _detect_color_depth()

_256_CUBE = []
for _r in range(6):
    for _g in range(6):
        for _b in range(6):
            _256_CUBE.append((_r * 51 if _r else 0, _g * 51 if _g else 0, _b * 51 if _b else 0))

_16_PALETTE = [
    (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
    (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
    (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
    (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
]

def _rgb_to_256(r, g, b):
    best_idx = 16
    best_dist = float('inf')
    for i, (cr, cg, cb) in enumerate(_256_CUBE):
        dr = r - cr
        dg = g - cg
        db = b - cb
        d = dr * dr + dg * dg + db * db
        if d < best_dist:
            best_dist = d
            best_idx = i + 16
    gray_idx = int(round(0.299 * r + 0.587 * g + 0.114 * b) / 255 * 23) + 232
    gray_val = 8 + 10 * (gray_idx - 232)
    dr = r - gray_val
    dg = g - gray_val
    db = b - gray_val
    gray_dist = dr * dr + dg * dg + db * db
    if gray_dist < best_dist:
        best_idx = gray_idx
    return best_idx

def _rgb_to_16(r, g, b):
    best_idx = 0
    best_dist = float('inf')
    for i, (cr, cg, cb) in enumerate(_16_PALETTE):
        dr = r - cr
        dg = g - cg
        db = b - cb
        d = dr * dr + dg * dg + db * db
        if d < best_dist:
            best_dist = d
            best_idx = i
    return 30 + best_idx if best_idx < 8 else 90 + (best_idx - 8)

def _color_seq(r, g, b):
    if _COLOR_DEPTH >= _COLOR_DEPTH_24BIT:
        return f"\033[38;2;{r};{g};{b}m"
    if _COLOR_DEPTH >= _COLOR_DEPTH_256:
        return f"\033[38;5;{_rgb_to_256(r, g, b)}m"
    if _COLOR_DEPTH >= _COLOR_DEPTH_16:
        return f"\033[{_rgb_to_16(r, g, b)}m"
    return ""

def _select_chars(brightness, algorithm, bg=BG_DARK):
    ramp = ALGORITHM_RAMPS[algorithm]
    arr = _ALGORITHM_ARRAYS[algorithm]
    n_chars = len(ramp) - 1
    indices = np.clip((brightness / 255.0 * n_chars).astype(np.int32), 0, n_chars)
    char_map = arr[indices]
    if bg == BG_DARK:
        dark_mask = brightness < DARK_THRESHOLD
        char_map[dark_mask] = ' '
    return char_map

def frame_to_ascii(frame, width, color_mode, algorithm, bg=BG_DARK):
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
    char_map = _select_chars(brightness, algorithm, bg)
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
                parts.append(f"{_color_seq(rv, gv, bv)}{ch}")
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
                parts.append(f"{_color_seq(g_val, g_val, g_val)}{ch}")
            parts.append(RESET)
            lines.append(''.join(parts))
        return '\n'.join(lines)

def image_to_ascii(image_path, width, color_mode=COLOR_COLORED, algorithm=ALGO_CHARS, bg=BG_DARK):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    return frame_to_ascii(img, width, color_mode, algorithm, bg)

def _256_index_to_rgb(idx):
    if idx >= 232:
        v = 8 + 10 * (idx - 232)
        return (v, v, v)
    if idx >= 16:
        idx -= 16
        b = idx % 6
        g = (idx // 6) % 6
        r = idx // 36
        return (r * 51 if r else 0, g * 51 if g else 0, b * 51 if b else 0)
    return _16_PALETTE[idx] if idx < 16 else (255, 255, 255)

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
                elif seq.startswith('38;5;'):
                    try:
                        current_color = _256_index_to_rgb(int(seq.split(';')[-1]))
                    except ValueError:
                        pass
                elif seq.strip().isdigit() and int(seq.strip()) >= 30 and int(seq.strip()) <= 97:
                    code = int(seq.strip())
                    if code >= 90:
                        idx = code - 90 + 8
                    elif code >= 30:
                        idx = code - 30
                    else:
                        idx = 7
                    if 0 <= idx < 16:
                        current_color = _16_PALETTE[idx]
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

def ascii_to_rgb_image(ascii_frame, has_ansi, char_w=7, char_h=14, font_size=12, render_mode=RENDER_MODERN, bg=BG_DARK):
    lines = ascii_frame.split('\n')
    font_path = find_monospace_font()
    if render_mode == RENDER_RETRO:
        char_w = 10
        char_h = 20
        font_size = 18
    max_len = 0
    parsed_lines = []
    for line in lines:
        if has_ansi:
            parsed = parse_ansi_colored_line(line)
            max_len = max(max_len, len(parsed))
            parsed_lines.append(parsed)
        else:
            parsed_lines.append(list(line))
            max_len = max(max_len, len(line))
    img_w = max_len * char_w
    img_h = len(parsed_lines) * char_h
    if img_w <= 0 or img_h <= 0:
        return np.zeros((1, 1, 3), dtype=np.uint8)
    if bg == BG_NONE:
        img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    else:
        img = Image.new('RGB', (img_w, img_h), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    if font_path:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = ImageFont.load_default()
    else:
        font = ImageFont.load_default()
    for row_idx, line_data in enumerate(parsed_lines):
        y_pos = row_idx * char_h
        col_idx = 0
        for item in line_data:
            if isinstance(item, tuple) and len(item) == 4:
                ch, cr, cg, cb = item
            else:
                ch = item
                cr, cg, cb = 255, 255, 255
            x_pos = col_idx * char_w
            if ch and ch.strip():
                if bg == BG_NONE:
                    draw.text((x_pos, y_pos), ch, fill=(cr, cg, cb, 255), font=font)
                else:
                    draw.text((x_pos, y_pos), ch, fill=(cr, cg, cb), font=font)
            col_idx += 1
    return np.array(img)

def render_png(ascii_frame, output_path, has_ansi, render_mode=RENDER_MODERN, bg=BG_DARK):
    img_arr = ascii_to_rgb_image(ascii_frame, has_ansi, render_mode=render_mode, bg=bg)
    if bg == BG_NONE and img_arr.shape[2] == 4:
        pil_img = Image.fromarray(img_arr, 'RGBA')
    else:
        if img_arr.shape[2] == 4:
            img_arr = img_arr[:, :, :3]
        pil_img = Image.fromarray(img_arr, 'RGB')
    pil_img.save(output_path)
    return output_path

def render_mp4(video_path, media_width, color_mode, algorithm, fps, audio_path, output_path, render_mode=RENDER_MODERN, bg=BG_DARK):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        return None
    first_ascii = frame_to_ascii(first_frame, media_width, color_mode, algorithm, bg)
    first_rgb = ascii_to_rgb_image(first_ascii, color_mode != COLOR_BW, render_mode=render_mode, bg=bg)
    if first_rgb.shape[2] == 4:
        first_rgb = first_rgb[:, :, :3]
    render_h, render_w = first_rgb.shape[:2]
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
        '-f', 'rawvideo', '-pixel_format', 'rgb24',
        '-video_size', f'{render_w}x{render_h}', '-framerate', str(fps),
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
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except FileNotFoundError:
        cap.release()
        return None
    proc.stdin.write(first_rgb.tobytes())
    frame_count = 1
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        ascii_art = frame_to_ascii(frame, media_width, color_mode, algorithm, bg)
        rgb_arr = ascii_to_rgb_image(ascii_art, color_mode != COLOR_BW, render_mode=render_mode, bg=bg)
        if rgb_arr.shape[2] == 4:
            rgb_arr = rgb_arr[:, :, :3]
        if rgb_arr.shape[0] != render_h or rgb_arr.shape[1] != render_w:
            rgb_pil = Image.fromarray(rgb_arr, 'RGB')
            rgb_pil = rgb_pil.resize((render_w, render_h), Image.LANCZOS)
            rgb_arr = np.array(rgb_pil)
        proc.stdin.write(rgb_arr.tobytes())
        frame_count += 1
        if total_frames > 0 and frame_count % 30 == 0:
            pct = int(frame_count / total_frames * 100)
            sys.stderr.write(f"\r  Rendering... {pct}%")
            sys.stderr.flush()
    proc.stdin.close()
    proc.wait()
    cap.release()
    sys.stderr.write("\r  Rendering... done!\n")
    if proc.returncode != 0:
        return None
    return output_path

def format_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"

def sanitize_filename(name, max_len=50):
    sanitized = re.sub(r'[^\w\s-]', '', name)
    sanitized = re.sub(r'[\s]+', '-', sanitized.strip())
    return sanitized[:max_len] if sanitized else "untitled"

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
    except Exception:
        return False

def compute_display_width_for_terminal(src_w, src_h):
    try:
        term_w = os.get_terminal_size().columns
        term_h = os.get_terminal_size().lines
    except OSError:
        term_w = 80
        term_h = 24
    max_height = max(term_h - 3, 10)
    width = min(src_w, term_w)
    ascii_h = max(1, int(width * src_h / src_w / 2)) if src_w > 0 else max(1, width // 2)
    if ascii_h > max_height and max_height > 0:
        width = max(20, int(max_height * src_w / src_h * 2))
        width = min(width, term_w)
    return width

def compute_ascii_height(ascii_width, orig_w, orig_h):
    if orig_w <= 0 or orig_h <= 0:
        return max(1, ascii_width // 2)
    return max(1, int(ascii_width * orig_h / orig_w / 2))

def generate_output_name(media_type, original_name, color_mode, algorithm, extension):
    ts = int(time.time())
    safe_name = sanitize_filename(os.path.splitext(original_name)[0])
    return f"ASCIIDEIA_{media_type}_{safe_name}_{color_mode}_{algorithm}_{ts}.{extension}"
