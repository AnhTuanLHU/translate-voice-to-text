import whisper
import os

print("🔄 Đang tải model Whisper tiny...")
model = whisper.load_model("tiny")
print("✅ Model đã tải xong!")

# Tạo file audio test đơn giản
print("🎤 Tìm file audio trong thư mục...")
audio_files = ["C:\Users\Tuan\Documents\Sound Recordings\test.m4a"]
for file in os.listdir("."):
    if file.lower().endswith(('.wav', '.mp3')):
        audio_files.append(file)

if audio_files:
    print(f"📁 Tìm thấy {len(audio_files)} file audio:")
    for i, file in enumerate(audio_files):
        print(f"   {i+1}. {file}")
    
    # Test với file đầu tiên
    test_file = audio_files[0]
    print(f"\n🎤 Đang test với file: {test_file}")
    
    try:
        result = model.transcribe(test_file, language="vi")
        print("✅ Hoàn thành!")
        print(f"\n📝 Kết quả: {result['text']}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
else:
    print("❌ Không tìm thấy file audio (.wav, .mp3) trong thư mục!")
    print("💡 Hãy copy file audio vào thư mục này")

