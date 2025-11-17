"""
speaker_identifier.py
---------------------------------
Performs speaker diarization using PyAnnote (if available)
and provides a fallback method if the model or token is missing.

Integrated with MeetingPipeline (audio → STT → Diarization → Summary)
"""

import os
from dataclasses import dataclass
from typing import List, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class SpeakerSegment:
    """Represents one identified speaker segment."""
    start: float
    end: float
    speaker_id: str
    text: str = ""

class SpeakerDiarizer:
    """
    Handles speaker diarization using PyAnnote if available,
    otherwise falls back to a mock implementation.
    """

    def __init__(self):
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        self.pipeline = None
        if self.hf_token:
            try:
                from pyannote.audio import Pipeline
                print("🔄 Loading pyannote speaker diarization model...")
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization",
                    use_auth_token=self.hf_token
                )
                print("✅ PyAnnote diarization model loaded successfully!")
            except Exception as e:
                print(f"⚠️ Could not load pyannote: {e}")
                print("📊 Falling back to simple speaker detection.")
        else:
            print("⚠️ No Hugging Face token found. Using fallback diarizer.")

    def diarize_audio(self, audio_file: str) -> List[SpeakerSegment]:
        """Performs diarization on the given audio file."""
        if not os.path.exists(audio_file):
            print(f"❌ Audio file not found: {audio_file}")
            return []

        if self.pipeline:
            try:
                print(f"🎧 Running diarization on: {audio_file}")
                diarization_result = self.pipeline(audio_file)

                speaker_segments = []
                for turn, _, speaker in diarization_result.itertracks(yield_label=True):
                    speaker_segments.append(
                        SpeakerSegment(
                            start=turn.start,
                            end=turn.end,
                            speaker_id=speaker
                        )
                    )
                print(f"✅ Diarization complete: {len(speaker_segments)} speaker segments found.")
                return speaker_segments
            except Exception as e:
                print(f"⚠️ PyAnnote diarization failed: {e}")
                print("📊 Falling back to single-speaker mode.")

        # --- Fallback mode ---
        print("⚙️ Using fallback diarization (Speaker 1 only).")
        return [
            SpeakerSegment(
                start=0.0,
                end=9999.0,
                speaker_id="Speaker 1"
            )
        ]

    def merge_with_transcript(self, speaker_segments: List[SpeakerSegment], transcript_segments: List[Any]) -> List[Any]:
        """
        Merge diarization with transcript segments.
        Attaches text to speakers based on time or sequential order.
        """
        merged = []

        if not transcript_segments:
            print("⚠️ No transcript segments found.")
            return []

        if not speaker_segments:
            print("⚠️ No diarization found. Assigning all to Speaker 1.")
            for seg in transcript_segments:
                merged.append(type('Merged', (), {
                    'speaker_id': 'Speaker 1',
                    'text': getattr(seg, 'text', str(seg))
                })())
            return merged

        print("🔗 Merging transcript with diarization results...")
        speaker_idx = 0
        for seg in transcript_segments:
            speaker = speaker_segments[min(speaker_idx, len(speaker_segments) - 1)]
            merged.append(type('Merged', (), {
                'speaker_id': speaker.speaker_id,
                'text': getattr(seg, 'text', str(seg))
            })())
            speaker_idx = (speaker_idx + 1) % len(speaker_segments)

        print(f"✅ Merged {len(merged)} transcript segments with speaker labels.")
        return merged
