"""Real-time Speech-to-Text Module"""
from .audio_capture import AudioRecorder
from .realtime_stt import RealTimeTranscriber, TranscriptionSegment
__all__ = ['AudioRecorder', 'RealTimeTranscriber', 'TranscriptionSegment']
