#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit GUI cho Vietnamese STT
"""

import streamlit as st
import tempfile
import tempfile
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import os
# Ensure test_whisper.py is in the same directory or provide the correct import path
try:
    from test_whisper import VietnameseSTT
except ImportError:
    st.error("Không tìm thấy module 'test_whisper'. Hãy chắc chắn rằng file 'test_whisper.py' nằm cùng thư mục với ứng dụng này hoặc cài đặt đúng package.")
    st.stop()
import time
import json
import subprocess

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

# Chọn chế độ dịch
mode_option = st.sidebar.radio(
    "Chọn chế độ dịch:",
    ["Dịch qua file", "Dịch trực tiếp (Thu âm)", "Upload Video"]
)

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
    return VietnameseSTT(model_size=size)




# Load model
with st.spinner(f" Đang tải model {model_size}..."):
    stt = load_model(model_size)

st.sidebar.success(f" Model {model_size} đã sẵn sàng!")

# Không dùng file-server: giữ flow đơn giản, ít lỗi nhất (hiển thị video với st.video và cung cấp download SRT/VTT)


def clear_uploaded_assets():
    """Clear uploaded video/subtitle assets from session state."""
    removed = []
    for key in ('video_bytes', 'srt_content', 'vtt_content', 'video_url'):
        if key in st.session_state:
            st.session_state.pop(key, None)
            removed.append(key)
    return removed


def burn_in_subtitles(video_bytes: bytes, srt_text: str) -> bytes:
    """Write video and srt to temp files, run ffmpeg to burn subtitles, return burned video bytes.

    Raises RuntimeError with stderr if ffmpeg fails or is not found.
    """
    if not video_bytes:
        raise RuntimeError("No video bytes provided")
    if not srt_text:
        raise RuntimeError("No SRT content provided")

    in_vid = None
    in_srt = None
    out_vid = None
    try:
        # Write files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as fvid:
            fvid.write(video_bytes)
            in_vid = fvid.name
        with tempfile.NamedTemporaryFile(delete=False, suffix='.srt', mode='w', encoding='utf-8') as fsrt:
            fsrt.write(srt_text)
            in_srt = fsrt.name

        # Output path
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as fout:
            out_vid = fout.name

        # Run ffmpeg to burn subtitles. Uses subtitles filter which supports SRT.
        cmd = [
            'ffmpeg', '-y', '-i', in_vid,
            '-vf', f"subtitles={in_srt}",
            '-c:a', 'copy', out_vid
        ]

        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            stderr = proc.stderr.decode('utf-8', errors='ignore')
            raise RuntimeError(f"ffmpeg failed: {stderr}")

        # Read output bytes
        with open(out_vid, 'rb') as fh:
            data = fh.read()
        return data
    finally:
        for p in (in_vid, in_srt, out_vid):
            try:
                if p and os.path.exists(p):
                    os.unlink(p)
            except Exception:
                pass

# Main content

col1, col2 = st.columns([1, 1])

with col1:
    if mode_option == "Dịch qua file":
        st.header(" Upload File")
        # Upload file
        uploaded_file = st.file_uploader(
            "Chọn file âm thanh:",
            type=['wav', 'mp3', 'm4a', 'flac'],
            help="Hỗ trợ: WAV, MP3, M4A, FLAC, MP4"
        )
        if uploaded_file:
            # If uploaded file is a video, show video player; else show audio player
            filename = uploaded_file.name.lower()
            is_video = any(filename.endswith(ext) for ext in ('.mp4', '.webm', '.ogg', '.mov', '.m4v', '.mkv'))
            if is_video:
                st.video(uploaded_file)
            else:
                st.audio(uploaded_file, format='audio/wav')

            if st.button("Chuyển đổi thành văn bản", type="primary"):
                with st.spinner("Đang xử lý..."):
                    try:
                        # Lưu file tạm
                        # For audio uploads, save as .wav; for video, save original bytes so model can extract audio
                        if is_video:
                            suffix = "." + filename.split('.')[-1]
                        else:
                            suffix = ".wav"
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                            tmp_file.write(uploaded_file.getvalue())
                            tmp_file_path = tmp_file.name

                        # Xác định ngôn ngữ đầu ra
                        if language_option == "Tiếng Việt":
                            lang = "vi"
                        else:
                            lang = "en"

                        # Transcribe
                        start_time = time.time()
                        result = stt.transcribe_file(tmp_file_path, language=lang)
                        process_time = time.time() - start_time

                        # Xóa file tạm
                        try:
                            os.unlink(tmp_file_path)
                        except Exception:
                            pass

                        # Lưu kết quả vào session state
                        st.session_state['transcription_result'] = result
                        st.session_state['process_time'] = process_time
                        st.session_state['selected_language'] = language_option

                        # If this was a video and we have segments, generate SRT and VTT and save video bytes
                        if is_video and 'segments' in result and result['segments']:
                            def seconds_to_srt_time(s):
                                ms = int((s - int(s)) * 1000)
                                h = int(s // 3600)
                                m = int((s % 3600) // 60)
                                sec = int(s % 60)
                                return f"{h:02}:{m:02}:{sec:02},{ms:03}"

                            srt_lines = []
                            for i, seg in enumerate(result['segments'], start=1):
                                start = seconds_to_srt_time(seg['start'])
                                end = seconds_to_srt_time(seg['end'])
                                text = seg.get('text', '').replace('\n', ' ').strip()
                                srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
                            srt_content = "\n".join(srt_lines)
                            # Convert SRT -> VTT (WEBVTT)
                            vtt_content = "WEBVTT\n\n" + srt_content.replace(',', '.')
                            st.session_state['srt_content'] = srt_content
                            st.session_state['vtt_content'] = vtt_content
                            # Save video bytes to session for embedding
                            st.session_state['video_bytes'] = uploaded_file.getvalue()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")
    elif mode_option == "Upload Video":
        st.header(" Upload Video")
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
                        # save temp video file
                        suffix = "." + filename.split('.')[-1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_vid:
                            tmp_vid.write(uploaded_video.getvalue())
                            tmp_vid_path = tmp_vid.name

                        if language_option == "Tiếng Việt":
                            lang = "vi"
                        else:
                            lang = "en"

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

                        # If segments exist, create SRT/VTT and save bytes
                        if 'segments' in result and result['segments']:
                            def seconds_to_srt_time(s):
                                ms = int((s - int(s)) * 1000)
                                h = int(s // 3600)
                                m = int((s % 3600) // 60)
                                sec = int(s % 60)
                                return f"{h:02}:{m:02}:{sec:02},{ms:03}"

                            srt_lines = []
                            for i, seg in enumerate(result['segments'], start=1):
                                start = seconds_to_srt_time(seg['start'])
                                end = seconds_to_srt_time(seg['end'])
                                text = seg.get('text', '').replace('\n', ' ').strip()
                                srt_lines.append(f"{i}\n{start} --> {end}\n{text}\n")
                            srt_content = "\n".join(srt_lines)
                            vtt_content = "WEBVTT\n\n" + srt_content.replace(',', '.')
                            st.session_state['srt_content'] = srt_content
                            st.session_state['vtt_content'] = vtt_content
                            st.session_state['video_bytes'] = uploaded_video.getvalue()
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")

    else:
        st.header("🎤 Dịch trực tiếp (Thu âm)")
        st.info("Nhấn nút ghi âm bên dưới để bắt đầu thu giọng nói.")
        class AudioProcessor(AudioProcessorBase):
            def __init__(self):
                self.audio_frames = []
            def recv(self, frame):
                self.audio_frames.append(frame.to_ndarray())
                return frame

        ctx = webrtc_streamer(key="audio", audio_processor_factory=AudioProcessor, media_stream_constraints={"audio": True, "video": False})
        tmp_file_path = None
        # Chỉ xử lý khi trạng thái ghi âm đã dừng
        if ctx.state == "STOPPED" and ctx.audio_processor and ctx.audio_processor.audio_frames:
            import numpy as np
            import soundfile as sf
            audio_np = np.concatenate(ctx.audio_processor.audio_frames, axis=0)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                sf.write(tmp_file.name, audio_np, 16000)
                tmp_file_path = tmp_file.name
            st.audio(tmp_file_path, format='audio/wav')
            if st.button("Chuyển đổi thành văn bản", type="primary"):
                with st.spinner("Đang xử lý..."):
                    try:
                        if language_option == "Tiếng Việt":
                            lang = "vi"
                        else:
                            lang = "en"
                        start_time = time.time()
                        result = stt.transcribe_file(tmp_file_path, language=lang)
                        process_time = time.time() - start_time
                        os.unlink(tmp_file_path)
                        st.session_state['transcription_result'] = result
                        st.session_state['process_time'] = process_time
                        st.session_state['selected_language'] = language_option
                    except Exception as e:
                        st.error(f"❌ Lỗi: {str(e)}")

with col2:
    st.header("📝 Kết quả")
    
    if 'transcription_result' in st.session_state:
        result = st.session_state['transcription_result']
        process_time = st.session_state['process_time']
        selected_language = st.session_state.get('selected_language', 'Tiếng Việt')
        
        # Hiển thị thông tin
        st.info(f"⏱️ Thời gian xử lý: {process_time:.2f}s")
        st.info(f"🌏 Ngôn ngữ: {selected_language}")
        
        # Hiển thị văn bản
        st.subheader(f"Văn bản ({selected_language}):")
        st.text_area(
            "Kết quả chuyển đổi:",
            value=result['text'],
            height=200,
            help="Văn bản đã được chuyển đổi từ giọng nói"
        )
        st.markdown("**Để copy văn bản, hãy chọn toàn bộ và nhấn Ctrl+C (hoặc Command+C trên Mac).**")
        
        # Download button
        st.download_button(
            label="💾 Tải xuống file text",
            data=result['text'],
            file_name="transcription.txt",
            mime="text/plain"
        )
        
        # Hiển thị segments nếu có
        if 'segments' in result and result['segments']:
            st.subheader("⏰ Timestamps:")
            
            for i, segment in enumerate(result['segments'][:5]):  # Hiển thị 5 segment đầu
                st.write(f"**{segment['start']:.1f}s - {segment['end']:.1f}s:** {segment['text']}")

            # Nếu có video bytes và vtt, nhúng video kèm phụ đề (hiển thị một lần duy nhất)
            if st.session_state.get('video_bytes') and st.session_state.get('vtt_content'):
                st.subheader("Video (hiển thị trực tiếp)")
                # Display video using st.video (safer and simpler)
                st.video(st.session_state['video_bytes'])

                st.markdown("**Lưu ý:** Nếu trình duyệt không hiển thị phụ đề tự động, hãy tải VTT/SRT bằng các nút bên dưới và dùng trình phát ngoài (VLC, mpv) để kiểm tra phụ đề.")

                # Download buttons for SRT and VTT
                st.download_button("Tải VTT", data=st.session_state['vtt_content'], file_name="subtitles.vtt", mime="text/vtt")
                st.download_button("Tải SRT", data=st.session_state['srt_content'], file_name="subtitles.srt", mime="text/plain")
                # Clear uploaded assets
                if st.button("Xóa tệp"):
                    removed = clear_uploaded_assets()
                    if removed:
                        st.success(f"Đã xóa: {', '.join(removed)}")
                    else:
                        st.info("Không có tệp nào để xóa.")
                # Add burned-in subtitles button
                if st.button("Thêm phụ đề vào video"):
                    # Run ffmpeg burn-in
                    try:
                        if 'video_bytes' not in st.session_state or 'srt_content' not in st.session_state:
                            st.error("Không tìm thấy video hoặc phụ đề (SRT). Hãy chuyển đổi trước để tạo SRT và upload video.)")
                        else:
                            with st.spinner("Đang tạo video có phụ đề (ffmpeg)..."):
                                try:
                                    burned = burn_in_subtitles(st.session_state['video_bytes'], st.session_state['srt_content'])
                                    st.session_state['burned_video_bytes'] = burned
                                    st.success("Hoàn thành: video đã được chèn phụ đề.")
                                except RuntimeError as re:
                                    st.error(f"Lỗi khi chạy ffmpeg: {str(re)}")
                    except Exception as e:
                        st.error(f"Lỗi: {str(e)}")

                # If burned video exists, show and allow download
                if st.session_state.get('burned_video_bytes'):
                    st.subheader("Video với phụ đề (đã ghim)")
                    st.video(st.session_state['burned_video_bytes'])
                    st.download_button("Tải video đã ghim phụ đề", data=st.session_state['burned_video_bytes'], file_name="video_with_subs.mp4", mime='video/mp4')
    
    else:
        st.info("Hãy upload file âm thanh và nhấn 'Chuyển đổi'")

# Footer
st.markdown("---")
st.markdown("**Tips:** Sử dụng file âm thanh chất lượng tốt để có kết quả chính xác nhất")

# Model info
with st.expander("ℹ️ Thông tin model"):
    info = stt.get_model_info()
    st.json(info)