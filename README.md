## Hướng dẫn chạy

Git clone https://github.com/AnhTuanLHU/translate-voice-to-text

==========================================================================

Cài thư viện:
```powershell
python --version
pip install streamlit openai-whisper
winget install --id Gyan.FFmpeg -e --source winget
ffmpeg -version
```

Sau đó chạy file:
```powershell
streamlit run .\streamlit_app.PY
```
```

- Đã sửa typo `Python --versiom` thành `python --version`.
