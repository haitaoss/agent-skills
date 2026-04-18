#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path


TIMESTAMP_RE = re.compile(r"\[(\d+):(\d{2})\.(\d{1,3})\]")


@dataclass(frozen=True)
class MatchedPair:
    stem: str
    lrc: Path
    mp3: Path


def parse_offset_ms(seconds_text: str) -> int:
    try:
        seconds = Decimal(seconds_text)
    except InvalidOperation as exc:
        raise SystemExit(f"Invalid seconds value: {seconds_text}") from exc
    milliseconds = (seconds * Decimal("1000")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    )
    return int(milliseconds)


def milliseconds_to_seconds_text(milliseconds: int) -> str:
    seconds = (Decimal(milliseconds) / Decimal("1000")).quantize(
        Decimal("0.001"), rounding=ROUND_HALF_UP
    )
    normalized = format(seconds, "f").rstrip("0").rstrip(".")
    return normalized or "0"


def shift_lrc_text(text: str, offset_ms: int) -> str:
    def replace(match: re.Match[str]) -> str:
        minute_text, second_text, fraction_text = match.groups()
        fraction_width = len(fraction_text)
        fraction_scale = 10 ** (3 - fraction_width)
        total_ms = (
            ((int(minute_text) * 60) + int(second_text)) * 1000
            + int(fraction_text) * fraction_scale
        )
        shifted_ms = max(0, total_ms + offset_ms)
        new_minutes = shifted_ms // 60000
        new_seconds = (shifted_ms % 60000) // 1000
        new_fraction = (shifted_ms % 1000) // fraction_scale
        return (
            f"[{new_minutes:0{len(minute_text)}d}:{new_seconds:02d}"
            f".{new_fraction:0{fraction_width}d}]"
        )

    return TIMESTAMP_RE.sub(replace, text)


def strip_awlrc_lines(text: str) -> str:
    return "".join(
        line for line in text.splitlines(keepends=True) if not line.startswith("[awlrc:")
    )


