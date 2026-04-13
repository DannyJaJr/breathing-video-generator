# Minimal Navy SEAL box breathing video with working voice
import os
import numpy as np
from moviepy.editor import VideoClip, ImageClip, AudioFileClip, CompositeVideoClip, ColorClip

DURATION = 128
WIDTH, HEIGHT = 1080, 1080
BOX_SIZE = 600
BOX_THICKNESS = 10
BOX_COLOR = (255, 255, 255)
BG_COLOR = (30, 60, 120)
LOGO_PATH = "logo.png"
VOICE_PATH = "meditation_voice.mp3"
OUTPUT_PATH = "RealityCheckMeditation_minimal.mp4"

STEPS = ["INHALE", "HOLD", "EXHALE", "HOLD"]

def make_box_frame(t):
	img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
	img[:, :] = BG_COLOR
	margin = (WIDTH - BOX_SIZE) // 2
	x0, y0 = margin, margin
	x1, y1 = x0 + BOX_SIZE, y0 + BOX_SIZE
	phase = int((t // 4) % 4)
	phase_time = t % 4
	progress = phase_time / 4.0
	import cv2
	cv2.rectangle(img, (x0, y0), (x1, y1), BOX_COLOR, BOX_THICKNESS)
	# Animate line along the box
	if phase == 0:
		x = int(x0 + progress * BOX_SIZE)
		cv2.line(img, (x0, y0), (x, y0), (0,255,0), BOX_THICKNESS*2)
	elif phase == 1:
		y = int(y0 + progress * BOX_SIZE)
		cv2.line(img, (x1, y0), (x1, y), (255,255,0), BOX_THICKNESS*2)
	elif phase == 2:
		x = int(x1 - progress * BOX_SIZE)
		cv2.line(img, (x1, y1), (x, y1), (0,255,255), BOX_THICKNESS*2)
	elif phase == 3:
		y = int(y1 - progress * BOX_SIZE)
		cv2.line(img, (x0, y1), (x0, y), (255,0,255), BOX_THICKNESS*2)
	return img

box_clip = VideoClip(make_box_frame, duration=DURATION)
background = ColorClip((WIDTH, HEIGHT), BG_COLOR, duration=DURATION)

clips = [background, box_clip]
if os.path.exists(LOGO_PATH):
	logo = ImageClip(LOGO_PATH).resize(width=200).set_position(("left", "top")).set_duration(DURATION)
	clips.append(logo)

video = CompositeVideoClip(clips)

voice = AudioFileClip(VOICE_PATH)
video = video.set_audio(voice)

video.write_videofile(OUTPUT_PATH, fps=30, audio_codec="aac")
