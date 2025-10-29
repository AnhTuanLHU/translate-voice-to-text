#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session-related helpers for Streamlit app.
"""

from __future__ import annotations

from typing import List
import streamlit as st


def clear_uploaded_assets() -> List[str]:
    removed: List[str] = []
    for key in ("video_bytes", "srt_content", "vtt_content", "video_url", "burned_video_bytes"):
        if key in st.session_state:
            st.session_state.pop(key, None)
            removed.append(key)
    return removed


