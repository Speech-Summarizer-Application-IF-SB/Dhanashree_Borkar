"""
Audio Capture Module for AI Meeting Summarizer
Handles real-time audio recording with threading
"""

import sounddevice as sd
import numpy as np
import queue
import threading
import wave
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import sys

class AudioRecorder:
    """
    Real-time audio recorder with callback support for live transcription
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_duration: float = 1.0,  # Process audio in 1-second chunks
        device: Optional[int] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.device = device
        
        # Audio queue for threading
        self.audio_queue = queue.Queue()
        
        # Control flags
        self.is_recording = False
        self.recording_thread = None
        
        # Audio buffer for complete recording
        self.audio_buffer = []
        
        # Callbacks for real-time processing
        self.chunk_callback = None
        
        # Session info
        self.session_start = None
        self.output_dir = Path("outputs/recordings")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def list_devices(self):
        """List all available audio devices"""
        print("\n🎤 Available Audio Devices:")
        print("-" * 50)
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                marker = "📌" if i == sd.default.device[0] else "  "
                print(f"{marker} [{i}] {device['name']} (Channels: {device['max_input_channels']})")
        return devices
    
    def audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream - called for each audio chunk"""
        if status:
            print(f"⚠️ Audio callback status: {status}", file=sys.stderr)
        
        # Copy audio data to queue
        audio_chunk = indata.copy()
        self.audio_queue.put(audio_chunk)
    
    def process_audio_queue(self):
        """Process audio from queue in separate thread"""
        while self.is_recording:
            try:
                # Get audio chunk with timeout
                audio_chunk = self.audio_queue.get(timeout=0.1)
                
                # Store in buffer
                self.audio_buffer.append(audio_chunk)
                
                # Call chunk callback if provided (for real-time STT)
                if self.chunk_callback:
                    self.chunk_callback(audio_chunk, self.sample_rate)
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Error processing audio: {e}")
    
    def start_recording(self, chunk_callback: Optional[Callable] = None):
        """Start recording audio"""
        if self.is_recording:
            print("⚠️ Already recording!")
            return False
        
        print("🎙️ Starting recording...")
        self.is_recording = True
        self.audio_buffer = []
        self.chunk_callback = chunk_callback
        self.session_start = datetime.now()
        
        # Start processing thread
        self.recording_thread = threading.Thread(
            target=self.process_audio_queue,
            daemon=True
        )
        self.recording_thread.start()
        
        # Start audio stream
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=self.channels,
            samplerate=self.sample_rate,
            device=self.device,
            blocksize=int(self.sample_rate * self.chunk_duration)
        )
        self.stream.start()
        
        print(f"✅ Recording started at {self.sample_rate}Hz")
        return True
    
    def stop_recording(self) -> Optional[Path]:
        """Stop recording and save audio file"""
        if not self.is_recording:
            print("⚠️ Not currently recording!")
            return None
        
        print("⏹️ Stopping recording...")
        self.is_recording = False
        
        # Stop stream
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        # Wait for processing thread to finish
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        # Save audio to file
        if self.audio_buffer:
            return self.save_audio()
        else:
            print("⚠️ No audio data recorded")
            return None
    
    def save_audio(self) -> Path:
        """Save recorded audio to WAV file"""
        # Combine all audio chunks
        audio_data = np.concatenate(self.audio_buffer, axis=0)
        
        # Generate filename with timestamp
        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"meeting_{timestamp}.wav"
        
        # Convert float32 to int16 for WAV
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save as WAV file
        with wave.open(str(filename), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())
        
        duration = len(audio_data) / self.sample_rate
        print(f"✅ Audio saved: {filename}")
        print(f"📊 Duration: {duration:.1f} seconds")
        
        return filename
    
    def get_recording_status(self) -> dict:
        """Get current recording status"""
        if self.is_recording and self.session_start:
            duration = (datetime.now() - self.session_start).total_seconds()
        else:
            duration = 0
        
        return {
            "is_recording": self.is_recording,
            "duration": duration,
            "buffer_size": len(self.audio_buffer),
            "sample_rate": self.sample_rate
        }


def test_recording():
    """Test function to verify audio recording works"""
    print("🎯 Testing Audio Recording Module")
    print("=" * 50)
    
    # Create recorder
    recorder = AudioRecorder()
    
    # List available devices
    recorder.list_devices()
    
    # Enhanced chunk callback for testing with better visualization
    def test_callback(chunk, sample_rate):
        # Calculate RMS (volume level)
        rms = np.sqrt(np.mean(chunk**2))
        # Scale for better visibility (adjust multiplier as needed)
        bars = int(rms * 500)  # Increased sensitivity
        max_bars = 50
        bars = min(bars, max_bars)
        
        # Color-coded volume levels
        if bars < 10:
            level = "🔇 LOW "
        elif bars < 30:
            level = "🔊 GOOD"
        else:
            level = "📢 LOUD"
        
        # Create visual meter
        filled = '█' * bars
        empty = '░' * (max_bars - bars)
        
        # Clear line and show meter
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear line
        sys.stdout.write(f'🎤 {level} [{filled}{empty}] {bars*2}%')
        sys.stdout.flush()
    
    try:
        # Test recording for 5 seconds
        print("\n\n🎤 Recording for 5 seconds... Speak into your microphone!")
        recorder.start_recording(chunk_callback=test_callback)
        
        # Record for 5 seconds
        time.sleep(5)
        
        # Stop and save
        audio_file = recorder.stop_recording()
        
        if audio_file:
            print(f"\n✅ Test successful! Audio saved to: {audio_file}")
            print("\n💡 You can play this file to verify the recording quality")
        else:
            print("\n❌ Test failed - no audio recorded")
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Recording interrupted by user")
        recorder.stop_recording()
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        recorder.stop_recording()


if __name__ == "__main__":
    # Run test when module is executed directly
    test_recording()