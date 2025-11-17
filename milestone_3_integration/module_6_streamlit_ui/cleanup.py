"""
Project Cleanup Script
Organizes files and creates missing __init__.py files
"""

from pathlib import Path
import shutil

def create_init_files():
    """Create __init__.py files in all module directories"""
    
    init_contents = {
        "milestone_1_stt/module_2_realtime_stt/__init__.py": '''"""Real-time Speech-to-Text Module"""
from .audio_capture import AudioRecorder
from .realtime_stt import RealTimeTranscriber, TranscriptionSegment
__all__ = ['AudioRecorder', 'RealTimeTranscriber', 'TranscriptionSegment']
''',
        
        "milestone_2_diarization_summarization/module_3_diarization/__init__.py": '''"""Speaker Diarization Module"""
from .speaker_identifier import SpeakerDiarizer, SpeakerSegment
__all__ = ['SpeakerDiarizer', 'SpeakerSegment']
''',
        
        "milestone_2_diarization_summarization/module_4_summarization/__init__.py": '''"""Meeting Summarization Module"""
from .summarizer import MeetingSummarizer, MeetingSummary
__all__ = ['MeetingSummarizer', 'MeetingSummary']
''',
        
        "milestone_3_integration/module_5_backend_integration/__init__.py": '''"""Backend Integration Pipeline"""
from .pipeline import MeetingPipeline
__all__ = ['MeetingPipeline']
''',
        
        "milestone_3_integration/module_6_streamlit_ui/__init__.py": '''"""Streamlit User Interface"""
__all__ = []
''',
        
        "milestone_4_finalization/module_7_testing_optimization/__init__.py": '''"""Testing and Optimization Module"""
from .ExportManager import ExportManager
from .email_sender import EmailSender
__all__ = ['ExportManager', 'EmailSender']
''',
        
        "shared/__init__.py": '''"""Shared utilities and configuration"""
from .config import get_config, Config
__all__ = ['get_config', 'Config']
'''
    }
    
    for file_path, content in init_contents.items():
        full_path = Path(file_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Created: {file_path}")

def cleanup_duplicates():
    """Remove duplicate files and folders"""
    
    # Files/folders to delete
    to_delete = [
        "src",  # Old src folder
        "speaker_diarization.py",  # Duplicate
        ".vscode",  # IDE files (optional)
    ]
    
    for item in to_delete:
        path = Path(item)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
                print(f"🗑️  Deleted folder: {item}")
            else:
                path.unlink()
                print(f"🗑️  Deleted file: {item}")

def verify_structure():
    """Verify the project structure is correct"""
    
    required_files = [
        "main.py",
        "requirements.txt",
        ".env.example",
        "milestone_1_stt/module_2_realtime_stt/audio_capture.py",
        "milestone_1_stt/module_2_realtime_stt/realtime_stt.py",
        "milestone_2_diarization_summarization/module_3_diarization/speaker_identifier.py",
        "milestone_2_diarization_summarization/module_4_summarization/summarizer.py",
        "milestone_3_integration/module_5_backend_integration/pipeline.py",
        "milestone_3_integration/module_6_streamlit_ui/streamlit_app.py",
        "milestone_4_finalization/module_7_testing_optimization/ExportManager.py",
        "milestone_4_finalization/module_7_testing_optimization/email_sender.py",
        "shared/config.py",
    ]
    
    print("\n🔍 Verifying project structure...")
    missing = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing:
        print(f"\n⚠️  {len(missing)} files missing!")
        return False
    else:
        print("\n✅ All required files present!")
        return True

def main():
    """Run cleanup"""
    print("🧹 AI Meeting Summarizer - Project Cleanup")
    print("=" * 50)
    
    print("\n📝 Step 1: Creating __init__.py files...")
    create_init_files()
    
    print("\n🗑️  Step 2: Removing duplicates...")
    cleanup_duplicates()
    
    print("\n🔍 Step 3: Verifying structure...")
    valid = verify_structure()
    
    if valid:
        print("\n✅ Cleanup complete! Project structure is correct.")
        print("\n🚀 Next steps:")
        print("   1. Run: python main.py")
        print("   2. Test the application")
        print("   3. Fix any remaining bugs")
    else:
        print("\n⚠️  Some files are missing. Check the list above.")

if __name__ == "__main__":
    main()