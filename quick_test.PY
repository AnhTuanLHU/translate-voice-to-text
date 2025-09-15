        # Hiển thị kết quả
import whisper
import os

# Tải model Whisper với size "tiny" (tránh lỗi PyTorch)
print("🔄 Đang tải model Whisper tiny...")
model = whisper.load_model("base")
print("✅ Model đã tải xong!")

# Chuyển đổi file audio thành văn bản
print("🎤 Đang xử lý file audio...")
audio_file = r"C:\Users\Tuan\Documents\Sound Recordings\test.m4a"
print(f"📁 File audio: {audio_file}")

# Kiểm tra file có tồn tại không
if os.path.exists(audio_file):
    print("✅ File tồn tại!")
    try:
        result = model.transcribe(audio_file, language="vi")
        print("✅ Hoàn thành!")
        
        # Hiển thị kết quả
        print("\n📝 Kết quả chuyển đổi:")
        print(result["text"])
    except Exception as e:
        print(f"❌ Lỗi xử lý: {e}")
        print("💡 Có thể cần cài đặt FFmpeg hoặc chuyển đổi file sang định dạng khác")
else:
    print("❌ File không tồn tại!")
    print("💡 Hãy kiểm tra đường dẫn file audio")