def normalize_lyrics_for_verify(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    return normalized.rstrip("\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="")


def resolve_ffprobe(ffmpeg_path: Path, ffprobe_arg: str | None) -> Path:
    if ffprobe_arg:
        return Path(ffprobe_arg)
    candidate = ffmpeg_path.with_name(
        "ffprobe.exe" if ffmpeg_path.suffix.lower() == ".exe" else "ffprobe"
    )
    if candidate.exists():
        return candidate
    return Path("ffprobe")


def normalize_language(language: str | None) -> str | None:
    if not language:
        return None
    normalized = language.strip().lower()
    if normalized in {"", "none", "null", "off"}:
        return None
    return normalized


def run_checked(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def create_temp_mp3(path: Path, label: str) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix=f"{path.stem}.{label}.",
        suffix=path.suffix,
        dir=path.parent,
        delete=False,
    ) as handle:
        return Path(handle.name)


def prepare_lrc_text(original: str, offset_ms: int, keep_awlrc: bool) -> str:
    prepared = original
    if offset_ms != 0:
        prepared = shift_lrc_text(prepared, offset_ms)
    if not keep_awlrc:
        prepared = strip_awlrc_lines(prepared)
    return prepared


def write_metadata_tag(
    input_path: Path, output_path: Path, ffmpeg_path: Path, tag_name: str, value: str
) -> None:
    command = [
        str(ffmpeg_path),
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(input_path),
        "-map",
        "0",
        "-c",
        "copy",
        "-id3v2_version",
        "3",
        "-write_id3v1",
        "1",
        "-metadata",
        f"{tag_name}={value}",
        str(output_path),
    ]
    run_checked(command)


def probe_tags(mp3_path: Path, ffprobe_path: Path, language: str | None) -> dict[str, str]:
    requested = ["lyrics"]
    if language:
        requested.append(f"lyrics-{language}")
    probe_command = [
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        f"format_tags={','.join(requested)}",
        "-of",
        "json",
        str(mp3_path),
    ]
    probe_output = run_checked(probe_command).stdout
    return json.loads(probe_output).get("format", {}).get("tags", {})


def verify_lyrics_tags(
    mp3_path: Path, lyrics: str, ffprobe_path: Path, language: str | None
) -> None:
    tags = probe_tags(mp3_path, ffprobe_path, language)
    expected = normalize_lyrics_for_verify(lyrics)
    actual_generic = normalize_lyrics_for_verify(tags.get("lyrics"))
    if actual_generic != expected:
        raise RuntimeError(f"Failed to verify generic lyrics tag in {mp3_path}")
    if language:
        actual_language = normalize_lyrics_for_verify(tags.get(f"lyrics-{language}"))
        if actual_language != expected:
            raise RuntimeError(
                f"Failed to verify language lyrics tag lyrics-{language} in {mp3_path}"
            )


def write_lyrics_tags(
    input_mp3_path: Path,
    output_mp3_path: Path,
    lyrics: str,
    ffmpeg_path: Path,
    ffprobe_path: Path,
    language: str | None,
) -> None:
    intermediate: Path | None = None
    final_output = output_mp3_path
    try:
        if language:
            intermediate = create_temp_mp3(output_mp3_path, "lyrics-generic")
            write_metadata_tag(
                input_path=input_mp3_path,
                output_path=intermediate,
                ffmpeg_path=ffmpeg_path,
                tag_name="lyrics",
                value=lyrics,
            )
            write_metadata_tag(
                input_path=intermediate,
                output_path=output_mp3_path,
                ffmpeg_path=ffmpeg_path,
                tag_name=f"lyrics-{language}",
                value=lyrics,
            )
        else:
            write_metadata_tag(
                input_path=input_mp3_path,
                output_path=output_mp3_path,
                ffmpeg_path=ffmpeg_path,
                tag_name="lyrics",
                value=lyrics,
            )

        verify_lyrics_tags(
            mp3_path=final_output,
            lyrics=lyrics,
            ffprobe_path=ffprobe_path,
            language=language,
        )
    finally:
        if intermediate and intermediate.exists():
            intermediate.unlink()


def trim_audio(
    input_mp3_path: Path, output_mp3_path: Path, ffmpeg_path: Path, seconds_text: str
) -> None:
    command = [
        str(ffmpeg_path),
        "-loglevel",
        "error",
        "-y",
        "-ss",
        seconds_text,
        "-i",
        str(input_mp3_path),
        "-map",
        "0",
        "-c",
        "copy",
        "-id3v2_version",
        "3",
        "-write_id3v1",
        "1",
        str(output_mp3_path),
    ]
    run_checked(command)


def collect_paths(paths: list[str], recursive: bool, suffix: str) -> list[Path]:
    collected: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            pattern = f"**/*{suffix}" if recursive else f"*{suffix}"
            collected.extend(sorted(path.glob(pattern)))
        else:
            collected.append(path)
    unique: dict[str, Path] = {}
    for path in collected:
        unique[str(path.resolve())] = path
    return list(unique.values())


def find_pairs(directory: Path, recursive: bool) -> list[MatchedPair]:
    lrc_pattern = "**/*.lrc" if recursive else "*.lrc"
    mp3_pattern = "**/*.mp3" if recursive else "*.mp3"
    lrc_files = {
        str(path.relative_to(directory).with_suffix("")).lower(): path
        for path in sorted(directory.glob(lrc_pattern))
    }
    mp3_files = {
        str(path.relative_to(directory).with_suffix("")).lower(): path
        for path in sorted(directory.glob(mp3_pattern))
    }
    shared = sorted(set(lrc_files) & set(mp3_files))
    return [
        MatchedPair(stem=stem, lrc=lrc_files[stem], mp3=mp3_files[stem]) for stem in shared
    ]


def sync_pair(
    lrc_path: Path,
    mp3_path: Path,
    offset_ms: int,
    trim_audio_enabled: bool,
    keep_awlrc: bool,
    ffmpeg_path: Path,
    ffprobe_path: Path,
    language: str | None,
) -> list[str]:
    if trim_audio_enabled and offset_ms > 0:
        raise SystemExit(
            "--trim-audio only supports negative offsets because this workflow trims"
            " audio from the start instead of padding silence."
        )

    original_lrc = read_text(lrc_path)
    prepared_lrc = prepare_lrc_text(
        original=original_lrc, offset_ms=offset_ms, keep_awlrc=keep_awlrc
    )
    if prepared_lrc != original_lrc:
        write_text(lrc_path, prepared_lrc)

    trim_input: Path = mp3_path
    trim_output: Path | None = None
    embed_output: Path | None = None
    messages: list[str] = []
    try:
        if trim_audio_enabled and offset_ms < 0:
            trim_output = create_temp_mp3(mp3_path, "trimmed")
            trim_seconds = milliseconds_to_seconds_text(-offset_ms)
            trim_audio(
                input_mp3_path=mp3_path,
                output_mp3_path=trim_output,
                ffmpeg_path=ffmpeg_path,
                seconds_text=trim_seconds,
            )
            trim_input = trim_output
            messages.append(f"trimmed {mp3_path} by {trim_seconds}s")

        embed_output = create_temp_mp3(mp3_path, "embedded")
        write_lyrics_tags(
            input_mp3_path=trim_input,
            output_mp3_path=embed_output,
            lyrics=prepared_lrc,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            language=language,
        )
        embed_output.replace(mp3_path)

        if prepared_lrc != original_lrc:
            messages.append(f"updated {lrc_path}")
        messages.append(f"embedded {lrc_path} -> {mp3_path}")
        return messages
    finally:
        if trim_output and trim_output.exists():
            trim_output.unlink()
        if embed_output and embed_output.exists():
            embed_output.unlink()


def command_shift(args: argparse.Namespace) -> int:
    offset_ms = parse_offset_ms(args.seconds)
    targets = collect_paths(args.paths, recursive=args.recursive, suffix=".lrc")
    if not targets:
        raise SystemExit("No .lrc files found.")

    for path in targets:
        original = read_text(path)
        shifted = shift_lrc_text(original, offset_ms)
        destination = (
            path if args.in_place else path.with_name(f"{path.stem}.shifted{path.suffix}")
        )
        write_text(destination, shifted)
        print(f"shifted {path} -> {destination}")
    return 0


def command_trim_audio(args: argparse.Namespace) -> int:
    targets = collect_paths(args.paths, recursive=args.recursive, suffix=".mp3")
    if not targets:
        raise SystemExit("No .mp3 files found.")

    seconds = Decimal(args.seconds)
    if seconds <= 0:
        raise SystemExit("trim-audio requires a positive --seconds value.")

    for path in targets:
        destination = (
            path if args.in_place else path.with_name(f"{path.stem}.trimmed{path.suffix}")
        )
        working_output = destination
        temp_output: Path | None = None
        try:
            if args.in_place:
                temp_output = create_temp_mp3(path, "trimmed")
                working_output = temp_output
            trim_audio(
                input_mp3_path=path,
                output_mp3_path=working_output,
                ffmpeg_path=Path(args.ffmpeg),
                seconds_text=args.seconds,
            )
            if args.in_place:
                assert temp_output is not None
                temp_output.replace(path)
            print(f"trimmed {path} -> {destination}")
        finally:
            if temp_output and temp_output.exists():
                temp_output.unlink()
    return 0


def command_embed(args: argparse.Namespace) -> int:
    ffmpeg_path = Path(args.ffmpeg)
    ffprobe_path = resolve_ffprobe(ffmpeg_path, args.ffprobe)
    language = normalize_language(args.language)
    messages = sync_pair(
        lrc_path=Path(args.lrc),
        mp3_path=Path(args.mp3),
        offset_ms=0,
        trim_audio_enabled=False,
        keep_awlrc=args.keep_awlrc,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        language=language,
    )
    for message in messages:
        print(message)
    return 0


def command_sync_pair(args: argparse.Namespace) -> int:
    ffmpeg_path = Path(args.ffmpeg)
    ffprobe_path = resolve_ffprobe(ffmpeg_path, args.ffprobe)
    language = normalize_language(args.language)
    offset_ms = parse_offset_ms(args.seconds)
    messages = sync_pair(
        lrc_path=Path(args.lrc),
        mp3_path=Path(args.mp3),
        offset_ms=offset_ms,
        trim_audio_enabled=args.trim_audio,
        keep_awlrc=args.keep_awlrc,
        ffmpeg_path=ffmpeg_path,
        ffprobe_path=ffprobe_path,
        language=language,
    )
    for message in messages:
        print(message)
    return 0


def command_sync_dir(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    ffmpeg_path = Path(args.ffmpeg)
    ffprobe_path = resolve_ffprobe(ffmpeg_path, args.ffprobe)
    offset_ms = parse_offset_ms(args.seconds)
    language = normalize_language(args.language)
    pairs = find_pairs(directory, recursive=args.recursive)
    if not pairs:
        raise SystemExit(f"No matching .lrc/.mp3 pairs found in {directory}")

    for pair in pairs:
        messages = sync_pair(
            lrc_path=pair.lrc,
            mp3_path=pair.mp3,
            offset_ms=offset_ms,
            trim_audio_enabled=args.trim_audio,
            keep_awlrc=args.keep_awlrc,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
            language=language,
        )
        for message in messages:
            print(message)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Shift LRC timestamps, optionally trim MP3 audio from the start, remove stale"
            " awlrc blocks, and sync embedded MP3 lyrics."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    shift_parser = subparsers.add_parser(
        "shift", help="Shift timestamps inside one or more .lrc files."
    )
    shift_parser.add_argument("paths", nargs="+", help="One or more .lrc files or directories.")
    shift_parser.add_argument(
        "--seconds",
        required=True,
        help="Signed offset in seconds. Use -40 to move lyrics 40 seconds earlier.",
    )
    shift_parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the original .lrc files.",
    )
    shift_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into directories passed as positional paths.",
    )
    shift_parser.set_defaults(func=command_shift)

    trim_parser = subparsers.add_parser(
        "trim-audio", help="Trim one or more MP3 files from the start."
    )
    trim_parser.add_argument("paths", nargs="+", help="One or more .mp3 files or directories.")
    trim_parser.add_argument(
        "--seconds",
        required=True,
        help="Positive seconds removed from the start of each MP3.",
    )
    trim_parser.add_argument("--ffmpeg", required=True, help="Path to ffmpeg executable.")
    trim_parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the original .mp3 files.",
    )
    trim_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into directories passed as positional paths.",
    )
    trim_parser.set_defaults(func=command_trim_audio)

    embed_parser = subparsers.add_parser(
        "embed",
        help="Write a finished .lrc file into MP3 lyrics tags, stripping awlrc by default.",
    )
    embed_parser.add_argument("--mp3", required=True, help="Target MP3 path.")
    embed_parser.add_argument("--lrc", required=True, help="Source LRC path.")
    embed_parser.add_argument("--ffmpeg", required=True, help="Path to ffmpeg executable.")
    embed_parser.add_argument("--ffprobe", help="Optional path to ffprobe executable.")
    embed_parser.add_argument(
        "--language",
        default="zho",
        help="Optional ISO 639-2 language code for the language-specific lyrics tag.",
    )
    embed_parser.add_argument(
        "--keep-awlrc",
        action="store_true",
        help="Keep [awlrc:...] lines instead of stripping them before embedding.",
    )
    embed_parser.set_defaults(func=command_embed)

    sync_pair_parser = subparsers.add_parser(
        "sync-pair",
        help=(
            "Shift one .lrc/.mp3 pair, optionally trim the MP3 from the start, then"
            " embed the cleaned LRC."
        ),
    )
    sync_pair_parser.add_argument("--mp3", required=True, help="Target MP3 path.")
    sync_pair_parser.add_argument("--lrc", required=True, help="Source LRC path.")
    sync_pair_parser.add_argument(
        "--seconds",
        default="0",
        help="Signed lyric offset in seconds applied before embedding.",
    )
    sync_pair_parser.add_argument(
        "--trim-audio",
        action="store_true",
        help="Trim the MP3 start by the absolute value of a negative offset.",
    )
    sync_pair_parser.add_argument("--ffmpeg", required=True, help="Path to ffmpeg executable.")
    sync_pair_parser.add_argument("--ffprobe", help="Optional path to ffprobe executable.")
    sync_pair_parser.add_argument(
        "--language",
        default="zho",
        help="Optional ISO 639-2 language code for the language-specific lyrics tag.",
    )
    sync_pair_parser.add_argument(
        "--keep-awlrc",
        action="store_true",
        help="Keep [awlrc:...] lines instead of stripping them before embedding.",
    )
    sync_pair_parser.set_defaults(func=command_sync_pair)

    sync_parser = subparsers.add_parser(
        "sync-dir",
        help=(
            "Match .lrc and .mp3 files by basename, optionally shift the LRC, optionally"
            " trim MP3 audio, then embed the cleaned LRC."
        ),
    )
    sync_parser.add_argument(
        "--directory",
        required=True,
        help="Directory containing matching .lrc and .mp3 files.",
    )
    sync_parser.add_argument(
        "--seconds",
        default="0",
        help="Signed lyric offset in seconds applied before embedding.",
    )
    sync_parser.add_argument(
        "--trim-audio",
        action="store_true",
        help="Trim the MP3 start by the absolute value of a negative offset.",
    )
    sync_parser.add_argument("--ffmpeg", required=True, help="Path to ffmpeg executable.")
    sync_parser.add_argument("--ffprobe", help="Optional path to ffprobe executable.")
    sync_parser.add_argument(
        "--language",
        default="zho",
        help="Optional ISO 639-2 language code for the language-specific lyrics tag.",
    )
    sync_parser.add_argument(
        "--keep-awlrc",
        action="store_true",
        help="Keep [awlrc:...] lines instead of stripping them before embedding.",
    )
    sync_parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories when matching pairs.",
    )
    sync_parser.set_defaults(func=command_sync_dir)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr or str(exc))
        raise
