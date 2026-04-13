import os
import threading
from dataclasses import dataclass
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, StringVar, Text, Tk, filedialog, messagebox
import tkinter as tk
from tkinter import ttk

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    ColorClip,
    CompositeAudioClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    VideoClip,
)


DEFAULT_BG_COLOR = (30, 60, 120)
DEFAULT_BOX_COLOR = (255, 255, 255)
DEFAULT_ACCENT_COLORS = [
    (0, 255, 0),
    (255, 255, 0),
    (0, 255, 255),
    (255, 0, 255),
]
DEFAULT_STEPS = ["INHALE", "HOLD", "EXHALE", "HOLD"]
DEFAULT_FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
BREATHING_PRESETS = {
    "box-4-4-4-4": [("INHALE", 4), ("HOLD", 4), ("EXHALE", 4), ("HOLD", 4)],
    "calm-4-4-6-2": [("INHALE", 4), ("HOLD", 4), ("EXHALE", 6), ("HOLD", 2)],
    "relax-4-7-8": [("INHALE", 4), ("HOLD", 7), ("EXHALE", 8)],
    "triangle-4-4-4": [("INHALE", 4), ("HOLD", 4), ("EXHALE", 4)],
    "energy-bellows": [("INHALE", 1), ("EXHALE", 1)],
    "calm-aum": [("INHALE", 7), ("AUM", 9), ("REST", 7)],
    "nadi-shodhana": [
        ("INHALE RIGHT", 5),
        ("HOLD", 3),
        ("EXHALE LEFT", 5),
    ],
    "euphoric-breathwork": [
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE NOSE", 3),
        ("EXHALE MOUTH", 3),
        ("INHALE MOUTH", 3),
        ("HOLD TENSION", 8),
        ("SOFT HOLD", 4),
        ("EXHALE LIPS", 6),
        ("ROUND BREAK", 14),
    ],
}
BREATHING_COACHING_LINES = {
    "box-4-4-4-4": {
        "INHALE": "Inhale slowly through your nose.",
        "HOLD": "Hold gently.",
        "EXHALE": "Exhale slowly through your mouth.",
    },
    "calm-4-4-6-2": {
        "INHALE": "Inhale gently through the nose.",
        "HOLD": "Hold softly.",
        "EXHALE": "Exhale slowly and let tension go.",
    },
    "relax-4-7-8": {
        "INHALE": "Inhale through the nose for four seconds.",
        "HOLD": "Hold for seven seconds.",
        "EXHALE": "Exhale forcefully through the mouth for eight seconds.",
    },
    "triangle-4-4-4": {
        "INHALE": "Inhale through the nose.",
        "HOLD": "Hold.",
        "EXHALE": "Exhale slowly through the mouth.",
    },
    "energy-bellows": {
        "INHALE": "Inhale",
        "EXHALE": "Exhale",
    },
    "calm-aum": {
        "INHALE": "Inhale slowly.",
        "AUM": "Aaaaaaaaa Ouuuuuuuuuuu. Mmmmmmmmmmmmm.",
        "REST": "Rest and feel some peace.",
    },
    "nadi-shodhana": {
        "INHALE RIGHT": "Inhale slowly through the right nostril.",
        "HOLD": "Close both nostrils and hold gently.",
        "EXHALE LEFT": "Exhale slowly through the left nostril.",
    },
    "euphoric-breathwork": {
        "INHALE NOSE": "Breathing in through the nose.",
        "EXHALE MOUTH": "Relaxing the breath out through the mouth.",
        "INHALE MOUTH": "Big deep breath in through the mouth.",
        "HOLD TENSION": "Hold. Squeeze fists, abs, arms, legs, calves, feet. Tongue up. Eyes to the third eye.",
        "SOFT HOLD": "Release the squeeze. Hold the breath and enjoy.",
        "EXHALE LIPS": "Release the breath slowly through the mouth with pursed lips.",
        "ROUND BREAK": "Breathe naturally. The next round begins in a few moments.",
    },
}


@dataclass
class VideoSettings:
    duration: int
    width: int
    height: int
    output_path: str
    mode: str = "breathing"
    title: str = "Box Breathing"
    subtitle: str = ""
    logo_path: str = ""
    voice_path: str = ""
    music_path: str = ""
    background_image_path: str = ""
    box_size: int = 600
    box_thickness: int = 10
    fps: int = 30
    seconds_per_slide: int = 4
    slide_lines: list[str] | None = None
    breathing_preset: str = "box-4-4-4-4"
    breathing_cycles: int = 8
    breathing_steps: list[tuple[str, int]] | None = None
    generate_voiceover: bool = True
    coaching_lines: dict[str, str] | None = None


