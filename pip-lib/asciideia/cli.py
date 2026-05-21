import cv2
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import threading
from collections import deque
from pathlib import Path

from .core import (
    ALGO_CHARS, ALGO_BLOCKS, ALGO_DOTS,
    ALGORITHM_MODES, ALGORITHM_RAMPS,
    COLOR_COLORED, COLOR_BW, COLOR_GRAY,
    COLOR_MODES,
    RENDER_MODERN, RENDER_RETRO, RENDER_MODES,
    RENDER_MODE_LABELS,
    BG_DARK, BG_NONE, BG_MODES, BG_LABELS,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS,
    DARK_THRESHOLD, RETRO_CHAR_WIDTH,
    SPEED_STEPS, SPEED_DEFAULT_IDX,
    COLOR_LABELS, ALGO_LABELS,
    RESET, BOLD, DIM, CURSOR_UP, CURSOR_HOME, CLEAR_SCREEN,
    HIDE_CURSOR, SHOW_CURSOR, ALT_SCREEN_ON, ALT_SCREEN_OFF,
    C_CYAN, C_GREEN, C_YELLOW, C_RED, C_GRAY, C_MAGENTA, C_BLUE, C_WHITE,
    _color_seq, _select_chars, _detect_color_depth,
    _COLOR_HINT_STYLE, _ALGO_HINT_STYLE,
    frame_to_ascii, image_to_ascii,
    ascii_to_rgb_image, render_png, render_mp4,
    format_time, sanitize_filename, generate_output_name,
    get_video_metadata, get_image_metadata,
    has_audio_track, extract_audio,
    compute_display_width_for_terminal, compute_ascii_height,
    _enable_windows_ansi, _256_index_to_rgb, parse_ansi_colored_line,
)

from .api import (
    is_url, detect_platform, download_video,
    _validate_color, _validate_algo, _validate_render_mode, _validate_bg,
    _detect_media_type,
)

_IS_WINDOWS = sys.platform == 'win32'

if _IS_WINDOWS:
    import msvcrt
    import ctypes
else:
    import termios
    import tty

SCRIPT_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = Path(tempfile.gettempdir()) / "asciideia_temp"

BANNER = r"""
 █████  ███████  ██████ ██ ██ ██████  ███████ ██  █████
██   ██ ██      ██      ██ ██ ██   ██ ██      ██ ██   ██
███████ ███████ ██      ██ ██ ██   ██ █████   ██ ███████
██   ██      ██ ██      ██ ██ ██   ██ ██      ██ ██   ██
██   ██ ███████  ██████ ██ ██ ██████  ███████ ██ ██   ██
"""

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
            pass

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
        if not _IS_WINDOWS:
            try:
                fd = sys.stdin.fileno()
                self._old_term = termios.tcgetattr(fd)
                tty.setcbreak(fd)
            except Exception:
                self._old_term = None
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        if _IS_WINDOWS:
            self._listen_windows()
        else:
            self._listen_posix()

    def _listen_posix(self):
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

    def _listen_windows(self):
        while not self._stop_event.is_set():
            try:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in (b'\x00', b'\xe0'):
                        msvcrt.getch()
                        continue
                    decoded = ch.decode('utf-8', errors='ignore')
                    if not decoded:
                        continue
                    if decoded == '\x1b':
                        with self._lock:
                            self._queue.append('\x1b')
                    else:
                        with self._lock:
                            self._queue.append(decoded.lower())
                else:
                    time.sleep(0.02)
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
        if not _IS_WINDOWS and self._old_term is not None:
            try:
                fd = sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSADRAIN, self._old_term)
            except Exception:
                pass


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


def play_ascii_image(image_path, color_mode=COLOR_COLORED, algorithm=ALGO_CHARS, bg=BG_DARK):
    img = cv2.imread(image_path)
    if img is None:
        print(f"  {C_RED}[ERROR]{RESET} Cannot read image: {image_path}")
        return
    h, w = img.shape[:2]
    display_width = compute_display_width_for_terminal(w, h)
    ascii_art = frame_to_ascii(img, display_width, color_mode, algorithm, bg)
    try:
        term_w = os.get_terminal_size().columns
        term_h = os.get_terminal_size().lines - 3
    except OSError:
        term_w = 80
        term_h = 21
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
                ascii_art = frame_to_ascii(img, display_width, color_mode, algorithm, bg)
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


