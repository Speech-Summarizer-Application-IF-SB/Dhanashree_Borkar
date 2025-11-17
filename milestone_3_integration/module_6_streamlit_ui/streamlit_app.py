"""
AI Meeting Summarizer - Streamlit Application
Clean, working version with pipeline integration
"""

import streamlit as st
import time
from pathlib import Path
from datetime import datetime
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import modules
from milestone_3_integration.module_5_backend_integration.pipeline import MeetingPipeline
from milestone_4_finalization.module_7_testing_optimization.ExportManager import ExportManager
from milestone_4_finalization.module_7_testing_optimization.email_sender import EmailSender

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI Meeting Summarizer",
    page_icon="🎙️",
    layout="wide"
)

# ==================== INITIALIZE ====================
def init_session_state():
    """Initialize session state variables"""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = MeetingPipeline()
    if 'transcript_segments' not in st.session_state:
        st.session_state.transcript_segments = []
    if 'meeting_start_time' not in st.session_state:
        st.session_state.meeting_start_time = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False

init_session_state()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.title("⚙️ Settings")
    st.markdown("---")
    
    meeting_name = st.text_input("Meeting Name", "Team Meeting")
    meeting_type = st.selectbox("Meeting Type", ["general", "standup", "brainstorm", "review"])
    
    st.markdown("---")
    st.subheader("🎤 STT Settings")
    stt_model = st.selectbox("Model", ["whisper", "vosk"])
    whisper_size = st.selectbox("Whisper Size", ["tiny", "base", "small", "medium"])
    
    st.markdown("---")
    enable_diarization = st.checkbox("Enable Speaker ID", value=True)
    email_recipient = st.text_input("Email To", placeholder="email@example.com")

# ==================== HEADER ====================
st.title("🎙️ AI Meeting Summarizer")
st.markdown("**Real-time transcription • Speaker identification • AI summaries**")
st.markdown("---")

# ==================== RECORDING CONTROLS ====================
st.subheader("🎙️ Recording Controls")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("🔴 Start", disabled=st.session_state.pipeline.is_recording, use_container_width=True):
        try:
            # Callback for transcript updates
            def on_transcript(segment):
                st.session_state.transcript_segments.append(segment)
            
            # Start recording
            success = st.session_state.pipeline.start_recording(
                callback=on_transcript,
                model_type=stt_model,
                model_size=whisper_size
            )
            
            if success:
                st.session_state.meeting_start_time = datetime.now()
                st.session_state.transcript_segments = []
                st.success("🎙️ Recording started!")
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

with col2:
    if st.button("⏹️ Stop", disabled=not st.session_state.pipeline.is_recording, use_container_width=True):
        try:
            # Stop recording
            audio_file = st.session_state.pipeline.stop_recording()
            
            if audio_file:
                st.session_state.processing = True
                st.success("⏹️ Recording stopped!")
                st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error: {e}")

with col3:
    if st.session_state.pipeline.is_recording and st.session_state.meeting_start_time:
        duration = int((datetime.now() - st.session_state.meeting_start_time).total_seconds())
        st.info(f"🔴 RECORDING - {duration // 60:02d}:{duration % 60:02d}")
    else:
        st.info("⚪ NOT RECORDING")

# Auto-refresh during recording
if st.session_state.pipeline.is_recording:
    time.sleep(1)
    st.rerun()

# ==================== METRICS ====================
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

# ==================== LIVE TRANSCRIPT ====================
st.markdown("---")
st.subheader("💬 Live Transcript")

if len(st.session_state.transcript_segments) > 0:
    with st.container():
        for segment in st.session_state.transcript_segments[-10:]:
            with st.chat_message("assistant"):
                st.write(segment.text)
else:
    st.info("👆 Start recording to see live transcription")

# ==================== PROCESSING ====================
if st.session_state.processing:
    st.markdown("---")
    st.subheader("🔄 Processing Meeting...")
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Process meeting
        status.text("🔄 Processing...")
        progress_bar.progress(50)
        
        summary = st.session_state.pipeline.process_meeting(
            enable_diarization=enable_diarization,
            meeting_type=meeting_type
        )
        
        progress_bar.progress(100)
        status.text("✅ Complete!")
        time.sleep(1)
        
        st.session_state.processing = False
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Processing error: {e}")
        st.session_state.processing = False

# ==================== SUMMARY DISPLAY ====================
results = st.session_state.pipeline.get_results()

if results['summary']:
    st.markdown("---")
    st.subheader("🤖 AI Summary")
    
    # Display summary
    summary_md = results['summary'].to_markdown()
    st.markdown(summary_md)
    
    # Export buttons
    st.markdown("---")
    st.subheader("📤 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 PDF", use_container_width=True):
            try:
                export_manager = ExportManager()
                pdf_path = export_manager.export_pdf(results['summary'], meeting_name)
                st.success(f"✅ PDF: {pdf_path.name}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with col2:
        md_content = results['summary'].to_markdown()
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
                    success = email_sender.send_summary(
                        email_recipient,
                        results['summary'],
                        meeting_name
                    )
                    if success:
                        st.success(f"✅ Sent to {email_recipient}")
                    else:
                        st.error("❌ Email not configured. Check .env file")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.9rem;'>
    Made with ❤️ • AI Meeting Summarizer v1.0
</div>
""", unsafe_allow_html=True)