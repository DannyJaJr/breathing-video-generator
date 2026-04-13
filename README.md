# Video Tool

`Video Tool` is a local Python desktop app for generating guided breathing videos.

It can create videos with:

- animated breathing visuals
- spoken breathing guidance
- background music
- optional logo and background image
- multiple breathing presets such as box breathing, 4-7-8, AUM, Nadi Shodhana, Bellows Breath

This app is built for local use on macOS and uses a Tkinter desktop window.

## What This App Does

You open the app, choose a breathing preset or custom rhythm, adjust the title and output path, then click `Create Video Now`.

The app renders an `.mp4` video using:

- `moviepy` for video composition
- `opencv-python` for animation drawing
- `gTTS` for generated voice guidance
- `pydub` for audio timing and stitching

## Current Main Entry Point

Launch the app with:

```bash
cd /Users/daniellafontant/Applications/video-tool
./venv/bin/python app.py
```

The app code is in [app.py](/Users/daniellafontant/Applications/video-tool/app.py).

## Default Startup Mode

Right now the app opens preconfigured for `Box Breathing`.

Default values:

- Mode: `breathing`
- Breathing preset: `box-4-4-4-4`
- Cycles: `8`
- Title: `Box Breathing`
- Subtitle: `A simple guided breathing practice for calm and focus.`
- Output: `box_breathing_guided.mp4`
- Music: `ambient_music.mp3` if available

## Files In This Folder

- [app.py](/Users/daniellafontant/Applications/video-tool/app.py): main desktop app
- [ambient_music.mp3](/Users/daniellafontant/Applications/video-tool/ambient_music.mp3): default background music
- [aum-om.mp3](/Users/daniellafontant/Applications/video-tool/aum-om.mp3): AUM breathing music
- [logo.png](/Users/daniellafontant/Applications/video-tool/logo.png): optional logo
- [venv](/Users/daniellafontant/Applications/video-tool/venv): local virtual environment

## Requirements

### System Requirements

- macOS
- Python with `tkinter` support
- a working virtual environment

Important:

If your Python installation does not include `tkinter`, the desktop window will not open.

On Homebrew Python 3.12, install Tk support with:

```bash
brew install python-tk@3.12
```

## Python Packages and Versions

These versions are currently installed in the project virtual environment:

- `moviepy==1.0.3`
- `numpy==2.4.4`
- `opencv-python==4.13.0.92`
- `gTTS==2.5.4`
- `pydub==0.25.1`
- `pillow==12.2.0`
- `imageio==2.37.3`
- `imageio-ffmpeg==0.6.0`
- `requests==2.33.1`

## Install or Rebuild the Environment

If you need to rebuild the environment from scratch:

```bash
cd /Users/daniellafontant/Applications/video-tool
rm -rf venv
/opt/homebrew/bin/python3.12 -m venv venv
./venv/bin/pip install moviepy==1.0.3 numpy==2.4.4 opencv-python==4.13.0.92 gTTS==2.5.4 pydub==0.25.1 pillow==12.2.0 imageio==2.37.3 imageio-ffmpeg==0.6.0 requests==2.33.1
```

If Tk support is still missing after rebuilding, install it first:

```bash
brew install python-tk@3.12
```

## How To Launch

From the project folder:

```bash
cd /Users/daniellafontant/Applications/video-tool
./venv/bin/python app.py
```

If your shell is already using the virtual environment, this also works:

```bash
python app.py
add file logo.png
```

## How To Use The App

### 1. Open the app

Run:

```bash
./venv/bin/python app.py
```

### 2. Check the breathing preset

At the top of the window, choose a preset in the `Breathing preset` dropdown.

Examples:

- `box-4-4-4-4`
- `relax-4-7-8`


### 3. Review or edit the fields

Main fields:

- `Cycles`
- `Title`
- `Subtitle`
- `Output`
- `Logo`
- `Voice`
- `Music`
- `Background`

The app also includes:

- `Breathing steps for custom rhythm`
- `Coaching lines for voiceover`

These let you override the preset and create your own breathing video.

### 4. Start the render

Scroll down and click:

```text
Create Video Now
```

That is the button that starts the video generation.

### 5. Know when the video is done

While rendering:

- the button is disabled
- the status changes to:

```text
Rendering video. This can take a minute or two.
```

When the video finishes:

- a popup says the video was created
- the status shows the saved file path

## Common Preset Behavior

### Box Breathing

The current default preset.

Guidance:

- `Inhale slowly through your nose.`
- `Hold gently.`
- `Exhale slowly through your mouth.`
- `Hold gently.`

### 4-7-8

Useful for sleep or anxiety support.

### AUM Breathing

Uses:

- `Inhale slowly`
- long `AUM` exhale
- rest period

### Nadi Shodhana

Alternate nostril breathing with guided left/right nostril steps.

### Bellows Breath

Fast `1 second inhale / 1 second exhale` energizing preset.

## Troubleshooting

### Error: `No module named '_tkinter'`

Your Python does not include Tk support.

Fix:

```bash
brew install python-tk@3.12
```

Then rerun the app.

### The app opens but the bottom is cut off

The app window is scrollable.

- scroll down
- the render button is near the bottom

### Voice sounds wrong or too slow

The app currently uses `gTTS` for generated voice guidance.

It can time the voice clips to the breathing steps, but it does not provide advanced voice selection like a guaranteed female voice picker.

### Rendering fails

Check:

- the output path is valid
- audio/image files exist
- the virtual environment is installed correctly

## Quick Start For A Complete Beginner

If you have never used this project before:

1. Open Terminal
2. Go to the project:

```bash
cd /Users/daniellafontant/Applications/video-tool
```

3. Start the app:

```bash
./venv/bin/python app.py
```

4. Leave the default `Box Breathing` settings as they are
5. Click `Create Video Now`
6. Wait for the popup confirmation
7. Find your video at:

```text
/Users/daniellafontant/Applications/video-tool/box_breathing_guided.mp4
```

## Notes

- This project is currently a local desktop tool, not a packaged Mac app
- The render can take time depending on video duration
- Generated voice quality depends on the text-to-speech backend