def play_ascii_video(video_path, color_mode=None, algorithm=None, bg=BG_DARK):
    if color_mode is None:
        color_mode = COLOR_COLORED
    if algorithm is None:
        algorithm = ALGO_CHARS

    cap_preview = cv2.VideoCapture(video_path)
    if not cap_preview.isOpened():
        print(f"  {C_RED}[ERROR]{RESET} Cannot open video file.")
        return
    src_w = int(cap_preview.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap_preview.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap_preview.release()

    display_width = compute_display_width_for_terminal(src_w, src_h)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"  {C_RED}[ERROR]{RESET} Cannot open video file.")
        return

    meta = get_video_metadata(video_path)
    if not meta:
        print(f"  {C_RED}[ERROR]{RESET} Cannot read video metadata.")
        cap.release()
        return

    fps = meta['fps']
    total_frames = meta['total_frames']
    duration = meta['duration']

    speed_idx = SPEED_DEFAULT_IDX
    speed = SPEED_STEPS[speed_idx]

    has_aud = has_audio_track(video_path)
    audio_player = None
    sound_on = has_aud

    if has_aud:
        audio_path = os.path.join(str(TEMP_DIR), f"audio_{int(time.time())}.wav")
        os.makedirs(str(TEMP_DIR), exist_ok=True)
        print(f"\n  {C_CYAN}▸{RESET} Extracting audio...")
        if extract_audio(video_path, audio_path):
            audio_player = AudioPlayer(audio_path)
        else:
            sound_on = False
            has_aud = False

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
        ascii_art = frame_to_ascii(frame, display_width, color_mode, algorithm, bg)
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
            hints = _build_hints(color_mode, algorithm, paused, sound_on, has_aud, is_video=True, speed=speed)
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
                elif key == 's' and has_aud:
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
                    ascii_art = frame_to_ascii(last_frame_raw, display_width, color_mode, algorithm, bg)
                    sys.stdout.write(CURSOR_HOME)
                    sys.stdout.write(ascii_art)
                completion = f"\n{RESET}{C_GREEN}  \u25b6 Playback complete!{RESET}"
                hints = _build_hints(color_mode, algorithm, paused, sound_on, has_aud, is_video=True, speed=speed)
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


def ask_choice(prompt, options, default=1):
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        marker = f" {BOLD}[default]{RESET}" if i == default else ""
        print(f"    {C_CYAN}{i}.{RESET} {opt}{marker}")
    while True:
        try:
            raw = input(f"  {C_CYAN}▸{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            return default
        if not raw:
            return default
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw)
        print(f"  {C_YELLOW}[WARN]{RESET} Enter a number 1-{len(options)}")


