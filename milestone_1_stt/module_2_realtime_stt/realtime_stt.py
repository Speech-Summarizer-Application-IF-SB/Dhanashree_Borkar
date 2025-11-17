"""
Real-Time Speech-to-Text Transcriber
Supports both Whisper and Vosk for redundancy
"""

import whisper
import numpy as np
import json
import queue
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    from vosk import Model, KaldiRecognizer
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️ Vosk not available, using Whisper only")

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed text"""
    text: str
    timestamp: float
    duration: float
    confidence: float = 1.0
    is_final: bool = True

class RealTimeTranscriber:
    """
    Real-time speech-to-text engine with multiple model support
    """
    
    def __init__(
        self,
        model_type: str = "whisper",  # "whisper" or "vosk"
        model_size: str = "base",     # for whisper: tiny, base, small, medium
        language: str = "en",
        sample_rate: int = 16000
    ):
        self.model_type = model_type
        self.language = language
        self.sample_rate = sample_rate
        
        # Transcript storage
        self.full_transcript = []
        self.current_sentence = ""
        
        # Audio buffer for Whisper (needs chunks of audio)
        self.audio_buffer = []
        self.buffer_duration = 5.0  # Process 5 seconds at a time for Whisper
        
        # Callback for UI updates
        self.transcript_callback = None
        
        # Processing flags
        self.is_processing = False
        self.processing_thread = None
        self.audio_queue = queue.Queue()
        
        # Initialize the model
        self._initialize_model(model_size)
        
        print(f"✅ Transcriber initialized with {model_type} ({model_size if model_type=='whisper' else 'default'})")
    
    def _initialize_model(self, model_size: str):
        """Initialize STT model based on type"""
        if self.model_type == "whisper":
            print(f"🔄 Loading Whisper model ({model_size})...")
            self.model = whisper.load_model(model_size)
            print("✅ Whisper model loaded")
            
        elif self.model_type == "vosk" and VOSK_AVAILABLE:
            model_path = Path("models/vosk-model-small-en-us-0.15")
            if not model_path.exists():
                raise FileNotFoundError(f"Vosk model not found at {model_path}")
            
            print(f"🔄 Loading Vosk model from {model_path}...")
            self.model = Model(str(model_path))
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            self.recognizer.SetWords(True)
            print("✅ Vosk model loaded")
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def process_audio_chunk(self, audio_chunk: np.ndarray) -> Optional[str]:
        """Process a single audio chunk and return transcription"""
        
        if self.model_type == "whisper":
            # Whisper needs accumulated audio (not single chunks)
            self.audio_buffer.append(audio_chunk)
            
            # Check if we have enough audio to process
            buffer_size = len(self.audio_buffer) * len(audio_chunk) / self.sample_rate
            
            if buffer_size >= self.buffer_duration:
                # Combine buffered audio
                combined_audio = np.concatenate(self.audio_buffer)
                
                # Clear buffer but keep last second for context
                keep_samples = int(self.sample_rate * 1.0)  # Keep 1 second
                if len(combined_audio) > keep_samples:
                    self.audio_buffer = [combined_audio[-keep_samples:]]
                else:
                    self.audio_buffer = []
                
                # Transcribe with Whisper
                try:
                    result = self.model.transcribe(
                        combined_audio,
                        language=self.language,
                        fp16=False,
                        verbose=False
                    )
                    
                    text = result["text"].strip()
                    if text:
                        return text
                except Exception as e:
                    print(f"❌ Whisper error: {e}")
                    
        elif self.model_type == "vosk" and VOSK_AVAILABLE:
            # Vosk processes chunks directly
            # Convert float32 to int16 for Vosk
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            
            if self.recognizer.AcceptWaveform(audio_int16.tobytes()):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    return text
            else:
                # Partial result
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text and len(partial_text) > len(self.current_sentence):
                    self.current_sentence = partial_text
                    return f"[PARTIAL] {partial_text}"
        
        return None
    
    def start_realtime_transcription(self, callback: Optional[Callable] = None):
        """Start real-time transcription with callback for UI updates"""
        if self.is_processing:
            print("⚠️ Already processing!")
            return
        
        self.is_processing = True
        self.transcript_callback = callback
        self.full_transcript = []
        self.audio_buffer = []
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_audio_stream,
            daemon=True
        )
        self.processing_thread.start()
        
        print("🎙️ Real-time transcription started")
    
    def _process_audio_stream(self):
        """Process audio stream in background thread"""
        while self.is_processing:
            try:
                # Get audio from queue
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Process the chunk
                transcription = self.process_audio_chunk(audio_chunk)
                
                if transcription:
                    # Handle partial vs final transcriptions
                    if "[PARTIAL]" in transcription:
                        # Update partial transcription
                        text = transcription.replace("[PARTIAL]", "").strip()
                        segment = TranscriptionSegment(
                            text=text,
                            timestamp=time.time(),
                            duration=0,
                            is_final=False
                        )
                    else:
                        # Final transcription
                        segment = TranscriptionSegment(
                            text=transcription,
                            timestamp=time.time(),
                            duration=len(audio_chunk) / self.sample_rate,
                            is_final=True
                        )
                        
                        # Add to full transcript
                        self.full_transcript.append(segment)
                        self.current_sentence = ""
                    
                    # Send to callback if provided
                    if self.transcript_callback:
                        self.transcript_callback(segment)
                        
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Processing error: {e}")
    
    def add_audio(self, audio_chunk: np.ndarray):
        """Add audio chunk to processing queue"""
        if self.is_processing:
            self.audio_queue.put(audio_chunk)
    
    def stop_transcription(self) -> List[TranscriptionSegment]:
        """Stop transcription and return full transcript"""
        print("⏹️ Stopping transcription...")
        self.is_processing = False
        
        if self.processing_thread:
            self.processing_thread.join(timeout=2.0)
        
        # Process any remaining audio in buffer
        if self.model_type == "whisper" and self.audio_buffer:
            combined_audio = np.concatenate(self.audio_buffer)
            try:
                result = self.model.transcribe(
                    combined_audio,
                    language=self.language,
                    fp16=False,
                    verbose=False
                )
                
                text = result["text"].strip()
                if text:
                    segment = TranscriptionSegment(
                        text=text,
                        timestamp=time.time(),
                        duration=len(combined_audio) / self.sample_rate
                    )
                    self.full_transcript.append(segment)
            except Exception as e:
                print(f"❌ Final transcription error: {e}")
        
        print(f"✅ Transcription complete: {len(self.full_transcript)} segments")
        return self.full_transcript
    
    def get_full_text(self) -> str:
        """Get complete transcript as text"""
        return " ".join([seg.text for seg in self.full_transcript if seg.is_final])
    
    def get_formatted_transcript(self) -> str:
        """Get formatted transcript with timestamps"""
        formatted = []
        for seg in self.full_transcript:
            if seg.is_final:
                timestamp = datetime.fromtimestamp(seg.timestamp).strftime("%H:%M:%S")
                formatted.append(f"[{timestamp}] {seg.text}")
        
        return "\n".join(formatted)
    
    def calculate_wer(self, reference_text: str) -> float:
        """Calculate Word Error Rate for evaluation"""
        try:
            from jiwer import wer
            hypothesis = self.get_full_text()
            if hypothesis and reference_text:
                error_rate = wer(reference_text, hypothesis)
                return error_rate
        except ImportError:
            print("⚠️ jiwer not installed, cannot calculate WER")
        return -1.0


def test_live_transcription():
    """Test real-time transcription with audio recording"""
    import sys
    sys.path.append('src')
    from audio.audio_capture import AudioRecorder
    
    print("🎯 Testing Real-Time Speech-to-Text")
    print("=" * 50)
    
    # Create transcriber and recorder
    transcriber = RealTimeTranscriber(
        model_type="whisper",
        model_size="base",
        language="en"
    )
    
    recorder = AudioRecorder(sample_rate=16000)
    
    # Transcript display
    transcript_lines = []
    
    def transcription_callback(segment: TranscriptionSegment):
        """Callback to display transcriptions"""
        if segment.is_final:
            transcript_lines.append(segment.text)
            print(f"\n📝 Transcribed: {segment.text}")
        else:
            # Show partial transcription
            sys.stdout.write(f"\r💭 Speaking: {segment.text}...")
            sys.stdout.flush()
    
    def audio_chunk_callback(chunk, sample_rate):
        """Callback to process audio chunks"""
        # Send to transcriber
        transcriber.add_audio(chunk.flatten())
        
        # Show volume level
        rms = np.sqrt(np.mean(chunk**2))
        bars = int(rms * 500)
        bars = min(bars, 30)
        sys.stdout.write(f"\r🎤 [{'█' * bars}{'░' * (30-bars)}]")
        sys.stdout.flush()
    
    try:
        # Start transcription
        transcriber.start_realtime_transcription(callback=transcription_callback)
        
        # Start recording with callback
        print("\n🎙️ Recording for 20 seconds... Speak clearly!")
        print("💡 Try saying: 'Hello, this is a test of the meeting summarizer.'")
        print("-" * 50)
        
        recorder.start_recording(chunk_callback=audio_chunk_callback)
        
        # Record for 20 seconds
        time.sleep(20)
        
        # Stop everything
        audio_file = recorder.stop_recording()
        full_transcript = transcriber.stop_transcription()
        
        # Show results
        print("\n" + "=" * 50)
        print("📊 TRANSCRIPTION RESULTS")
        print("=" * 50)
        print(f"Audio saved: {audio_file}")
        print(f"Total segments: {len(full_transcript)}")
        print("\n📝 Full Transcript:")
        print("-" * 50)
        print(transcriber.get_full_text())
        print("-" * 50)
        print("\n📑 Formatted Transcript:")
        print(transcriber.get_formatted_transcript())
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        recorder.stop_recording()
        transcriber.stop_transcription()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_live_transcription()