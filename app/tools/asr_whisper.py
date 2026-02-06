"""Whisper ASR 工具 - 使用 faster-whisper"""
from faster_whisper import WhisperModel
from pathlib import Path


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    device: str = "cpu",
    compute_type: str = "int8"
) -> dict:
    """
    使用 faster-whisper 转录音频
    
    Args:
        audio_path: 音频文件路径
        model_size: 模型大小 (tiny, base, small, medium, large-v2)
        device: 设备 (cpu, cuda)
        compute_type: 计算类型 (int8, float16, float32)
    """
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    
    segments, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        vad_filter=True
    )
    
    result_segments = []
    for segment in segments:
        result_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    
    return {
        "segments": result_segments,
        "language": info.language,
        "source": audio_path
    }
