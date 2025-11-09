"""
LLM-based Summarization Module
Generates intelligent meeting summaries using Groq or HuggingFace models.
"""

import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# ✅ Load environment variables from .env file
load_dotenv()

# ✅ Import required libraries
from groq import Groq
from transformers import pipeline


# -------------------- DATA CLASS --------------------
@dataclass
class MeetingSummary:
    """Structured meeting summary."""
    raw_transcript: str
    summary: str
    key_points: List[str]
    action_items: List[str]
    decisions: List[str]
    participants: List[str]
    duration: float
    timestamp: datetime
    speaker_stats: Dict[str, float] = None

    def to_markdown(self) -> str:
        """Convert summary to markdown format."""
        md = [
            "# Meeting Summary",
            f"**Date:** {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"**Duration:** {self.duration:.1f} minutes\n",
        ]

        if self.participants:
            md.append("## Participants")
            md.extend([f"- {p}" for p in self.participants])
            md.append("")

        md.append("## Summary")
        md.append(self.summary)
        md.append("")

        if self.key_points:
            md.append("## Key Points")
            md.extend([f"- {kp}" for kp in self.key_points])
            md.append("")

        if self.action_items:
            md.append("## Action Items")
            md.extend([f"- [ ] {a}" for a in self.action_items])
            md.append("")

        if self.decisions:
            md.append("## Decisions Made")
            md.extend([f"- {d}" for d in self.decisions])
            md.append("")

        if self.speaker_stats:
            md.append("## Speaking Time")
            md.extend([f"- {s}: {p:.1f}%" for s, p in self.speaker_stats.items()])

        return "\n".join(md)


# -------------------- MAIN CLASS --------------------
class MeetingSummarizer:
    """
    Intelligent meeting summarizer using LLMs (Groq or HuggingFace).
    """

    def __init__(
        self,
        provider: str = "groq",
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.3,
    ):
        self.provider = provider.lower()
        self.temperature = temperature
        self.model_name = model_name
        self.client = None
        self.summarizer = None

        if self.provider == "groq":
            self._init_groq(api_key)
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    # -------------------- INITIALIZERS --------------------
    def _init_groq(self, api_key: Optional[str]):
        """Initialize Groq client."""
        api_key = api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing Groq API key. Set GROQ_API_KEY in your .env file.")

        self.client = Groq(api_key=api_key)
        self.model_name = self.model_name or "llama-3.3-70b-versatile"
        print(f"✅ Groq initialized with model: {self.model_name}")

    def _init_huggingface(self):
        """Initialize HuggingFace summarizer."""
        self.model_name = self.model_name or "facebook/bart-large-cnn"
        print(f"⏳ Loading HuggingFace model: {self.model_name} ...")

        self.summarizer = pipeline(
            "summarization",
            model=self.model_name,
            device=-1  # CPU
        )
        print("✅ HuggingFace model loaded successfully!")

    # -------------------- SUMMARIZATION --------------------
    def summarize(self, transcript: str, style: str = "detailed") -> MeetingSummary:
        """Generate meeting summary."""
        print("\n🧠 Generating meeting summary...")

        if self.provider == "groq":
            summary_data = self._summarize_with_groq(transcript, style)
        else:
            summary_data = self._summarize_with_huggingface(transcript)

        meeting_summary = MeetingSummary(
            raw_transcript=transcript,
            summary=summary_data.get("summary", ""),
            key_points=summary_data.get("key_points", []),
            action_items=summary_data.get("action_items", []),
            decisions=summary_data.get("decisions", []),
            participants=[],
            duration=len(transcript.split()) / 150,  # rough minutes estimate
            timestamp=datetime.now(),
            speaker_stats={},
        )

        print("✅ Summary generated successfully!")
        return meeting_summary

    # -------------------- GROQ --------------------
    def _summarize_with_groq(self, transcript: str, style: str) -> Dict:
        """Summarize using Groq API."""
        prompt = f"""
        Summarize the following meeting in detail:

        {transcript}

        Return JSON with keys:
        summary, key_points, action_items, decisions.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert meeting summarizer."},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            return self._parse_summary_response(content)

        except Exception as e:
            print(f"❌ Groq error: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_points": [],
                "action_items": [],
                "decisions": [],
            }

    # -------------------- HUGGINGFACE --------------------
    def _summarize_with_huggingface(self, transcript: str) -> Dict:
        """Summarize using HuggingFace pipeline."""
        try:
            result = self.summarizer(transcript[:4000], max_length=200, min_length=50, do_sample=False)
            combined_summary = result[0]["summary_text"]

            return {
                "summary": combined_summary,
                "key_points": self._extract_key_points(combined_summary),
                "action_items": [],
                "decisions": [],
            }
        except Exception as e:
            print(f"❌ HuggingFace error: {e}")
            return {
                "summary": f"Error generating summary: {str(e)}",
                "key_points": [],
                "action_items": [],
                "decisions": [],
            }

    # -------------------- HELPERS --------------------
    def _parse_summary_response(self, text: str) -> Dict:
        """Try to parse model output as JSON."""
        try:
            import re
            json_match = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️ JSON parse error: {e}")

        return {"summary": text.strip(), "key_points": [], "action_items": [], "decisions": []}

    def _extract_key_points(self, text: str) -> List[str]:
        """Simple key point extractor from summary text."""
        sentences = text.split(".")
        return [s.strip() for s in sentences if len(s.strip()) > 30][:5]


# -------------------- TEST FUNCTION --------------------
def test_summarizer():
    """Run test with sample transcript."""
    print("\n🚀 Testing Meeting Summarizer\n" + "=" * 50)

    sample_transcript = """
    Speaker 1: Let's start our project meeting. We’ll discuss progress and blockers.
    Speaker 2: The frontend is 80% done, but API integration is pending.
    Speaker 3: I'll handle integration by Thursday.
    Speaker 1: Great, we’ll review on Friday.
    """

    summarizer = MeetingSummarizer(provider="groq")  # or "huggingface"
    summary = summarizer.summarize(sample_transcript)

    print("\n" + "=" * 50)
    print("📄 MEETING SUMMARY\n" + "=" * 50)
    print(summary.to_markdown())


# -------------------- MAIN --------------------
if __name__ == "__main__":
    test_summarizer()
