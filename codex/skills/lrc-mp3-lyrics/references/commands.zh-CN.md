# LRC MP3 Lyrics 命令说明

当脚本需要明确命令配方时，优先参考这里。

## 默认联动操作

单首歌且每首偏移量不同的时候，用 `sync-pair`。

```powershell
python scripts/lrc_mp3_tool.py sync-pair --lrc "C:\path\song.lrc" --mp3 "C:\path\song.mp3" --seconds -25 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
```

- 负数偏移表示歌词提前。
- `--trim-audio` 会把 MP3 开头按同样的绝对秒数裁掉。
- `sync-pair`、`sync-dir`、`embed` 默认会去掉 `[awlrc:...]` 行。

## 目录批量联动

同一个目录里的成对 `.lrc/.mp3` 都用相同偏移量时，用 `sync-dir`。

```powershell
python scripts/lrc_mp3_tool.py sync-dir --directory "C:\path\music" --seconds -40 --trim-audio --ffmpeg "C:\path\ffmpeg.exe"
```

## 只改 LRC

用户明确只想改外部 `.lrc` 时，用 `shift`。

```powershell
python scripts/lrc_mp3_tool.py shift --in-place --seconds -40 "C:\path\song.lrc"
```

## 只刷新 MP3 内嵌歌词

`.lrc` 已经正确，只想把内容重新写进 MP3 标签时，用 `embed`。

```powershell
python scripts/lrc_mp3_tool.py embed --mp3 "C:\path\song.mp3" --lrc "C:\path\song.lrc" --ffmpeg "C:\path\ffmpeg.exe"
```

## 只裁音频

用户明确只想裁音频、不改歌词时，用 `trim-audio`。

```powershell
python scripts/lrc_mp3_tool.py trim-audio --in-place --seconds 25 --ffmpeg "C:\path\ffmpeg.exe" "C:\path\song.mp3"
```

## 注意

- `sync-pair` 和 `sync-dir` 里的 `--trim-audio` 只支持负数歌词偏移。
- 正数偏移只会让歌词变晚，脚本不会自动在音频前面补静音。
- `embed` 默认同时写入 `lyrics` 和 `lyrics-zho`，如果不要语言标签，传 `--language none`。