def parse_breathing_steps(raw_text: str):
    steps = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Breathing step must look like LABEL:SECONDS. Problem line: {line}")
        label, seconds = line.split(":", 1)
        label = label.strip().upper()
        seconds = int(seconds.strip())
        if not label or seconds <= 0:
            raise ValueError(f"Breathing step must have a label and positive seconds. Problem line: {line}")
        steps.append((label, seconds))
    return steps


def total_breathing_duration(steps: list[tuple[str, int]], cycles: int):
    return sum(seconds for _, seconds in steps) * cycles


def build_timeline_steps(settings: VideoSettings):
    steps = settings.breathing_steps or BREATHING_PRESETS[settings.breathing_preset]
    timeline = []
    current_start = 0
    for _ in range(settings.breathing_cycles):
        for label, seconds in steps:
            timeline.append(
                {
                    "label": label,
                    "duration": seconds,
                    "start": current_start,
                    "end": current_start + seconds,
                }
            )
            current_start += seconds
    return timeline


def coaching_lines_for_settings(settings: VideoSettings):
    if settings.coaching_lines:
        return settings.coaching_lines
    return BREATHING_COACHING_LINES.get(settings.breathing_preset, {})


def phase_kind(label: str):
    if "ROUND BREAK" in label or "REST" in label:
        return "rest"
    if "HOLD" in label:
        return "hold"
    if "AUM" in label:
        return "aum"
    if "INHALE" in label:
        return "inhale"
    if "EXHALE" in label:
        return "exhale"
    return "neutral"


