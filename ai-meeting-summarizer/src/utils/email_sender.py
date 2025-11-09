"""
Email Sender Module
Sends meeting summaries via email with attachments
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class EmailSender:
    """
    Handles sending meeting summaries via email
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        email_address: Optional[str] = None,
        email_password: Optional[str] = None
    ):
        self.smtp_host = smtp_host or os.getenv("EMAIL_HOST", "smtp.gmail.com")
        self.smtp_port = smtp_port or int(os.getenv("EMAIL_PORT", "587"))
        self.email_address = email_address or os.getenv("EMAIL_ADDRESS")
        self.email_password = email_password or os.getenv("EMAIL_PASSWORD")
        
        # Validate configuration
        if not self.email_address or not self.email_password:
            print("⚠️ Email credentials not configured")
            print("   Set EMAIL_ADDRESS and EMAIL_PASSWORD in your .env file")
    
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return bool(self.email_address and self.email_password)
    
    def send_summary(
        self,
        to_email: str,
        summary,  # MeetingSummary object
        meeting_name: str,
        attach_files: Optional[list] = None
    ) -> bool:
        """
        Send meeting summary via email
        
        Args:
            to_email: Recipient email address
            summary: MeetingSummary object
            meeting_name: Name of the meeting
            attach_files: Optional list of file paths to attach
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            print("❌ Email not configured. Cannot send.")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Meeting Summary: {meeting_name}"
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Date'] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            
            # Create email body
            html_body = self._create_html_email(summary, meeting_name)
            text_body = summary.to_markdown()
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Attach files if provided
            if attach_files:
                for file_path in attach_files:
                    self._attach_file(msg, file_path)
            
            # Send email
            print(f"📧 Sending email to {to_email}...")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Email sent successfully to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("❌ Email authentication failed. Check your credentials.")
            print("   For Gmail: Use an App Password, not your regular password")
            print("   Generate at: https://myaccount.google.com/apppasswords")
            return False
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False
    
    def _create_html_email(self, summary, meeting_name: str) -> str:
        """Create beautiful HTML email body"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .section {{
                    background: #f8f9fa;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                }}
                .section h2 {{
                    color: #667eea;
                    margin-top: 0;
                    font-size: 20px;
                }}
                ul {{
                    padding-left: 20px;
                }}
                li {{
                    margin: 8px 0;
                }}
                .metadata {{
                    background: #e9ecef;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .metadata p {{
                    margin: 5px 0;
                    color: #666;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 2px solid #e9ecef;
                    color: #999;
                    font-size: 14px;
                }}
                .action-item {{
                    background: #fff3cd;
                    padding: 10px;
                    margin: 5px 0;
                    border-radius: 5px;
                    border-left: 3px solid #ffc107;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎙️ {meeting_name}</h1>
                <p>Meeting Summary Report</p>
            </div>
            
            <div class="metadata">
                <p><strong>📅 Date:</strong> {summary.timestamp.strftime('%A, %B %d, %Y at %I:%M %p')}</p>
                <p><strong>⏱️ Duration:</strong> {summary.duration:.1f} minutes</p>
                {f'<p><strong>👥 Participants:</strong> {", ".join(summary.participants)}</p>' if summary.participants else ''}
            </div>
            
            <div class="section">
                <h2>📋 Summary</h2>
                <p>{summary.summary}</p>
            </div>
        """
        
        if summary.key_points:
            html += """
            <div class="section">
                <h2>🔑 Key Points</h2>
                <ul>
            """
            for point in summary.key_points:
                html += f"<li>{point}</li>"
            html += "</ul></div>"
        
        if summary.action_items:
            html += """
            <div class="section">
                <h2>✅ Action Items</h2>
            """
            for item in summary.action_items:
                html += f'<div class="action-item">☐ {item}</div>'
            html += "</div>"
        
        if summary.decisions:
            html += """
            <div class="section">
                <h2>⚖️ Decisions Made</h2>
                <ul>
            """
            for decision in summary.decisions:
                html += f"<li>{decision}</li>"
            html += "</ul></div>"
        
        if summary.speaker_stats:
            html += """
            <div class="section">
                <h2>💬 Speaking Time</h2>
                <ul>
            """
            for speaker, percentage in summary.speaker_stats.items():
                html += f"<li><strong>{speaker}:</strong> {percentage:.1f}%</li>"
            html += "</ul></div>"
        
        html += """
            <div class="footer">
                <p>📧 This summary was generated automatically by AI Meeting Summarizer</p>
                <p>Powered by Whisper, PyAnnote, and Groq LLM</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _attach_file(self, msg: MIMEMultipart, file_path: Path):
        """Attach a file to the email"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                print(f"⚠️ Attachment not found: {file_path}")
                return
            
            # Read file
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            # Encode file
            encoders.encode_base64(part)
            
            # Add header
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            
            # Attach to message
            msg.attach(part)
            print(f"📎 Attached: {file_path.name}")
            
        except Exception as e:
            print(f"⚠️ Could not attach {file_path}: {e}")
    
    def send_test_email(self, to_email: str) -> bool:
        """Send a test email to verify configuration"""
        if not self.is_configured():
            return False
        
        try:
            msg = MIMEMultipart()
            msg['Subject'] = "Test Email - AI Meeting Summarizer"
            msg['From'] = self.email_address
            msg['To'] = to_email
            
            body = """
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>✅ Test Email Successful!</h2>
                <p>Your email configuration is working correctly.</p>
                <p>You can now send meeting summaries via email.</p>
                <br>
                <p style="color: #666; font-size: 14px;">
                    - AI Meeting Summarizer
                </p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)
            
            print(f"✅ Test email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Test email failed: {e}")
            return False


def test_email():
    """Test email functionality"""
    print("🎯 Testing Email Sender")
    print("=" * 50)
    
    email_sender = EmailSender()
    
    if not email_sender.is_configured():
        print("\n❌ Email not configured!")
        print("\n📝 To configure email:")
        print("1. Open your .env file")
        print("2. Add these lines:")
        print("   EMAIL_ADDRESS=your_email@gmail.com")
        print("   EMAIL_PASSWORD=your_app_password")
        print("\n💡 For Gmail:")
        print("   - Don't use your regular password")
        print("   - Generate an App Password at:")
        print("     https://myaccount.google.com/apppasswords")
        return
    
    # Get test email
    test_email_address = input("\n📧 Enter test email address: ").strip()
    
    if not test_email_address:
        print("❌ No email provided")
        return
    
    # Send test email
    print("\n📨 Sending test email...")
    success = email_sender.send_test_email(test_email_address)
    
    if success:
        print("\n✅ Email configuration is working!")
        print("💡 Check your inbox (and spam folder)")
    else:
        print("\n❌ Email test failed")
        print("💡 Check your email credentials in .env file")


if __name__ == "__main__":
    test_email()