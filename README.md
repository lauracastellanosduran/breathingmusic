# Breathing Room TV ambient music

Weekly production cycle for Breathing Room ambient long-form videos. Each video is one purpose — focus, relax, meditate, or sleep — with one sonic world and one visual world. Videos are rendered for human review and kept private. This repo does not publish to YouTube.

The rules for a cycle live in `docs/AMBIENT_MASTER_RULES.md`.

## Run a cycle

```bash
python -m breathingroom
```

The cycle writes `cycles/<date>/` with a scorecard, the working title, music prompts, a concept thumbnail, metadata, and a QA report.

Music is requested from ElevenLabs only after a title is chosen, with `force_instrumental` set. Set `ELEVENLABS_API_KEY` in the environment. A 30-minute master is three sections of up to 10 minutes, joined with a 15-second crossfade and a final fade.

A finished picture uses `VISUAL_PLATE` when that video file is set. For a rainy window, the cycle can also build the picture from `assets/rainy-window-daylight.jpg`: the still stays put, and original rain scrolls downward. Rain and streams are never reversed. Without a plate or that still, the cycle stops before a final video and leaves the concept unpublished.

`upload_status` in metadata is always `PRIVATE`.
