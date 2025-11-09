"""
Model Download Script for AI Meeting Summarizer
Downloads required models for STT and diarization
"""

import os
import json
import whisper
import subprocess
import requests
import zipfile
from pathlib import Path
import sys

def download_whisper_model():
    """Download Whisper model for speech-to-text"""
    print("📥 Downloading Whisper model...")
    try:
        # This will download and cache the model
        model = whisper.load_model("base")
        print("✅ Whisper model downloaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error downloading Whisper: {e}")
        return False

def download_vosk_model():
    """Download Vosk model as an alternative STT option"""
    print("📥 Downloading Vosk model...")
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Small English model (40MB)
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    model_path = models_dir / "vosk-model-small-en-us-0.15"
    
    if model_path.exists():
        print("✅ Vosk model already exists!")
        return True
    
    try:
        # Download the model
        print("Downloading from:", model_url)
        response = requests.get(model_url, stream=True)
        zip_path = models_dir / "vosk_model.zip"
        
        # Save with progress bar
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for data in response.iter_content(block_size):
                downloaded += len(data)
                f.write(data)
                # Show progress
                progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                sys.stdout.write(f'\rProgress: {progress:.1f}%')
                sys.stdout.flush()
        
        print("\n📦 Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(models_dir)
        
        # Clean up zip file
        zip_path.unlink()
        print("✅ Vosk model downloaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Vosk: {e}")
        return False

def setup_pyannote():
    """Setup pyannote for speaker diarization"""
    print("📥 Setting up pyannote for speaker diarization...")
    
    instructions = """
    🔑 Pyannote requires Hugging Face authentication:
    
    1. Go to: https://huggingface.co/pyannote/speaker-diarization-3.1
    2. Accept the model conditions
    3. Go to: https://huggingface.co/settings/tokens
    4. Create a token with 'read' access
    5. Add to your .env file: HUGGINGFACE_TOKEN=your_token_here
    
    The model will be downloaded automatically on first use.
    """
    print(instructions)
    return True

def download_sample_audio():
    """Download sample audio files for testing"""
    print("📥 Creating sample audio directory...")
    
    samples_dir = Path("data/audio_samples")
    samples_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a README for sample audio
    readme_content = """
    # Sample Audio Files
    
    Place your test audio files here for development.
    
    Recommended sources:
    - AMI Meeting Corpus: http://groups.inf.ed.ac.uk/ami/corpus/
    - LibriSpeech samples: https://www.openslr.org/12/
    - Or record your own test meetings!
    
    Supported formats: .wav, .mp3, .m4a, .flac
    """
    
    with open(samples_dir / "README.md", "w") as f:
        f.write(readme_content)
    
    print("✅ Sample directory created! Add test audio files to data/audio_samples/")
    return True

def main():
    print("🚀 AI Meeting Summarizer - Model Setup")
    print("=" * 50)
    
    results = {
        "Whisper": download_whisper_model(),
        "Vosk": download_vosk_model(),
        "Pyannote": setup_pyannote(),
        "Samples": download_sample_audio()
    }
    
    print("\n" + "=" * 50)
    print("📊 Setup Summary:")
    for component, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {component}")
    
    if all(results.values()):
        print("\n🎉 All models ready! You can now start building your app.")
    else:
        print("\n⚠️ Some components need manual setup. Check the instructions above.")
    
    print("\n💡 Next steps:")
    print("  1. Add your API keys to .env file")
    print("  2. Run: python src/audio/audio_capture.py (to test audio)")
    print("  3. Run: streamlit run src/ui/streamlit_app.py (to start the app)")

if __name__ == "__main__":
    main()