"""
Configuration Manager for AI Meeting Summarizer
Loads settings from .env file and provides easy access
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class APIConfig:
    """API Keys and credentials"""
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    huggingface_token: str = field(default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    def validate(self) -> bool:
        """Check if required API keys are present"""
        if not self.groq_api_key:
            print("⚠️  Warning: GROQ_API_KEY not found in .env")
            return False
        if not self.huggingface_token:
            print("⚠️  Warning: HUGGINGFACE_TOKEN not found in .env")
            return False
        return True


@dataclass
class EmailConfig:
    """Email configuration for sending summaries"""
    host: str = field(default_factory=lambda: os.getenv("EMAIL_HOST", "smtp.gmail.com"))
    port: int = field(default_factory=lambda: int(os.getenv("EMAIL_PORT", "587")))
    use_tls: bool = field(default_factory=lambda: os.getenv("EMAIL_USE_TLS", "true").lower() == "true")
    address: str = field(default_factory=lambda: os.getenv("EMAIL_ADDRESS", ""))
    password: str = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.address and self.password)


@dataclass
class ModelConfig:
    """Model settings for STT, Diarization, and LLM"""
    # STT Settings
    stt_model: str = field(default_factory=lambda: os.getenv("STT_MODEL", "whisper"))
    whisper_model_size: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL_SIZE", "base"))
    vosk_model_path: str = field(default_factory=lambda: os.getenv("VOSK_MODEL_PATH", "models/vosk-model-small-en-us-0.15"))
    
    # Diarization
    diarization_model: str = field(default_factory=lambda: os.getenv("DIARIZATION_MODEL", "pyannote/speaker-diarization-3.1"))
    
    # LLM Settings
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama-3.1-70b-versatile"))
    llm_temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2000")))
    
    @property
    def whisper_model_path(self) -> Path:
        """Get full path to Whisper model cache"""
        return PROJECT_ROOT / "models" / "whisper"
    
    @property
    def vosk_model_full_path(self) -> Path:
        """Get full path to Vosk model"""
        return PROJECT_ROOT / self.vosk_model_path


@dataclass
class AudioConfig:
    """Audio recording and processing settings"""
    sample_rate: int = field(default_factory=lambda: int(os.getenv("SAMPLE_RATE", "16000")))
    channels: int = field(default_factory=lambda: int(os.getenv("CHANNELS", "1")))
    chunk_size: int = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1024")))
    audio_format: str = field(default_factory=lambda: os.getenv("AUDIO_FORMAT", "int16"))
    
    # Voice Activity Detection
    vad_threshold: float = field(default_factory=lambda: float(os.getenv("VAD_THRESHOLD", "0.5")))
    silence_duration: float = field(default_factory=lambda: float(os.getenv("SILENCE_DURATION", "1.5")))


@dataclass
class PathConfig:
    """Directory paths for data storage"""
    data_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("DATA_DIR", "data"))
    models_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("MODELS_DIR", "models"))
    outputs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("OUTPUTS_DIR", "outputs"))
    recordings_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("RECORDINGS_DIR", "outputs/recordings"))
    transcripts_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("TRANSCRIPTS_DIR", "data/transcripts"))
    summaries_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("SUMMARIES_DIR", "data/summaries"))
    exports_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("EXPORTS_DIR", "outputs/exports"))
    logs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / os.getenv("LOGS_DIR", "outputs/logs"))
    
    def create_directories(self):
        """Create all required directories if they don't exist"""
        for path in [self.data_dir, self.models_dir, self.outputs_dir, 
                     self.recordings_dir, self.transcripts_dir, self.summaries_dir,
                     self.exports_dir, self.logs_dir]:
            path.mkdir(parents=True, exist_ok=True)
        print("✅ All directories created/verified")


@dataclass
class ProcessingConfig:
    """Processing and performance settings"""
    enable_real_time_stt: bool = field(default_factory=lambda: os.getenv("ENABLE_REAL_TIME_STT", "true").lower() == "true")
    enable_diarization: bool = field(default_factory=lambda: os.getenv("ENABLE_DIARIZATION", "true").lower() == "true")
    enable_auto_summary: bool = field(default_factory=lambda: os.getenv("ENABLE_AUTO_SUMMARY", "true").lower() == "true")
    
    max_recording_duration: int = field(default_factory=lambda: int(os.getenv("MAX_RECORDING_DURATION", "7200")))
    processing_threads: int = field(default_factory=lambda: int(os.getenv("PROCESSING_THREADS", "4")))
    use_gpu: bool = field(default_factory=lambda: os.getenv("USE_GPU", "true").lower() == "true")


