"""
Speaker Diarization Module
Identifies different speakers in audio using pyannote
"""

import os
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings("ignore")

# Check if pyannote is available
try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.speaker_diarization import SpeakerDiarization
    PYANNOTE_AVAILABLE = True
except ImportError:
    PYANNOTE_AVAILABLE = False
    print("⚠️ Pyannote not available. Install with: pip install pyannote.audio")

@dataclass
class SpeakerSegment:
    """Represents a speaker segment"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str = ""
    confidence: float = 1.0
    
    @property
    def duration(self):
        return self.end_time - self.start_time

class SpeakerDiarizer:
    """
    Speaker diarization using pyannote or simple voice activity detection
    """
    
    def __init__(
        self,
        auth_token: Optional[str] = None,
        min_speaker_duration: float = 0.5,
        use_pyannote: bool = True
    ):
        self.min_speaker_duration = min_speaker_duration
        self.use_pyannote = use_pyannote and PYANNOTE_AVAILABLE
        
        if self.use_pyannote:
            self._initialize_pyannote(auth_token)
        else:
            print("📊 Using simple VAD-based speaker detection")
            self.pipeline = None
    
    def _initialize_pyannote(self, auth_token: str):
        """Initialize pyannote pipeline"""
        try:
            # Load from environment if not provided
            if not auth_token:
                from dotenv import load_dotenv
                load_dotenv()
                auth_token = os.getenv("HUGGINGFACE_TOKEN")
            
            if not auth_token:
                print("⚠️ No Hugging Face token provided. Using fallback method.")
                self.use_pyannote = False
                return
            
            print("🔄 Loading pyannote speaker diarization model...")
            
            # Use the pretrained pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=auth_token
            )
            
            # Move to GPU if available
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                print("✅ Pyannote model loaded (GPU)")
            else:
                print("✅ Pyannote model loaded (CPU)")
                
        except Exception as e:
            print(f"⚠️ Could not load pyannote: {e}")
            print("📊 Falling back to simple speaker detection")
            self.use_pyannote = False
    
    def diarize_audio(self, audio_path: Path) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on audio file
        """
        if self.use_pyannote and self.pipeline:
            return self._diarize_with_pyannote(audio_path)
        else:
            return self._diarize_with_vad(audio_path)
    
    def _diarize_with_pyannote(self, audio_path: Path) -> List[SpeakerSegment]:
        """Use pyannote for speaker diarization"""
        print("🎯 Performing speaker diarization with pyannote...")
        
        try:
            # Run diarization
            diarization = self.pipeline(str(audio_path))
            
            # Convert to speaker segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                if turn.duration >= self.min_speaker_duration:
                    segment = SpeakerSegment(
                        speaker_id=speaker,
                        start_time=turn.start,
                        end_time=turn.end,
                        confidence=1.0
                    )
                    segments.append(segment)
            
            # Sort by start time
            segments.sort(key=lambda x: x.start_time)
            
            print(f"✅ Found {len(set(s.speaker_id for s in segments))} speakers")
            print(f"📊 Total segments: {len(segments)}")
            
            return segments
            
        except Exception as e:
            print(f"❌ Pyannote error: {e}")
            return self._diarize_with_vad(audio_path)
    
    def _diarize_with_vad(self, audio_path: Path) -> List[SpeakerSegment]:
        """
        Simple Voice Activity Detection based diarization
        This is a fallback when pyannote isn't available
        """
        print("🎯 Performing simple speaker segmentation...")
        
        import wave
        import scipy.signal as signal
        
        try:
            # Read audio file
            with wave.open(str(audio_path), 'rb') as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                audio_data = wf.readframes(n_frames)
                
            # Convert to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Simple energy-based VAD
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.010 * sample_rate)    # 10ms hop
            
            # Calculate energy for each frame
            energies = []
            for i in range(0, len(audio_np) - frame_length, hop_length):
                frame = audio_np[i:i + frame_length]
                energy = np.sum(frame ** 2) / frame_length
                energies.append(energy)
            
            energies = np.array(energies)
            
            # Threshold for speech detection
            energy_threshold = np.mean(energies) + 0.5 * np.std(energies)
            
            # Detect speech segments
            speech_frames = energies > energy_threshold
            
            # Apply median filter to smooth
            speech_frames = signal.medfilt(speech_frames.astype(float), kernel_size=21).astype(bool)
            
            # Find speech segments
            segments = []
            in_speech = False
            start_time = 0
            speaker_count = 0
            
            for i, is_speech in enumerate(speech_frames):
                current_time = i * hop_length / sample_rate
                
                if is_speech and not in_speech:
                    # Start of speech segment
                    in_speech = True
                    start_time = current_time
                    
                elif not is_speech and in_speech:
                    # End of speech segment
                    in_speech = False
                    end_time = current_time
                    
                    # Add segment if long enough
                    if end_time - start_time >= self.min_speaker_duration:
                        # Simple speaker alternation (not real diarization)
                        speaker_id = f"SPEAKER_{(speaker_count % 2) + 1}"
                        speaker_count += 1
                        
                        segment = SpeakerSegment(
                            speaker_id=speaker_id,
                            start_time=start_time,
                            end_time=end_time,
                            confidence=0.7  # Lower confidence for VAD
                        )
                        segments.append(segment)
            
            print(f"✅ Found {len(segments)} speech segments")
            print("⚠️ Note: Using simple VAD - speakers may not be accurately identified")
            
            return segments
            
        except Exception as e:
            print(f"❌ VAD error: {e}")
            return []
    
    def merge_with_transcript(
        self,
        speaker_segments: List[SpeakerSegment],
        transcript_segments: List,
        audio_path: Optional[Path] = None
    ) -> List[SpeakerSegment]:
        """
        Merge speaker diarization with transcript
        """
        print("🔄 Merging speakers with transcript...")
        
        # Create a copy of speaker segments
        merged_segments = []
        
        for speaker_seg in speaker_segments:
            # Find overlapping transcript segments
            speaker_text = []
            
            for trans_seg in transcript_segments:
                # Check if transcript segment overlaps with speaker segment
                trans_time = getattr(trans_seg, 'timestamp', 0)
                trans_duration = getattr(trans_seg, 'duration', 0)
                
                # Simple time-based matching (can be improved)
                if (trans_time >= speaker_seg.start_time and 
                    trans_time <= speaker_seg.end_time):
                    speaker_text.append(getattr(trans_seg, 'text', ''))
            
            # Create merged segment
            merged_seg = SpeakerSegment(
                speaker_id=speaker_seg.speaker_id,
                start_time=speaker_seg.start_time,
                end_time=speaker_seg.end_time,
                text=' '.join(speaker_text),
                confidence=speaker_seg.confidence
            )
            
            if merged_seg.text:  # Only add if there's text
                merged_segments.append(merged_seg)
        
        print(f"✅ Merged {len(merged_segments)} segments with text")
        return merged_segments
    
    def format_diarized_transcript(self, segments: List[SpeakerSegment]) -> str:
        """
        Format diarized transcript for display
        """
        formatted = []
        current_speaker = None
        
        for segment in segments:
            # Add speaker label if changed
            if segment.speaker_id != current_speaker:
                formatted.append(f"\n[{segment.speaker_id}]:")
                current_speaker = segment.speaker_id
            
            # Add text
            if segment.text:
                formatted.append(segment.text)
        
        return ' '.join(formatted)
    
    def get_speaker_statistics(self, segments: List[SpeakerSegment]) -> Dict:
        """
        Calculate speaking time statistics for each speaker
        """
        stats = {}
        
        for segment in segments:
            if segment.speaker_id not in stats:
                stats[segment.speaker_id] = {
                    'total_time': 0,
                    'turn_count': 0,
                    'words_spoken': 0
                }
            
            stats[segment.speaker_id]['total_time'] += segment.duration
            stats[segment.speaker_id]['turn_count'] += 1
            
            if segment.text:
                stats[segment.speaker_id]['words_spoken'] += len(segment.text.split())
        
        # Calculate percentages
        total_time = sum(s['total_time'] for s in stats.values())
        for speaker_stats in stats.values():
            speaker_stats['percentage'] = (speaker_stats['total_time'] / total_time * 100) if total_time > 0 else 0
        
        return stats


