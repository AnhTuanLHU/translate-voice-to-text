#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vietnamese Speech-to-Text System using Whisper
Hệ thống chuyển đổi giọng nói tiếng Việt thành văn bản
"""

import whisper
import os
import time
import logging
from typing import Optional, Dict, List, Union
from pathlib import Path

class VietnameseSTT:
    """Class chính để xử lý Speech-to-Text tiếng Việt"""
    
    def __init__(self, model_size: str = "base", device: str = "auto"):
        """
        Khởi tạo Vietnamese STT
        
        Args:
            model_size: Kích thước model ("tiny", "base", "small", "medium", "large")
            device: Thiết bị sử dụng ("auto", "cpu", "cuda")
        """
        self.model_size = model_size
        self.device = device
        self.model = None
        self.logger = self._setup_logger()
        
        # Tải model
        self._load_model()
    
    def _setup_logger(self):
        """Thiết lập logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _load_model(self):
        """Tải Whisper model"""
        try:
            self.logger.info(f"🔄 Đang tải model Whisper {self.model_size}...")
            start_time = time.time()
            
            # Sửa lỗi PyTorch compatibility
            import torch
            torch.backends.cudnn.enabled = False
            
            self.model = whisper.load_model(
                self.model_size, 
                device="cpu"  # Force CPU để tránh lỗi
            )
            
            load_time = time.time() - start_time
            self.logger.info(f"✅ Model đã tải thành công ({load_time:.2f}s)")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi tải model: {e}")
            raise
    
    def transcribe_file(self, 
                       audio_path: Union[str, Path], 
                       language: str = "vi",
                       task: str = "transcribe",
                       **kwargs) -> Dict:
        """
        Chuyển đổi file âm thanh thành văn bản
        
        Args:
            audio_path: Đường dẫn file âm thanh
            language: Ngôn ngữ (mặc định "vi" cho tiếng Việt)
            task: Loại task ("transcribe" hoặc "translate")
            **kwargs: Các tham số khác cho Whisper
            
        Returns:
            Dict chứa kết quả transcribe
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Không tìm thấy file: {audio_path}")
        
        self.logger.info(f"🎤 Đang xử lý file: {audio_path}")
        
        try:
            start_time = time.time()
            
            # Transcribe với Whisper
            result = self.model.transcribe(
                str(audio_path),
                language=language,
                task=task,
                **kwargs
            )
            
            process_time = time.time() - start_time
            
            # Thêm thông tin metadata
            result['processing_time'] = process_time
            result['model_size'] = self.model_size
            result['audio_file'] = str(audio_path)
            
            self.logger.info(f"✅ Hoàn thành ({process_time:.2f}s)")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi transcribe: {e}")
            raise
    
    def transcribe_text_only(self, audio_path: Union[str, Path]) -> str:
        """
        Chuyển đổi file âm thanh và chỉ trả về văn bản
        
        Args:
            audio_path: Đường dẫn file âm thanh
            
        Returns:
            Văn bản tiếng Việt
        """
        result = self.transcribe_file(audio_path)
        return result['text'].strip()
    
    def transcribe_with_timestamps(self, audio_path: Union[str, Path]) -> List[Dict]:
        """
        Chuyển đổi với thông tin timestamp cho từng đoạn
        
        Args:
            audio_path: Đường dẫn file âm thanh
            
        Returns:
            List các dict chứa text và timestamp
        """
        result = self.transcribe_file(audio_path)
        
        segments = []
        for segment in result.get('segments', []):
            segments.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'].strip(),
                'confidence': segment.get('no_speech_prob', 0)
            })
        
        return segments
    
    def batch_transcribe(self, 
                        audio_files: List[Union[str, Path]], 
                        output_dir: Optional[str] = None) -> List[Dict]:
        """
        Xử lý nhiều file âm thanh cùng lúc
        
        Args:
            audio_files: List đường dẫn các file âm thanh
            output_dir: Thư mục lưu kết quả (tùy chọn)
            
        Returns:
            List kết quả transcribe
        """
        results = []
        
        self.logger.info(f"🔄 Bắt đầu xử lý {len(audio_files)} file...")
        
        for i, audio_file in enumerate(audio_files, 1):
            self.logger.info(f"📁 Xử lý file {i}/{len(audio_files)}: {audio_file}")
            
            try:
                result = self.transcribe_file(audio_file)
                results.append(result)
                
                # Lưu kết quả nếu có output_dir
                if output_dir:
                    self._save_result(result, output_dir)
                    
            except Exception as e:
                self.logger.error(f"❌ Lỗi xử lý {audio_file}: {e}")
                results.append({
                    'audio_file': str(audio_file),
                    'error': str(e),
                    'text': ''
                })
        
        self.logger.info(f"✅ Hoàn thành xử lý {len(results)} file")
        return results
    
    def _save_result(self, result: Dict, output_dir: str):
        """Lưu kết quả ra file"""
        os.makedirs(output_dir, exist_ok=True)
        
        audio_file = Path(result['audio_file'])
        output_file = Path(output_dir) / f"{audio_file.stem}_transcript.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"File: {result['audio_file']}\n")
            f.write(f"Thời gian xử lý: {result['processing_time']:.2f}s\n")
            f.write(f"Model: {result['model_size']}\n")
            f.write(f"Ngôn ngữ: {result['language']}\n")
            f.write("-" * 50 + "\n")
            f.write(result['text'])
        
        self.logger.info(f"💾 Đã lưu kết quả: {output_file}")
    
    def get_model_info(self) -> Dict:
        """Lấy thông tin model"""
        return {
            'model_size': self.model_size,
            'device': self.device,
            'model_loaded': self.model is not None,
            'supported_languages': whisper.tokenizer.LANGUAGES
        }

# Hàm tiện ích
def create_stt(model_size: str = "base") -> VietnameseSTT:
    """
    Tạo instance VietnameseSTT nhanh
    
    Args:
        model_size: Kích thước model
        
    Returns:
        VietnameseSTT instance
    """
    return VietnameseSTT(model_size=model_size)

# Test function
def test_vietnamese_stt():
    """Test Vietnamese STT system"""
    print("🎯 Test Vietnamese STT System")
    print("=" * 40)
    
    # Tạo STT instance
    stt = create_stt("base")
    
    # Hiển thị thông tin model
    info = stt.get_model_info()
    print(f"📊 Model info: {info}")
    
    # Test với file audio (thay đổi đường dẫn)
    test_file = r"C:\Users\Tuan\Documents\Sound Recordings\test.m4a"
    
    if os.path.exists(test_file):
        print(f"\n🎤 Test với file: {test_file}")
        
        try:
            # Transcribe
            text = stt.transcribe_text_only(test_file)
            print(f"📝 Kết quả: {text}")
            
            # Transcribe với timestamp
            segments = stt.transcribe_with_timestamps(test_file)
            print(f"\n⏰ Segments ({len(segments)}):")
            for seg in segments[:3]:  # Hiển thị 3 segment đầu
                print(f"   {seg['start']:.1f}s - {seg['end']:.1f}s: {seg['text']}")
                
        except Exception as e:
            print(f"❌ Lỗi test: {e}")
    else:
        print(f"❌ Không tìm thấy file test: {test_file}")

if __name__ == "__main__":
    test_vietnamese_stt()