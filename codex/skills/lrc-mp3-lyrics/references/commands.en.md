# LRC MP3 Lyrics Commands

Use these commands when the bundled script needs a concrete recipe.

## Default grouped operation

Use `sync-pair` for one song when the user gives a per-song offset.

```powershell
python scripts/lrc_mp3_tool.py sync-pair --lrc "C:\path\song.lrc" --mp3 "C:\path\song.mp3" --seconds -25 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
```

- Negative offsets move lyrics earlier.
- `--trim-audio` trims the MP3 start by the same absolute amount.
- `sync-pair`, `sync-dir`, and `embed` strip `[awlrc:...]` lines by default.

## Directory-wide grouped operation

Use `sync-dir` when every matched pair in one directory should receive the same offset.

```powershell
python scripts/lrc_mp3_tool.py sync-dir --directory "C:\path\music" --seconds -40 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
```

## LRC-only movement

Use `shift` when only the external `.lrc` file should change.

```powershell
python scripts/lrc_mp3_tool.py shift --in-place --seconds -40 "C:\path\song.lrc"
```

## MP3-only tag refresh

Use `embed` when the `.lrc` is already correct and only the MP3 tags need to be refreshed.

```powershell
python scripts/lrc_mp3_tool.py embed --mp3 "C:\path\song.mp3" --lrc "C:\path\song.lrc" --ffmpeg "C:\path\ffmpeg.exe"
```

## Audio-only trimming

Use `trim-audio` when the user explicitly wants to cut audio without changing lyrics.

```powershell
python scripts/lrc_mp3_tool.py trim-audio --in-place --seconds 25 --ffmpeg "C:\path\ffmpeg.exe" "C:\path\song.mp3"
```

## Notes

- `--trim-audio` only supports negative lyric offsets in `sync-pair` and `sync-dir`.
- Positive offsets shift lyrics later, but the script does not pad silence at the start of the MP3.
- `embed` writes both `lyrics` and `lyrics-zho` by default. Pass `--language none` to skip the language-specific tag.
