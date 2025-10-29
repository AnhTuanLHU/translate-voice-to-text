#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recording service for WebRTC audio capture in Streamlit.

Provides:
- get_rtc_configuration(): STUN servers
- get_media_stream_constraints(): audio constraints with echo cancellation
- BufferingAudioProcessor: collects frames without loopback
- drain_audio_receiver(ctx): retrieve frames & sample rate from receiver
- save_frames_to_wav_bytes(arrays, sample_rate): to WAV bytes
"""

from __future__ import annotations

from typing import List, Tuple


def get_rtc_configuration() -> dict:
    return {
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}],
    }


def get_media_stream_constraints() -> dict:
    return {
        "audio": {
            "echoCancellation": True,
            "noiseSuppression": True,
            "autoGainControl": True,
        },
        "video": False,
    }


class BufferingAudioProcessor:
    """Mixin-like processor collecting audio frames without loopback."""

    def __init__(self) -> None:
        self.audio_frames: List[object] = []

    def recv(self, frame):
        # frame: av.AudioFrame
        try:
            self.audio_frames.append(frame.to_ndarray())
        except Exception:
            pass
        return None


def drain_audio_receiver(ctx) -> Tuple[List[object], int]:
    """Pull all pending frames from audio_receiver.

    Returns (arrays, sample_rate). Defaults to 48000 if not found.
    """
    arrays: List[object] = []
    sample_rate = 48000
    try:
        while True:
            frames = list(ctx.audio_receiver.get_frames(timeout=0.2))
            if not frames:
                break
            for frame in frames:
                if hasattr(frame, "to_ndarray"):
                    arrays.append(frame.to_ndarray())
                if hasattr(frame, "sample_rate") and frame.sample_rate:
                    sample_rate = int(frame.sample_rate)
    except Exception:
        pass
    return arrays, sample_rate


def save_frames_to_wav_bytes(arrays: List[object], sample_rate: int) -> bytes:
    import numpy as np
    import soundfile as sf
    from io import BytesIO

    if not arrays:
        raise ValueError("No audio frames to save")
    audio_np = np.concatenate(arrays, axis=0)
    wav_buf = BytesIO()
    sf.write(wav_buf, audio_np, sample_rate or 48000, format="WAV")
    return wav_buf.getvalue()


