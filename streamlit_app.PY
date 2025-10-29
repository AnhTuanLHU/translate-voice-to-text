#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit GUI cho Vietnamese STT
"""

import streamlit as st
import tempfile
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import tempfile
import os
import time
import json

# Services
from services.transcription_service import TranscriptionService
from services.subtitles_service import build_srt, build_vtt_from_srt, burn_in_subtitles
from services.session_utils import clear_uploaded_assets
from services.recording_service import (
    get_rtc_configuration,
    get_media_stream_constraints,
    BufferingAudioProcessor,
    drain_audio_receiver,
    save_frames_to_wav_bytes,
)

# Cấu hình trang
st.set_page_config(
    page_title="Vietnamese Speech-to-Text",
    page_icon="🎤",
    layout="wide"
)

# Tiêu đề
st.title("🎤 Vietnamese Speech-to-Text")
st.markdown("Chuyển đổi giọng nói tiếng Việt thành văn bản")

# Sidebar
st.sidebar.header("⚙️ Cài đặt")

# Chọn ngôn ngữ chuyển đổi
language_option = st.sidebar.selectbox(
    "Chọn ngôn ngữ chuyển đổi:",
    ["Tiếng Việt", "Tiếng Anh"],
    index=0,
    help="Chọn ngôn ngữ đầu ra cho văn bản"
)

# Chọn model size
model_size = st.sidebar.selectbox(
    "Chọn kích thước model:",
    ["tiny", "base", "small", "medium", "large"],
    index=1,
    help="Model lớn hơn = chính xác hơn nhưng chậm hơn"
)

# Khởi tạo model
@st.cache_resource
def load_model(size):
    """Cache model để tránh tải lại"""
    return TranscriptionService(model_size=size)

# Load model
with st.spinner(f" Đang tải model {model_size}..."):
    stt = load_model(model_size)

st.sidebar.success(f" Model {model_size} đã sẵn sàng!")

# Không dùng file-server: giữ flow đơn giản, ít lỗi nhất (hiển thị video với st.video và cung cấp download SRT/VTT)
 

# Main content

col1, col2 = st.columns([1, 1])

with col1:
    st.header("Nguồn dữ liệu")
    tab_file, tab_video, tab_record = st.tabs(["📁 Dịch qua file", "📹 Upload Video", "🎙️ Thu âm trực tiếp"])

    with tab_file:
        st.subheader("Upload File")
        uploaded_file = st.file_uploader(
            "Chọn file âm thanh:",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Hỗ trợ: WAV, MP3, M4A, FLAC, MP4"
        )
        if uploaded_file:
            filename = uploaded_file.name.lower()
            is_video = any(filename.endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.mov', '.m4v', '.mkv'))
            st.video(uploaded_file) if is_video else st.audio(uploaded_file, format='audio/wav')

            if st.button("Chuyển đổi thành văn bản", type="primary", key="btn_transcribe_file"):
                with st.spinner("Đang xử lý..."):
                    try:
                        suffix = "." + filename.split('.')[-1] if is_video else ".wav"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name

                        lang = "vi" if language_option == "Tiếng Việt" else "en"

                        start_time = time.time()
                        result = stt.transcribe_file(tmp_file_path, language=lang)
                        process_time = time.time() - start_time

                        try:
                            os.unlink(tmp_file_path)
                        except Exception:
                            pass

                        st.session_state['transcription_result'] = result
                        st.session_state['process_time'] = process_time
                        st.session_state['selected_language'] = language_option

                        if is_video and 'segments' in result and result['segments']:
                            srt_content = build_srt(result['segments'])
                            vtt_content = build_vtt_from_srt(srt_content)
                            st.session_state['srt_content'] = srt_content
                            st.session_state['vtt_content'] = vtt_content
                            st.session_state['video_bytes'] = uploaded_file.getvalue()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")


    with tab_video:
        st.subheader("Upload Video")
        uploaded_video = st.file_uploader(
            "Chọn file video:",
            type=['mp4', 'webm', 'mov', 'mkv', 'm4v'],
            help="Hỗ trợ: MP4, WEBM, MOV, MKV"
        )
        if uploaded_video:
            filename = uploaded_video.name.lower()
            st.video(uploaded_video)
            if st.button("Chuyển đổi thành văn bản (Video)", key='transcribe_video'):
                with st.spinner("Đang xử lý video..."):
                    try:
                        suffix = "." + filename.split('.')[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_vid:
                            tmp_vid.write(uploaded_video.getvalue())
                            tmp_vid_path = tmp_vid.name

                        lang = "vi" if language_option == "Tiếng Việt" else "en"

                        start_time = time.time()
                        result = stt.transcribe_file(tmp_vid_path, language=lang)
                        process_time = time.time() - start_time

                        try:
                            os.unlink(tmp_vid_path)
                        except Exception:
                            pass

                        st.session_state['transcription_result'] = result
                        st.session_state['process_time'] = process_time
                        st.session_state['selected_language'] = language_option

                        if 'segments' in result and result['segments']:
                            srt_content = build_srt(result['segments'])
                            vtt_content = build_vtt_from_srt(srt_content)
                            st.session_state['srt_content'] = srt_content
                            st.session_state['vtt_content'] = vtt_content
                            st.session_state['video_bytes'] = uploaded_video.getvalue()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")

    with tab_record:
        st.subheader("🎤 Ghi âm trực tiếp")
        st.info("Nhấn Start để ghi âm, Stop để kết thúc rồi bấm Chuyển đổi.")

        class AudioProcessor(AudioProcessorBase, BufferingAudioProcessor):
            def __init__(self):
                BufferingAudioProcessor.__init__(self)
            def recv(self, frame):
                return BufferingAudioProcessor.recv(self, frame)

        rtc_configuration = get_rtc_configuration()

        ctx = webrtc_streamer(
            key="inline_record_audio",
            audio_processor_factory=AudioProcessor,
            media_stream_constraints=get_media_stream_constraints(),
            rtc_configuration=rtc_configuration,
        )

        # Nút lưu thủ công: gom frame từ audio_receiver và lưu thành WAV bytes
        if ctx and ctx.audio_receiver and st.button("Lưu ghi âm", key="btn_save_record_inline"):
            try:
                arrays, sample_rate = drain_audio_receiver(ctx)
                if not arrays and ctx.audio_processor and ctx.audio_processor.audio_frames:
                    arrays = list(ctx.audio_processor.audio_frames)

                if arrays:
                    st.session_state['recorded_wav_bytes'] = save_frames_to_wav_bytes(arrays, sample_rate)
                    st.success("Đã lưu bản ghi âm")
                else:
                    st.warning("Chưa có dữ liệu âm thanh để lưu. Hãy bấm Start và nói trước khi lưu.")
            except Exception as e:
                st.error(f"❌ Lỗi khi lưu ghi âm: {e}")

        if ctx and ctx.state == "STOPPED" and ctx.audio_processor and ctx.audio_processor.audio_frames:
            import numpy as np
            # Ghi 48kHz để tránh méo tốc độ; dùng helper để thống nhất
            st.session_state['recorded_wav_bytes'] = save_frames_to_wav_bytes(
                list(ctx.audio_processor.audio_frames), 48000
            )
            st.audio(st.session_state['recorded_wav_bytes'], format='audio/wav')
            st.download_button(
                label="💾 Tải ghi âm (WAV)",
                data=st.session_state['recorded_wav_bytes'],
                file_name="recording.wav",
                mime="audio/wav",
                key="dl_recorded_wav_inline",
            )
            if st.button("Chuyển đổi thành văn bản", type="primary", key="btn_transcribe_inline_record"):
                with st.spinner("Đang xử lý..."):
                    try:
                        lang = "vi" if language_option == "Tiếng Việt" else "en"
                        start_time = time.time()
                        # Ghi tạm bytes ra file để phù hợp API
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_in:
                            tmp_in.write(st.session_state['recorded_wav_bytes'])
                            tmp_in_path = tmp_in.name
                        result = stt.transcribe_file(tmp_in_path, language=lang)
                        process_time = time.time() - start_time
                        try:
                            os.unlink(tmp_in_path)
                        except Exception:
                            pass
                        st.session_state['transcription_result'] = result
                        st.session_state['process_time'] = process_time
                        st.session_state['selected_language'] = language_option
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")

with col2:
    st.header("Kết quả")
    if 'transcription_result' in st.session_state:
        result = st.session_state['transcription_result']
        process_time = st.session_state['process_time']
        selected_language = st.session_state.get('selected_language', 'Tiếng Việt')

        st.caption(f"⏱️ {process_time:.2f}s • 🌏 {selected_language}")

        tab_text, tab_timestamps, tab_video_out = st.tabs(["📝 Văn bản", "⏰ Timestamps", "🎬 Video & Phụ đề"])

        with tab_text:
            st.text_area(
                "Kết quả chuyển đổi:",
                value=result['text'],
                height=240,
                help="Văn bản đã được chuyển đổi từ giọng nói"
            )
            st.download_button(
                label="💾 Tải xuống file text",
                data=result['text'],
                file_name="transcription.txt",
                mime="text/plain"
            )

        with tab_timestamps:
            if 'segments' in result and result['segments']:
                for i, segment in enumerate(result['segments'][:20]):
                    st.write(f"**{segment['start']:.1f}s - {segment['end']:.1f}s:** {segment['text']}")
            else:
                st.info("Không có timestamps khả dụng.")

        with tab_video_out:
            if st.session_state.get('video_bytes') and st.session_state.get('vtt_content'):
                # Hiển thị video đã burn phụ đề nếu có, nếu không thì hiển thị video gốc
                if st.session_state.get('burned_video_bytes'):
                    st.subheader("Video với phụ đề")
                    st.video(st.session_state['burned_video_bytes'])
                else:
                    st.subheader("Xem nhanh video")
                    st.video(st.session_state['video_bytes'])

                srt_lines = st.session_state['srt_content'].count('\n\n') + 1
                st.info(f"📊 **Thông tin phụ đề:** {srt_lines} đoạn phụ đề đã được tạo")

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        "📄 Tải VTT", 
                        data=st.session_state['vtt_content'], 
                        file_name="subtitles.vtt", 
                        mime="text/vtt",
                        help="Định dạng WebVTT cho trình duyệt"
                    )
                with col_dl2:
                    st.download_button(
                        "📄 Tải SRT", 
                        data=st.session_state['srt_content'], 
                        file_name="subtitles.srt", 
                        mime="text/plain",
                        help="Định dạng SRT cho VLC, Media Player"
                    )

                st.markdown("""
                **💡 Hướng dẫn:**
                - Trình duyệt: dùng VTT cùng tên với video để hiển thị phụ đề
                - VLC/Media Player: đặt SRT cùng thư mục, cùng tên file
                - YouTube: upload SRT khi tải video
                """)

                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    if st.button("Thêm phụ đề vào video", key="btn_burn_subs"):
                        try:
                            with st.spinner("🔄 Đang chèn phụ đề (ffmpeg)..."):
                                burned = burn_in_subtitles(st.session_state['video_bytes'], st.session_state['srt_content'])
                                st.session_state['burned_video_bytes'] = burned
                                st.success("✅ Video đã được chèn phụ đề.")
                        except RuntimeError as re:
                            error_msg = str(re)
                            if "ffmpeg not found" in error_msg:
                                st.error("❌ ffmpeg chưa được cài đặt!")
                            else:
                                st.error(f"❌ **Lỗi ffmpeg:** {error_msg}")
                                st.info("💡 Kiểm tra định dạng video và phụ đề.")
                with col_act2:
                    if st.button("Xóa tệp", key="btn_clear_assets"):
                        removed = clear_uploaded_assets()
                        st.success(f"Đã xóa: {', '.join(removed)}") if removed else st.info("Không có tệp để xóa.")

                # Nút tải video đã burn phụ đề nếu có
                if st.session_state.get('burned_video_bytes'):
                    st.download_button("💾 Tải video đã ghim phụ đề", data=st.session_state['burned_video_bytes'], file_name="video_with_subs.mp4", mime='video/mp4')
            else:
                st.info("Chưa có video hoặc phụ đề để hiển thị.")
    else:
        st.info("Hãy cung cấp dữ liệu ở cột trái để bắt đầu.")

# Footer
st.markdown("---")
st.markdown("**Tips:** Sử dụng file âm thanh chất lượng tốt để có kết quả chính xác nhất")

# Model info
with st.expander("ℹ️ Thông tin model"):
    info = stt.get_model_info()
    st.json(info)