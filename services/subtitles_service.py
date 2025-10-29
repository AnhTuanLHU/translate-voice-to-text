#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitle utilities: generate SRT/VTT from segments and burn-in via ffmpeg.
"""

from __future__ import annotations

from typing import Dict, List
import tempfile
import subprocess
import os


def _seconds_to_srt_time(seconds: float) -> str:
    milliseconds = int((seconds - int(seconds)) * 1000)
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{sec:02},{milliseconds:03}"


def build_srt(segments: List[Dict]) -> str:
    lines: List[str] = []
    for idx, seg in enumerate(segments, start=1):
        start = _seconds_to_srt_time(seg["start"])  # required keys per app
        end = _seconds_to_srt_time(seg["end"])      # required keys per app
        text = str(seg.get("text", "")).replace("\n", " ").strip()
        lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)


def build_vtt_from_srt(srt_content: str) -> str:
    return "WEBVTT\n\n" + srt_content.replace(",", ".")


def burn_in_subtitles(video_bytes: bytes, srt_text: str) -> bytes:
    if not video_bytes:
        raise RuntimeError("No video bytes provided")
    if not srt_text:
        raise RuntimeError("No SRT content provided")

    # Ensure ffmpeg is present
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise RuntimeError("ffmpeg not found. Please install ffmpeg to use subtitle burning feature.")

    temp_dir = tempfile.mkdtemp()
    in_vid = os.path.join(temp_dir, "input.mp4")
    in_srt = os.path.join(temp_dir, "subtitles.srt")
    out_vid = os.path.join(temp_dir, "output.mp4")

    try:
        with open(in_vid, "wb") as fvid:
            fvid.write(video_bytes)

        # UTF-8 BOM for Windows compatibility
        with open(in_srt, "w", encoding="utf-8-sig") as fsrt:
            fsrt.write(srt_text)

        srt_for_filter = in_srt.replace("\\", "/").replace(":", "\\:")
        subtitles_filter = f"subtitles='{srt_for_filter}':charenc=UTF-8"

        cmd = [
            "ffmpeg", "-y",
            "-i", in_vid,
            "-vf", subtitles_filter,
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            out_vid,
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {proc.stderr}")

        with open(out_vid, "rb") as fh:
            return fh.read()
    finally:
        try:
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception:
            pass