def ask_path(prompt, is_export=False, expected_type=None):
    while True:
        try:
            raw = input(f"  {C_CYAN}▸{RESET} {prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not raw:
            return None
        expanded = os.path.expanduser(raw)
        if is_export:
            result = os.path.abspath(expanded)
            os.makedirs(result, exist_ok=True)
            return result
        if os.path.isfile(expanded):
            return expanded
        print(f"  {C_RED}[ERROR]{RESET} File not found: {raw}")


def ask_yes_no(prompt, default='n'):
    suffix = " (Y/n)" if default == 'y' else " (y/N)"
    while True:
        try:
            raw = input(f"  {C_CYAN}▸{RESET} {prompt}{suffix}: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return default == 'y'
        if not raw:
            return default == 'y'
        if raw in ('y', 'yes'):
            return True
        if raw in ('n', 'no'):
            return False


def _do_render(path, is_video, original_name, bg=BG_DARK):
    color_opts = [f"{C_CYAN}Colored{RESET}", f"{C_WHITE}Black & White{RESET}", f"{C_GRAY}Grayscale{RESET}"]
    color_choice = ask_choice("Render color mode?", color_opts, default=1)
    color_mode = COLOR_MODES[color_choice - 1]

    algo_opts = [f"{C_GREEN}Characters{RESET}", f"{C_YELLOW}Blocks{RESET}", f"{C_MAGENTA}Dots{RESET}"]
    algo_choice = ask_choice("Render algorithm?", algo_opts, default=1)
    algorithm = ALGORITHM_MODES[algo_choice - 1]

    render_opts = [
        f"{RENDER_MODE_LABELS[RENDER_MODERN]} — full resolution, filter-like detail",
        f"{RENDER_MODE_LABELS[RENDER_RETRO]} — small character grid, visible ASCII characters",
    ]
    render_choice = ask_choice("Render mode?", render_opts, default=1)
    render_mode = RENDER_MODES[render_choice - 1]

    bg_opts = [
        f"{BG_LABELS[BG_DARK]} — black background, dark pixels empty",
        f"{BG_LABELS[BG_NONE]} — no background, dark pixels visible",
    ]
    bg_choice = ask_choice("Background?", bg_opts, default=1)
    bg_mode = BG_MODES[bg_choice - 1]

    export_dir = ask_path("Export to folder", is_export=True)
    if not export_dir:
        return

    meta = get_video_metadata(path) if is_video else get_image_metadata(path)
    width = compute_display_width_for_terminal(meta['width'], meta['height']) if meta else 80

    if is_video:
        audio_path = None
        if has_audio_track(path):
            tmp = os.path.join(str(TEMP_DIR), f"audio_{int(time.time())}.wav")
            os.makedirs(str(TEMP_DIR), exist_ok=True)
            print(f"\n  {C_CYAN}▸{RESET} Extracting audio...")
            if extract_audio(path, tmp):
                audio_path = tmp

        filename = generate_output_name('video', original_name, color_mode, algorithm, 'mp4')
        out_path = os.path.join(export_dir, filename)
        print(f"\n  {C_CYAN}▸{RESET} Rendering video...")
        result = render_mp4(path, width, color_mode, algorithm, meta['fps'] if meta else 30, audio_path, out_path, render_mode, bg_mode)
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
        if result:
            print(f"  {C_GREEN}[INFO]{RESET} Rendered: {result}")
            _open_file(result)
        else:
            print(f"  {C_RED}[ERROR]{RESET} Render failed.")
    else:
        ascii_art = image_to_ascii(path, width, color_mode, algorithm, bg_mode)
        has_ansi = color_mode != COLOR_BW
        ext = 'png'
        filename = generate_output_name('image', original_name, color_mode, algorithm, ext)
        out_path = os.path.join(export_dir, filename)
        render_png(ascii_art, out_path, has_ansi, render_mode, bg_mode)
        print(f"  {C_GREEN}[INFO]{RESET} Rendered: {out_path}")
        _open_file(out_path)


def _open_file(filepath):
    try:
        if sys.platform == 'darwin':
            subprocess.Popen(['open', filepath])
        elif _IS_WINDOWS:
            os.startfile(filepath)
        else:
            subprocess.Popen(['xdg-open', filepath])
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
        'render_mode': 'modern',
        'bg': 'dark',
    }
    positional = []
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith('-') and arg not in ('-',):
            print(f"  {C_YELLOW}[WARN]{RESET} Unknown flag: {arg}")
            i += 1
            continue
        lower = arg.lower()
        if lower in ('color', 'colour', 'c'):
            if i + 1 < len(args):
                i += 1
                config['color'] = _validate_color(args[i])
        elif lower in ('algo', 'algorithm', 'a'):
            if i + 1 < len(args):
                i += 1
                config['algo'] = _validate_algo(args[i])
        elif lower in ('render', 'r'):
            if i + 1 < len(args):
                i += 1
                config['render'] = args[i]
        elif lower in ('render_mode', 'rm', 'rendition'):
            if i + 1 < len(args):
                i += 1
                config['render_mode'] = _validate_render_mode(args[i])
        elif lower in ('bg', 'background'):
            if i + 1 < len(args):
                i += 1
                config['bg'] = _validate_bg(args[i])
        else:
            positional.append(arg)
        i += 1

    if len(positional) < 1:
        return None

    mode_lower = positional[0].lower()
    if mode_lower in ('image', 'i', 'img'):
        config['mode'] = 'image'
    elif mode_lower in ('video', 'v', 'vid'):
        config['mode'] = 'video'
    else:
        return None

    if len(positional) >= 2:
        config['path'] = positional[1]

    return config


def run_oneline(config):
    path = config.get('path')
    if not path:
        print(f"  {C_RED}[ERROR]{RESET} No file path provided.")
        return

    if is_url(path):
        print(f"\n  {C_CYAN}▸{RESET} Downloading video...")
        try:
            dl_path, dl_title = download_video(path)
        except RuntimeError as e:
            print(f"  {C_RED}[ERROR]{RESET} {e}")
            return
        if not dl_path:
            print(f"  {C_RED}[ERROR]{RESET} Download failed.")
            return
        path = dl_path
        config['mode'] = 'video'
    else:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(path):
            print(f"  {C_RED}[ERROR]{RESET} File not found: {path}")
            return
        detected = _detect_media_type(path)
        if detected:
            config['mode'] = detected

    mode = config.get('mode')
    color_mode = _validate_color(config.get('color', 'colored'))
    algorithm = _validate_algo(config.get('algo', 'chars'))
    bg_mode = _validate_bg(config.get('bg', 'dark'))
    render_dir = config.get('render')
    render_mode = _validate_render_mode(config.get('render_mode', 'modern'))

    if render_dir:
        render_dir = os.path.abspath(os.path.expanduser(render_dir))
        os.makedirs(render_dir, exist_ok=True)

    if mode == 'image':
        if render_dir:
            from .api import render_image
            try:
                out = render_image(path, output_dir=render_dir, color=color_mode, algo=algorithm, render_mode=render_mode, bg=bg_mode)
                print(f"  {C_GREEN}[INFO]{RESET} Rendered: {out}")
            except Exception as e:
                print(f"  {C_RED}[ERROR]{RESET} {e}")
        else:
            play_ascii_image(path, color_mode, algorithm, bg_mode)
    elif mode == 'video':
        if render_dir:
            from .api import render_video
            try:
                out = render_video(path, output_dir=render_dir, color=color_mode, algo=algorithm, render_mode=render_mode, bg=bg_mode)
                print(f"  {C_GREEN}[INFO]{RESET} Rendered: {out}")
            except Exception as e:
                print(f"  {C_RED}[ERROR]{RESET} {e}")
        else:
            play_ascii_video(path, color_mode, algorithm, bg_mode)
    else:
        print(f"  {C_RED}[ERROR]{RESET} Could not determine media type. Use 'image' or 'video'.")


def run_interactive():
    while True:
        print(f"\n{BANNER}{C_CYAN}  ASCII Art Media Converter & Player{RESET}")
        print(f"  {'─' * 45}")

        mode_choice = ask_choice("Media type?", ["Image", "Video"], default=2)
        is_video = mode_choice == 2

        prompt = "Path to video file or URL" if is_video else "Path to image file"
        path = ask_path(prompt, expected_type='video' if is_video else 'image')
        if not path:
            next_choice = ask_choice("What next?", ["Start again", "Exit"], default=1)
            if next_choice == 2:
                break
            continue

        if is_video and is_url(path):
            print(f"\n  {C_CYAN}▸{RESET} Downloading video...")
            try:
                dl_path, dl_title = download_video(path)
            except RuntimeError as e:
                print(f"  {C_RED}[ERROR]{RESET} {e}")
                next_choice = ask_choice("What next?", ["Start again", "Exit"], default=1)
                if next_choice == 2:
                    break
                continue
            if not dl_path:
                print(f"  {C_RED}[ERROR]{RESET} Download failed.")
                next_choice = ask_choice("What next?", ["Start again", "Exit"], default=1)
                if next_choice == 2:
                    break
                continue
            path = dl_path

        original_name = os.path.splitext(os.path.basename(path))[0]

        if is_video:
            meta = get_video_metadata(path)
            if meta:
                audio_str = "Yes" if has_audio_track(path) else "No"
                print(f"  {C_GREEN}[INFO]{RESET} Video: {meta['width']}x{meta['height']} @ {meta['fps']:.1f} FPS | Audio: {audio_str} | {format_time(meta['duration'])}")
        else:
            meta = get_image_metadata(path)
            if meta:
                print(f"  {C_GREEN}[INFO]{RESET} Image: {meta['width']}x{meta['height']} | Format: {meta['format']}")

        try:
            tw = os.get_terminal_size().columns
            th = os.get_terminal_size().lines
            print(f"  {C_GRAY}Terminal: {tw}x{th} chars{RESET}")
        except OSError:
            pass

        do_render = ask_yes_no("Render as standard media?", default='n')

        if do_render:
            _do_render(path, is_video, original_name)
        else:
            if is_video:
                play_ascii_video(path)
            else:
                play_ascii_image(path)

        next_choice = ask_choice("What next?", ["Start again", "Exit"], default=1)
        if next_choice == 2:
            break


def show_help():
    print(f"\n{BANNER}")
    print(f"  {C_CYAN}Usage:{RESET}")
    print(f"    asciideia                          {C_GRAY}Interactive mode{RESET}")
    print(f"    asciideia <mode> <path> [flags]     {C_GRAY}Oneline mode{RESET}")
    print(f"    asciideia help                     {C_GRAY}Show this help{RESET}")
    print(f"\n  {C_CYAN}Modes:{RESET}")
    print(f"    image | i | img                    {C_GRAY}Image to ASCII{RESET}")
    print(f"    video | v | vid                    {C_GRAY}Video to ASCII{RESET}")
    print(f"\n  {C_CYAN}Flags:{RESET}")
    print(f"    color | c <mode>                   {C_GRAY}colored, bw, gray{RESET}")
    print(f"    algo  | a <mode>                   {C_GRAY}chars, blocks, dots{RESET}")
    print(f"    render | r <folder>                {C_GRAY}Render to PNG/MP4{RESET}")
    print(f"    render_mode | rm <mode>            {C_GRAY}modern, retro{RESET}")
    print(f"    bg | background <mode>             {C_GRAY}dark, none{RESET}")
    print(f"\n  {C_CYAN}Examples:{RESET}")
    print(f"    asciideia image photo.png")
    print(f"    asciideia video clip.mp4 color bw algo blocks")
    print(f"    asciideia i photo.png bg none render ./output")
    print(f"    asciideia v clip.mp4 rm retro bg dark r ./out")
    print()


def main():
    try:
        _enable_windows_ansi()
        os.makedirs(str(TEMP_DIR), exist_ok=True)
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
        if TEMP_DIR.exists():
            shutil.rmtree(str(TEMP_DIR), ignore_errors=True)
