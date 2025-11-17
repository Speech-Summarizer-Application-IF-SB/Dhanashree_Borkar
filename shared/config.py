"""
Global Configuration Loader for AI Meeting Summarizer
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    groq_api_key: str
    whisper_model: str = "tiny"
    output_dir: str = "outputs/recordings"

def get_config():
    """Load environment variables and return Config object"""
    load_dotenv()

    groq_key = os.getenv("GROQ_API_KEY")

    if not groq_key:
        raise ValueError("❌ Missing GROQ_API_KEY in .env file!")

    return Config(
        groq_api_key=groq_key,
        whisper_model=os.getenv("WHISPER_MODEL", "tiny"),
        output_dir=os.getenv("OUTPUT_DIR", "outputs/recordings")
    )
