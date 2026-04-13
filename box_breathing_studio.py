


from moviepy.editor import *
import numpy as np
import os
from gtts import gTTS

# Fix for ImageMagick v7+ and font issues
os.environ["IMAGEMAGICK_BINARY"] = "magick"

# Parameters
duration = 128
width, height = 1080, 1080  # Square video
box_size = 600
box_thickness = 10
box_color = (255, 255, 255)
bg_color = (30, 60, 120)
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
logo_path = "logo.png"
music_path = "ambient_music.mp3"
output_path = "RealityCheckMeditation.mp4"

# Step 1: Generate the TTS audio for each step and concatenate
steps = ["Inhale", "Hold", "Exhale", "Hold"]
tts_files = []
if not os.path.exists("tts_done.flag"):
    from pydub import AudioSegment
    silence = AudioSegment.silent(duration=4000)  # 4 seconds
    for i in range(32):
        for step in steps:
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

# Step 2: Create the box breathing animation
def make_box_frame(t):
    # t: time in seconds
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:, :] = bg_color
    # Box coordinates
    margin = (width - box_size) // 2
    x0, y0 = margin, margin
    x1, y1 = x0 + box_size, y0 + box_size
    # Which phase and progress
    phase = int((t // 4) % 4)
    phase_time = t % 4
    progress = phase_time / 4.0
    # Draw static box
    import cv2
    cv2.rectangle(img, (x0, y0), (x1, y1), box_color, box_thickness)
    # Animate line along the box
    if phase == 0:  # Top side (left to right)
        x = int(x0 + progress * box_size)
        cv2.line(img, (x0, y0), (x, y0), (0,255,0), box_thickness*2)
    elif phase == 1:  # Right side (top to bottom)
        y = int(y0 + progress * box_size)
        cv2.line(img, (x1, y0), (x1, y), (255,255,0), box_thickness*2)
    elif phase == 2:  # Bottom side (right to left)
        x = int(x1 - progress * box_size)
        cv2.line(img, (x1, y1), (x, y1), (0,255,255), box_thickness*2)
    elif phase == 3:  # Left side (bottom to top)
        y = int(y1 - progress * box_size)
        cv2.line(img, (x0, y1), (x0, y), (255,0,255), box_thickness*2)
    return img

box_clip = VideoClip(make_box_frame, duration=duration)

# Step text overlay
def step_text(t):
    phase = int((t // 4) % 4)
    return steps[phase].upper()

text_clips = [
    TextClip(step_text(i*4), fontsize=90, color="white", font=font_path, size=(width, None), method="caption")
    .set_position("center").set_start(i*4).set_duration(4)
    for i in range(duration // 4)
]

# Background and logo
background = ColorClip((width, height), bg_color, duration=duration)
if os.path.exists(logo_path):
    logo = ImageClip(logo_path).resize(width=200).set_position(("left", "top")).set_duration(duration)
    clips = [background, box_clip, logo] + text_clips
else:
    clips = [background, box_clip] + text_clips

video = CompositeVideoClip(clips)

# Audio
voice = AudioFileClip("meditation_voice.mp3").volumex(1.5)  # Boost voice
music = AudioFileClip(music_path).volumex(0.5)  # Boost music
audio = CompositeAudioClip([voice, music])
video = video.set_audio(audio)

video.write_videofile(output_path, fps=30, audio_codec="aac")