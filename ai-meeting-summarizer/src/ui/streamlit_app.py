"""
AI Meeting Summarizer - Minimal Working Version
"""

import streamlit as st
import numpy as np
import time
from pathlib import Path
from datetime import datetime
import sys

# Add src directory to path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

# Import modules (with error handling)
try:
    from audio.audio_capture import AudioRecorder
    from stt.realtime_stt import RealTimeTranscriber, TranscriptionSegment
    from diarization.speaker_identifier import SpeakerDiarizer
    from summarization.summarizer import MeetingSummarizer
    from summarization.ExportManager import ExportManager
    from utils.email_sender import EmailSender
    IMPORTS_OK = True
except Exception as e:
    st.error(f"Import Error: {e}")
    IMPORTS_OK = False

# Page config
st.set_page_config(
    page_title="AI Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcript_segments' not in st.session_state:
    st.session_state.transcript_segments = []
if 'meeting_start_time' not in st.session_state:
    st.session_state.meeting_start_time = None
if 'audio_file' not in st.session_state:
    st.session_state.audio_file = None
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    
    meeting_name = st.text_input("Meeting Name", value="Team Meeting")
    meeting_type = st.selectbox("Meeting Type", ["General", "Standup", "Brainstorm"])
    
    st.markdown("---")
    st.subheader("🎤 STT Settings")
    stt_model = st.selectbox("Model", ["Whisper (Accurate)", "Vosk (Fast)"])
    whisper_size = st.selectbox("Whisper Size", ["tiny", "base", "small"])
    
    st.markdown("---")
    enable_diarization = st.checkbox("Enable Speaker ID", value=True)
    email_recipient = st.text_input("Email To", placeholder="email@example.com")

# Header
st.title("🎙️ AI Meeting Summarizer")
st.markdown("**Real-time transcription • Speaker identification • AI summaries**")
st.markdown("---")

# Check imports
if not IMPORTS_OK:
    st.error("⚠️ Some modules failed to import. Check console for details.")
    st.stop()

# Recording Controls
st.subheader("🎙️ Recording Controls")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔴 Start", disabled=st.session_state.recording, use_container_width=True):
        try:
            # Initialize recorder
            st.session_state.recorder = AudioRecorder(sample_rate=16000)
            
            # Initialize transcriber
            model_type = "whisper" if "Whisper" in stt_model else "vosk"
            st.session_state.transcriber = RealTimeTranscriber(
                model_type=model_type,
                model_size=whisper_size,
                language="en"
            )
            
            # Callbacks
            def transcription_callback(segment):
                if segment.is_final:
                    st.session_state.transcript_segments.append(segment)
            
            def audio_callback(chunk, sample_rate):
                st.session_state.transcriber.add_audio(chunk.flatten())
            
            # Start
            st.session_state.transcriber.start_realtime_transcription(callback=transcription_callback)
            st.session_state.recorder.start_recording(chunk_callback=audio_callback)
            
            st.session_state.recording = True
            st.session_state.meeting_start_time = datetime.now()
            st.session_state.transcript_segments = []
            
            st.success("🎙️ Recording started!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error starting recording: {e}")

with col2:
    if st.button("⏹️ Stop", disabled=not st.session_state.recording, use_container_width=True):
        try:
            # Stop recording
            audio_file = st.session_state.recorder.stop_recording()
            st.session_state.transcriber.stop_transcription()
            
            st.session_state.recording = False
            st.session_state.audio_file = audio_file
            st.session_state.processing = True
            
            st.success("⏹️ Recording stopped!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error stopping: {e}")

with col3:
    if st.session_state.recording and st.session_state.meeting_start_time:
        duration = int((datetime.now() - st.session_state.meeting_start_time).total_seconds())
        st.info(f"🔴 RECORDING - {duration // 60:02d}:{duration % 60:02d}")
    else:
        st.info("⚪ NOT RECORDING")

# Auto-refresh during recording
if st.session_state.recording:
    time.sleep(1)
    st.rerun()

# Metrics
if len(st.session_state.transcript_segments) > 0:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Segments", len(st.session_state.transcript_segments))
    with col2:
        duration = int((datetime.now() - st.session_state.meeting_start_time).total_seconds()) if st.session_state.meeting_start_time else 0
        st.metric("Duration", f"{duration // 60}m {duration % 60}s")
    with col3:
        words = sum([len(seg.text.split()) for seg in st.session_state.transcript_segments])
        st.metric("Words", words)

# Live Transcript
st.markdown("---")
st.subheader("💬 Live Transcript")

if len(st.session_state.transcript_segments) > 0:
    with st.container():
        for segment in st.session_state.transcript_segments[-10:]:  # Last 10 segments
            with st.chat_message("assistant"):
                st.write(segment.text)
else:
    st.info("👆 Start recording to see live transcription")

# Processing
if st.session_state.processing and not st.session_state.recording:
    st.markdown("---")
    st.subheader("🔄 Processing...")
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Diarization
        if enable_diarization and st.session_state.audio_file:
            status.text("👥 Identifying speakers...")
            progress_bar.progress(33)
            
            diarizer = SpeakerDiarizer(use_pyannote=True)
            speaker_segments = diarizer.diarize_audio(st.session_state.audio_file)
            diarized_segments = diarizer.merge_with_transcript(
                speaker_segments,
                st.session_state.transcript_segments
            )
        else:
            diarized_segments = []
        
        # Summarization
        status.text("🧠 Generating summary...")
        progress_bar.progress(66)
        
        # Get full text
        if diarized_segments:
            full_text = "\n".join([f"{s.speaker_id}: {s.text}" for s in diarized_segments])
        else:
            full_text = " ".join([s.text for s in st.session_state.transcript_segments])
        
        # Generate summary
        summarizer = MeetingSummarizer(provider="groq")
        st.session_state.summary = summarizer.summarize(full_text, style=meeting_type.lower())
        
        progress_bar.progress(100)
        status.text("✅ Complete!")
        time.sleep(1)
        
        st.session_state.processing = False
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
        st.session_state.processing = False

# Summary Display
if st.session_state.summary:
    st.markdown("---")
    st.subheader("🤖 AI Summary")
    
    # Display summary
    summary_md = st.session_state.summary.to_markdown()
    st.markdown(summary_md)
    
    # Export buttons
    st.markdown("---")
    st.subheader("📤 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 PDF", use_container_width=True):
            try:
                export_manager = ExportManager()
                pdf_path = export_manager.export_pdf(st.session_state.summary, meeting_name)
                st.success(f"✅ PDF: {pdf_path}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        md_content = st.session_state.summary.to_markdown()
        st.download_button(
            label="📝 Markdown",
            data=md_content,
            file_name=f"{meeting_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col3:
        if st.button("📧 Email", disabled=not email_recipient, use_container_width=True):
            if email_recipient:
                try:
                    email_sender = EmailSender()
                    email_sender.send_summary(email_recipient, st.session_state.summary, meeting_name)
                    st.success(f"✅ Sent to {email_recipient}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    Made with ❤️ • AI Meeting Summarizer v1.0
</div>
""", unsafe_allow_html=True)