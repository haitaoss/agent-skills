---
name: lrc-mp3-lyrics
description: Shift `.lrc` timestamps, remove stale `[awlrc:...]` blocks, trim matching `.mp3` audio from the start when lyrics are moved earlier, and sync embedded MP3 lyrics through `ffmpeg` and `ffprobe`. Use when Codex needs grouped lyric offset work across `.lrc`, MP3 audio, and embedded lyric tags, or when it needs to repair or rewrite embedded MP3 lyric tags without re-deriving the workflow in conversation.
---

# LRC MP3 Lyrics

Use `scripts/lrc_mp3_tool.py` instead of ad hoc timestamp math or one-off `ffmpeg` commands.

## Quick Start

Prefer these entry points:

```powershell
python scripts/lrc_mp3_tool.py sync-pair --lrc "C:\path\song.lrc" --mp3 "C:\path\song.mp3" --seconds -25 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
python scripts/lrc_mp3_tool.py sync-dir --directory "C:\path\music" --seconds -40 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
python scripts/lrc_mp3_tool.py embed --mp3 "C:\path\song.mp3" --lrc "C:\path\song.lrc" --ffmpeg "C:\path\ffmpeg.exe"
```

## Workflow

1. Default grouped "offset" behavior: use `sync-pair` for per-song offsets or `sync-dir` for one shared offset across matched pairs.
2. Add `--trim-audio` when negative offsets should also remove the same amount from the start of the MP3 audio.
3. Use `shift` only when the user explicitly wants to change the external `.lrc` without touching audio or MP3 tags.
4. Use `embed` only when the `.lrc` is already correct and the MP3 tags just need to be refreshed.
5. `embed`, `sync-pair`, and `sync-dir` strip stale `[awlrc:...]` lines by default because some players prefer that encoded block over normal LRC timestamps. Pass `--keep-awlrc` only when the user explicitly wants to preserve it.

## Command Notes

- Negative offsets move lyrics earlier; positive offsets move lyrics later.
- `--trim-audio` only supports negative offsets. The script trims the start of the MP3; it does not pad silence for positive offsets.
- Timestamp fractions with 1, 2, or 3 digits are preserved with the same width after shifting.
- Any timestamp that would become negative is clamped to `00:00`.
- `embed` and grouped sync commands write both `lyrics` and, by default, `lyrics-zho`. Pass `--language none` to skip the language-specific tag.
- `sync-dir` only processes `.lrc`/`.mp3` pairs with the same basename.

## Bilingual References

- English command reference: `references/commands.en.md`
- Chinese command reference: `references/commands.zh-CN.md`

## Validation

```powershell
python scripts/lrc_mp3_tool.py sync-pair --lrc "C:\path\song.lrc" --mp3 "C:\path\song.mp3" --seconds -25 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
python C:\Users\lin\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```
