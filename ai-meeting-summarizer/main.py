"""
AI Meeting Summarizer - Streamlit Application
Main UI for real-time meeting transcription and summarization
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


import streamlit as st
import numpy as np
import time
import json
from pathlib import Path
from datetime import datetime
import threading
import queue
import sys
import os

# Add project src directory to path so imports like `from audio.audio_capture import ...` resolve
# (main.py lives in the project root; the packages are under `src/`)
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, "src"))

# Import our modules
from src.audio.audio_capture import AudioRecorder
from src.stt.realtime_stt import RealTimeTranscriber, TranscriptionSegment
from src.diarization.speaker_identifier import SpeakerDiarizer
from src.summarization.summarizer import MeetingSummarizer
from src.summarization.ExportManager import ExportManager
from src.utils.config import get_config
from src.utils.email_sender import EmailSender


# Page configuration
st.set_page_config(
    page_title="AI Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container */
    .main {
        padding-top: 0rem;
    }
    
    /* Recording indicator */
    .recording-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 1.5s infinite;
    }
    
    .recording-active {
        background-color: #ff4444;
    }
    
    .recording-inactive {
        background-color: #888888;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    /* Volume meter */
    .volume-meter {
        height: 8px;
        background: linear-gradient(to right, 
            #00ff00 0%, #00ff00 60%, 
            #ffff00 60%, #ffff00 80%, 
            #ff0000 80%, #ff0000 100%);
        border-radius: 4px;
        overflow: hidden;
    }
    
    /* Transcript box */
    .transcript-box {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        color: #fff;
    }
    
    /* Speaker labels */
    .speaker-label {
        font-weight: bold;
        color: #4CAF50;
        margin-top: 10px;
    }
    
    /* Action buttons */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        font-weight: 600;
    }
    
    /* Status card */
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 20px;
        color: white;
        margin-bottom: 20px;
    }
    
    /* Summary sections */
    .summary-section {
        background-color: #2d2d2d;
        border-left: 4px solid #4CAF50;
        padding: 15px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: App Configuration ---
st.sidebar.title("Settings")
config = get_config()
meeting_name = st.sidebar.text_input("Meeting Name", "Team Sync")
email_option = st.sidebar.text_input("Send Summary To (Email)", "")

# --- Main Layout ---
st.title("🎙️ AI Meeting Summarizer")
st.markdown(f"#### Meeting: {meeting_name}")

# Recording Controls
st.subheader("Recording Controls")
col1, col2 = st.columns(2)
start_button = col1.button("Start Recording")
stop_button = col2.button("Stop Recording")

recording_indicator = st.empty()

# Transcript Section
st.subheader("Live Transcript")
transcript_box = st.empty()

# Speaker Diarization Section
st.subheader("Speaker Diarization")
speaker_box = st.empty()

# Summary Section
st.subheader("Meeting Summary")
summary_box = st.empty()

# Export Section
st.subheader("Export Options")
export_col1, export_col2 = st.columns(2)
export_txt = export_col1.button("Export Transcript (TXT)")
export_pdf = export_col2.button("Export Summary (PDF)")

# --- Placeholder / Real-time Logic ---
# Initialize modules
audio_recorder = AudioRecorder()
transcriber = RealTimeTranscriber()
diarizer = SpeakerDiarizer()
summarizer = MeetingSummarizer()
email_sender = EmailSender()
export_manager = ExportManager()

# State variables
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = []
if 'summary' not in st.session_state:
    st.session_state.summary = ""

def start_recording_fn():
    st.session_state.recording = True
    audio_recorder.start_recording()
    recording_indicator.markdown('<div class="recording-indicator recording-active"></div> Recording...', unsafe_allow_html=True)

def stop_recording_fn():
    st.session_state.recording = False
    audio_recorder.stop_recording()
    recording_indicator.markdown('<div class="recording-indicator recording-inactive"></div> Not Recording', unsafe_allow_html=True)
    # Generate summary after recording
    st.session_state.summary = summarizer.summarize(st.session_state.transcript)
    summary_box.markdown(f'<div class="summary-section">{st.session_state.summary}</div>', unsafe_allow_html=True)
    # Send email if provided
    if email_option:
        email_sender.send(email_option, st.session_state.summary)

if start_button:
    start_recording_fn()

if stop_button:
    stop_recording_fn()

# Live transcription loop (simplified)
if st.session_state.recording:
    new_segment = transcriber.get_segment()  # blocking or non-blocking
    if new_segment:
        st.session_state.transcript.append(f"{new_segment.speaker}: {new_segment.text}")
        # Update transcript box
        transcript_box.markdown('<div class="transcript-box">' + "<br>".join(st.session_state.transcript) + '</div>', unsafe_allow_html=True)
        # Update speaker diarization (placeholder)
        speaker_box.markdown('<br>'.join([f'<span class="speaker-label">{s.speaker}</span>: {s.text}' for s in st.session_state.transcript]), unsafe_allow_html=True)

# Export buttons
if export_txt:
    export_manager.export_transcript_txt(st.session_state.transcript, meeting_name)
if export_pdf:
    export_manager.export_summary_pdf(st.session_state.summary, meeting_name)
