import os
import numpy as np
from gtts import gTTS
from moviepy.editor import (
    VideoClip, ImageClip, AudioFileClip, CompositeAudioClip, CompositeVideoClip, TextClip, ColorClip
)

# Fix for ImageMagick v7+ and font issues
os.environ["IMAGEMAGICK_BINARY"] = "magick"

# Parameters
DURATION = 128
WIDTH, HEIGHT = 1080, 1080  # Square video
BOX_SIZE = 600
BOX_THICKNESS = 10
BOX_COLOR = (255, 255, 255)
BG_COLOR = (30, 60, 120)
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"
LOGO_PATH = "logo.png"
MUSIC_PATH = "ambient_music.mp3"
OUTPUT_PATH = "RealityCheckMeditation_Merged.mp4"

STEPS = ["Inhale", "Hold", "Exhale", "Hold"]

# --- Step 1: Generate the TTS audio for each step and concatenate ---
if not os.path.exists("tts_done.flag"):
    from pydub import AudioSegment
    silence = AudioSegment.silent(duration=4000)  # 4 seconds
    tts_files = []
    for i in range(32):
        for step in STEPS:
            tts = gTTS(step, lang="en")
            fname = f"tts_{i}_{step}.mp3"
            tts.save(fname)
            # Pad to 4 seconds
            seg = AudioSegment.from_file(fname)
            if len(seg) < 4000:
                seg = seg + silence[:4000 - len(seg)]
            else:
                seg = seg[:4000]
            seg.export(fname, format="mp3")
            tts_files.append(fname)
    # Concatenate all TTS mp3s
    combined = AudioSegment.empty()
    for fname in tts_files:
        combined += AudioSegment.from_file(fname)
    combined.export("meditation_voice.mp3", format="mp3")
    # Clean up
    for fname in tts_files:
        if os.path.exists(fname):
            os.remove(fname)
    with open("tts_done.flag", "w"): pass

# --- Step 2: Create the box breathing animation ---
def make_box_frame(t):
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img[:, :] = BG_COLOR
    # Box coordinates
    margin = (WIDTH - BOX_SIZE) // 2
    x0, y0 = margin, margin
    x1, y1 = x0 + BOX_SIZE, y0 + BOX_SIZE
    # Which phase and progress
    phase = int((t // 4) % 4)
    phase_time = t % 4
    progress = phase_time / 4.0
    # Draw static box
    import cv2
    cv2.rectangle(img, (x0, y0), (x1, y1), BOX_COLOR, BOX_THICKNESS)
    # Animate line along the box
    if phase == 0:  # Top side (left to right)
        x = int(x0 + progress * BOX_SIZE)
        cv2.line(img, (x0, y0), (x, y0), (0,255,0), BOX_THICKNESS*2)
    elif phase == 1:  # Right side (top to bottom)
        y = int(y0 + progress * BOX_SIZE)
        cv2.line(img, (x1, y0), (x1, y), (255,255,0), BOX_THICKNESS*2)
    elif phase == 2:  # Bottom side (right to left)
        x = int(x1 - progress * BOX_SIZE)
        cv2.line(img, (x1, y1), (x, y1), (0,255,255), BOX_THICKNESS*2)
    elif phase == 3:  # Left side (bottom to top)
        y = int(y1 - progress * BOX_SIZE)
        cv2.line(img, (x0, y1), (x0, y), (255,0,255), BOX_THICKNESS*2)
    return img

box_clip = VideoClip(make_box_frame, duration=DURATION)

# Step text overlay
def step_text(t):
    phase = int((t // 4) % 4)
    return STEPS[phase].upper()

text_clips = [
    TextClip(step_text(i*4), fontsize=90, color="white", font=FONT_PATH, size=(WIDTH, None), method="caption")
    .set_position("center").set_start(i*4).set_duration(4)
    for i in range(DURATION // 4)
]

# Background and logo
background = ColorClip((WIDTH, HEIGHT), BG_COLOR, duration=DURATION)
if os.path.exists(LOGO_PATH):
    logo = ImageClip(LOGO_PATH).resize(width=200).set_position(("left", "top")).set_duration(DURATION)
    clips = [background, box_clip, logo] + text_clips
else:
    clips = [background, box_clip] + text_clips

video = CompositeVideoClip(clips)

# Audio
voice = AudioFileClip("meditation_voice.mp3").volumex(1.5)  # Boost voice
music = AudioFileClip(MUSIC_PATH).volumex(0.5)  # Boost music
audio = CompositeAudioClip([voice, music])
video = video.set_audio(audio)

video.write_videofile(OUTPUT_PATH, fps=30, audio_codec="aac")
