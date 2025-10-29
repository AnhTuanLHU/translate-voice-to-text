#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Transcription service module that wraps VietnameseSTT model loading and inference.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _import_vietnamese_stt():
    """Import VietnameseSTT from test_whisper.py or test_whisper.PY for Windows case-insensitivity.

    Raises ImportError if not found.
    """
    try:
        from test_whisper import VietnameseSTT  # type: ignore
        return VietnameseSTT
    except Exception:
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_whisper", "test_whisper.PY")
        if spec is None or spec.loader is None:
            raise ImportError("Cannot find test_whisper module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[attr-defined]
        try:
            return getattr(module, "VietnameseSTT")
        except AttributeError as exc:
            raise ImportError("VietnameseSTT not found in test_whisper module") from exc


class TranscriptionService:
    """High-level service for STT operations."""

    def __init__(self, model_size: str = "base") -> None:
        VietnameseSTT = _import_vietnamese_stt()
        self._engine = VietnameseSTT(model_size=model_size)

    def transcribe_file(self, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        return self._engine.transcribe_file(file_path, language=language)

    def get_model_info(self) -> Dict[str, Any]:
        return self._engine.get_model_info()


