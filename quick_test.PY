#!/usr/bin/env python3
"""
quick_test.py
Minimal, low-dependency test script to transcribe a local audio/video file using openai-whisper.
Usage:
    python quick_test.py --file /path/to/file.mp4 --model base --lang vi --srt out.srt

This script prefers to be simple and robust for local testing.
"""
import argparse
import os
import sys

try:
    import whisper
except Exception as e:
    print("Missing dependency: openai-whisper (pip install openai-whisper)")
    raise

def seconds_to_srt_time(s):
    ms = int((s - int(s)) * 1000)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    return f"{h:02}:{m:02}:{sec:02},{ms:03}"

def segments_to_srt(segments):
    lines = []
    for i, seg in enumerate(segments, start=1):
        start = seconds_to_srt_time(seg['start'])
        end = seconds_to_srt_time(seg['end'])
        text = seg.get('text', '').replace('\n', ' ').strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description="Quick transcription test with Whisper")
    p.add_argument('--file', '-f', required=True, help='Path to audio/video file')
    p.add_argument('--model', '-m', default='base', help='Whisper model size (tiny|base|small|medium|large)')
    p.add_argument('--lang', '-l', default=None, help='Language code (e.g., vi, en). If omitted, Whisper will auto-detect.')
    p.add_argument('--srt', help='If provided, save segments as an SRT file at this path')
    args = p.parse_args()

    filepath = args.file
    if not os.path.exists(filepath):
        print(f"❌ File does not exist: {filepath}")
        sys.exit(2)

    print(f"🔄 Loading Whisper model '{args.model}' (this may take a while)...")
    try:
        model = whisper.load_model(args.model)
    except Exception as e:
        print(f"❌ Failed to load Whisper model: {e}")
        sys.exit(3)

    print(f"🎤 Transcribing {filepath} ...")
    try:
        if args.lang:
            result = model.transcribe(filepath, language=args.lang)
        else:
            result = model.transcribe(filepath)
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        print("💡 If this mentions ffmpeg, please install ffmpeg on your system and ensure it's in PATH.")
        sys.exit(4)

    print("✅ Transcription complete.\n")
    text = result.get('text', '')
    print("--- Transcribed text ---\n")
    print(text)
    print("------------------------\n")

    if args.srt and 'segments' in result and result['segments']:
        srt_text = segments_to_srt(result['segments'])
        try:
            with open(args.srt, 'w', encoding='utf-8') as fh:
                fh.write(srt_text)
            print(f"� Saved SRT to: {args.srt}")
        except Exception as e:
            print(f"❌ Failed to write SRT file: {e}")

if __name__ == '__main__':
    main()