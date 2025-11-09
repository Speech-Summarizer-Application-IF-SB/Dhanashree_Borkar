#!/bin/bash

# Create project structure
mkdir -p ai-meeting-summarizer/{src,data,models,tests,docs,outputs}
cd ai-meeting-summarizer

# Create subdirectories
mkdir -p src/{audio,stt,diarization,summarization,ui,utils}
mkdir -p data/{audio_samples,transcripts,summaries}
mkdir -p outputs/{logs,exports}

# Create initial Python files
touch src/__init__.py
touch src/audio/audio_capture.py
touch src/stt/transcriber.py
touch src/diarization/speaker_identifier.py
touch src/summarization/summarizer.py
touch src/ui/streamlit_app.py
touch src/utils/config.py
touch src/utils/helpers.py

# Create requirements.txt
cat > requirements.txt << 'EOF'
# Core Audio Processing
pyaudio==0.2.14
sounddevice==0.4.6
soundfile==0.12.1
numpy==1.24.3
scipy==1.11.4

# Speech-to-Text
openai-whisper==20231117
vosk==0.3.45
faster-whisper==1.0.0

# Speaker Diarization
pyannote.audio==3.1.1
torch==2.1.2
torchaudio==2.1.2

# LLM and Summarization
groq==0.4.1
transformers==4.36.2
langchain==0.1.0
tiktoken==0.5.2

# UI and API
streamlit==1.29.0
streamlit-webrtc==0.47.1
streamlit-audiorecorder==0.0.5

# Evaluation & Metrics
jiwer==3.0.3
rouge-score==0.1.2
nltk==3.8.1

# Export and Communication
reportlab==4.0.8
markdown2==2.4.12
python-docx==1.1.0
smtplib  # Built-in, no install needed
email-validator==2.1.0

# Utilities
python-dotenv==1.0.0
pydantic==2.5.3
loguru==0.7.2
tqdm==4.66.1
pandas==2.1.4
pyarrow==14.0.2
asyncio  # Built-in

# Development
pytest==7.4.3
black==23.12.1
flake8==6.1.0
ipykernel==6.27.1
jupyter==1.0.0
EOF

# Create .env template
cat > .env.example << 'EOF'
# API Keys
GROQ_API_KEY=your_groq_api_key_here
HUGGINGFACE_TOKEN=your_hf_token_here

# Email Configuration
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Model Paths
WHISPER_MODEL=base
VOSK_MODEL_PATH=./models/vosk-model-en-us-0.22

# App Configuration
SAMPLE_RATE=16000
CHUNK_DURATION=30  # seconds
MIN_SPEAKER_DURATION=0.5  # minimum duration for speaker segment
EOF

# Create README
cat > README.md << 'EOF'
# 🎯 AI Live Meeting Summarizer

A real-time meeting transcription and summarization tool that uses cutting-edge AI to:
- Transcribe live audio with speaker identification
- Generate intelligent summaries using LLMs
- Export and email meeting notes instantly

## Features
- 🎙️ Real-time speech-to-text with <15% WER
- 👥 Automatic speaker diarization
- 🤖 AI-powered summarization
- 📧 One-click email and export
- 📊 Beautiful Streamlit interface

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment: `cp .env.example .env` and add your API keys
3. Run the app: `streamlit run src/ui/streamlit_app.py`
EOF

echo "✅ Project structure created successfully!"
echo "📁 Navigate to: cd ai-meeting-summarizer"
echo "🔧 Next: Create virtual environment and install dependencies"