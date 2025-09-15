#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit GUI cho Vietnamese STT
"""

import streamlit as st
import tempfile
import os
from test_whisper import VietnameseSTT
import time

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

# Main content
col1, col2 = st.columns([1, 1])

with col1:
    st.header(" Upload File")
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Chọn file âm thanh:",
        type=['wav', 'mp3', 'm4a', 'flac', 'mp4'],
        help="Hỗ trợ: WAV, MP3, M4A, FLAC, MP4"
    )
    
    if uploaded_file:
        st.audio(uploaded_file, format='audio/wav')
        
        # Transcribe button
        if st.button("�� Chuyển đổi thành văn bản", type="primary"):
            with st.spinner("Đang xử lý..."):
                try:
                    # Lưu file tạm
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Transcribe
                    start_time = time.time()
                    result = stt.transcribe_file(tmp_file_path)
                    process_time = time.time() - start_time
                    
                    # Xóa file tạm
                    os.unlink(tmp_file_path)
                    
                    # Lưu kết quả vào session state
                    st.session_state['transcription_result'] = result
                    st.session_state['process_time'] = process_time
                    
                except Exception as e:
                    st.error(f"❌ Lỗi: {str(e)}")

with col2:
    st.header("📝 Kết quả")
    
    if 'transcription_result' in st.session_state:
        result = st.session_state['transcription_result']
        process_time = st.session_state['process_time']
        
        # Hiển thị thông tin
        st.info(f"⏱️ Thời gian xử lý: {process_time:.2f}s")
        st.info(f"🌏 Ngôn ngữ: {result.get('language', 'vi')}")
        
        # Hiển thị văn bản
        st.subheader("Văn bản:")
        st.text_area(
            "Kết quả chuyển đổi:",
            value=result['text'],
            height=200,
            help="Văn bản đã được chuyển đổi từ giọng nói"
        )
        
        # Copy button
        if st.button("📋 Copy văn bản"):
            st.write("✅ Đã copy vào clipboard!")
        
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
    
    else:
        st.info("�� Hãy upload file âm thanh và nhấn 'Chuyển đổi'")

# Footer
st.markdown("---")
st.markdown("�� **Tips:** Sử dụng file âm thanh chất lượng tốt để có kết quả chính xác nhất")

# Model info
with st.expander("ℹ️ Thông tin model"):
    info = stt.get_model_info()
    st.json(info)