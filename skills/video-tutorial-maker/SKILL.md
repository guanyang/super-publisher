---
name: video-tutorial-maker
description: Create scripted tutorial videos with narration, TTS, aligned subtitles, MP4 rendering, and platform variants. Use when Codex needs to create or revise tutorial, explainer, product walkthrough, course, demo, or short-form videos; generate 16:9 landscape output by default unless the user explicitly asks for 9:16, 1:1, or another format.
---

# Video Tutorial Maker

Use this skill to turn a topic, outline, script, or existing video into a finished tutorial video package.

Default assumption: produce a 16:9 landscape MP4 first. Create 9:16 or other platform variants only when requested or clearly useful.

## Workflow

1. Define the deliverable.
   - Confirm the topic, target audience, tone, duration, language, and required output path when they are unclear.
   - If the user does not specify aspect ratio, use `1920x1080` landscape video.
   - For coding or software tutorials, prefer a clear slide/screen sequence over dense narration.

2. Write the video package.
   - Create a concise script with one narration block per scene or slide.
   - For each scene, define title, subtitle, bullets or screen action, visual style, and narration.
   - Keep on-screen text shorter than narration. Do not force full captions into the visual design.

3. Generate speech.
   - Prefer `edge-tts` when available because it is free and more natural than basic system voices.
   - For Chinese, start with `zh-CN-XiaoxiaoNeural`; adjust voice or rate only if the user asks or the result is clearly poor.
   - Generate audio per scene, not one large narration file. Per-scene audio makes transition sync and subtitle offsetting deterministic.

4. Build subtitles from the same timeline as audio.
   - Use the subtitle output from TTS when available.
   - Parse both `00:00:01.234` and `00:00:01,234` timestamp formats.
   - Offset each scene subtitle by the cumulative scene duration.
   - Verify the final subtitle file contains real timestamps and no `NaN`.

5. Render video.
   - Render each scene to a fixed duration equal to its audio duration plus any intended pause.
   - If a scene has a trailing pause, pad that scene's audio with silence to the exact scene video duration before concatenating.
   - Concatenate padded scene audio, not raw scene audio. Otherwise voice will drift earlier after each transition.
   - Mux video, audio, and soft subtitles into MP4 when supported; otherwise output the subtitle file as a sidecar.

6. Produce platform variants.
   - Default final output: `1920x1080`, SAR `1:1`, DAR `16:9`.
   - For converting a 16:9 master to 9:16 without losing content, use a blurred or darkened background plus the full-width original video centered.
   - Avoid cropping important tutorial content unless the user explicitly wants a crop-first social cut.

7. Verify before delivery.
   - Use `ffprobe` to confirm width, height, aspect ratio, streams, duration, and file size.
   - Compare final video and audio durations. Differences should be near zero; a few milliseconds is fine.
   - Extract at least one preview frame for visual inspection; for long videos, inspect an early and mid/late frame.
   - Check subtitles for timestamp validity and obvious drift.

## Edge TTS Pattern

Use a project virtualenv if one exists:

```bash
.venv/bin/edge-tts --voice zh-CN-XiaoxiaoNeural --rate +0% \
  --file scene-01.txt \
  --write-media scene-01.mp3 \
  --write-subtitles scene-01.vtt
```

If network or TTS fails, report the exact blocker and either retry after permission is granted or fall back to a clearly labeled system TTS draft.

## Sync Rules

The most common drift bug is this:

```text
scene video duration = raw audio duration + pause
concatenated audio   = raw audio duration only
```

This creates cumulative drift. Fix it by padding every scene audio to the corresponding scene video duration:

```bash
ffmpeg -y -i scene-01.mp3 \
  -af "apad,atrim=0:SCENE_DURATION" \
  -ar 24000 -ac 1 -c:a pcm_s16le scene-01-padded.wav
```

Concatenate `scene-XX-padded.wav` files, then mux that audio with the video.

## 9:16 Conversion Pattern

When the source is 16:9 and content must not be cropped:

```bash
ffmpeg -y -i input.mp4 \
  -filter_complex "[0:v]split=2[bgsrc][fgsrc];\
[bgsrc]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,\
gblur=sigma=32,eq=brightness=-0.12:saturation=0.75[bg];\
[fgsrc]scale=1080:-2[fg];\
[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p,setsar=1[v]" \
  -map "[v]" -map 0:a:0 -map '0:s?' \
  -c:v libx264 -preset veryfast -crf 20 \
  -c:a copy -c:s mov_text -movflags +faststart output-9x16.mp4
```

After conversion, verify:

```bash
ffprobe -v error \
  -show_entries stream=index,codec_type,codec_name,width,height,sample_aspect_ratio,display_aspect_ratio,duration \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 output-9x16.mp4
```

Expected video values for this 9:16 variant:

```text
width=1080
height=1920
sample_aspect_ratio=1:1
display_aspect_ratio=9:16
```

## Delivery

In the final answer, provide the absolute path to the finished MP4 and mention the verification actually run. If there are multiple outputs, identify the recommended one first, usually the 16:9 file.