@dataclass
class DiarizationConfig:
    """Speaker diarization specific settings"""
    min_speakers: int = field(default_factory=lambda: int(os.getenv("MIN_SPEAKERS", "1")))
    max_speakers: int = field(default_factory=lambda: int(os.getenv("MAX_SPEAKERS", "10")))
    min_segment_duration: float = field(default_factory=lambda: float(os.getenv("MIN_SEGMENT_DURATION", "1.0")))


@dataclass
class SummarizationConfig:
    """Summarization settings"""
    summary_style: str = field(default_factory=lambda: os.getenv("SUMMARY_STYLE", "professional"))
    include_timestamps: bool = field(default_factory=lambda: os.getenv("INCLUDE_TIMESTAMPS", "true").lower() == "true")
    include_speaker_stats: bool = field(default_factory=lambda: os.getenv("INCLUDE_SPEAKER_STATS", "true").lower() == "true")
    include_action_items: bool = field(default_factory=lambda: os.getenv("INCLUDE_ACTION_ITEMS", "true").lower() == "true")


@dataclass
class ExportConfig:
    """Export and file format settings"""
    default_format: str = field(default_factory=lambda: os.getenv("DEFAULT_EXPORT_FORMAT", "pdf"))
    pdf_page_size: str = field(default_factory=lambda: os.getenv("PDF_PAGE_SIZE", "A4"))
    pdf_font_size: int = field(default_factory=lambda: int(os.getenv("PDF_FONT_SIZE", "11")))


class Config:
    """Main configuration class that combines all config sections"""
    
    def __init__(self):
        self.api = APIConfig()
        self.email = EmailConfig()
        self.model = ModelConfig()
        self.audio = AudioConfig()
        self.paths = PathConfig()
        self.processing = ProcessingConfig()
        self.diarization = DiarizationConfig()
        self.summarization = SummarizationConfig()
        self.export = ExportConfig()
        
        # App metadata
        self.app_name = os.getenv("APP_NAME", "AI Meeting Summarizer")
        self.app_version = os.getenv("APP_VERSION", "1.0.0")
        self.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # Create necessary directories
        self.paths.create_directories()
    
    def validate(self) -> bool:
        """Validate all configurations"""
        print("🔍 Validating configuration...")
        
        valid = True
        
        # Check API keys
        if not self.api.validate():
            print("❌ API configuration incomplete")
            valid = False
        else:
            print("✅ API keys configured")
        
        # Check email (optional)
        if self.email.is_configured():
            print("✅ Email configured")
        else:
            print("⚠️  Email not configured (optional)")
        
        # Check model paths
        if not self.model.vosk_model_full_path.exists() and self.model.stt_model == "vosk":
            print(f"⚠️  Vosk model not found at {self.model.vosk_model_full_path}")
            print("   Run: python utils/download_models.py")
        
        return valid
    
    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        return {
            "App": f"{self.app_name} v{self.app_version}",
            "STT Model": self.model.stt_model,
            "LLM Model": self.model.llm_model,
            "Diarization": "Enabled" if self.processing.enable_diarization else "Disabled",
            "GPU": "Enabled" if self.processing.use_gpu else "Disabled",
            "Email": "Configured" if self.email.is_configured() else "Not configured"
        }
    
    def print_summary(self):
        """Print configuration summary"""
        print("\n" + "="*50)
        print(f"🎙️  {self.app_name} v{self.app_version}")
        print("="*50)
        for key, value in self.get_summary().items():
            print(f"{key:20s}: {value}")
        print("="*50 + "\n")


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reload_config() -> Config:
    """Force reload configuration from .env file"""
    global _config_instance
    load_dotenv(override=True)
    _config_instance = Config()
    return _config_instance


# Quick access functions
def get_api_key(service: str) -> str:
    """Quick access to API keys"""
    config = get_config()
    keys = {
        "groq": config.api.groq_api_key,
        "huggingface": config.api.huggingface_token,
        "openai": config.api.openai_api_key
    }
    return keys.get(service.lower(), "")


if __name__ == "__main__":
    # Test configuration
    config = get_config()
    config.print_summary()
    
    if config.validate():
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has issues. Please check your .env file")
        print("\n📝 Copy .env.example to .env and fill in your API keys:")
        print("   cp .env.example .env")