AI Meeting Summarizer 

Infosys Springboard AI Virtual Internship 

📌 Overview

The AI Meeting Summarizer is a fully modular, production-grade system that converts real-time meeting audio into structured insights.
It performs:

Speech-to-Text (STT)

Speaker Diarization (Who spoke when)

Topic-wise Summarization using LLaMA-3.3 70B (Groq API)

PDF export of meeting notes

Automated email delivery

Streamlit-based user interface

The project is implemented with an enterprise-style, milestone-driven architecture emphasizing separation of concerns, testability, and clarity.

✨ Key Capabilities
🎙 Real-Time Speech Recognition

Whisper-based STT

16kHz continuous audio streaming

Handles accents and noisy environments

Fallback lightweight STT pipeline (if Whisper GPU acceleration unavailable)

👥 Speaker Diarization

Identifies individual speakers

Merges segments into speaker-aware transcript

Lightweight fallback diarizer for offline mode

🧠 AI-Powered Summaries

Uses Groq LLaMA-3.3 70B for:

Concise summary

Key decisions

Action points

Highlights & agenda tracking

Fully prompt-engineered for meeting workflows

📄 Export & Reporting

Automatically generates:

PDF summary

Plain text summary

Structured JSON output

Ready for integration with documentation workflows

📩 Auto Email Delivery

Sends meeting notes and attachments to configured emails

Uses secure SMTP environment variables


🛠 Tech Stack
Core Libraries
Feature	Technology
Speech-to-Text	Whisper (OpenAI)
Speaker Diarization	pyannote (fallback implemented)
Summarization	Groq LLaMA-3.3 70B
Frontend	Streamlit
Audio Processing	sounddevice, numpy
PDF Generation	ReportLab
Email System	smtplib (secure SMTP)
Configuration	python-dotenv

📁 Future Enhancements

Multi-language support

Real-time speaker recognition (voice embeddings)

Integration with calendars & task managers

Cloud deployment (AWS / Azure)

Meeting sentiment analysis