def make_breathing_frame_factory(
    width: int,
    height: int,
    box_size: int,
    box_thickness: int,
    steps_timeline: list[dict],
):
    def make_box_frame(t: float):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:, :] = DEFAULT_BG_COLOR

        import cv2

        step_index = 0
        for index, step in enumerate(steps_timeline):
            if t < step["end"] or index == len(steps_timeline) - 1:
                step_index = index
                break

        current_step = steps_timeline[step_index]
        step_progress = (t - current_step["start"]) / current_step["duration"]
        step_progress = max(0.0, min(1.0, step_progress))
        label = current_step["label"]
        kind = phase_kind(label)

        center_x = width // 2
        center_y = height // 2 + 40
        min_radius = max(70, box_size // 7)
        max_radius = max(min_radius + 40, box_size // 3)

        if kind == "inhale":
            radius = int(min_radius + (max_radius - min_radius) * step_progress)
        elif kind == "exhale":
            radius = int(max_radius - (max_radius - min_radius) * step_progress)
        elif kind == "aum":
            radius = int(max_radius - ((max_radius - min_radius) * 0.35 * step_progress))
        elif kind == "hold":
            radius = max_radius
        elif kind == "rest":
            radius = int(min_radius + (max_radius - min_radius) * 0.15)
        else:
            radius = max_radius if step_index > 0 and phase_kind(steps_timeline[step_index - 1]["label"]) == "inhale" else min_radius

        phase_colors = {
            "inhale": (78, 205, 196),
            "exhale": (255, 159, 67),
            "aum": (167, 139, 250),
            "hold": (255, 214, 102),
            "rest": (129, 140, 248),
            "neutral": (255, 255, 255),
        }
        accent = phase_colors.get(kind, (255, 255, 255))

        if kind == "rest":
            overlay_alpha = 0.22 + (0.08 * np.sin(t * 2.0))
            overlay = np.full((height, width, 3), (65, 90, 150), dtype=np.uint8)
            img = cv2.addWeighted(overlay, overlay_alpha, img, 1 - overlay_alpha, 0)

        if kind == "hold":
            pulse = 10 + int(8 * np.sin(t * 5.5))
            cv2.circle(img, (center_x, center_y), radius + 28 + pulse, accent, 4)

        if kind == "rest":
            for ring_index in range(3):
                ring_radius = radius + 35 + ring_index * 28 + int(step_progress * 22)
                ring_alpha = max(0.0, 1.0 - (ring_index * 0.25) - (step_progress * 0.35))
                ring_color = tuple(int(channel * ring_alpha) for channel in accent)
                cv2.circle(img, (center_x, center_y), ring_radius, ring_color, 2)

        cv2.circle(img, (center_x, center_y), radius, DEFAULT_BOX_COLOR, box_thickness)
        inner_radius = max(12, radius - 22)
        cv2.circle(img, (center_x, center_y), inner_radius, accent, 6)

        progress_bar_width = min(width - 180, 700)
        progress_bar_height = 18
        bar_x0 = (width - progress_bar_width) // 2
        bar_y0 = height - 120
        filled_width = int(progress_bar_width * step_progress)
        cv2.rectangle(
            img,
            (bar_x0, bar_y0),
            (bar_x0 + progress_bar_width, bar_y0 + progress_bar_height),
            (180, 200, 230),
            2,
        )
        cv2.rectangle(
            img,
            (bar_x0, bar_y0),
            (bar_x0 + filled_width, bar_y0 + progress_bar_height),
            accent,
            -1,
        )

        indicator_labels = {
            "inhale": "Expand",
            "exhale": "Release",
            "aum": "Chant",
            "hold": "Hold",
            "rest": "Pause",
            "neutral": "",
        }
        indicator_text = indicator_labels.get(kind, "")
        if indicator_text:
            cv2.putText(
                img,
                indicator_text,
                (bar_x0, bar_y0 - 18),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                accent,
                2,
                cv2.LINE_AA,
            )

        return img

    return make_box_frame


def build_text_clips(settings: VideoSettings):
    clips = []
    center_y = settings.height // 2
    title_y = max(48, center_y - (settings.box_size // 2) - 160)
    steps_timeline = build_timeline_steps(settings)

    if settings.title.strip():
        title_clip = (
            TextClip(
                settings.title.strip(),
                fontsize=54,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 120, None),
                method="caption",
            )
            .set_position(("center", title_y))
            .set_duration(settings.duration)
        )
        clips.append(title_clip)

    if settings.subtitle.strip():
        subtitle_clip = (
            TextClip(
                settings.subtitle.strip(),
                fontsize=30,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 120, None),
                method="caption",
            )
            .set_position(("center", title_y + 64))
            .set_duration(settings.duration)
        )
        clips.append(subtitle_clip)

    for step in steps_timeline:
        step_clip = (
            TextClip(
                step["label"],
                fontsize=82,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 120, None),
                method="caption",
            )
            .set_position(("center", center_y - 40))
            .set_start(step["start"])
            .set_duration(step["duration"])
        )
        clips.append(step_clip)

        count_clip = (
            TextClip(
                f"{step['duration']} sec",
                fontsize=34,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 120, None),
                method="caption",
            )
            .set_position(("center", center_y + 56))
            .set_start(step["start"])
            .set_duration(step["duration"])
        )
        clips.append(count_clip)

    if settings.breathing_preset == "energy-bellows":
        intro_text = (
            "Quick inhale through your nose.\n"
            "Quick exhale through your nose."
        )
        outro_text = "Take one deep breath in, then relax."

        clips.append(
            TextClip(
                intro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 260))
            .set_start(0)
            .set_duration(min(8, settings.duration))
        )

        clips.append(
            TextClip(
                outro_text,
                fontsize=30,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 220))
            .set_start(max(0, settings.duration - 6))
            .set_duration(min(6, settings.duration))
        )

    if settings.breathing_preset == "calm-aum":
        intro_text = (
            "Sit upright and relax your shoulders.\n"
            "Inhale through the nose, then exhale with Aaaah, Oooo, Mmmm."
        )
        outro_text = "Rest in silence for a few seconds and feel the resonance."

        clips.append(
            TextClip(
                intro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 260))
            .set_start(0)
            .set_duration(min(9, settings.duration))
        )

        clips.append(
            TextClip(
                outro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 220))
            .set_start(max(0, settings.duration - 8))
            .set_duration(min(8, settings.duration))
        )

    if settings.breathing_preset == "nadi-shodhana":
        intro_text = (
            "Sit comfortably with a tall spine.\n"
            "Use your right thumb and ring finger to alternate nostrils.\n"
            "Keep the breath soft, smooth, and steady."
        )
        outro_text = "Return to natural breathing and notice the calm, balanced feeling."

        clips.append(
            TextClip(
                intro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 270))
            .set_start(0)
            .set_duration(min(10, settings.duration))
        )

        clips.append(
            TextClip(
                outro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 220))
            .set_start(max(0, settings.duration - 8))
            .set_duration(min(8, settings.duration))
        )

    if settings.breathing_preset == "euphoric-breathwork":
        intro_text = (
            "Lie down or sit tall in a safe and comfortable place.\n"
            "If you are new to breathwork, it is better to lie down.\n"
            "Breathe in through the nose, out through the mouth, then follow the guided rounds."
        )
        outro_text = "Take a deep breath in and let it go. Relax and listen to the music for a little while longer."

        clips.append(
            TextClip(
                intro_text,
                fontsize=26,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 280))
            .set_start(0)
            .set_duration(min(12, settings.duration))
        )

        clips.append(
            TextClip(
                outro_text,
                fontsize=28,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", settings.height - 220))
            .set_start(max(0, settings.duration - 10))
            .set_duration(min(10, settings.duration))
        )

    return clips


def build_audio_track(settings: VideoSettings):
    audio_clips = []

    generated_voice_path = ""
    if settings.mode == "breathing" and settings.generate_voiceover:
        generated_voice_path = generate_breathing_voiceover(settings)

    voice_source = generated_voice_path or settings.voice_path
    if voice_source and os.path.exists(voice_source):
        voice_clip = AudioFileClip(voice_source)
        if voice_clip.duration > settings.duration:
            voice_clip = voice_clip.subclip(0, settings.duration)
        audio_clips.append(voice_clip.volumex(1.2))

    if settings.music_path and os.path.exists(settings.music_path):
        music = AudioFileClip(settings.music_path)
        if music.duration > settings.duration:
            music = music.subclip(0, settings.duration)
        elif music.duration < settings.duration:
            music = music.audio_loop(duration=settings.duration)
        audio_clips.append(music.volumex(0.35))

    if not audio_clips:
        return None

    return CompositeAudioClip(audio_clips)


def generate_breathing_voiceover(settings: VideoSettings):
    try:
        from gtts import gTTS
        from pydub import AudioSegment
    except Exception as exc:
        raise RuntimeError(
            "Voice generation needs gTTS and pydub installed in the project environment."
        ) from exc

    cache_dir = Path(settings.output_path).parent / ".video_tool_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    output_mp3 = cache_dir / "guided_breathing_voice.mp3"
    timeline = build_timeline_steps(settings)
    coaching_lines = coaching_lines_for_settings(settings)
    combined = AudioSegment.empty()

    for index, step in enumerate(timeline):
        temp_file = cache_dir / f"step_{index}_{step['label'].lower()}.mp3"
        spoken_text = coaching_lines.get(step["label"], step["label"].title())
        tts = gTTS(spoken_text, lang="en")
        tts.save(str(temp_file))

        segment = AudioSegment.from_file(temp_file)
        target_ms = step["duration"] * 1000
        if len(segment) < target_ms:
            segment += AudioSegment.silent(duration=target_ms - len(segment))
        else:
            segment = segment[:target_ms]
        combined += segment

        if temp_file.exists():
            temp_file.unlink()

    combined.export(output_mp3, format="mp3")
    return str(output_mp3)


def build_background_clip(settings: VideoSettings):
    if settings.background_image_path and os.path.exists(settings.background_image_path):
        return (
            ImageClip(settings.background_image_path)
            .resize(newsize=(settings.width, settings.height))
            .set_duration(settings.duration)
        )
    return ColorClip((settings.width, settings.height), DEFAULT_BG_COLOR, duration=settings.duration)


def render_video(settings: VideoSettings):
    if settings.mode == "slides":
        return render_slides_video(settings)

    settings.duration = total_breathing_duration(
        settings.breathing_steps or BREATHING_PRESETS[settings.breathing_preset],
        settings.breathing_cycles,
    )
    box_size = min(settings.box_size, settings.width - 120, settings.height - 220)
    steps_timeline = build_timeline_steps(settings)
    frame_fn = make_breathing_frame_factory(
        width=settings.width,
        height=settings.height,
        box_size=box_size,
        box_thickness=settings.box_thickness,
        steps_timeline=steps_timeline,
    )

    background = build_background_clip(settings)
    box_clip = VideoClip(frame_fn, duration=settings.duration)
    clips = [background, box_clip]

    if settings.logo_path and os.path.exists(settings.logo_path):
        logo_clip = (
            ImageClip(settings.logo_path)
            .resize(width=min(180, settings.width // 5))
            .set_position((36, 36))
            .set_duration(settings.duration)
        )
        clips.append(logo_clip)

    clips.extend(build_text_clips(settings))
    video = CompositeVideoClip(clips)

    audio_track = build_audio_track(settings)
    if audio_track is not None:
        video = video.set_audio(audio_track)

    video.write_videofile(
        settings.output_path,
        fps=settings.fps,
        audio_codec="aac",
    )


def render_slides_video(settings: VideoSettings):
    clips = [build_background_clip(settings)]

    if settings.logo_path and os.path.exists(settings.logo_path):
        clips.append(
            ImageClip(settings.logo_path)
            .resize(width=min(180, settings.width // 5))
            .set_position((36, 36))
            .set_duration(settings.duration)
        )

    if settings.title.strip():
        clips.append(
            TextClip(
                settings.title.strip(),
                fontsize=64,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 120, None),
                method="caption",
            )
            .set_position(("center", 72))
            .set_duration(settings.duration)
        )

    if settings.subtitle.strip():
        clips.append(
            TextClip(
                settings.subtitle.strip(),
                fontsize=34,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
            )
            .set_position(("center", 150))
            .set_duration(settings.duration)
        )

    slide_lines = settings.slide_lines or []
    for index, line in enumerate(slide_lines):
        clips.append(
            TextClip(
                line,
                fontsize=58,
                color="white",
                font=DEFAULT_FONT_PATH,
                size=(settings.width - 180, None),
                method="caption",
                align="center",
            )
            .set_position(("center", "center"))
            .set_start(index * settings.seconds_per_slide)
            .set_duration(settings.seconds_per_slide)
        )

    video = CompositeVideoClip(clips)
    audio_track = build_audio_track(settings)
    if audio_track is not None:
        video = video.set_audio(audio_track)

    video.write_videofile(
        settings.output_path,
        fps=settings.fps,
        audio_codec="aac",
    )


class FilePicker(ttk.Frame):
    def __init__(self, master, label_text, variable, filetypes):
        super().__init__(master)
        self.variable = variable
        self.filetypes = filetypes

        ttk.Label(self, text=label_text, width=14).pack(side=LEFT, padx=(0, 8))
        ttk.Entry(self, textvariable=self.variable).pack(side=LEFT, fill=BOTH, expand=True)
        ttk.Button(self, text="Browse", command=self.browse).pack(side=RIGHT, padx=(8, 0))

    def browse(self):
        selected = filedialog.askopenfilename(filetypes=self.filetypes)
        if selected:
            self.variable.set(selected)


class VideoToolApp:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Video Tool")
        self.root.geometry("980x900")
        self.root.minsize(820, 700)

        cwd = Path.cwd()
        self.output_var = StringVar(value=str(cwd / "box_breathing_guided.mp4"))
        self.mode_var = StringVar(value="breathing")
        self.breathing_preset_var = StringVar(value="box-4-4-4-4")
        self.breathing_cycles_var = StringVar(value="8")
        self.generate_voiceover_var = tk.BooleanVar(value=True)
        self.title_var = StringVar(value="Box Breathing")
        self.subtitle_var = StringVar(value="A simple guided breathing practice for calm and focus.")
        self.duration_var = StringVar(value="128")
        self.width_var = StringVar(value="1080")
        self.height_var = StringVar(value="1080")
        self.seconds_per_slide_var = StringVar(value="4")
        self.logo_var = StringVar(value=str(cwd / "logo.png") if (cwd / "logo.png").exists() else "")
        self.voice_var = StringVar(value=str(cwd / "meditation_voice.mp3") if (cwd / "meditation_voice.mp3").exists() else "")
        self.music_var = StringVar(value=str(cwd / "ambient_music.mp3") if (cwd / "ambient_music.mp3").exists() else "")
        self.background_var = StringVar(value="")
        self.status_var = StringVar(value="Ready to create a video.")
        self.rendering = False

        self.build_ui()

    def build_ui(self):
        shell = ttk.Frame(self.root)
        shell.pack(fill=BOTH, expand=True)

        canvas = tk.Canvas(shell, highlightthickness=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        outer = ttk.Frame(canvas, padding=18)

        outer.bind(
            "<Configure>",
            lambda event: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=outer, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill="y")

        self.root.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )

        ttk.Label(
            outer,
            text="Create a video from local text and assets",
            font=("Helvetica", 18, "bold"),
        ).pack(anchor="w", pady=(0, 14))

        ttk.Label(
            outer,
            text="Scroll down to the Create Video button. The status message at the bottom will update while rendering.",
            wraplength=880,
            foreground="#355070",
        ).pack(anchor="w", pady=(0, 12))

        basic = ttk.Frame(outer)
        basic.pack(fill=BOTH, pady=(0, 10))

        self._combo_field(basic, "Mode", self.mode_var, ["breathing", "slides"], 0)
        self._combo_field(basic, "Breathing preset", self.breathing_preset_var, list(BREATHING_PRESETS.keys()), 1)
        self._field(basic, "Cycles", self.breathing_cycles_var, 2)
        self._field(basic, "Title", self.title_var, 3)
        self._field(basic, "Subtitle", self.subtitle_var, 4)
        self._field(basic, "Duration (s)", self.duration_var, 5)
        self._field(basic, "Width", self.width_var, 6)
        self._field(basic, "Height", self.height_var, 7)
        self._field(basic, "Seconds/slide", self.seconds_per_slide_var, 8)

        ttk.Checkbutton(
            outer,
            text="Generate guided breathing voice automatically",
            variable=self.generate_voiceover_var,
        ).pack(anchor="w", pady=(0, 8))

        output_row = ttk.Frame(outer)
        output_row.pack(fill=BOTH, pady=(0, 10))
        ttk.Label(output_row, text="Output", width=14).pack(side=LEFT, padx=(0, 8))
        ttk.Entry(output_row, textvariable=self.output_var).pack(side=LEFT, fill=BOTH, expand=True)
        ttk.Button(output_row, text="Save As", command=self.pick_output).pack(side=RIGHT, padx=(8, 0))

        FilePicker(
            outer,
            "Logo",
            self.logo_var,
            [("Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        ).pack(fill=BOTH, pady=4)
        FilePicker(
            outer,
            "Voice",
            self.voice_var,
            [("Audio", "*.mp3 *.wav *.m4a"), ("All files", "*.*")],
        ).pack(fill=BOTH, pady=4)
        FilePicker(
            outer,
            "Music",
            self.music_var,
            [("Audio", "*.mp3 *.wav *.m4a"), ("All files", "*.*")],
        ).pack(fill=BOTH, pady=4)
        FilePicker(
            outer,
            "Background",
            self.background_var,
            [("Images", "*.png *.jpg *.jpeg"), ("All files", "*.*")],
        ).pack(fill=BOTH, pady=4)

        slides_frame = ttk.Frame(outer)
        slides_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        ttk.Label(
            slides_frame,
            text="Slides text (one line = one slide in slides mode)",
        ).pack(anchor="w", pady=(0, 6))
        self.slides_text = Text(slides_frame, height=6, wrap="word")
        self.slides_text.pack(fill=BOTH, expand=True)
        self.slides_text.insert(
            "1.0",
            "Start with a clear message.\nAdd your logo and background.\nExport a simple video in one click.",
        )

        breath_frame = ttk.Frame(outer)
        breath_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        ttk.Label(
            breath_frame,
            text="Breathing steps for custom rhythm (LABEL:SECONDS, one per line)",
        ).pack(anchor="w", pady=(0, 6))
        self.breathing_text = Text(breath_frame, height=5, wrap="word")
        self.breathing_text.pack(fill=BOTH, expand=True)
        self.breathing_text.insert("1.0", self.steps_to_text(BREATHING_PRESETS["box-4-4-4-4"]))
        self.root.after(0, self.bind_preset_updates)

        coaching_frame = ttk.Frame(outer)
        coaching_frame.pack(fill=BOTH, expand=True, pady=(8, 0))
        ttk.Label(
            coaching_frame,
            text="Coaching lines for voiceover (LABEL:spoken sentence, one per line)",
        ).pack(anchor="w", pady=(0, 6))
        self.coaching_text = Text(coaching_frame, height=5, wrap="word")
        self.coaching_text.pack(fill=BOTH, expand=True)
        self.coaching_text.insert("1.0", self.coaching_to_text(BREATHING_COACHING_LINES["box-4-4-4-4"]))

        actions = ttk.Frame(outer)
        actions.pack(fill=BOTH, pady=(16, 8))
        self.create_button = ttk.Button(actions, text="Create Video Now", command=self.start_render)
        self.create_button.pack(side=LEFT)
        ttk.Button(actions, text="Use Project Assets", command=self.restore_defaults).pack(side=LEFT, padx=10)

        ttk.Label(
            outer,
            text="Status",
            font=("Helvetica", 12, "bold"),
        ).pack(anchor="w", pady=(10, 2))

        ttk.Label(
            outer,
            textvariable=self.status_var,
            wraplength=700,
            foreground="#1f3b63",
        ).pack(anchor="w", pady=(10, 0))

    def _field(self, parent, label, variable, row):
        ttk.Label(parent, text=label, width=14).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

    def _combo_field(self, parent, label, variable, values, row):
        ttk.Label(parent, text=label, width=14).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
        combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
        combo.grid(row=row, column=1, sticky="ew", pady=4)
        parent.columnconfigure(1, weight=1)

    def pick_output(self):
        selected = filedialog.asksaveasfilename(
            defaultextension=".mp4",
            filetypes=[("MP4 video", "*.mp4")],
        )
        if selected:
            self.output_var.set(selected)

    def restore_defaults(self):
        cwd = Path.cwd()
        self.mode_var.set("breathing")
        self.breathing_preset_var.set("box-4-4-4-4")
        self.breathing_cycles_var.set("8")
        self.generate_voiceover_var.set(True)
        self.title_var.set("Box Breathing")
        self.subtitle_var.set("A simple guided breathing practice for calm and focus.")
        self.duration_var.set("128")
        self.seconds_per_slide_var.set("4")
        self.logo_var.set(str(cwd / "logo.png") if (cwd / "logo.png").exists() else "")
        self.voice_var.set(str(cwd / "meditation_voice.mp3") if (cwd / "meditation_voice.mp3").exists() else "")
        self.music_var.set(str(cwd / "ambient_music.mp3") if (cwd / "ambient_music.mp3").exists() else "")
        self.background_var.set("")
        self.slides_text.delete("1.0", END)
        self.slides_text.insert(
            "1.0",
            "Start with a clear message.\nAdd your logo and background.\nExport a simple video in one click.",
        )
        self.breathing_text.delete("1.0", END)
        self.breathing_text.insert("1.0", self.steps_to_text(BREATHING_PRESETS["box-4-4-4-4"]))
        self.coaching_text.delete("1.0", END)
        self.coaching_text.insert("1.0", self.coaching_to_text(BREATHING_COACHING_LINES["box-4-4-4-4"]))
        self.status_var.set("Project assets restored.")

    def steps_to_text(self, steps):
        return "\n".join(f"{label}:{seconds}" for label, seconds in steps)

    def coaching_to_text(self, lines):
        return "\n".join(f"{label}:{text}" for label, text in lines.items())

    def bind_preset_updates(self):
        for child in self.root.winfo_children():
            self._bind_preset_updates_recursive(child)

    def _bind_preset_updates_recursive(self, widget):
        if isinstance(widget, ttk.Combobox) and widget.cget("textvariable") == str(self.breathing_preset_var):
            widget.bind("<<ComboboxSelected>>", self.on_preset_changed)
        for child in widget.winfo_children():
            self._bind_preset_updates_recursive(child)

    def on_preset_changed(self, _event=None):
        preset_name = self.breathing_preset_var.get()
        if preset_name in BREATHING_PRESETS:
            self.breathing_text.delete("1.0", END)
            self.breathing_text.insert("1.0", self.steps_to_text(BREATHING_PRESETS[preset_name]))
        if preset_name in BREATHING_COACHING_LINES:
            self.coaching_text.delete("1.0", END)
            self.coaching_text.insert("1.0", self.coaching_to_text(BREATHING_COACHING_LINES[preset_name]))
        if preset_name == "box-4-4-4-4":
            self.title_var.set("Box Breathing")
            self.subtitle_var.set("A simple guided breathing practice for calm and focus.")
            self.breathing_cycles_var.set("8")
            self.duration_var.set("128")
            self.music_var.set(str(Path.cwd() / "ambient_music.mp3") if (Path.cwd() / "ambient_music.mp3").exists() else "")
        elif preset_name == "energy-bellows":
            self.title_var.set("For Increasing Energy: The Bellows Breath")
            self.subtitle_var.set("A natural double-shot of espresso.")
            self.breathing_cycles_var.set("15")
            self.duration_var.set("30")
            self.music_var.set(str(Path.cwd() / "ambient_music.mp3") if (Path.cwd() / "ambient_music.mp3").exists() else "")
        elif preset_name == "calm-aum":
            self.title_var.set("AUM Breathing (Udgeeth Pranayama)")
            self.subtitle_var.set("A calming, vibrational breathing technique for deep relaxation.")
            self.breathing_cycles_var.set("5")
            self.duration_var.set("115")
            self.music_var.set(str(Path.cwd() / "aum-om.mp3") if (Path.cwd() / "aum-om.mp3").exists() else "")
        elif preset_name == "nadi-shodhana":
            self.title_var.set("Nadi Shodhana (Alternate Nostril Breathing)")
            self.subtitle_var.set("A balancing practice for calm, clarity, and nervous system regulation.")
            self.breathing_cycles_var.set("15")
            self.duration_var.set("300")
            self.music_var.set(str(Path.cwd() / "ambient_music.mp3") if (Path.cwd() / "ambient_music.mp3").exists() else "")
        elif preset_name == "euphoric-breathwork":
            self.title_var.set("Euphoric Breathwork")
            self.subtitle_var.set("A guided round-based breathwork meditation for deep release.")
            self.breathing_cycles_var.set("4")
            self.duration_var.set("404")
            self.music_var.set(str(Path.cwd() / "ambient_music.mp3") if (Path.cwd() / "ambient_music.mp3").exists() else "")
        elif preset_name == "relax-4-7-8":
            self.title_var.set("Sleep or Anxiety: 4-7-8 Breathing")
            self.subtitle_var.set("This acts like a natural tranquilizer.")
            self.breathing_cycles_var.set("6")
            self.duration_var.set("114")
            self.music_var.set(str(Path.cwd() / "ambient_music.mp3") if (Path.cwd() / "ambient_music.mp3").exists() else "")

    def parse_coaching_lines(self, raw_text: str):
        lines = {}
        for line in raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" not in line:
                raise ValueError(f"Coaching line must look like LABEL:spoken sentence. Problem line: {line}")
            label, text = line.split(":", 1)
            label = label.strip().upper()
            text = text.strip()
            if not label or not text:
                raise ValueError(f"Coaching line must have a label and spoken sentence. Problem line: {line}")
            lines[label] = text
        return lines

    def start_render(self):
        if self.rendering:
            return

        try:
            settings = VideoSettings(
                duration=int(self.duration_var.get()),
                width=int(self.width_var.get()),
                height=int(self.height_var.get()),
                output_path=self.output_var.get().strip(),
                mode=self.mode_var.get().strip(),
                title=self.title_var.get(),
                subtitle=self.subtitle_var.get(),
                logo_path=self.logo_var.get().strip(),
                voice_path=self.voice_var.get().strip(),
                music_path=self.music_var.get().strip(),
                background_image_path=self.background_var.get().strip(),
                seconds_per_slide=int(self.seconds_per_slide_var.get()),
                breathing_preset=self.breathing_preset_var.get().strip(),
                breathing_cycles=int(self.breathing_cycles_var.get()),
                generate_voiceover=self.generate_voiceover_var.get(),
                coaching_lines=self.parse_coaching_lines(self.coaching_text.get("1.0", END)),
                slide_lines=[
                    line.strip()
                    for line in self.slides_text.get("1.0", END).splitlines()
                    if line.strip()
                ],
                breathing_steps=parse_breathing_steps(self.breathing_text.get("1.0", END)),
            )
        except ValueError:
            messagebox.showerror(
                "Invalid input",
                "Check your numbers and custom breathing steps. Use LABEL:SECONDS on each line.",
            )
            return

        if (
            settings.duration <= 0
            or settings.width <= 0
            or settings.height <= 0
            or settings.seconds_per_slide <= 0
            or settings.breathing_cycles <= 0
        ):
            messagebox.showerror(
                "Invalid input",
                "Width, height, seconds per slide, and cycles must be greater than zero.",
            )
            return

        if not settings.output_path:
            messagebox.showerror("Missing output", "Choose an output file for the video.")
            return

        if settings.mode == "slides":
            if not settings.slide_lines:
                messagebox.showerror("Missing slides", "Add at least one line of slide text.")
                return
            settings.duration = len(settings.slide_lines) * settings.seconds_per_slide
        else:
            if not settings.breathing_steps:
                messagebox.showerror("Missing breathing steps", "Add at least one breathing step.")
                return
            settings.duration = total_breathing_duration(settings.breathing_steps, settings.breathing_cycles)

        output_dir = os.path.dirname(settings.output_path) or "."
        os.makedirs(output_dir, exist_ok=True)

        self.rendering = True
        self.create_button.configure(state="disabled")
        self.status_var.set("Rendering video. This can take a minute or two.")

        worker = threading.Thread(target=self._render_worker, args=(settings,), daemon=True)
        worker.start()

    def _render_worker(self, settings: VideoSettings):
        try:
            render_video(settings)
        except Exception as exc:
            self.root.after(0, lambda: self._render_failed(str(exc)))
            return

        self.root.after(0, lambda: self._render_complete(settings.output_path))

    def _render_complete(self, output_path: str):
        self.rendering = False
        self.create_button.configure(state="normal")
        self.status_var.set(f"Video created: {output_path}")
        messagebox.showinfo("Video created", f"Saved video to:\n{output_path}")

    def _render_failed(self, error_message: str):
        self.rendering = False
        self.create_button.configure(state="normal")
        self.status_var.set("Rendering failed. See the error message and adjust the inputs.")
        messagebox.showerror("Render failed", error_message)


def main():
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    app = VideoToolApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
