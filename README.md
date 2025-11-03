# 🎤 Vietnamese Speech-to-Text Application

Ứng dụng chuyển đổi giọng nói tiếng Việt thành văn bản sử dụng Whisper AI.

## 🚀 Cài đặt nhanh

### 1. Clone repository
```bash
git clone https://github.com/AnhTuanLHU/translate-voice-to-text
cd translate-voice-to-text
```

### 2. Cài đặt dependencies (Chọn 1 trong 2 cách)

#### **Cách A: Sử dụng npm (Khuyến nghị)**
```bash
# Cài đặt Node.js dependencies
npm install

```

#### **Cách B: Sử dụng pip truyền thống**
```bash
# Cài đặt FFmpeg (Windows)
winget install --id Gyan.FFmpeg -e --source winget

# Chạy ứng dụng
python -m streamlit run streamlit_app.py
```

### 3. Truy cập ứng dụng
- Mở trình duyệt tại: `http://localhost:8501`

## 📋 Yêu cầu hệ thống

- **Python**: 3.8+
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB+)
- **Storage**: ~2GB cho models Whisper
- **OS**: Windows, macOS, Linux

## 🎯 Tính năng

- ✅ **Upload file âm thanh**: WAV, MP3, M4A, FLAC
- ✅ **Upload video**: MP4, WEBM, MOV, MKV
- ✅ **Ghi âm trực tiếp**: Sử dụng microphone
- ✅ **Hỗ trợ đa ngôn ngữ**: Tiếng Việt, Tiếng Anh
- ✅ **Tạo phụ đề**: SRT, VTT format
- ✅ **Burn phụ đề**: Chèn phụ đề vào video
- ✅ **Timestamps**: Thời gian chính xác từng đoạn

## 🔧 Troubleshooting

### Lỗi "streamlit not found"
```bash
python -m streamlit run streamlit_app.py
```

### Lỗi FFmpeg
- Đảm bảo FFmpeg đã được cài đặt và có trong PATH
- Restart terminal sau khi cài đặt

### Model loading chậm
- Lần đầu sẽ tải model Whisper (~1-2GB)
- Chọn model nhỏ hơn (tiny, base) để tải nhanh hơn

## 📜 Available Scripts (npm)

```bash
npm start          # Chạy ứng dụng Streamlit
npm run dev        # Chạy với auto-reload
npm run setup      # Cài đặt Python deps + FFmpeg
npm run install-python-deps  # Chỉ cài Python dependencies
npm run install-ffmpeg       # Chỉ cài FFmpeg
npm run check-ffmpeg         # Kiểm tra FFmpeg
```