def test_diarization():
    """Test speaker diarization on a sample audio file"""
    print("🎯 Testing Speaker Diarization")
    print("=" * 50)
    
    # Check for test audio file
    test_audio = Path("outputs/recordings")
    audio_files = list(test_audio.glob("*.wav"))
    
    if not audio_files:
        print("❌ No audio files found. Please run audio_capture.py first to record a test file.")
        return
    
    # Use the most recent audio file
    audio_file = sorted(audio_files)[-1]
    print(f"📁 Using audio file: {audio_file}")
    
    # Initialize diarizer
    diarizer = SpeakerDiarizer(use_pyannote=True)
    
    # Perform diarization
    segments = diarizer.diarize_audio(audio_file)
    
    if segments:
        print("\n📊 Diarization Results:")
        print("-" * 50)
        
        for i, segment in enumerate(segments[:10]):  # Show first 10 segments
            print(f"{i+1}. [{segment.speaker_id}] {segment.start_time:.1f}s - {segment.end_time:.1f}s ({segment.duration:.1f}s)")
        
        # Show statistics
        stats = diarizer.get_speaker_statistics(segments)
        print("\n📈 Speaker Statistics:")
        print("-" * 50)
        
        for speaker, data in stats.items():
            print(f"{speaker}:")
            print(f"  - Speaking time: {data['total_time']:.1f}s ({data['percentage']:.1f}%)")
            print(f"  - Number of turns: {data['turn_count']}")
    else:
        print("❌ No speaker segments found")


if __name__ == "__main__":
    test_diarization()