"""
Complete Meeting Processing Pipeline
Handles: Audio → STT → Diarization → Summarization
"""

import sys
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from milestone_1_stt.module_2_realtime_stt.audio_capture import AudioRecorder
from milestone_1_stt.module_2_realtime_stt.realtime_stt import RealTimeTranscriber
from milestone_2_diarization_summarization.module_3_diarization.speaker_identifier import SpeakerDiarizer
from milestone_2_diarization_summarization.module_4_summarization.summarizer import MeetingSummarizer


class MeetingPipeline:
    """
    End-to-end meeting processing pipeline
    Integrates all components for seamless operation
    """
    
    def __init__(self):
        """Initialize all components"""
        self.recorder = None
        self.transcriber = None
        self.diarizer = SpeakerDiarizer()
        self.summarizer = MeetingSummarizer(provider="groq")
        
        # Storage
        self.audio_file = None
        self.transcript_segments = []
        self.diarized_segments = []
        self.summary = None
        
        self.is_recording = False
    
    def start_recording(self, callback=None, model_type="whisper", model_size="base"):
        """
        Start audio recording with real-time transcription
        
        Args:
            callback: Function to call when new transcript segment arrives
            model_type: "whisper" or "vosk"
            model_size: Model size for Whisper (tiny, base, small, medium)
        """
        if self.is_recording:
            print("⚠️ Already recording!")
            return False
        
        print("🎙️ Initializing recording pipeline...")
        
        # Initialize recorder
        self.recorder = AudioRecorder(sample_rate=16000)
        
        # Initialize transcriber
        self.transcriber = RealTimeTranscriber(
            model_type=model_type,
            model_size=model_size,
            language="en"
        )
        
        # Transcription callback
        def transcription_callback(segment):
            if segment.is_final:
                self.transcript_segments.append(segment)
                if callback:
                    callback(segment)
        
        # Audio processing callback
        def audio_callback(chunk, sample_rate):
            self.transcriber.add_audio(chunk.flatten())
        
        # Start transcription
        self.transcriber.start_realtime_transcription(callback=transcription_callback)
        
        # Start recording
        self.recorder.start_recording(chunk_callback=audio_callback)
        
        self.is_recording = True
        print("✅ Recording started!")
        return True
    
    def stop_recording(self):
        """
        Stop recording and save audio file
        
        Returns:
            Path to saved audio file
        """
        if not self.is_recording:
            print("⚠️ Not currently recording!")
            return None
        
        print("⏹️ Stopping recording...")
        
        # Stop recording
        self.audio_file = self.recorder.stop_recording()
        
        # Stop transcription
        self.transcriber.stop_transcription()
        
        self.is_recording = False
        print(f"✅ Recording stopped. Audio saved: {self.audio_file}")
        
        return self.audio_file
    
    def process_meeting(self, enable_diarization=True, meeting_type="general"):
        """
        Process complete meeting: diarization + summarization
        
        Args:
            enable_diarization: Whether to perform speaker diarization
            meeting_type: Type of meeting for better summarization
        
        Returns:
            MeetingSummary object
        """
        if not self.audio_file or not self.transcript_segments:
            print("❌ No recording to process!")
            return None
        
        print("\n🔄 Processing meeting...")
        print("=" * 50)
        
        # Step 1: Speaker Diarization
        if enable_diarization:
            print("👥 Performing speaker diarization...")
            try:
                speaker_segments = self.diarizer.diarize_audio(self.audio_file)
                self.diarized_segments = self.diarizer.merge_with_transcript(
                    speaker_segments,
                    self.transcript_segments
                )
                print(f"✅ Identified {len(set([s.speaker_id for s in self.diarized_segments]))} speakers")
            except Exception as e:
                print(f"⚠️ Diarization error: {e}")
                print("   Continuing without speaker identification...")
                self.diarized_segments = []
        
        # Step 2: Prepare transcript
        if self.diarized_segments:
            # Use diarized transcript with speaker labels
            full_text = "\n".join([
                f"{seg.speaker_id}: {seg.text}" 
                for seg in self.diarized_segments
            ])
        else:
            # Use plain transcript
            full_text = " ".join([seg.text for seg in self.transcript_segments])
        
        print(f"📝 Transcript prepared ({len(full_text)} characters)")
        
        # Step 3: AI Summarization
        print("🧠 Generating AI summary...")
        try:
            self.summary = self.summarizer.summarize(full_text, style=meeting_type)
            print("✅ Summary generated successfully!")
        except Exception as e:
            print(f"❌ Summarization error: {e}")
            return None
        
        print("=" * 50)
        return self.summary
    
    def get_results(self):
        """
        Get all processed results
        
        Returns:
            Dictionary with all results
        """
        return {
            "audio_file": self.audio_file,
            "transcript": self.transcript_segments,
            "diarized": self.diarized_segments,
            "summary": self.summary,
            "is_recording": self.is_recording
        }
    
    def reset(self):
        """Reset pipeline for new meeting"""
        self.audio_file = None
        self.transcript_segments = []
        self.diarized_segments = []
        self.summary = None
        self.is_recording = False
        print("🔄 Pipeline reset")


# ==================== TEST FUNCTION ====================
def test_pipeline():
    """Test the complete pipeline"""
    import time
    
    print("🎯 Testing Meeting Pipeline")
    print("=" * 50)
    
    # Create pipeline
    pipeline = MeetingPipeline()
    
    # Start recording
    def on_transcript(segment):
        print(f"📝 Transcribed: {segment.text[:50]}...")
    
    pipeline.start_recording(callback=on_transcript)
    
    # Record for 10 seconds
    print("\n🎤 Recording for 10 seconds... Speak now!")
    time.sleep(10)
    
    # Stop recording
    audio_file = pipeline.stop_recording()
    
    if audio_file:
        # Process meeting
        summary = pipeline.process_meeting(enable_diarization=True)
        
        if summary:
            print("\n📊 RESULTS:")
            print("=" * 50)
            print(summary.to_markdown())
    else:
        print("❌ No audio recorded")


if __name__ == "__main__":
    test_pipeline()